"""Project-session operations that write approved content to a TOW vault."""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from tow_core import ConfigError, body_bytes, serialize_entries, write_text_atomic

NOTE_FOLDERS = ("projects", "areas", "resources", "inbox")


def cmd_send(
    vault: Path,
    cfg: Mapping[str, str],
    draft: Path,
    dest: str,
    source: Path | None,
    transformed: bool,
    apply: bool,
) -> int:
    """Preview or create a new vault note from an approved project draft."""
    root = vault.resolve()
    relative = Path(dest)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.parts[0] not in {cfg[key] for key in NOTE_FOLDERS}
        or ".." in relative.parts
        or len(relative.parts) < 2
    ):
        raise ConfigError("send destination must be a vault-relative file under a configured note folder")
    target = root / relative
    note_folder = (root / relative.parts[0]).resolve()
    if (
        not note_folder.is_relative_to(root)
        or not target.parent.resolve().is_relative_to(note_folder)
        or not target.resolve().is_relative_to(note_folder)
    ):
        raise ConfigError(f"send destination must stay inside its configured note folder: {dest}")

    if source is None:
        raise ConfigError("send requires --source")
    try:
        content = draft.read_bytes()
        source_content = source.read_bytes()
        if not transformed and body_bytes(content) != source_content:
            raise ConfigError("send draft body does not match the source")
    except OSError as e:
        raise ConfigError(f"send can't read its input: {e}") from e

    if not apply:
        print(f"would create {dest}")
        return 0

    missing: list[Path] = []
    parent = target.parent
    while not parent.exists():
        missing.append(parent)
        parent = parent.parent
    created_dirs: list[Path] = []
    created_identity: tuple[int, int] | None = None
    try:
        for folder in reversed(missing):
            try:
                folder.mkdir()
            except FileExistsError:
                if not folder.is_dir():
                    raise
            else:
                created_dirs.append(folder)
        if not target.parent.resolve().is_relative_to(note_folder) or not target.resolve().is_relative_to(note_folder):
            raise ConfigError(f"send destination must stay inside its configured note folder: {dest}")
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o666)
        info = os.fstat(fd)
        created_identity = (info.st_dev, info.st_ino)
        with os.fdopen(fd, "wb") as output:
            output.write(content)
        if target.read_bytes() != content:
            raise ConfigError(f"send verification failed: {dest}")
    except BaseException:
        try:
            if created_identity is not None:
                try:
                    info = target.lstat()
                except FileNotFoundError:
                    pass
                else:
                    if (info.st_dev, info.st_ino) == created_identity:
                        target.unlink()
        finally:
            _remove_empty_dirs(created_dirs)
        raise
    print(f"created {dest}")
    return 0


def git(cwd: Path, *args: str) -> str | None:
    """Run Git in cwd and return stripped stdout, or None when unavailable or unsuccessful."""
    try:
        result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def exclude_target(project: Path) -> tuple[Path, str] | None:
    """Return the repository-local exclude file and a root-relative pattern for this project's .tow folder."""
    toplevel_text = git(project, "rev-parse", "--show-toplevel")
    exclude_text = git(project, "rev-parse", "--git-path", "info/exclude")
    if toplevel_text is None or exclude_text is None:
        return None
    toplevel = Path(toplevel_text).resolve()
    project_root = project.resolve()
    try:
        relative = project_root.relative_to(toplevel)
    except ValueError:
        return None
    pattern = f"/{relative.as_posix() + '/' if relative.parts else ''}.tow/"
    exclude_path = Path(exclude_text)
    if not exclude_path.is_absolute():
        exclude_path = project_root / exclude_path
    return exclude_path.resolve(), pattern


def project_mode(project: Path) -> Literal["local", "shared", "none"]:
    """Return local when config is ignored, shared in Git otherwise, or none outside Git."""
    if git(project, "rev-parse", "--show-toplevel") is None:
        return "none"
    return "local" if git(project, "check-ignore", "-q", ".tow/config.json") is not None else "shared"


