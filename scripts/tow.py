#!/usr/bin/env python3
"""TOW vault convention checks (standard library only).

  tow.py [--root DIR] config                 print the settings in effect (.tow/config.json or legacy tow.json)
  tow.py [--root DIR] init [--dictionaries] [--apply]
                                             list/create vault setup files and PARA folders
  tow.py [--root DIR] migrate [--apply] [--remove-legacy]
                                             copy 0.4.x files into .tow/, or separately remove verified originals
  tow.py [--root DIR] lint [PATH...]         check classification fields and tag counts (default: the search scope)
  tow.py [--root DIR] verify-body BEFORE AFTER
                                             compare body bytes of two vault-local snapshots after metadata edits
  tow.py [--root DIR] find [PREFIX] [--type T] [--status S] [--kind K] [--tag TAG] [--all]
                                             notes that meet every condition (--all: with project archives)
  tow.py [--root DIR] ontology CMD [ARG...]  run the tag-ontology CLI with the vault's settings

Note metadata is parsed through `tag-ontology scan --json`. `verify-body` only separates a leading frontmatter block.
Set TOW_TAG_ONTOLOGY to change the CLI command (default: npx --yes tag-ontology@0.1.3).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Final, Literal, TypedDict, cast

from tow_core import DEFAULT_CLI as DEFAULT_CLI
from tow_core import CliError as CliError
from tow_core import ConfigError as ConfigError
from tow_core import is_legacy_vault as is_legacy_vault
from tow_core import read_user_config as read_user_config
from tow_core import resolve_vault as resolve_vault
from tow_core import run_cli as run_cli
from tow_core import serialize_entries as serialize_entries
from tow_core import tow_kind as tow_kind
from tow_core import write_text_atomic as write_text_atomic
from tow_core import write_user_config as write_user_config

DEFAULTS: Final[dict[str, str]] = {
    "projects": "01_Projects",
    "areas": "02_Areas",
    "resources": "03_Resources",
    "archives": "04_Archives",
    "projectArchive": "archive",
    "tagDictionary": "Tag-Dictionary.json",
    "categoryDictionary": "Category-Dictionary.md",
    "inbox": "00_Inbox",
    "attachments": "99_Etc/attachments",
    "dailyNotes": "02_Areas/daily-notes",
    "misc": "99_Etc",
    "scope": "para",
}
TOW_DEFAULTS: Final[dict[str, str]] = {
    **DEFAULTS,
    "tagDictionary": ".tow/tag-dictionary.json",
    "categoryDictionary": ".tow/category-dictionary.json",
}
PARA: Final = ("projects", "areas", "resources", "archives")
FOLDER_KEYS: Final = (*PARA, "projectArchive", "inbox", "misc")
WORKFLOW_PATHS: Final = ("attachments", "dailyNotes")
DICTIONARY_PATHS: Final = ("categoryDictionary", "tagDictionary")
SCOPES: Final = ("para", "vault")

ALLOWED: Final[dict[str, frozenset[str]]] = {
    "type": frozenset({"resource", "project", "area", "daily-note"}),
    "status": frozenset({"draft", "in-progress", "complete"}),
    "kind": frozenset({"idea", "research", "proposal", "specification", "design", "plan", "retro", "log"}),
}
RETIRED: Final = ("confidence", "stage", "related")
FIND_FILTERS: Final = ("type", "status", "kind", "tag")
TAG_LIMIT: Final = 15
OVERVIEW_TAG_LIMIT: Final = 20
NUMBERED_SECTION: Final = re.compile(r"\d+\.\d+\. ")
CATEGORY_VALUE: Final = re.compile(r"^(?:- |### )`([^`]+)`")
CATEGORY_NAME: Final = re.compile(r"[A-Za-z0-9-]+(?:/[A-Za-z0-9-]+)*")

NOTE_COMMANDS: Final = frozenset({"scan", "usage", "show"})
PATH_COMMANDS: Final = frozenset({"scan", "usage"})
VALUE_OPTIONS: Final = frozenset({"--root", "--dictionary", "--exclude", "--names", "--base"})
INIT_HINT: Final = 'run "tow init --dictionaries" to preview missing starter files'
STARTER_CATEGORIES: Final = serialize_entries({})
LEGACY_STARTER_CATEGORIES: Final = """---
updated: {today}
---

# Category Dictionary

Registered `category` values. A value is the first backtick token of a bullet line or of a `###` heading;
every other line is description. Example entries, once registered:

    ### `ai` — artificial intelligence
    - `ai/rag` : retrieval-augmented generation (RAG)

