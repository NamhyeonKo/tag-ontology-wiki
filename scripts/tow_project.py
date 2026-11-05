"""Project-session operations that write approved content to a TOW vault."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any, Literal, cast

from tow_core import CliError, ConfigError, body_bytes, run_cli, serialize_entries, tow_kind, write_text_atomic

NOTE_FOLDERS = ("projects", "areas", "resources", "inbox")
DOCUMENTS = ".tow/documents.json"
LOCAL_DOCUMENTS = ".tow/documents.local.json"
PROJECT_DICTIONARY = ".tow/tag-dictionary.json"


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
        if tracked is None:
            raise ConfigError("can't determine whether .tow contains tracked files; local mode is unavailable")
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


def cmd_project_tag(project: Path, vault: Path, vault_cfg: Mapping[str, str], changes: Path, apply: bool) -> int:
    """Preview or apply an approved change set to project document metadata and the project dictionary.

    Writes only project .tow/ files; project documents and the vault dictionary are never written.
    """
    project_root = project.resolve()
    if tow_kind(project_root) != "project":
        raise ConfigError(f"not a TOW project; run tow project init first: {project_root}")
    if (project_root / ".tow").resolve() != project_root / ".tow":
        raise ConfigError(f"project .tow must be a folder inside the project: {project_root}")
    documents, concepts = _read_changes(changes)
    vault_tags = _read_object(vault / vault_cfg["tagDictionary"])
    old = {name: _read_object(project_root / name, missing_ok=True) for name in (DOCUMENTS, LOCAL_DOCUMENTS)}
    old_dictionary = _read_object(project_root / PROJECT_DICTIONARY, missing_ok=True)

    project_only = {key: value for key, value in old_dictionary.items() if key not in vault_tags}
    # subset resolves names ignoring case and through aliases, so the vault already has those concepts.
    vault_names = {name.lower() for key, entry in vault_tags.items() for name in [key, *_strings(entry, "aliases")]}
    for tag, concept in concepts.items():
        if tag.lower() in vault_names:
            raise ConfigError(f"concept already in the vault dictionary: {tag}; attach the vault concept instead")
        existing = project_only.get(tag)
        project_only[tag] = {**(cast(dict[str, Any], existing) if isinstance(existing, dict) else {}), **concept}

    mode = project_mode(project_root)
    new = {name: dict(entries) for name, entries in old.items()}
    for key, tags in documents.items():
        path = _document_path(project_root, key)
        for tag in tags:
            if tag not in vault_tags and tag not in project_only:
                raise ConfigError(f"unknown tag {tag!r} for {key}: not in the vault or project dictionary")
        for entries in new.values():
            entries.pop(key, None)
        if not tags:
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except FileNotFoundError:
            raise ConfigError(f"project document not found: {key}") from None
        except OSError as e:
            raise ConfigError(f"can't read project document {key}: {e}") from e
        local = mode == "shared" and not _tracked(project_root, key)
        new[LOCAL_DOCUMENTS if local else DOCUMENTS][key] = {"tags": tags, "sha256": digest}
    if (
        mode == "shared"
        and new[LOCAL_DOCUMENTS] != old[LOCAL_DOCUMENTS]
        and git(project_root, "check-ignore", "-q", LOCAL_DOCUMENTS) is None
    ):
        raise ConfigError(
            f"{LOCAL_DOCUMENTS} is not ignored by Git; add it to the Git exclude file "
            "(git rev-parse --git-path info/exclude) before tagging untracked or ignored files"
        )

    used = {tag for entries in new.values() for entry in entries.values() for tag in _strings(entry, "tags")}
    broader = {tag for entry in project_only.values() for tag in _strings(entry, "broader")}
    request = sorted(tag for tag in used | broader if tag in vault_tags)
    dictionary = _subset(vault, vault_cfg, request) if request else {}
    dictionary.update(project_only)
    if dictionary != old_dictionary:
        _check(project_root, serialize_entries(dictionary))

    new[PROJECT_DICTIONARY] = dictionary
    old[PROJECT_DICTIONARY] = old_dictionary
    lines = [
        line for name in (DOCUMENTS, LOCAL_DOCUMENTS, PROJECT_DICTIONARY) for line in _diff(name, old[name], new[name])
    ]
    if not lines:
        print("no changes")
        return 0
    if not apply:
        for line in lines:
            print(f"would {line}")
        return 0
    # ponytail: three independent atomic replaces, not one transaction; rerunning the same changes file
    # converges because each documents value is the complete tag list. Dictionary first, so a partial
    # write never leaves document tags missing from it.
    for name in (PROJECT_DICTIONARY, DOCUMENTS, LOCAL_DOCUMENTS):
        if new[name] != old[name]:
            write_text_atomic(project_root / name, serialize_entries(new[name]))
            print(f"updated {name}")
    return 0


def _read_object(path: Path, missing_ok: bool = False) -> dict[str, Any]:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if missing_ok:
            return {}
        raise ConfigError(f"can't find {path}") from None
    except (OSError, ValueError) as e:
        raise ConfigError(f"can't read {path}: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must hold a JSON object")
    return cast(dict[str, Any], raw)


def _read_changes(path: Path) -> tuple[dict[str, list[str]], dict[str, dict[str, Any]]]:
    raw = _read_object(path)
    documents: object = raw.get("documents")
    concepts: object = raw.get("concepts", {})
    if (
        set(raw) - {"documents", "concepts"}
        or not isinstance(documents, dict)
        or not isinstance(concepts, dict)
        or not all(_is_strings(tags) for tags in cast(dict[str, object], documents).values())
        or not all(
            isinstance(concept, dict)
            and set(cast(dict[str, object], concept)) == {"description", "broader"}
            and isinstance(cast(dict[str, object], concept)["description"], str)
            and _is_strings(cast(dict[str, object], concept)["broader"])
            for concept in cast(dict[str, object], concepts).values()
        )
    ):
        raise ConfigError(
            f"invalid changes file {path}: expected "
            '{"documents": {path: [tag, ...]}, "concepts": {tag: {"description": str, "broader": [tag, ...]}}}'
        )
    return cast(dict[str, list[str]], documents), cast(dict[str, dict[str, Any]], concepts)


def _is_strings(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in cast(list[object], value))


def _strings(entry: object, field: str) -> list[str]:
    """A string-list field of a stored entry; malformed entries give nothing (check reports them)."""
    value = cast(dict[str, object], entry).get(field) if isinstance(entry, dict) else None
    return cast(list[str], value) if _is_strings(value) else []


def _document_path(project_root: Path, key: str) -> Path:
    posix = PurePosixPath(key)
    path = project_root / key
    if (
        "\\" in key
        or posix.as_posix() != key
        or posix.is_absolute()
        or ".." in posix.parts
        or not path.resolve().is_relative_to(project_root)
    ):
        raise ConfigError(f"project document must be a normalized relative path inside the project: {key}")
    if posix.suffix != ".md":
        raise ConfigError(f"project document must be a .md file: {key}")
    return path


def _tracked(project_root: Path, key: str) -> bool:
    listed = git(project_root, "--literal-pathspecs", "ls-files", "--", key)
    if listed is None:
        raise ConfigError(f"can't determine whether {key} is tracked by Git")
    return bool(listed)


def _cli_json(args: list[str]) -> tuple[bool, dict[str, Any]]:
    """Run the tag-ontology CLI with --json; return whether it succeeded and its result document."""
    result = run_cli(args, capture=True)
    failure = result.stderr.strip() or f"tag-ontology {args[0]} exited with code {result.returncode} without JSON"
    if result.returncode not in (0, 1):
        raise CliError(failure)
    try:
        data: object = json.loads(result.stdout)
    except ValueError:
        raise CliError(failure) from None
    if not isinstance(data, dict):
        raise CliError(failure)
    return result.returncode == 0, cast(dict[str, Any], data)


def _errors(data: Mapping[str, Any]) -> str:
    return "; ".join(str(issue["message"]) for issue in data.get("issues", []) if issue.get("severity") == "error")


def _subset(vault: Path, vault_cfg: Mapping[str, str], tags: list[str]) -> dict[str, Any]:
    args = ["subset", *tags, "--root", str(vault), "--dictionary", vault_cfg["tagDictionary"], "--names", "kebab"]
    ok, data = _cli_json([*args, "--json"])
    dictionary: object = data.get("dictionary")
    if not ok or not isinstance(dictionary, dict):
        raise ConfigError(f"tag-ontology subset of the vault dictionary failed: {_errors(data)}")
    return cast(dict[str, Any], dictionary)


def _check(project_root: Path, text: str) -> None:
    """Validate a candidate project dictionary from a temporary file before it replaces the real one."""
    with tempfile.TemporaryDirectory() as folder:
        candidate = Path(folder) / "tag-dictionary.json"
        candidate.write_text(text, encoding="utf-8")
        ok, data = _cli_json(["check", "--root", str(project_root), "--dictionary", str(candidate), "--json"])
    if not ok:
        raise ConfigError(f"the new project dictionary fails tag-ontology check: {_errors(data)}")


def _diff(name: str, before: Mapping[str, object], after: Mapping[str, object]) -> list[str]:
    lines: list[str] = []
    for key in sorted(before.keys() | after.keys()):
        if key not in after:
            lines.append(f"remove {key} from {name}")
        elif key not in before:
            lines.append(f"add {key} to {name}")
        elif before[key] != after[key]:
            lines.append(f"update {key} in {name}")
    return lines


def _remove_empty_dirs(paths: list[Path]) -> None:
    for path in reversed(paths):
        try:
            path.rmdir()
        except OSError:
            break
