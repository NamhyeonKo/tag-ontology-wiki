"""Project-session operations that write approved content to a TOW vault."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any, Literal, cast

from tow_core import (
    CliError,
    ConfigError,
    body_bytes,
    run_cli,
    serialize_entries,
    tow_kind,
    vault_layout,
    write_text_atomic,
)

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
        or relative.suffix != ".md"
        or any(part.startswith(".") for part in relative.parts)
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
        if not transformed and body_bytes(content) != body_bytes(source_content):
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


def _git_run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False)
    except OSError:
        return None


def git(cwd: Path, *args: str) -> str | None:
    """Run Git in cwd and return stripped stdout, or None when unavailable or unsuccessful."""
    result = _git_run(cwd, *args)
    return result.stdout.strip() if result is not None and result.returncode == 0 else None


def _git_root(project: Path) -> Path | None:
    """Resolve the Git root, distinguishing an ordinary folder from a broken Git checkout."""
    root = project.resolve()
    result = _git_run(root, "rev-parse", "--show-toplevel")
    if result is not None and result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    marker = next((folder / ".git" for folder in (root, *root.parents) if (folder / ".git").exists()), None)
    if marker is None:
        return None
    cause = result.stderr.strip() if result is not None else "git executable is unavailable"
    if result is not None and not cause:
        cause = f"git rev-parse exited with status {result.returncode}"
    raise ConfigError(f"Git failed for project {root} ({cause}); repair Git access before continuing")


def _git_files(cwd: Path, *args: str) -> list[str]:
    """Return exact NUL-delimited Git paths or fail with Git's diagnostic."""
    result = _git_run(cwd, *args)
    if result is None:
        raise ConfigError("Git executable is unavailable; can't determine project file Git status")
    if result.returncode != 0:
        cause = result.stderr.strip() or f"git exited with status {result.returncode}"
        raise ConfigError(f"Git failed while determining project file status: {cause}")
    return [path for path in result.stdout.split("\0") if path]


def exclude_target(project: Path) -> tuple[Path, str] | None:
    """Return the repository-local exclude file and a root-relative pattern for this project's .tow folder."""
    toplevel = _git_root(project)
    if toplevel is None:
        return None
    exclude_text = git(project, "rev-parse", "--git-path", "info/exclude")
    if exclude_text is None:
        raise ConfigError("Git failed while resolving the repository-local exclude file")
    project_root = project.resolve()
    try:
        relative = project_root.relative_to(toplevel)
    except ValueError as e:
        raise ConfigError(f"project root is outside its Git repository: {project_root}") from e
    pattern = f"/{relative.as_posix() + '/' if relative.parts else ''}.tow/"
    exclude_path = Path(exclude_text)
    if not exclude_path.is_absolute():
        exclude_path = project_root / exclude_path
    return exclude_path.resolve(), pattern


def project_mode(project: Path) -> Literal["local", "shared", "none"]:
    """Return local when config is ignored, shared in Git otherwise, or none outside Git."""
    if _git_root(project) is None:
        return "none"
    result = _git_run(project, "check-ignore", "-q", ".tow/config.json")
    if result is None:
        raise ConfigError("Git executable is unavailable; can't determine project mode")
    if result.returncode not in (0, 1):
        raise ConfigError(f"Git failed while determining project mode: {result.stderr.strip()}")
    return "local" if result.returncode == 0 else "shared"


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
    if vault_layout(project_root) != "plain":
        raise ConfigError(f"project root is a vault; refusing project init: {project_root}")
    if project_root == Path.home().resolve():
        raise ConfigError("project root must not be the home directory")
    if mode not in ("local", "shared"):
        raise ConfigError(f"invalid project mode: {mode}")
    config: dict[str, object] = {"kind": "project"}
    if excludes:
        config["exclude"] = excludes
    config_text = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    layout = vault_layout(vault)
    manual_folder = "tow" if layout == "tow" else ".tow" if layout == "dot" else None
    manual = vault / manual_folder / "tags.md" if manual_folder is not None else None
    try:
        manual_text = manual.read_bytes().decode("utf-8") if manual is not None else None
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
    if target is not None:
        for path in outputs:
            result = _git_run(project_root, "check-ignore", "-q", path.relative_to(project_root).as_posix())
            if result is None:
                raise ConfigError("Git executable is unavailable; can't check project metadata ignores")
            if result.returncode not in (0, 1):
                cause = result.stderr.strip() or f"git exited with status {result.returncode}"
                raise ConfigError(f"Git failed while checking project metadata ignores: {cause}")
            if mode == "shared" and result.returncode == 0:
                raise ConfigError("shared project metadata is ignored by Git; remove the conflicting ignore rule first")
    if mode == "local" and target is not None:
        tracked = _git_files(project_root, "-c", "core.quotepath=false", "ls-files", "-z", ".tow")
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
            print("vault has no tow/tags.md (run tow migrate)")
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
        print("vault has no tow/tags.md (run tow migrate)")
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