Register new values through the `tow-classify` skill.
"""


class Heading(TypedDict):
    level: int
    text: str


class Note(TypedDict):
    """The fields TOW uses from a `notes` item of `tag-ontology scan --json`."""

    path: str
    frontmatter: dict[str, Any] | None
    tags: list[str]
    headings: list[Heading]


@dataclass(frozen=True)
class Issue:
    code: str
    severity: Literal["error", "warning"]
    path: str
    message: str


# ---- Pure functions: scan result -> findings


def lint(notes: Iterable[Note], categories: set[str]) -> list[Issue]:
    """Convention issues of the notes that have frontmatter, in note order."""
    issues: list[Issue] = []
    for note in notes:
        if note["frontmatter"] is not None:
            issues += _note_issues(note, note["frontmatter"], categories)
    return issues


def _note_issues(note: Note, fm: dict[str, Any], categories: set[str]) -> Iterator[Issue]:
    path, tags = note["path"], note["tags"]
    for prop in RETIRED:
        if prop in fm:
            yield Issue("retired-property", "error", path, f"unused property '{prop}'")
    if any("/" in t for t in tags) and "type" not in fm:
        yield Issue(
            "legacy",
            "warning",
            path,
            "classification values ('/') are still in tags and there is no type: move them to classification fields",
        )
    else:
        yield from _field_issues(path, fm, tags, categories)
    limit = OVERVIEW_TAG_LIMIT if _is_overview(note) else TAG_LIMIT
    if len(tags) > limit:
        yield Issue("too-many-tags", "warning", path, f"{len(tags)} tags, limit {limit} (3-10 recommended)")


def _field_issues(path: str, fm: dict[str, Any], tags: list[str], categories: set[str]) -> Iterator[Issue]:
    for key, allowed in ALLOWED.items():
        value = fm.get(key)
        if value is not None and not (isinstance(value, str) and value in allowed):
            yield Issue(
                "invalid-value", "error", path, f"{key} value {value!r} is not allowed ({' | '.join(sorted(allowed))})"
            )
    if fm.get("type") != "project":
        for key in ("status", "kind"):
            if key in fm:
                yield Issue("project-only", "error", path, f"{key} is only for type: project notes")
    for c in _as_list(fm.get("category")):
        if c not in categories:
            yield Issue("unknown-category", "error", path, f"unregistered category '{c}'")
    lowered = [t.lower() for t in tags]  # Obsidian treats tags that differ only in case as one tag
    duplicates = sorted({t for t in tags if lowered.count(t.lower()) > 1})
    if duplicates:
        yield Issue("duplicate-tag", "error", path, f"duplicate tags: {', '.join(duplicates)}")


def _is_overview(note: Note) -> bool:
    """A note with three or more numbered sections (## N.k.) is an overview of several topics."""
    numbered = [h for h in note["headings"] if h["level"] == 2 and NUMBERED_SECTION.match(h["text"])]
    return len(numbered) >= 3


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in cast(list[object], value)]
    return [str(value)]


def category_values(text: str) -> set[str]:
    """Values registered in the category dictionary: the first backtick token of a bullet line or a `###` heading."""
    return {m.group(1) for line in text.splitlines() if (m := CATEGORY_VALUE.match(line))}


def category_entries(text: str) -> dict[str, dict[str, str]]:
    """Parse a JSON category dictionary and reject values outside its data contract."""
    try:
        raw: object = json.loads(text)
    except ValueError as e:
        raise ConfigError(f"invalid category dictionary JSON: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError("category dictionary must be a JSON object")
    entries: dict[str, dict[str, str]] = {}
    for value, entry in cast(dict[str, object], raw).items():
        if not isinstance(entry, dict):
            raise ConfigError(f"category dictionary entry {value!r} must be an object")
        fields = cast(dict[object, object], entry)
        description = fields.get("description")
        if set(fields) != {"description"} or not isinstance(description, str):
            raise ConfigError(f"category dictionary entry {value!r} must contain only a string description")
        entries[value] = {"description": description}
    return entries


def load_categories(root: Path, cfg: Mapping[str, str]) -> set[str]:
    """Load registered category values from JSON or a legacy Markdown dictionary."""
    path = root / cfg["categoryDictionary"]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"can't read the category dictionary: {path}; {INIT_HINT}") from e
    if path.suffix == ".json":
        return set(category_entries(text))
    if path.suffix == ".md":
        return category_values(text)
    raise ConfigError(f"unsupported category dictionary format: {path}")


