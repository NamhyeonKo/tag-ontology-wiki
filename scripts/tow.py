#!/usr/bin/env python3
"""TOW vault convention checks (standard library only).

  tow.py [--root DIR] config                 print the settings in effect (tow/config.json or older vault config)
  tow.py [--root DIR] init [--scope {para,vault}] [--dictionaries] [--apply]
                                             list/create vault setup files and PARA folders (--scope vault: no folders)
  tow.py [--root DIR] migrate [--scope {para,vault}] [--apply] [--remove-legacy]
                                             move older vault files into tow/, or separately remove verified originals
  tow.py [--root DIR] lint [PATH...]         check classification fields and tag counts (default: the search scope)
  tow.py [--root DIR] verify-body BEFORE AFTER
                                             compare body bytes of two vault-local snapshots after metadata edits
  tow.py [--root DIR] find [PREFIX] [--type T] [--status S] [--kind K] [--tag TAG] [--all]
                                             notes that meet every condition (--all: with project archives)
  tow.py [--root DIR] lookup TAG [--exact]    notes matching one concept in the vault and current project
  tow.py [--root DIR] search "<query>"        search notes with a query
  tow.py [--root DIR] ontology CMD [ARG...]  run the tag-ontology CLI with the vault's settings
  tow.py [--root DIR] project init --mode {local,shared} [--exclude GLOB] [--apply]
                                             initialize project metadata
  tow.py [--root DIR] project tag CHANGES [--apply]
                                             attach approved tags to project documents and refresh the subset
  tow.py project status|files              report project metadata or list Markdown files by Git status
  tow.py [--root DIR] project concepts PROJECT
                                             print additions for project-only concepts (from inside the vault)

Note metadata is parsed through `tag-ontology scan --json`. `verify-body` only separates a leading frontmatter block.
Set TOW_TAG_ONTOLOGY to change the CLI command (default: npx --yes tag-ontology@0.3.1).
"""

from __future__ import annotations