def _project_root(project: Path) -> Path:
    root = project.resolve()
    if tow_kind(root) != "project":
        raise ConfigError(f"not a TOW project; run tow project init first: {root}")
    if (root / ".tow").resolve() != root / ".tow":
        raise ConfigError(f"project .tow must be a folder inside the project: {root}")
    if not (root / ".tow").is_dir():
        raise ConfigError(f"project .tow must be a folder: {root}")
    return root


def _document_sha256(path: Path, key: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as e:
        raise ConfigError(f"can't read project document {key}: {e}") from e


def cmd_project_tag(project: Path, vault: Path, vault_cfg: Mapping[str, str], changes: Path, apply: bool) -> int:
    """Preview or apply an approved change set to project document metadata and the project dictionary.

    Writes only project .tow/ files; project documents and the vault dictionary are never written.
    """
    project_root = _project_root(project)
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
        if not _exists_exactly(project_root, key):
            raise ConfigError(f"project document not found with this exact path and case: {key}")
        digest = _document_sha256(path, key)
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

    # Shared mode: vault concepts enter the shared dictionary only through documents.json, so tags of local
    # files stay local; new project-only concepts must come in through a tracked document for the same reason.
    sources = [new[DOCUMENTS]] if mode == "shared" else list(new.values())
    used = {tag for entries in sources for entry in entries.values() for tag in _strings(entry, "tags")}
    if mode == "shared":
        shared_concepts = _project_closure(used, project_only)
        for tag in concepts:
            if tag not in shared_concepts:
                raise ConfigError(
                    f"new concept {tag} is not used by any tracked document, and the project dictionary is "
                    "shared; tag a tracked document with it, or register it in the vault first "
                    "(from inside the vault)"
                )
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
    # ponytail: separate atomic replaces, not one transaction; rerunning the same changes file converges
    # because each documents value is the complete tag list. Additions land before removals, so an entry
    # moving between the documents files is never missing from both.
    current = dict(old)
    steps = [(PROJECT_DICTIONARY, dictionary)]
    steps += [(name, {**old[name], **new[name]}) for name in (DOCUMENTS, LOCAL_DOCUMENTS)]
    steps += [(name, new[name]) for name in (DOCUMENTS, LOCAL_DOCUMENTS)]
    for name, entries in steps:
        if entries != current[name]:
            write_text_atomic(project_root / name, serialize_entries(entries))
            current[name] = entries
    for name in (PROJECT_DICTIONARY, DOCUMENTS, LOCAL_DOCUMENTS):
        if new[name] != old[name]:
            print(f"updated {name}")
    return 0


def cmd_lookup(
    vault: Path,
    cfg: Mapping[str, str],
    project: Path | None,
    tag: str,
    exact: bool,
    vault_args: list[str],
    vault_skipped: str | None = None,
) -> int:
    """Print one concept's matching notes from the connected vault and current project.

    `vault_skipped` is why the vault has no notes to search; it is reported instead of an empty vault result.
    """
    vault_root = vault.resolve()
    vault_dictionary = _read_object(vault_root / cfg["tagDictionary"])
    results: list[dict[str, Any]] = []
    unavailable: list[str] = []
    answered = False
    query = tag.lower()

    def known(dictionary: Mapping[str, Any]) -> bool:
        return any(
            tag == name or query == name.lower() or query in {alias.lower() for alias in _strings(entry, "aliases")}
            for name, entry in dictionary.items()
        )

    def lookup(
        source: Literal["vault", "project"],
        args: list[str],
        docs: list[str] | None = None,
        excludes: list[str] | None = None,
    ) -> None:
        nonlocal answered
        try:
            ok, data = _cli_json(args)
        except (CliError, OSError) as e:
            unavailable.append(f"{source}: {e}")
            return
        if not ok:
            unavailable.append(f"{source}: {_errors(data) or 'tag-ontology show failed'}")
            return
        resolved = data.get("tag")
        note_matches = data.get("noteMatches")
        if not isinstance(resolved, str) or not isinstance(note_matches, list):
            unavailable.append(f"{source}: invalid tag-ontology show result")
            return
        place_results: list[dict[str, Any]] = []
        for raw_note in cast(list[object], note_matches):
            if not isinstance(raw_note, dict):
                unavailable.append(f"{source}: invalid tag-ontology show result")
                return
            note = cast(dict[str, Any], raw_note)
            path = note.get("path")
            matches = note.get("matches")
            if not isinstance(path, str) or not isinstance(matches, list):
                unavailable.append(f"{source}: invalid tag-ontology show result")
                return
            if (
                source == "project"
                and docs is not None
                and excludes is not None
                and not _project_path_in_scope(path, docs, excludes)
            ):
                continue
            tagged_matches: list[dict[str, str]] = []
            for raw_match in cast(list[object], matches):
                if not isinstance(raw_match, dict):
                    unavailable.append(f"{source}: invalid tag-ontology show result")
                    return
                match = cast(dict[str, Any], raw_match)
                matched_tag = match.get("tag")
                match_source = match.get("source")
                if not isinstance(matched_tag, str) or match_source not in {"tags", "bodyTags", "overlay"}:
                    unavailable.append(f"{source}: invalid tag-ontology show result")
                    return
                tagged_matches.append({"tag": matched_tag, "source": match_source})
            place_results.append(
                {
                    "source": source,
                    "path": path,
                    "matches": [
                        {
                            "tag": match["tag"],
                            "source": match["source"],
                            "kind": "exact" if match["tag"] == resolved else "narrower",
                        }
                        for match in tagged_matches
                    ],
                }
            )
        results.extend(sorted(place_results, key=lambda result: result["path"]))
        answered = True

    if known(vault_dictionary):
        if vault_skipped is None:
            lookup("vault", vault_args)
        else:
            unavailable.append(f"vault: {vault_skipped}")

    if project is not None:
        try:
            project_root = _project_root(project)
            project_config = _read_object(project_root / ".tow" / "config.json")
            docs, excludes = _project_scope(project_config)
            project_dictionary = _read_object(project_root / PROJECT_DICTIONARY, missing_ok=True)
        except (CliError, ConfigError, OSError, ValueError) as e:
            unavailable.append(f"project: {e}")
        else:
            merged_dictionary = {**project_dictionary, **vault_dictionary}
            if known(merged_dictionary):
                with tempfile.TemporaryDirectory() as folder:
                    dictionary_path = Path(folder) / "tag-dictionary.json"
                    dictionary_path.write_text(serialize_entries(merged_dictionary), encoding="utf-8")
                    args = ["show", tag, "--notes", "--json"]
                    if exact:
                        args.append("--exact")
                    args += ["--root", str(project_root), "--dictionary", str(dictionary_path), "--names", "kebab"]
                    for pattern in excludes:
                        args += ["--exclude", pattern]
                    for name in (DOCUMENTS, LOCAL_DOCUMENTS):
                        overlay = project_root / name
                        if overlay.is_file():
                            args += ["--tags-file", str(overlay)]
                    lookup("project", args, docs, excludes)

    print(json.dumps({"tag": tag, "results": results, "unavailable": unavailable}, ensure_ascii=False, indent=2))
    return 0 if answered else 1


def cmd_project_status(project: Path, vault: Path | None = None, cfg: Mapping[str, str] | None = None) -> int:
    """Report stale project document metadata and tags absent from the project dictionary."""
    root = _project_root(project)
    dictionaries = _read_object(root / PROJECT_DICTIONARY, missing_ok=True)
    vault_dictionaries: set[str] = set()
    if vault is not None and cfg is not None:
        vault_dictionaries = set(_read_object(vault / cfg["tagDictionary"]))
    else:
        print("vault dictionary not checked")
    mode = project_mode(root)
    overlays = [
        (name, _read_object(root / name, missing_ok=True))
        for name in (DOCUMENTS, LOCAL_DOCUMENTS)
        if (root / name).is_file()
    ]
    missing: list[tuple[str, str, list[str]]] = []
    reports: list[tuple[str, list[str]]] = []
    for name, entries in overlays:
        for key, raw_entry in entries.items():
            if not isinstance(raw_entry, dict):
                continue
            entry = cast(dict[str, Any], raw_entry)
            recorded = entry.get("sha256")
            if not isinstance(recorded, str):
                continue
            try:
                path = _document_path(root, key)
            except ConfigError:
                continue
            findings: list[str] = []
            exists = _exists_exactly(root, key)
            if mode == "shared" and name == DOCUMENTS and exists and not _tracked(root, key):
                findings.append(f"local-entry-in-shared {key}")
            if exists:
                digest = _document_sha256(path, key)
                if digest != recorded:
                    findings.append(f"stale {key}")
            else:
                findings.append(f"missing {key}")
                missing.append((key, recorded, findings))
            for tag in _strings(entry, "tags"):
                if tag not in dictionaries and tag not in vault_dictionaries:
                    findings.append(f"unknown-tag {key} {tag}")
            reports.append((key, findings))
    if missing:
        candidates: dict[str, list[str]] = {}
        for path in root.rglob("*.md"):
            relative = path.relative_to(root)
            if not path.is_file() or path.is_symlink() or any(part.startswith(".") for part in relative.parts):
                continue
            key = relative.as_posix()
            candidates.setdefault(_document_sha256(path, key), []).append(key)
        for old_key, recorded, findings in missing:
            findings.extend(f"  moved? {key}" for key in candidates.get(recorded, []) if key != old_key)
    lines = [line for _, findings in sorted(reports) for line in findings]
    for line in lines:
        print(line)
    if not lines:
        print("OK")
    return 0


def _project_excluded(key: str, pattern: str) -> bool:
    """Match a project document against a glob or any containing directory."""
    parts = PurePosixPath(key).parts
    pattern = pattern.removeprefix("./").rstrip("/")
    regex = re.escape(pattern)
    regex = regex.replace(r"\*\*/", "(?:.*/)?")
    regex = regex.replace(r"\*\*", ".*")
    regex = regex.replace(r"\*", "[^/]*")
    regex = regex.replace(r"\?", "[^/]")
    matcher = re.compile(f"^{regex}$")
    return any(matcher.fullmatch("/".join(parts[:index])) for index in range(1, len(parts) + 1))


def _project_scope(config: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    docs = config.get("docs", [])
    excludes = config.get("exclude", [])
    if not _is_strings(docs) or not _is_strings(excludes):
        raise ConfigError("project config docs and exclude must be lists of strings")
    return cast(list[str], docs), cast(list[str], excludes)


def _project_path_in_scope(key: str, docs: list[str], excludes: list[str]) -> bool:
    return (
        not docs or any(key == doc.rstrip("/") or key.startswith(doc.rstrip("/") + "/") for doc in docs)
    ) and not any(_project_excluded(key, pattern) for pattern in excludes)


def project_files(project: Path) -> list[tuple[Literal["tracked", "untracked", "ignored"], str]]:
    """List visible Markdown documents by Git status without opening their contents."""
    root = _project_root(project)
    config = _read_object(root / ".tow" / "config.json")
    docs, excludes = _project_scope(config)
    files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.md")
        if path.is_file()
        and not path.is_symlink()
        and path.suffix == ".md"
        and not any(part.startswith(".") for part in path.relative_to(root).parts)
    }
    files = {key for key in files if _project_path_in_scope(key, docs, excludes)}
    git_root = _git_root(root)
    if git_root is None:
        return [("untracked", key) for key in sorted(files)]
    root_for_git: Path = git_root
    relative_root = root.relative_to(root_for_git).as_posix()
    path_prefix = f"{relative_root}/" if relative_root != "." else ""

    def relative_git_paths(*args: str) -> set[str]:
        return {
            path.removeprefix(path_prefix)
            for path in _git_files(root_for_git, "-c", "core.quotepath=false", *args, "-z")
            if path.startswith(path_prefix)
        }

    tracked = relative_git_paths("ls-files")
    untracked = relative_git_paths("ls-files", "--others", "--exclude-standard")
    ignored = relative_git_paths("ls-files", "--others", "--ignored", "--exclude-standard")
    status_order = {"tracked": 0, "untracked": 1, "ignored": 2}
    return sorted(
        (
            ("tracked" if key in tracked else "ignored" if key in ignored else "untracked", key)
            for key in files
            if key in tracked or key in ignored or key in untracked
        ),
        key=lambda item: (status_order[item[0]], item[1]),
    )


def cmd_project_files(project: Path) -> int:
    for status, key in project_files(project):
        print(f"{status} {key}")
    return 0


def cmd_project_concepts(project: Path, vault: Path, cfg: Mapping[str, str]) -> int:
    """Print additions for project concepts that do not exist in the connected vault."""
    project_dictionary = _read_object(_project_root(project) / PROJECT_DICTIONARY, missing_ok=True)
    vault_dictionary = _read_object(vault.resolve() / cfg["tagDictionary"])
    project_only: dict[str, dict[str, Any]] = {
        tag: cast(dict[str, Any], entry)
        for tag, entry in project_dictionary.items()
        if tag not in vault_dictionary and isinstance(entry, dict)
    }
    related_by_tag: dict[str, set[str]] = {}
    for child, entry in project_only.items():
        for target in _strings(entry, "related"):
            if target in project_only:
                related_by_tag.setdefault(child, set()).add(target)
                related_by_tag.setdefault(target, set()).add(child)

    additions: list[dict[str, Any]] = []
    for tag in sorted(project_only):
        entry = project_only[tag]
        related = {target for target in _strings(entry, "related") if target in vault_dictionary}
        related.update(target for target in related_by_tag.get(tag, set()) if target < tag)
        additions.append(
            {
                "kind": "add",
                "draft": {
                    "name": tag,
                    "description": entry.get("description", ""),
                    "aliases": _strings(entry, "aliases"),
                    "parents": _strings(entry, "broader"),
                    "children": [],
                    "related": sorted(related),
                },
            }
        )
    print(json.dumps({"changes": additions}, ensure_ascii=False, indent=2))
    return 0


def _project_closure(used: set[str], project_only: Mapping[str, Any]) -> dict[str, Any]:
    """Project-only entries for the used tags, plus the project-only concepts above them through broader."""
    kept: dict[str, Any] = {}
    pending = [tag for tag in used if tag in project_only]
    while pending:
        tag = pending.pop()
        if tag not in kept:
            kept[tag] = project_only[tag]
            pending += [target for target in _strings(kept[tag], "broader") if target in project_only]
    return kept


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


def _exists_exactly(project_root: Path, key: str) -> bool:
    """Whether key names a file with exactly this spelling, even on a case-insensitive filesystem."""
    folder = project_root
    for part in PurePosixPath(key).parts:
        try:
            if part not in os.listdir(folder):
                return False
        except OSError:
            return False
        folder = folder / part
    return folder.is_file()


def _tracked(project_root: Path, key: str) -> bool:
    listed = _git_files(project_root, "-c", "core.quotepath=false", "--literal-pathspecs", "ls-files", "-z", "--", key)
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