def find(notes: Iterable[Note], prefix: str | None, filters: Mapping[str, str] | None = None) -> list[str]:
    """Paths of the notes that meet every condition given.

    `prefix` matches a category equal to it or below it (`prefix/...`). `filters` maps `type`, `status` or `kind`
    to the field's value, and `tag` to a tag on the note (ignoring case, as Obsidian does).
    """
    return [n["path"] for n in notes if n["frontmatter"] and _matches(n, n["frontmatter"], prefix, filters or {})]


def _matches(note: Note, fm: dict[str, Any], prefix: str | None, filters: Mapping[str, str]) -> bool:
    categories = _as_list(fm.get("category"))
    if prefix is not None and not any(c == prefix or c.startswith(prefix + "/") for c in categories):
        return False
    tag = filters.get("tag")
    if tag is not None and tag.lower() not in {t.lower() for t in note["tags"]}:
        return False
    return all(fm.get(key) == value for key, value in filters.items() if key != "tag")


def load_config(raw: object, defaults: Mapping[str, str] = DEFAULTS) -> dict[str, str]:
    """Validate config settings and merge them over the defaults."""
    if not isinstance(raw, dict):
        raise ConfigError("must be a JSON object")
    values = cast(dict[str, object], raw)
    kind = values.get("kind")
    if "kind" in values and kind != "vault":
        raise ConfigError('kind: must be "vault"')
    settings = {key: value for key, value in values.items() if key != "kind"}
    unknown = sorted(settings.keys() - defaults.keys())
    if unknown:
        raise ConfigError(f"unknown keys: {', '.join(unknown)}")
    for key, value in settings.items():
        if not isinstance(value, str) or not value:
            raise ConfigError(f"{key}: must be a non-empty string")
        if key in FOLDER_KEYS and ("/" in value or value in (".", "..")):
            raise ConfigError(f"{key}: must be a single folder name, without '/'")
        if key == "scope" and value not in SCOPES:
            raise ConfigError(f"scope: must be one of {', '.join(SCOPES)}")
        if key in DICTIONARY_PATHS and value.endswith("/"):
            raise ConfigError(f"{key}: must name a file, without a trailing '/'")
        if key in (*WORKFLOW_PATHS, *DICTIONARY_PATHS):
            path = Path(value)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ConfigError(f"{key}: must be a vault-relative path without '..'")
    return {**defaults, **cast(dict[str, str], settings)}


def ontology_args(command: str, args: list[str], root: str, cfg: dict[str, str], excludes: list[str]) -> list[str]:
    """Arguments for the tag-ontology CLI, with the vault root, dictionary, tag name rule and note scope added.

    `--all` is a TOW option: it keeps project archives in `show` and is not passed on.
    """
    out = [command, *(a for a in args if a != "--all"), "--root", root]
    if command != "scan":
        out += ["--dictionary", cfg["tagDictionary"], "--names", "kebab"]
    if command in NOTE_COMMANDS:
        out += excludes
    if command == "show" and cfg["scope"] == "para" and "--all" not in args:
        out += ["--exclude", f"**/{cfg['projectArchive']}"]
    return out


def scope_excludes(root: Path, cfg: dict[str, str], args: list[str]) -> list[str]:
    """--exclude arguments that limit notes to the search scope, except entries the args name.

    `para` keeps only the PARA folders at the root; `vault` keeps every note folder, excluding only the category
    dictionary unless it is explicitly selected.
    """
    # ponytail: names are passed as globs, so a folder name containing * ? [ may match differently.
    # If a vault needs that, ask for an escaping rule in the CLI contract.
    named = _named_roots(root, args)
    if cfg["scope"] == "vault":
        category_dictionary = Path(cfg["categoryDictionary"])
        outside = (
            [cfg["categoryDictionary"]]
            if category_dictionary.suffix == ".md" and category_dictionary.parts[0] not in named
            else []
        )
        return [arg for path in sorted(outside) if (root / path).exists() for arg in ("--exclude", path)]
    keep = {cfg[k] for k in PARA} | named
    return [
        arg
        for entry in sorted(root.iterdir())
        if not entry.name.startswith(".") and entry.name not in keep and (entry.is_dir() or entry.suffix == ".md")
        for arg in ("--exclude", entry.name)
    ]