def cmd_project_init(
    project: Path,
    vault: Path,
    vault_cfg: Mapping[str, str],
    mode: Literal["local", "shared"],
    excludes: list[str],
    apply: bool,
) -> int:
    """Preview or create the project metadata bundle without overwriting existing files."""
    del vault_cfg  # Project metadata never stores personal vault configuration.
    project_root = project.resolve()
    if mode not in ("local", "shared"):
        raise ConfigError(f"invalid project mode: {mode}")
    config: dict[str, object] = {"kind": "project"}
    if excludes:
        config["exclude"] = excludes
    config_text = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    manual = vault / ".tow" / "tags.md"
    try:
        manual_text = manual.read_bytes().decode("utf-8")
    except FileNotFoundError:
        manual_text = None
    except (OSError, UnicodeError) as e:
        raise ConfigError(f"can't read vault tag manual: {e}") from e
    outputs = {
        project_root / ".tow" / "config.json": config_text,
        project_root / ".tow" / "documents.json": serialize_entries({}),
        project_root / ".tow" / "tag-dictionary.json": serialize_entries({}),
    }
    if manual_text is not None:
        outputs[project_root / ".tow" / "tags.md"] = manual_text
    for path in outputs:
        if path.exists() or path.is_symlink():
            raise ConfigError(f"project init target already exists: {path.relative_to(project_root)}")
        if not path.resolve().is_relative_to(project_root):
            raise ConfigError(f"project init path must stay inside the project: {path}")

    target = exclude_target(project_root)
    if mode == "shared" and target is not None:
        ignored = [
            path
            for path in outputs
            if git(project_root, "check-ignore", "-q", path.relative_to(project_root).as_posix()) is not None
        ]
        if ignored:
            raise ConfigError("shared project metadata is ignored by Git; remove the conflicting ignore rule first")
    if mode == "local" and target is not None:
        tracked = git(project_root, "ls-files", ".tow")
        if tracked:
            raise ConfigError("local mode is unavailable while .tow contains tracked files")
    pattern: str | None = None
    exclude_original: str | None = None
    if target is not None:
        pattern = target[1]
        if mode == "shared":
            pattern = f"{pattern.rstrip('/')}/documents.local.json"
        try:
            exclude_original = target[0].read_text(encoding="utf-8")
        except FileNotFoundError:
            pass
        except OSError as e:
            raise ConfigError(f"can't read Git exclude file: {e}") from e
        existing = exclude_original or ""
        exclude_append = (
            ("" if not existing or existing.endswith("\n") else "\n") + pattern + "\n"
            if pattern not in existing.splitlines()
            else ""
        )
    else:
        exclude_append = None

    if not apply:
        for path in outputs:
            print(f"would create {path.relative_to(project_root)}")
        if manual_text is None:
            print("vault has no .tow/tags.md (run tow migrate)")
        if target is None:
            print("not in a Git repository; no exclude change")
        elif exclude_append:
            print(f"would add {pattern} to Git exclude")
        return 0

    created: list[Path] = []
    try:
        for path, text in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            write_text_atomic(path, text, exclusive=True)
            created.append(path)
            print(f"created {path.relative_to(project_root)}")
    except BaseException:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            (project_root / ".tow").rmdir()
        raise
    if manual_text is None:
        print("vault has no .tow/tags.md (run tow migrate)")
    if target is None:
        print("not in a Git repository; no exclude change")
    else:
        try:
            if exclude_append:
                target[0].parent.mkdir(parents=True, exist_ok=True)
                with target[0].open("a", encoding="utf-8", newline="") as exclude_file:
                    exclude_file.write(exclude_append)
                print(f"added {pattern} to Git exclude")
            check_path = ".tow/config.json" if mode == "local" else ".tow/documents.local.json"
            if git(project_root, "check-ignore", "-q", check_path) is None:
                raise ConfigError(f"Git exclude verification failed for {check_path}")
        except BaseException:
            for path in reversed(created):
                path.unlink(missing_ok=True)
            with contextlib.suppress(OSError):
                (project_root / ".tow").rmdir()
            if exclude_original is None:
                target[0].unlink(missing_ok=True)
            else:
                write_text_atomic(target[0], exclude_original)
            raise
    return 0


def _remove_empty_dirs(paths: list[Path]) -> None:
    for path in reversed(paths):
        try:
            path.rmdir()
        except OSError:
            break