import argparse
import contextlib
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
from tow_core import VaultLayout as VaultLayout
from tow_core import body_bytes as body_bytes
from tow_core import is_empty_plugin_dictionary as is_empty_plugin_dictionary
from tow_core import is_legacy_vault as is_legacy_vault
from tow_core import read_user_config as read_user_config
from tow_core import resolve_project as resolve_project
from tow_core import resolve_vault as resolve_vault
from tow_core import run_cli as run_cli
from tow_core import serialize_entries as serialize_entries
from tow_core import tow_kind as tow_kind
from tow_core import vault_folder as vault_folder
from tow_core import vault_layout as vault_layout
from tow_core import write_text_atomic as write_text_atomic
from tow_core import write_user_config as write_user_config
from tow_project import cmd_lookup as cmd_lookup
from tow_project import cmd_project_concepts as cmd_project_concepts
from tow_project import cmd_project_files as cmd_project_files
from tow_project import cmd_project_init as cmd_project_init
from tow_project import cmd_project_status as cmd_project_status
from tow_project import cmd_project_tag as cmd_project_tag
from tow_project import cmd_send as cmd_send
from tow_search import cmd_search as cmd_search

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
    "tagDictionary": "tow/tag-dictionary.json",
    "categoryDictionary": "tow/category-dictionary.json",
}
DOT_DEFAULTS: Final[dict[str, str]] = {
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
CATEGORY_NAME: Final = re.compile(r"[^\s`/]+(?:/[^\s`/]+)*")
TOW_BUNDLE: Final = (
    "tow/config.json",
    "tow/tags.md",
    "tow/tag-dictionary.json",
    "tow/categories.md",
    "tow/category-dictionary.json",
)
TOW_BUNDLE_STARTER_FILES: Final = {
    "tow/tags.md": "tags.md",
    "tow/categories.md": "categories.md",
}
DOT_BUNDLE: Final = tuple(path.replace("tow/", ".tow/", 1) for path in TOW_BUNDLE)
DOT_BUNDLE_STARTER_FILES: Final = {
    path.replace("tow/", ".tow/", 1): name for path, name in TOW_BUNDLE_STARTER_FILES.items()
}

KEPT_ORIGINALS: Final = (
    "tow: kept the original files; TOW now reads and writes tow/, so they no longer change. "
    'Preview "tow migrate --remove-legacy" to delete the verified originals once every device runs '
    "Tag Ontology plugin 0.10.1 or later"
)

NOTE_COMMANDS: Final = frozenset({"scan", "usage", "show"})
PATH_COMMANDS: Final = frozenset({"scan", "usage"})
VALUE_OPTIONS: Final = frozenset({"--root", "--dictionary", "--exclude", "--tags-file", "--names", "--base"})
INIT_HINT: Final = 'run "tow init" (add "--dictionaries" for free-form vaults) to preview missing starter files'
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
    dictionary unless it is explicitly selected. The visible vault bundle is never a note source.
    """
    # ponytail: names are passed as globs, so a folder name containing * ? [ may match differently.
    # If a vault needs that, ask for an escaping rule in the CLI contract.
    named = _named_roots(root, args)
    excluded = ["tow"] if (root / "tow").is_dir() else []
    if cfg["scope"] == "vault":
        category_dictionary = Path(cfg["categoryDictionary"])
        outside = (
            [cfg["categoryDictionary"]]
            if category_dictionary.suffix == ".md" and category_dictionary.parts[0] not in named
            else []
        )
        return [
            arg
            for path in sorted([*excluded, *outside])
            if (root / path).exists() or path == "tow"
            for arg in ("--exclude", path)
        ]
    keep = {cfg[k] for k in PARA} | named
    outside = {
        entry.name
        for entry in root.iterdir()
        if not entry.name.startswith(".")
        and entry.name not in keep
        and entry.name != "tow"
        and (entry.is_dir() or entry.suffix == ".md")
    }
    outside.update(excluded)
    return [arg for path in sorted(outside) for arg in ("--exclude", path)]


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
    layout = vault_layout(root)
    folder = vault_folder(layout)
    if folder is not None:
        path = root / folder / "config.json"
        defaults = TOW_DEFAULTS if layout == "tow" else DOT_DEFAULTS
    elif layout == "legacy":
        path, defaults = root / "tow.json", DEFAULTS
        if not path.exists():
            return dict(DEFAULTS)
    else:
        return dict(DEFAULTS)
    try:
        return load_config(json.loads(path.read_text(encoding="utf-8")), defaults)
    except (OSError, ValueError, ConfigError) as e:
        raise ConfigError(f"{path.relative_to(root)}: {e}") from e


def require_inside(root: Path, cwd: Path, command: str) -> None:
    """Require vault maintenance writes to run from inside the vault."""
    resolved_root = root.resolve()
    if not cwd.resolve().is_relative_to(resolved_root):
        raise ConfigError(f"{command} changes the vault; run it inside {resolved_root}")


def plugin_dictionary_warning(root: Path, cfg: Mapping[str, str]) -> str | None:
    """Compare the Tag Ontology plugin's effective dictionary path with TOW's setting."""
    settings_path = root / ".obsidian" / "plugins" / "tag-ontology" / "data.json"
    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "plugin settings not checked (no .obsidian/plugins/tag-ontology/data.json)"
    except (OSError, ValueError) as e:
        return f"plugin settings not checked (can't read .obsidian/plugins/tag-ontology/data.json: {e})"
    if not isinstance(raw, dict):
        return "plugin settings not checked (invalid .obsidian/plugins/tag-ontology/data.json)"
    settings = cast(dict[str, object], raw)
    dictionary = settings.get("dictionaryPath")
    if settings.get("dictionaryPathExplicit") is not True or not isinstance(dictionary, str):
        return None
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
    clean = "OK" if result["notes"] else "no notes checked"
    print(f"{errors} error(s), {len(issues) - errors} warning(s)" if issues else clean)
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


def _rule_document_sources(root: Path, category_dictionary: str) -> list[tuple[Path, Path]]:
    category_source = category_dictionary if Path(category_dictionary).suffix == ".md" else "Category-Dictionary.md"
    return [
        (root / "Tag-Dictionary.md", root / "tow/tags.md"),
        (root / category_source, root / "tow/categories.md"),
    ]


def _rule_document_body(source: Path) -> str:
    body = body_bytes(source.read_bytes()).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    lines = body.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _manual_append_plan(
    root: Path,
    category_dictionary: str,
    bases: dict[Path, str] | None = None,
) -> tuple[dict[Path, str], list[tuple[Path, Path]]]:
    starters = Path(__file__).parent / "starters"
    bases = bases or {}
    updates: dict[Path, str] = {}
    appended: list[tuple[Path, Path]] = []
    for source, target in _rule_document_sources(root, category_dictionary):
        if not source.is_file():
            continue
        if not source.resolve().is_relative_to(root.resolve()):
            raise ConfigError(f"migration source must stay inside the vault: {source}")
        if not target.resolve().is_relative_to(root.resolve()):
            raise ConfigError(f"migration target must stay inside the vault: {target}")
        body = _rule_document_body(source)
        if target.is_file():
            current = target.read_text(encoding="utf-8")
        elif target in bases:
            current = bases[target]
        else:
            current = (starters / target.name).read_text(encoding="utf-8")
        updates[target] = current
        if body in current:
            continue
        prefix = current.rstrip("\n")
        separator = "\n\n" if prefix else ""
        updated = f"{prefix}{separator}## Moved from {source.name}\n\n{body}\n"
        updates[target] = updated
        appended.append((source, target))
    return updates, appended


def _report_manual_appends(root: Path, appended: list[tuple[Path, Path]], apply: bool) -> None:
    for source, target in appended:
        action = "appended" if apply else "would append"
        print(f"{action} {source.name} to {target.relative_to(root)}")


def _remove_rule_documents(root: Path, category_dictionary: str, apply: bool, *, report: bool = True) -> bool:
    candidates: list[tuple[Path, Path]] = []
    kept: list[tuple[Path, Path]] = []
    custom_category = root / category_dictionary
    for source, target in _rule_document_sources(root, category_dictionary):
        if not source.is_file() or (source == custom_category and source != root / "Category-Dictionary.md"):
            continue
        if not source.resolve().is_relative_to(root.resolve()):
            raise ConfigError(f"migration source must stay inside the vault: {source}")
        if not target.resolve().is_relative_to(root.resolve()):
            raise ConfigError(f"migration target must stay inside the vault: {target}")
        body = _rule_document_body(source)
        manual = target.read_text(encoding="utf-8") if target.is_file() else ""
        (candidates if body in manual else kept).append((source, target))
    if report:
        for source, target in kept:
            print(
                f"kept {source.name}: its text is not in {target.relative_to(root)} yet; "
                'run "tow migrate --apply" first'
            )
    for source, target in candidates:
        if report and not apply:
            print(f"would delete {source.relative_to(root)}")
            continue
        if not apply:
            continue
        source.unlink()
        if report:
            print(f"deleted {source.relative_to(root)}")
            print(
                f"notes that link to {source.name} need their links updated; "
                f"its text now lives in {target.relative_to(root)}"
            )
    return bool(candidates and apply)


def cmd_migrate(root: Path, apply: bool, remove_legacy: bool, scope: str | None = None) -> int:
    """Move legacy or dot-layout vault files into tow/, or separately remove verified originals.

    `scope` records the search scope in the tow/config.json a legacy migration creates.
    """
    layout = vault_layout(root)
    if scope is not None and remove_legacy:
        raise ConfigError("--scope applies when creating tow/, not with --remove-legacy")
    if layout in ("tow", "dot"):
        current = read_config(root)
        if scope is not None and scope != current["scope"]:
            raise ConfigError(
                f'this vault already has settings; set "scope": "{scope}" in {vault_folder(layout)}/config.json'
            )
        if not remove_legacy:
            warn_if_scope_is_empty(root, current, layout)
    if layout == "tow":
        raw = json.loads((root / "tow/config.json").read_text(encoding="utf-8"))
        cfg = load_config(raw, TOW_DEFAULTS)
        category_dictionary = str(cast(dict[str, object], raw).get("categoryDictionary", cfg["categoryDictionary"]))
        if remove_legacy:
            if (root / ".tow" / "config.json").is_file():
                return cmd_migrate_dot(root, apply, True)
            if is_legacy_vault(root):
                return cmd_migrate_legacy(root, apply, True)
            _remove_rule_documents(root, category_dictionary, apply)
            return 0
        updates, appended = _manual_append_plan(root, category_dictionary)
        _report_manual_appends(root, appended, apply)
        if not apply:
            if not appended:
                print("already in tow/")
            return 0
        for target, text in updates.items():
            write_text_atomic(target, text)
        if not appended:
            print("already in tow/")
        return 0
    if layout == "dot":
        return cmd_migrate_dot(root, apply, remove_legacy)
    if layout != "legacy":
        raise ConfigError(f"tow migrate requires a vault: {root}")
    return cmd_migrate_legacy(root, apply, remove_legacy, scope)


def cmd_migrate_dot(root: Path, apply: bool, remove_legacy: bool) -> int:
    """Copy every regular file from the dot bundle and verify before optional removal."""
    source_root = root / ".tow"
    config_source = source_root / "config.json"
    try:
        raw: object = json.loads(config_source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ConfigError(f".tow/config.json: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(".tow/config.json: expected kind vault")
    dot_config = cast(dict[str, object], raw)
    if dot_config.get("kind") != "vault":
        raise ConfigError(".tow/config.json: expected kind vault")
    migrated: dict[str, object] = {}
    for key, value in dot_config.items():
        if isinstance(value, str) and (value == ".tow" or value.startswith(".tow/")):
            migrated[key] = "tow" + value.removeprefix(".tow")
        else:
            migrated[key] = value
    expected_config = json.dumps(migrated, ensure_ascii=False, indent=2) + "\n"
    sources = sorted(source_root.rglob("*"))
    files = [path for path in sources if path.is_file()]
    if any(path.is_symlink() or (path.is_dir() and path.is_symlink()) for path in sources):
        raise ConfigError("migration does not support symlinks inside .tow/")
    expected: dict[Path, bytes] = {}
    for source in files:
        relative = source.relative_to(source_root)
        target = root / "tow" / relative
        if not target.resolve().is_relative_to(root.resolve()):
            raise ConfigError(f"migration target must stay inside the vault: {target}")
        expected[target] = expected_config.encode("utf-8") if source == config_source else source.read_bytes()
    category_dictionary = str(dot_config.get("categoryDictionary", TOW_DEFAULTS["categoryDictionary"]))
    manual_bases = {
        target: content.decode("utf-8")
        for target, content in expected.items()
        if target.name in {"tags.md", "categories.md"}
    }
    copied = expected.copy()
    if remove_legacy:
        manual_updates, appended = {}, []
    else:
        manual_bases.update({target: target.read_text(encoding="utf-8") for target in manual_bases if target.is_file()})
        manual_updates, appended = _manual_append_plan(root, category_dictionary, manual_bases)
    appended_targets = {target for _, target in appended}
    for target, text in manual_updates.items():
        expected[target] = text.encode("utf-8")
    _report_manual_appends(root, appended, apply)
    for target, content in copied.items():
        differs = (target.exists() or target.is_symlink()) and (not target.is_file() or target.read_bytes() != content)
        if differs and not remove_legacy:
            raise ConfigError(f"migration target already exists with different contents: {target.relative_to(root)}")

    if remove_legacy:
        try:
            _remove_rule_documents(root, category_dictionary, False, report=False)
        except (OSError, ConfigError) as e:
            raise ConfigError(f"migration verification failed: {e}") from e
        verified: list[Path] = []
        changed: list[tuple[Path, Path]] = []
        try:
            for source in files:
                target = root / "tow" / source.relative_to(source_root)
                if target.is_file() and target.read_bytes() == expected[target]:
                    verified.append(source)
                else:
                    changed.append((target, source))
        except OSError as e:
            raise ConfigError(f"migration verification failed: {e}") from e
        for target, source in changed:
            print(
                f"changed {target.relative_to(root)}; kept legacy original "
                f"{source.relative_to(root)} because it differs"
            )
        try:
            _remove_rule_documents(root, category_dictionary, apply)
        except (OSError, ConfigError) as e:
            raise ConfigError(f"migration verification failed: {e}") from e
        if not apply:
            for source in verified:
                print(f"would delete {source.relative_to(root)}")
            print("run again with --remove-legacy --apply to delete verified legacy files")
            return 0
        if verified:
            print(
                "update the Tag Ontology plugin to 0.10.1 or later on every device first; older plugins read "
                "the root or .tow/ file"
            )
        for source in verified:
            source.unlink()
            print(f"deleted {source.relative_to(root)}")
        for folder in sorted((path for path in source_root.rglob("*") if path.is_dir()), reverse=True):
            with contextlib.suppress(OSError):
                folder.rmdir()
        try:
            source_root.rmdir()
        except OSError:
            pass
        else:
            print("deleted .tow/")
        return 0

    if not apply:
        for target in expected:
            if not target.is_file():
                print(f"would create {target.relative_to(root)}")
        print("run again with --apply to create tow/")
        return 0
    created = False
    for target, content in expected.items():
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            write_text_atomic(target, content.decode("utf-8"), exclusive=True)
            print(f"created {target.relative_to(root)}")
            created = True
        elif target in appended_targets:
            write_text_atomic(target, content.decode("utf-8"))
    if any(not target.is_file() or target.read_bytes() != content for target, content in expected.items()):
        raise ConfigError("migration verification failed; dot-layout files were kept")
    print("migration complete")
    if created:
        print(KEPT_ORIGINALS, file=sys.stderr)
    return 0


def cmd_migrate_legacy(root: Path, apply: bool, remove_legacy: bool, scope: str | None = None) -> int:
    """Copy a legacy vault into tow/, or separately verify then remove its originals."""
    targets = tuple(root / path for path in TOW_BUNDLE)
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
    legacy_tag_source = validated_config["tagDictionary"] == "Tag-Dictionary.json"
    category_source_is_markdown = Path(validated_config["categoryDictionary"]).suffix == ".md"
    if legacy_tag_source:
        migrated_config.pop("tagDictionary", None)
    if category_source_is_markdown:
        migrated_config["categoryDictionary"] = TOW_DEFAULTS["categoryDictionary"]
    if scope is not None:
        if original_config.get("scope", scope) != scope:
            raise ConfigError(f'tow.json already sets "scope"; change it there instead of passing --scope {scope}')
        migrated_config["scope"] = scope
    migrated_config = {"kind": "vault", **migrated_config}
    if not remove_legacy and scope_is_empty(
        root, {**validated_config, "scope": str(migrated_config.get("scope", "para"))}
    ):
        folders = ", ".join(validated_config[key] for key in PARA)
        print(
            f"tow: warning: no PARA folders ({folders}) in {root}, so the migrated vault's search scope is empty; "
            'add "--scope vault" to search every folder, or preview "tow init" afterwards to create the PARA folders',
            file=sys.stderr,
        )

    tag_source = root / validated_config["tagDictionary"]
    category_source = root / validated_config["categoryDictionary"]
    missing_sources = [source for source in (tag_source, category_source) if not source.is_file()]
    for source in (tag_source, category_source):
        if not source.resolve().is_relative_to(root.resolve()):
            raise ConfigError(f"migration source must stay inside the vault: {source}")
    if Path(validated_config["categoryDictionary"]).suffix != ".md":
        raise ConfigError(f"migration requires a Markdown category dictionary: {category_source}")
    empty_plugin_starter = legacy_tag_source and is_empty_plugin_dictionary(root)
    try:
        tag_bytes = b"{\n}\n" if tag_source in missing_sources or empty_plugin_starter else tag_source.read_bytes()
        category_text = "" if category_source in missing_sources else category_source.read_text(encoding="utf-8")
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
            new_config_raw = json.loads(targets[0].read_text(encoding="utf-8"))
            new_config = cast(dict[str, object], new_config_raw) if isinstance(new_config_raw, dict) else {}
            tag_copy = targets[2].read_bytes()
            category_copy = category_entries(targets[4].read_text(encoding="utf-8"))
            changed_copies = [
                (copy, source)
                for copy, source, matches in (
                    (targets[2], tag_source, tag_copy == tag_bytes),
                    (targets[4], category_source, category_copy == category_entries_to_write),
                )
                if not matches and source not in missing_sources and (copy != targets[2] or legacy_tag_source)
            ]
            for copy, source in changed_copies:
                message = (
                    f"changed {copy.relative_to(root)}; kept legacy original {source.relative_to(root)} "
                    "because it differs"
                )
                print(message)
            legacy_paths = [config_path]
            if (
                legacy_tag_source
                and tag_source not in missing_sources
                and tag_source.is_file()
                and tag_copy == tag_bytes
            ):
                legacy_paths.append(tag_source)
            legacy_paths = [path for path in legacy_paths if path.is_file()]
            for manual in (targets[1], targets[3]):
                if not manual.is_file():
                    raise ConfigError(f"migration verification failed: missing {manual.relative_to(root)}")
        except (OSError, ValueError, ConfigError) as e:
            if isinstance(e, ConfigError) and str(e).startswith("migration verification failed"):
                raise
            raise ConfigError(f"migration verification failed: {e}") from e
        expected_values = {key: value for key, value in migrated_config.items() if key != "kind"}
        expected_values.pop("categoryDictionary", None)
        config_matches = new_config.get("kind") == "vault" and all(
            new_config.get(key) == value for key, value in expected_values.items()
        )
        if not config_matches:
            raise ConfigError("migration verification failed; legacy files were kept")
        try:
            _remove_rule_documents(root, validated_config["categoryDictionary"], apply)
        except (OSError, ConfigError) as e:
            raise ConfigError(f"migration verification failed: {e}") from e
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
        targets[1]: (starters / "tags.md").read_text(encoding="utf-8"),
        targets[2]: tag_bytes.decode("utf-8"),
        targets[3]: (starters / "categories.md").read_text(encoding="utf-8"),
        targets[4]: serialize_entries(category_entries_to_write),
    }
    config_target = targets[0]
    config_text = json.dumps(migrated_config, ensure_ascii=False, indent=2) + "\n"
    expected = {**output, config_target: config_text}
    missing_dictionary_targets = {
        targets[2] if source == tag_source else targets[4]
        for source in missing_sources
        if (targets[2] if source == tag_source else targets[4]).is_file()
    }
    expected = {target: text for target, text in expected.items() if target not in missing_dictionary_targets}
    output = {target: text for target, text in output.items() if target not in missing_dictionary_targets}
    for target in missing_dictionary_targets:
        source = tag_source if target == targets[2] else category_source
        print(f"kept existing {target.relative_to(root)} (no {source.name} to copy)")
    updates, appended = _manual_append_plan(root, validated_config["categoryDictionary"], output)
    output.update({target: text for target, text in updates.items() if target not in missing_dictionary_targets})
    expected.update({target: text for target, text in updates.items() if target not in missing_dictionary_targets})
    _report_manual_appends(root, appended, apply)
    for target, text in expected.items():
        if (
            (target.exists() or target.is_symlink())
            and (not target.is_file() or target.read_bytes() != text.encode("utf-8"))
            and target not in targets[1:4:2]
        ):
            raise ConfigError(f"migration target already exists with different contents: {target.relative_to(root)}")

    complete_before = all(target.is_file() for target in expected)
    for source in missing_sources:
        target = targets[2] if source == tag_source else targets[4]
        if not apply and not target.is_file():
            print(f"missing; would create empty dictionary {target.relative_to(root)}")
    for target, text in output.items():
        if not target.exists():
            if apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                write_text_atomic(target, text, exclusive=True)
                if (target == targets[2] and tag_source in missing_sources) or (
                    target == targets[4] and category_source in missing_sources
                ):
                    print(f"missing; created empty dictionary {target.relative_to(root)}")
            print(f"{'created' if apply else 'would create'} {target.relative_to(root)}")
        elif target in updates and apply and not (target.is_file() and target.read_text(encoding="utf-8") == text):
            write_text_atomic(target, text)

    if apply:
        try:
            if any(
                not target.is_file() or target.read_bytes() != text.encode("utf-8") for target, text in output.items()
            ):
                raise ConfigError("migration verification failed; legacy files were kept")
        except OSError as e:
            raise ConfigError(f"migration verification failed: {e}") from e
        if not config_target.exists():
            config_target.parent.mkdir(parents=True, exist_ok=True)
            write_text_atomic(config_target, config_text, exclusive=True)
            print(f"created {config_target.relative_to(root)}")
        try:
            if any(
                not target.is_file() or target.read_bytes() != text.encode("utf-8") for target, text in expected.items()
            ):
                raise ConfigError("migration verification failed; legacy files were kept")
        except OSError as e:
            raise ConfigError(f"migration verification failed: {e}") from e
        print("nothing to migrate" if complete_before else "migration complete")
        if not complete_before:
            print(KEPT_ORIGINALS, file=sys.stderr)
    elif all(target.is_file() for target in expected):
        print("nothing to migrate")
    else:
        if not config_target.exists():
            print(f"would create {config_target.relative_to(root)}")
        print("run again with --apply to create tow/")
    return 0


def cmd_find(
    root: Path, cfg: dict[str, str], prefix: str | None, filters: dict[str, str], include_archive: bool
) -> int:
    from tow_search import find_query, matches_scan_query, parse_query

    extra = [] if include_archive or cfg["scope"] == "vault" else ["--exclude", f"**/{cfg['projectArchive']}"]
    notes = scan(root, cfg, [], extra)["notes"]
    query, warnings, _ = parse_query(find_query(prefix, filters))
    if warnings or query is None:
        raise ConfigError("could not translate find options into a search query")
    for note_result in notes:
        if note_result["frontmatter"] and matches_scan_query(query, note_result):
            print(note_result["path"])
    return 0


def missing_paths(
    root: Path,
    cfg: dict[str, str],
    dictionaries: bool = False,
    layout: Literal["tow", "dot", "legacy", "plain"] = "plain",
) -> list[str]:
    """Folders and starter files missing from the selected vault layout."""
    legacy = layout == "legacy"
    folder = "tow" if layout in ("tow", "plain") else ".tow" if layout == "dot" else ""
    folders = [*(cfg[k] for k in PARA), cfg["inbox"]] if cfg["scope"] == "para" else []
    missing = [f"{f}/" for f in folders if not (root / f).is_dir()]
    if legacy:
        if cfg["scope"] == "para" or dictionaries:
            missing += [cfg[k] for k in DICTIONARY_PATHS if not (root / cfg[k]).exists()]
        return missing
    manuals = (f"{folder}/tags.md", f"{folder}/categories.md")
    dictionary_paths = [cfg[key] for key in DICTIONARY_PATHS] if cfg["scope"] == "para" or dictionaries else []
    return [
        *missing,
        *(path for path in (f"{folder}/config.json", *manuals) if not (root / path).exists()),
        *(path for path in dictionary_paths if not (root / path).exists()),
    ]


def _has_other_notes(root: Path, cfg: Mapping[str, str]) -> bool:
    """Whether the vault root holds a note or folder that the PARA scope would leave out."""
    para = {cfg[key] for key in (*PARA, "inbox")}
    return any(
        not entry.name.startswith(".")
        and entry.name not in para
        and entry.name != "tow"
        and (entry.is_dir() or entry.suffix == ".md")
        for entry in root.iterdir()
    )


def _starter_config(scope: str | None) -> str:
    if scope is None:
        return '{"kind": "vault"}\n'
    return json.dumps({"kind": "vault", "scope": scope}, indent=2) + "\n"


def cmd_init(
    root: Path,
    cfg: dict[str, str],
    apply: bool,
    dictionaries: bool = False,
    layout: Literal["tow", "dot", "legacy", "plain"] | None = None,
    scope: str | None = None,
) -> int:
    """List what's missing; with `apply`, create it. Never overwrites an existing file.

    `scope` records the search scope in a new vault config; `vault` keeps the folders as they are.
    """
    current_layout = layout or vault_layout(root)
    legacy = current_layout == "legacy"
    folder = vault_folder(current_layout) or ("tow" if current_layout == "plain" else "")
    if scope is not None and current_layout != "plain":
        if scope != cfg["scope"]:
            where = 'tow.json, or preview "tow migrate --scope ' + scope + '"' if legacy else f"{folder}/config.json"
            raise ConfigError(f'this vault already has settings; set "scope": "{scope}" in {where}')
        scope = None
    if current_layout == "plain" and scope is None and scope_is_empty(root, cfg) and _has_other_notes(root, cfg):
        print(
            "tow: this folder has notes outside the PARA folders; to keep its layout and search every folder, "
            'preview "tow init --scope vault" instead',
            file=sys.stderr,
        )
    if not legacy and is_empty_plugin_dictionary(root):
        print(
            "tow: Tag-Dictionary.json is the plugin's empty starter; it is not copied, the plugin switches to "
            "tow/tag-dictionary.json once it exists, and you can delete the root file",
            file=sys.stderr,
        )
    nonempty_legacy_dictionary = (root / "Tag-Dictionary.json").is_file() and not is_empty_plugin_dictionary(root)
    init_cfg = cfg
    if not legacy and current_layout == "plain":
        init_cfg = {**TOW_DEFAULTS, **{key: value for key, value in cfg.items() if value != DEFAULTS.get(key)}}
        if scope is not None:
            init_cfg["scope"] = scope
    init_cfg = {**init_cfg, **{key: Path(init_cfg[key].replace("\\", "/")).as_posix() for key in DICTIONARY_PATHS}}
    folders = [root / init_cfg[k] for k in (*PARA, "inbox")] if init_cfg["scope"] == "para" else []
    dictionary_paths = (
        [init_cfg[key] for key in DICTIONARY_PATHS] if init_cfg["scope"] == "para" or dictionaries else []
    )
    if legacy:
        files = [root / path for path in dictionary_paths]
    else:
        manuals = (f"{folder}/tags.md", f"{folder}/categories.md")
        bundle = (f"{folder}/config.json", *manuals, *dictionary_paths)
        files = [root / path for path in bundle]
        if nonempty_legacy_dictionary and init_cfg["tagDictionary"] == TOW_DEFAULTS["tagDictionary"]:
            files = [path for path in files if path != root / init_cfg["tagDictionary"]]
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
    dictionary_files = {root / path for path in dictionary_paths}
    if legacy:
        if layout == "legacy" or is_legacy_vault(root):
            print('tow: legacy vault; run "tow migrate" to create tow/', file=sys.stderr)
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
        starter_files = TOW_BUNDLE_STARTER_FILES if current_layout != "dot" else DOT_BUNDLE_STARTER_FILES
        starters = {
            str(p.relative_to(root)): (
                _starter_config(scope)
                if p.relative_to(root).as_posix() == f"{folder}/config.json"
                else (
                    LEGACY_STARTER_CATEGORIES.format(today=date.today().isoformat())
                    if p in dictionary_files and p == root / init_cfg["categoryDictionary"] and p.suffix == ".md"
                    else serialize_entries({})
                    if p in dictionary_files
                    else (Path(__file__).parent / "starters" / starter_files[p.relative_to(root).as_posix()]).read_text(
                        encoding="utf-8"
                    )
                )
            )
            for p in files
        }
    missing = missing_paths(root, init_cfg, dictionaries, current_layout)
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


def scope_is_empty(root: Path, cfg: Mapping[str, str]) -> bool:
    """Whether the default PARA scope names no existing folder, so pathless note scans read nothing."""
    return cfg["scope"] == "para" and not any((root / cfg[k]).is_dir() for k in PARA)


def empty_scope_message(root: Path, cfg: Mapping[str, str], layout: VaultLayout) -> str:
    """Why the scope is empty and the command or setting that fixes it in this layout."""
    folders = ", ".join(cfg[k] for k in PARA)
    if layout == "plain":
        fix = 'preview "tow init --scope vault" to search every folder'
    elif layout == "legacy":
        fix = 'preview "tow migrate --scope vault" (or set "scope": "vault" in tow.json) to search every folder'
    else:
        fix = f'set "scope": "vault" in {vault_folder(layout)}/config.json to search every folder'
    return (
        f"no PARA folders ({folders}) in {root}, so the search scope is empty; "
        f'{fix}, or preview "tow init" to create the PARA folders'
    )


def warn_if_scope_is_empty(root: Path, cfg: Mapping[str, str], layout: VaultLayout) -> bool:
    if not scope_is_empty(root, cfg):
        return False
    print(f"tow: warning: {empty_scope_message(root, cfg, layout)}", file=sys.stderr)
    return True


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
        if vault_layout(root) == "plain":
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
    p.add_argument(
        "--scope", choices=SCOPES, help="record the search scope in a new vault config (vault: every folder)"
    )
    p = sub.add_parser("migrate", help="preview or migrate an older vault into tow/")
    p.add_argument("--apply", action="store_true", help="write the migration or delete verified legacy files")
    p.add_argument("--remove-legacy", action="store_true", help="delete older files after verifying tow/ copies")
    p.add_argument("--scope", choices=SCOPES, help="record the search scope when a legacy vault moves into tow/")
    p = sub.add_parser("lint", help="check classification fields and tag counts")
    p.add_argument("paths", nargs="*")
    p = sub.add_parser("category", help="manage registered categories")
    category_sub = p.add_subparsers(dest="category_command", required=True)
    p = category_sub.add_parser("add", help="add a category value after approval")
    p.add_argument("value")
    p.add_argument("description")
    p.add_argument("--apply", action="store_true", help="write the category dictionary")
    p = sub.add_parser("project", help="manage project metadata")
    project_sub = p.add_subparsers(dest="project_command", required=True)
    p = project_sub.add_parser(
        "init", help="initialize project metadata; --apply creates the files, including .tow/.gitignore"
    )
    p.add_argument("--mode", choices=("local", "shared"), required=True)
    p.add_argument("--exclude", action="append", default=[], metavar="GLOB", help="exclude a project document glob")
    p.add_argument("--apply", action="store_true", help="create project metadata")
    p = project_sub.add_parser("tag", help="attach approved tags to project documents; --apply writes .tow/")
    p.add_argument("changes", type=Path, help='{"documents": {path: [tag, ...]}, "concepts": {tag: {...}}}')
    p.add_argument("--apply", action="store_true", help="write project .tow/ files")
    project_sub.add_parser("status", help="report stale documents and unknown tags")
    project_sub.add_parser("files", help="list Markdown files with Git status")
    p = project_sub.add_parser("concepts", help="print project-only concept additions for a vault")
    p.add_argument("project_path", type=Path, help="project directory")
    p = sub.add_parser("send", help="create a new vault note from a project draft")
    p.add_argument("draft", type=Path, help="draft note containing frontmatter and body")
    p.add_argument("dest", help="new vault-relative note path under a configured note folder")
    p.add_argument("--source", type=Path, help="original selected content to preserve exactly")
    p.add_argument("--transformed", action="store_true", help="allow draft body to differ from the source")
    p.add_argument("--apply", action="store_true", help="create the note (never overwrites)")
    p = sub.add_parser("verify-body", help="compare exact body bytes after a metadata-only edit (read-only)")
    p.add_argument("before", type=Path, help="independent snapshot inside the vault")
    p.add_argument("after", type=Path, help="candidate note inside the vault")
    p = sub.add_parser(
        "lookup",
        help="find notes matching one concept in the vault and current project; shortcut of tow search tag:<tag>",
    )
    p.add_argument("tag", help="tag name or alias")
    p.add_argument("--exact", action="store_true", help="match only this tag, not narrower concepts")
    p = sub.add_parser("search", help="search notes with a query")
    p.add_argument(
        "query",
        nargs="?",
        default="",
        help=(
            "search notes with a query: terms, tag:, title:, heading:, text:, path:, category:, type:, status:, kind:, "
            "source:; AND by space, OR, -NOT, ( ), quotes"
        ),
    )
    p = sub.add_parser("find", help="find notes by category prefix, frontmatter fields and tag")
    p.add_argument("prefix", nargs="?", help="category prefix: matches the category and everything below it")
    for key in FIND_FILTERS:
        p.add_argument(f"--{key}", help=f"only notes with this {key}")
    p.add_argument("--all", action="store_true", help="include project archive folders")
    p = sub.add_parser("ontology", help="run the tag-ontology CLI with the vault's settings")
    p.add_argument("cli_command")
    p.add_argument("cli_args", nargs=argparse.REMAINDER)
    arguments = list(sys.argv[1:] if argv is None else argv)
    command_index = 0
    while command_index < len(arguments):
        if arguments[command_index] == "--root":
            command_index += 2
        elif arguments[command_index].startswith("--root=") or arguments[command_index].startswith("-"):
            command_index += 1
        else:
            break
    if command_index < len(arguments) and arguments[command_index] == "search":
        query_arguments = arguments[command_index + 1 :]
        if query_arguments == ["-h"] or query_arguments == ["--help"]:
            args = parser.parse_args(arguments[: command_index + 1] + query_arguments)
            search_query = None
        else:
            if query_arguments[:1] == ["--"]:
                query_arguments = query_arguments[1:]
            search_query = " ".join(query_arguments)
            args = parser.parse_args(arguments[: command_index + 1])
    else:
        args = parser.parse_args(arguments)
        search_query = None
    filters: dict[str, str] = {}
    if args.command == "find":
        filters = {key: value for key in FIND_FILTERS if (value := getattr(args, key)) is not None}
        if args.prefix is None and not filters:
            parser.error("find needs a category prefix or at least one of --type, --status, --kind, --tag")

    if args.command == "search" and not search_query:
        parser.error("search needs a query")

    try:
        if args.command == "connect":
            return cmd_connect(args.vault, args.apply)
        if args.command == "project" and args.project_command == "files":
            project = resolve_project(Path.cwd(), None)
            return cmd_project_files(project or Path.cwd())
        if args.command == "project" and args.project_command == "status":
            try:
                vault_ref = resolve_vault(Path.cwd(), args.root, os.environ)
            except ConfigError as e:
                if args.root is None and str(e).startswith("no vault found"):
                    project = resolve_project(Path.cwd(), None)
                    return cmd_project_status(project or Path.cwd())
                raise
            project = resolve_project(Path.cwd(), vault_ref.root)
            return cmd_project_status(project or Path.cwd(), vault_ref.root, read_config(vault_ref.root))
        if args.command == "project" and args.project_command == "concepts":
            vault = resolve_vault(Path.cwd(), args.root, os.environ).root
            if not Path.cwd().resolve().is_relative_to(vault.resolve()):
                raise ConfigError(f"project concepts must run inside the vault: {vault}")
            return cmd_project_concepts(args.project_path, vault, read_config(vault))
        vault_ref = resolve_vault(Path.cwd(), args.root, os.environ)
        root = vault_ref.root
        if args.command in ("lookup", "search"):
            cfg = read_config(root)
            project = resolve_project(Path.cwd(), root)
            unregistered: Path | None = None
            if (
                project is not None
                and tow_kind(project) != "project"
                and not (project / ".tow" / "config.json").is_file()
            ):
                unregistered, project = project, None
            if args.command == "lookup":
                show_args = [args.tag, "--notes", "--json"]
                if args.exact:
                    show_args.append("--exact")
                vault_args = ontology_args("show", show_args, str(root), cfg, scope_excludes(root, cfg, []))
                skipped = (
                    "search scope is empty (no PARA folders); no vault notes were searched"
                    if warn_if_scope_is_empty(root, cfg, vault_ref.layout)
                    else None
                )
                return cmd_lookup(root, cfg, project, args.tag, args.exact, vault_args, skipped)
            query = search_query if search_query is not None else args.query
            vault_args = ontology_args("show", ["--notes", "--json"], str(root), cfg, scope_excludes(root, cfg, []))
            return cmd_search(root, cfg, project, query, vault_args, unregistered)
        if args.command == "verify-body":
            return cmd_verify_body(root, args.before, args.after)
        cfg = read_config(root)
        if args.command == "send":
            return cmd_send(root, cfg, args.draft, args.dest, args.source, args.transformed, args.apply)
        if args.command == "project":
            project = resolve_project(Path.cwd(), root)
            if project is None:
                raise ConfigError(f"project {args.project_command} must run outside the vault")
            if args.project_command == "tag":
                return cmd_project_tag(project, root, cfg, args.changes, args.apply)
            return cmd_project_init(project, root, cfg, args.mode, args.exclude, args.apply)
        if args.command == "config":
            print(json.dumps(cfg, ensure_ascii=False, indent=2))
            print(f"tow: vault {root} (from {vault_ref.source}, {vault_ref.layout})", file=sys.stderr)
            if vault_ref.layout == "dot":
                print(
                    'tow: this vault keeps TOW files in .tow/; run "tow migrate" to move them to tow/ '
                    "(Obsidian Sync does not sync .tow/)",
                    file=sys.stderr,
                )
            elif vault_ref.layout == "legacy":
                print(
                    'tow: this vault keeps TOW files in the vault root; run "tow migrate" to move them to tow/ '
                    "(Obsidian Sync does not sync .tow/)",
                    file=sys.stderr,
                )
            warning = plugin_dictionary_warning(root, cfg)
            if warning:
                print(f"tow: warning: {warning}", file=sys.stderr)
            return 0
        if args.command == "init":
            if args.apply:
                require_inside(root, Path.cwd(), "init --apply")
            return cmd_init(root, cfg, args.apply, args.dictionaries, vault_ref.layout, args.scope)
        if args.command == "migrate":
            if args.apply:
                require_inside(root, Path.cwd(), "migrate --apply")
            return cmd_migrate(root, args.apply, args.remove_legacy, args.scope)
        if args.command == "category":
            if args.apply:
                require_inside(root, Path.cwd(), "category add --apply")
            return cmd_category_add(root, cfg, args.value, args.description, args.apply)
        named: list[str] = args.paths if args.command == "lint" else []
        if args.command == "ontology" and args.cli_command in PATH_COMMANDS:
            named = args.cli_args
        if (
            args.command in ("lint", "find") or (args.command == "ontology" and args.cli_command in NOTE_COMMANDS)
        ) and not _named_roots(root, named):
            usage = args.command == "ontology" and args.cli_command == "usage" and "--help" not in named
            if usage and scope_is_empty(root, cfg):
                # Every leaf tag would come back as unused when no note is read.
                raise ConfigError(
                    f"{empty_scope_message(root, cfg, vault_ref.layout)}; "
                    "usage compares notes with the dictionary, so nothing was read"
                )
            warn_if_scope_is_empty(root, cfg, vault_ref.layout)
        if args.command == "lint":
            return cmd_lint(root, cfg, args.paths)
        if args.command == "find":
            return cmd_find(root, cfg, args.prefix, filters, args.all)
        if args.command == "ontology" and args.cli_command == "apply":
            require_inside(root, Path.cwd(), "ontology apply")
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