def _named_roots(root: Path, args: list[str]) -> set[str]:
    """The root entry that each path argument in CLI args lies under."""
    roots: set[str] = set()
    after_option = False
    for a in args:
        if after_option:
            after_option = False
        elif a in VALUE_OPTIONS:
            after_option = True
        elif not a.startswith("-"):
            path = Path(os.path.normpath(a))
            if path.is_absolute():
                if not path.is_relative_to(root):
                    continue
                path = path.relative_to(root)
            if path.parts and path.parts[0] not in (".", ".."):
                roots.add(path.parts[0])
    return roots


# ---- I/O: settings file, CLI calls, output


def body_bytes(content: bytes) -> bytes:
    """Body after a leading, delimiter-only frontmatter block; no YAML or Markdown interpretation."""
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].removeprefix(b"\xef\xbb\xbf").rstrip(b"\r\n") != b"---":
        return content
    for index, line in enumerate(lines[1:], 1):
        if line.rstrip(b"\r\n") == b"---":
            return b"".join(lines[index + 1 :])
    raise ConfigError("can't verify body: leading frontmatter has no closing '---' line")


def cmd_verify_body(root: Path, before: Path, after: Path) -> int:
    paths = [(root / path).resolve() for path in (before, after)]
    if any(not path.is_relative_to(root) for path in paths):
        raise ConfigError("verify-body requires two paths inside the vault")
    if paths[0].samefile(paths[1]):
        raise ConfigError("verify-body requires distinct files, not a self-comparison or hard-linked copy")
    if body_bytes(paths[0].read_bytes()) != body_bytes(paths[1].read_bytes()):
        print("body changed; metadata-only preservation check failed", file=sys.stderr)
        return 1
    print("body unchanged; metadata and formatting semantics were not validated")
    return 0


def read_config(root: Path) -> dict[str, str]:
    tow_config = root / ".tow" / "config.json"
    legacy_config = root / "tow.json"
    if tow_config.exists():
        path, defaults = tow_config, TOW_DEFAULTS
    elif legacy_config.exists():
        path, defaults = legacy_config, DEFAULTS
    else:
        return dict(DEFAULTS)
    try:
        return load_config(json.loads(path.read_text(encoding="utf-8")), defaults)
    except (OSError, ValueError, ConfigError) as e:
        raise ConfigError(f"{path.relative_to(root)}: {e}") from e


def plugin_dictionary_warning(root: Path, cfg: Mapping[str, str]) -> str | None:
    """Compare the Tag Ontology plugin's effective dictionary path with TOW's setting."""
    path = root / ".obsidian" / "plugins" / "tag-ontology" / "data.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "plugin settings not checked (no .obsidian/plugins/tag-ontology/data.json)"
    except (OSError, ValueError) as e:
        return f"plugin settings not checked (can't read .obsidian/plugins/tag-ontology/data.json: {e})"
    if not isinstance(raw, dict):
        return "plugin settings not checked (invalid .obsidian/plugins/tag-ontology/data.json)"
    settings = cast(dict[str, object], raw)
    dictionary = settings.get("dictionaryPath", "Tag-Dictionary.json")
    if not isinstance(dictionary, str):
        return "plugin settings not checked (invalid dictionaryPath in .obsidian/plugins/tag-ontology/data.json)"
    if settings.get("dictionaryPathExplicit", False) is not True and (root / ".tow" / "tag-dictionary.json").is_file():
        dictionary = ".tow/tag-dictionary.json"
    tow_dictionary = cfg["tagDictionary"]
    if dictionary == tow_dictionary:
        return None
    return f"plugin dictionary path differs: TOW uses {tow_dictionary}, Tag Ontology plugin uses {dictionary}"


def scan(root: Path, cfg: dict[str, str], paths: list[str], extra: list[str]) -> dict[str, Any]:
    args = ontology_args("scan", [*paths, "--json", *extra], str(root), cfg, scope_excludes(root, cfg, paths))
    result = run_cli(args, capture=True)
    failure = result.stderr.strip() or f"tag-ontology scan exited with code {result.returncode} without JSON output"
    if result.returncode not in (0, 1):
        raise CliError(failure)
    try:
        return json.loads(result.stdout)
    except ValueError:
        # A launcher such as npx exits 1 with nothing on stdout when it can't fetch the CLI.
        raise CliError(failure) from None


def cmd_lint(root: Path, cfg: dict[str, str], paths: list[str]) -> int:
    categories = load_categories(root, cfg)
    result = scan(root, cfg, paths, [])
    issues = [Issue(i["code"], i["severity"], i.get("path", ""), i["message"]) for i in result["issues"]]
    issues += lint(result["notes"], categories)
    for i in issues:
        print(f"{i.severity} {i.code} {i.path}: {i.message}")
    errors = sum(i.severity == "error" for i in issues)
    print(f"{errors} error(s), {len(issues) - errors} warning(s)" if issues else "OK")
    return 1 if errors else 0


def cmd_category_add(root: Path, cfg: dict[str, str], value: str, description: str, apply: bool) -> int:
    """Preview or add one category entry to the configured JSON dictionary."""
    path = root / cfg["categoryDictionary"]
    if path.suffix == ".md":
        raise ConfigError('category add requires a JSON dictionary; run "tow migrate"')
    if path.suffix != ".json":
        raise ConfigError(f"unsupported category dictionary format: {path}")
    if CATEGORY_NAME.fullmatch(value) is None:
        raise ConfigError(f"invalid category value: {value!r}")
    try:
        entries = category_entries(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise ConfigError(f"can't read the category dictionary: {path}; {INIT_HINT}") from e
    if value in entries:
        raise ConfigError(f"category already registered: {value}")
    entries[value] = {"description": description}
    if not apply:
        print(f"would add {json.dumps(value, ensure_ascii=False)}: {description}")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(path, serialize_entries(entries))
    print(f"added {json.dumps(value, ensure_ascii=False)}")
    return 0


def cmd_migrate(root: Path, apply: bool, remove_legacy: bool) -> int:
    """Copy a legacy vault into .tow/, or separately verify then remove its originals."""
    targets = (
        root / ".tow/config.json",
        root / ".tow/tags.md",
        root / ".tow/tag-dictionary.json",
        root / ".tow/categories.md",
        root / ".tow/category-dictionary.json",
    )
    if not remove_legacy and any(path.exists() or path.is_symlink() for path in targets):
        raise ConfigError("migration target already exists; migration never overwrites .tow/ files")
    if not remove_legacy and tow_kind(root) == "vault":
        raise ConfigError(f"tow migrate requires a legacy vault: {root}")
    if not is_legacy_vault(root):
        raise ConfigError(f"tow migrate requires a legacy vault: {root}")
    config_path = root / "tow.json"
    try:
        raw_config: object = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        validated_config = load_config(raw_config)
    except (OSError, ValueError, ConfigError) as e:
        raise ConfigError(f"tow.json: {e}") from e
    original_config = cast(dict[str, object], raw_config)
    migrated_config = {key: value for key, value in original_config.items() if key != "kind"}
    legacy_paths = {
        "tagDictionary": "Tag-Dictionary.json",
        "categoryDictionary": "Category-Dictionary.md",
    }
    dropped_keys = {key for key, path in legacy_paths.items() if migrated_config.get(key) == path}
    legacy_dictionary_keys = {key for key, path in legacy_paths.items() if validated_config[key] == path}
    for key in dropped_keys:
        migrated_config.pop(key, None)
    migrated_config = {"kind": "vault", **migrated_config}

    tag_source = root / validated_config["tagDictionary"]
    category_source = root / validated_config["categoryDictionary"]
    for source in (tag_source, category_source):
        if not source.is_file():
            raise ConfigError(f"migration source is missing or not a file: {source}")
    for source in (tag_source, category_source):
        if not source.resolve().is_relative_to(root.resolve()):
            raise ConfigError(f"migration source must stay inside the vault: {source}")
    if Path(validated_config["categoryDictionary"]).suffix != ".md":
        raise ConfigError(f"migration requires a Markdown category dictionary: {category_source}")
    try:
        tag_bytes = tag_source.read_bytes()
        category_text = category_source.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"can't read legacy dictionary: {e}") from e

    category_entries_to_write: dict[str, dict[str, str]] = {}
    for line in category_text.splitlines():
        match = CATEGORY_VALUE.match(line)
        if match is None:
            continue
        description = line[match.end() :].strip().lstrip(":—- ").strip()
        category_entries_to_write[match.group(1)] = {"description": description}

    if remove_legacy:
        try:
            legacy_config: object = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
            legacy_values = cast(dict[str, object], legacy_config) if isinstance(legacy_config, dict) else {}
            remove_tag_source = root / str(legacy_values.get("tagDictionary", "Tag-Dictionary.json"))
            remove_category_source = root / str(legacy_values.get("categoryDictionary", "Category-Dictionary.md"))
            if (
                remove_tag_source.resolve() != tag_source.resolve()
                or remove_category_source.resolve() != category_source.resolve()
            ):
                raise ConfigError("migration verification failed; legacy settings changed")
            if "tagDictionary" not in legacy_dictionary_keys and not remove_tag_source.is_file():
                raise ConfigError("migration verification failed; configured tag dictionary is missing")
            if "categoryDictionary" not in legacy_dictionary_keys and not remove_category_source.is_file():
                raise ConfigError("migration verification failed; configured category dictionary is missing")
            new_config_raw = json.loads(targets[0].read_text(encoding="utf-8"))
            new_config = cast(dict[str, object], new_config_raw) if isinstance(new_config_raw, dict) else {}
            tag_copy = targets[2].read_bytes()
            category_copy = category_entries(targets[4].read_text(encoding="utf-8"))
            for manual in (targets[1], targets[3]):
                starter = (Path(__file__).parent / "starters" / manual.name).read_bytes()
                if not manual.is_file() or manual.read_bytes() != starter:
                    raise ConfigError(f"migration verification failed: changed {manual.relative_to(root)}")
        except (OSError, ValueError, ConfigError) as e:
            raise ConfigError(f"migration verification failed: {e}") from e
        expected_keys = set(migrated_config)
        expected_keys.remove("kind")
        if (
            new_config.get("kind") != "vault"
            or set(new_config) - {"kind"} != expected_keys
            or any(new_config.get(key) != value for key, value in migrated_config.items() if key != "kind")
            or tag_copy != tag_bytes
            or set(category_copy) != category_values(category_text)
        ):
            raise ConfigError("migration verification failed; legacy files were kept")
        legacy_paths = [config_path]
        if "tagDictionary" in legacy_dictionary_keys:
            legacy_paths.append(remove_tag_source)
        if "categoryDictionary" in legacy_dictionary_keys:
            legacy_paths.append(remove_category_source)
        legacy_paths = [path for path in legacy_paths if path.is_file()]
        if not apply:
            for path in legacy_paths:
                print(f"would delete {path.relative_to(root)}")
            print("run again with --remove-legacy --apply to delete verified legacy files")
            return 0
        for path in legacy_paths:
            path.unlink()
            print(f"deleted {path.relative_to(root)}")
        return 0

    for target in targets:
        if not target.resolve().is_relative_to(root.resolve()):
            raise ConfigError(f"migration target must stay inside the vault: {target}")
    starters = Path(__file__).parent / "starters"
    output = {
        targets[0]: json.dumps(migrated_config, ensure_ascii=False, indent=2) + "\n",
        targets[1]: (starters / "tags.md").read_text(encoding="utf-8"),
        targets[2]: tag_bytes.decode("utf-8"),
        targets[3]: (starters / "categories.md").read_text(encoding="utf-8"),
        targets[4]: serialize_entries(category_entries_to_write),
    }
    for target, text in output.items():
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            write_text_atomic(target, text, exclusive=True)
        print(f"{'created' if apply else 'would create'} {target.relative_to(root)}")
    if not apply:
        print("run again with --apply to create .tow/")
    return 0


def cmd_find(
    root: Path, cfg: dict[str, str], prefix: str | None, filters: dict[str, str], include_archive: bool
) -> int:
    extra = [] if include_archive or cfg["scope"] == "vault" else ["--exclude", f"**/{cfg['projectArchive']}"]
    for path in find(scan(root, cfg, [], extra)["notes"], prefix, filters):
        print(path)
    return 0


def missing_paths(root: Path, cfg: dict[str, str], dictionaries: bool = False) -> list[str]:
    """Folders and starter files missing from the selected vault layout."""
    legacy = tow_kind(root) != "vault" and is_legacy_vault(root)
    folders = [*(cfg[k] for k in PARA), cfg["inbox"]] if cfg["scope"] == "para" else []
    missing = [f"{f}/" for f in folders if not (root / f).is_dir()]
    if legacy:
        if cfg["scope"] == "para" or dictionaries:
            missing += [cfg[k] for k in DICTIONARY_PATHS if not (root / cfg[k]).exists()]
        return missing
    bundle = (
        ".tow/config.json",
        ".tow/tags.md",
        ".tow/tag-dictionary.json",
        ".tow/categories.md",
        ".tow/category-dictionary.json",
    )
    return [*missing, *(path for path in bundle if not (root / path).exists())]


def cmd_init(
    root: Path,
    cfg: dict[str, str],
    apply: bool,
    dictionaries: bool = False,
    layout: Literal["tow", "legacy", "plain"] | None = None,
) -> int:
    """List what's missing; with `apply`, create it. Never overwrites an existing file."""
    legacy = layout == "legacy" if layout is not None else tow_kind(root) != "vault" and is_legacy_vault(root)
    init_cfg = cfg
    if not legacy and layout == "plain":
        init_cfg = {**TOW_DEFAULTS, **{key: value for key, value in cfg.items() if value != DEFAULTS.get(key)}}
    folders = [root / init_cfg[k] for k in (*PARA, "inbox")] if init_cfg["scope"] == "para" else []
    if legacy:
        files = [root / init_cfg[k] for k in DICTIONARY_PATHS] if init_cfg["scope"] == "para" or dictionaries else []
    else:
        files = [
            root / path
            for path in (
                ".tow/config.json",
                ".tow/tags.md",
                ".tow/tag-dictionary.json",
                ".tow/categories.md",
                ".tow/category-dictionary.json",
            )
        ]
    targets = [(p, True) for p in folders] + [(p, False) for p in files]
    resolved_files = [p.resolve() for p in files]
    if len(set(resolved_files)) != len(resolved_files):
        raise ConfigError("init dictionaries must use different file paths")
    for target, is_folder in targets:
        resolved = target.resolve()
        if not resolved.is_relative_to(root):
            raise ConfigError(f"init path must stay inside the vault: {target}")
        if (target.exists() or target.is_symlink()) and not (target.is_dir() if is_folder else target.is_file()):
            raise ConfigError(f"init expected a {'folder' if is_folder else 'file'}: {target}")
        for parent in target.parents:
            if parent.is_relative_to(root) and parent.exists() and not parent.is_dir():
                raise ConfigError(f"init expected a parent folder: {parent}")
        if any(resolved == f or resolved.is_relative_to(f) for f in resolved_files if is_folder or resolved != f):
            raise ConfigError(f"init file/folder paths conflict: {target}")
    if legacy:
        if layout == "legacy" or is_legacy_vault(root):
            print('tow: legacy vault; run "tow migrate" to create .tow/', file=sys.stderr)
        category_starter = (
            LEGACY_STARTER_CATEGORIES.format(today=date.today().isoformat())
            if Path(init_cfg["categoryDictionary"]).suffix == ".md"
            else STARTER_CATEGORIES
        )
        starters = {
            init_cfg["categoryDictionary"]: category_starter,
            init_cfg["tagDictionary"]: serialize_entries({}),
        }
    else:
        starters = {
            ".tow/config.json": '{"kind": "vault"}\n',
            ".tow/tags.md": (Path(__file__).parent / "starters/tags.md").read_text(encoding="utf-8"),
            ".tow/tag-dictionary.json": serialize_entries({}),
            ".tow/categories.md": (Path(__file__).parent / "starters/categories.md").read_text(encoding="utf-8"),
            ".tow/category-dictionary.json": serialize_entries({}),
        }
    missing = missing_paths(root, init_cfg, dictionaries)
    for path in missing:
        if apply:
            target = root / path
            if path.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                write_text_atomic(target, starters[path], exclusive=True)
        print(f"{'created' if apply else 'would create'} {path}")
    if not missing:
        print("nothing to create")
    elif not apply:
        print("run again with --apply to create these")
    return 0


def warn_if_scope_is_empty(root: Path, cfg: dict[str, str]) -> None:
    if cfg["scope"] == "para" and not any((root / cfg[k]).is_dir() for k in PARA):
        folders = ", ".join(cfg[k] for k in PARA)
        print(
            f"tow: warning: no PARA folders ({folders}) in {root}, so the default search scope is empty; "
            f'{INIT_HINT}, or set "scope": "vault" in tow.json to search every folder',
            file=sys.stderr,
        )


def cmd_connect(vault: Path | None, apply: bool) -> int:
    """Show, preview, or save the personal vault connection."""
    env_vault = os.environ.get("TOW_VAULT")
    current = str(Path(env_vault).expanduser().resolve()) if env_vault else read_user_config()
    if vault is None:
        if env_vault:
            print(f"connected: {Path(env_vault).expanduser().resolve()} (from TOW_VAULT; overrides ~/.tow/config.json)")
        elif current is not None:
            print(f"connected: {current} (from ~/.tow/config.json)")
        else:
            print("not connected")
        return 0
    root = vault.expanduser().resolve()
    if apply:
        write_user_config(root)
        print(f"connected {root}")
    else:
        if tow_kind(root) != "vault" and not is_legacy_vault(root):
            raise ConfigError(f"not a TOW vault; run setup inside the vault first: {root}")
        print(f"would connect {current or 'not connected'} → {root}")
    if env_vault:
        print("tow: warning: TOW_VAULT still overrides ~/.tow/config.json", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tow", description="TOW vault convention checks")
    parser.add_argument("--root", type=Path, default=None, help="vault folder (default: resolve from TOW settings)")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("connect", help="show or set the personal vault connection")
    p.add_argument("vault", nargs="?", type=Path, help="vault to connect")
    p.add_argument("--apply", action="store_true", help="write the connection")
    sub.add_parser("config", help="print the settings in effect")
    p = sub.add_parser("init", help="list missing vault setup files and folders; --apply creates them")
    p.add_argument("--apply", action="store_true", help="create what is missing (never overwrites)")
    p.add_argument("--dictionaries", action="store_true", help="include starter dictionaries in a free-form vault")
    p = sub.add_parser("migrate", help="preview or migrate a legacy vault into .tow/")
    p.add_argument("--apply", action="store_true", help="write the migration or delete verified legacy files")
    p.add_argument("--remove-legacy", action="store_true", help="delete legacy files after verifying .tow/ copies")
    p = sub.add_parser("lint", help="check classification fields and tag counts")
    p.add_argument("paths", nargs="*")
    p = sub.add_parser("category", help="manage registered categories")
    category_sub = p.add_subparsers(dest="category_command", required=True)
    p = category_sub.add_parser("add", help="add a category value after approval")
    p.add_argument("value")
    p.add_argument("description")
    p.add_argument("--apply", action="store_true", help="write the category dictionary")
    p = sub.add_parser("verify-body", help="compare exact body bytes after a metadata-only edit (read-only)")
    p.add_argument("before", type=Path, help="independent snapshot inside the vault")
    p.add_argument("after", type=Path, help="candidate note inside the vault")
    p = sub.add_parser("find", help="find notes by category prefix, frontmatter fields and tag")
    p.add_argument("prefix", nargs="?", help="category prefix: matches the category and everything below it")
    for key in FIND_FILTERS:
        p.add_argument(f"--{key}", help=f"only notes with this {key}")
    p.add_argument("--all", action="store_true", help="include project archive folders")
    p = sub.add_parser("ontology", help="run the tag-ontology CLI with the vault's settings")
    p.add_argument("cli_command")
    p.add_argument("cli_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    filters: dict[str, str] = {}
    if args.command == "find":
        filters = {key: value for key in FIND_FILTERS if (value := getattr(args, key)) is not None}
        if args.prefix is None and not filters:
            parser.error("find needs a category prefix or at least one of --type, --status, --kind, --tag")

    try:
        if args.command == "connect":
            return cmd_connect(args.vault, args.apply)
        vault_ref = resolve_vault(Path.cwd(), args.root, os.environ)
        root = vault_ref.root
        if args.command == "verify-body":
            return cmd_verify_body(root, args.before, args.after)
        cfg = read_config(root)
        if args.command == "config":
            print(json.dumps(cfg, ensure_ascii=False, indent=2))
            print(f"tow: vault {root} (from {vault_ref.source}, {vault_ref.layout})", file=sys.stderr)
            warning = plugin_dictionary_warning(root, cfg)
            if warning:
                print(f"tow: warning: {warning}", file=sys.stderr)
            return 0
        if args.command == "init":
            return cmd_init(root, cfg, args.apply, args.dictionaries, vault_ref.layout)
        if args.command == "migrate":
            return cmd_migrate(root, args.apply, args.remove_legacy)
        if args.command == "category":
            return cmd_category_add(root, cfg, args.value, args.description, args.apply)
        named: list[str] = args.paths if args.command == "lint" else []
        if args.command == "ontology" and args.cli_command in PATH_COMMANDS:
            named = args.cli_args
        if (
            args.command in ("lint", "find") or (args.command == "ontology" and args.cli_command in NOTE_COMMANDS)
        ) and not _named_roots(root, named):
            warn_if_scope_is_empty(root, cfg)
        if args.command == "lint":
            return cmd_lint(root, cfg, args.paths)
        if args.command == "find":
            return cmd_find(root, cfg, args.prefix, filters, args.all)
        dictionary = root / cfg["tagDictionary"]
        if args.cli_command not in ("scan", "--help", "--version") and not dictionary.exists():
            raise ConfigError(f"can't find the tag dictionary: {dictionary}; {INIT_HINT}")
        path_args: list[str] = args.cli_args if args.cli_command in PATH_COMMANDS else []
        excludes = scope_excludes(root, cfg, path_args)
        return run_cli(
            ontology_args(args.cli_command, args.cli_args, str(root), cfg, excludes), capture=False
        ).returncode
    except (ConfigError, CliError, OSError) as e:
        print(f"tow: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
