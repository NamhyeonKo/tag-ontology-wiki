#!/usr/bin/env python3
"""TOW vault convention checks (standard library only).

  tow.py [--root DIR] config                 print the settings in effect (tow.json + defaults)
  tow.py [--root DIR] lint [PATH...]         check classification fields and tag counts (default: all PARA folders)
  tow.py [--root DIR] find [PREFIX] [--type T] [--status S] [--kind K] [--tag TAG] [--all]
                                             notes that meet every condition (--all: with project archives)
  tow.py [--root DIR] ontology CMD [ARG...]  run the tag-ontology CLI with the vault's settings

Notes are read through `tag-ontology scan --json`; this script never parses Markdown itself.
Set TOW_TAG_ONTOLOGY to change the CLI command (default: npx --yes tag-ontology@0.1.2).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal, TypedDict, cast

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
}
PARA: Final = ("projects", "areas", "resources", "archives")
FOLDER_KEYS: Final = (*PARA, "projectArchive", "inbox", "misc")
WORKFLOW_PATHS: Final = ("attachments", "dailyNotes")

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

NOTE_COMMANDS: Final = frozenset({"scan", "usage", "show"})
PATH_COMMANDS: Final = frozenset({"scan", "usage"})
VALUE_OPTIONS: Final = frozenset({"--root", "--dictionary", "--exclude", "--names", "--base"})
# Public plugin directories require an exact version for downloaded executables.
DEFAULT_CLI: Final = "npx --yes tag-ontology@0.1.2"


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


class ConfigError(Exception):
    pass


class CliError(Exception):
    pass


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


def load_config(raw: object) -> dict[str, str]:
    """Validate the content of tow.json and merge it over the defaults."""
    if not isinstance(raw, dict):
        raise ConfigError("must be a JSON object")
    values = cast(dict[str, object], raw)
    unknown = sorted(values.keys() - DEFAULTS.keys())
    if unknown:
        raise ConfigError(f"unknown keys: {', '.join(unknown)}")
    for key, value in values.items():
        if not isinstance(value, str) or not value:
            raise ConfigError(f"{key}: must be a non-empty string")
        if key in FOLDER_KEYS and ("/" in value or value in (".", "..")):
            raise ConfigError(f"{key}: must be a single folder name, without '/'")
        if key in WORKFLOW_PATHS:
            path = Path(value)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ConfigError(f"{key}: must be a vault-relative path without '..'")
    return {**DEFAULTS, **cast(dict[str, str], values)}


def ontology_args(command: str, args: list[str], root: str, cfg: dict[str, str], excludes: list[str]) -> list[str]:
    """Arguments for the tag-ontology CLI, with the vault root, dictionary, tag name rule and note scope added.

    `--all` is a TOW option: it keeps project archives in `show` and is not passed on.
    """
    out = [command, *(a for a in args if a != "--all"), "--root", root]
    if command != "scan":
        out += ["--dictionary", cfg["tagDictionary"], "--names", "kebab"]
    if command in NOTE_COMMANDS:
        out += excludes
    if command == "show" and "--all" not in args:
        out += ["--exclude", f"**/{cfg['projectArchive']}"]
    return out


def scope_excludes(root: Path, cfg: dict[str, str], args: list[str]) -> list[str]:
    """An --exclude for each root entry (folder or .md) outside the PARA folders, except entries the args name."""
    # ponytail: names are passed as globs, so a folder name containing * ? [ may match differently.
    # If a vault needs that, ask for an escaping rule in the CLI contract.
    keep = {cfg[k] for k in PARA} | _named_roots(root, args)
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


def read_config(root: Path) -> dict[str, str]:
    path = root / "tow.json"
    if not path.exists():
        return dict(DEFAULTS)
    try:
        return load_config(json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, ConfigError) as e:
        raise ConfigError(f"tow.json: {e}") from e


def run_cli(args: list[str], capture: bool) -> subprocess.CompletedProcess[str]:
    command = shlex.split(os.environ.get("TOW_TAG_ONTOLOGY", DEFAULT_CLI))
    try:
        return subprocess.run([*command, *args], capture_output=capture, text=True, check=False)
    except FileNotFoundError as e:
        raise CliError(f"can't run the tag-ontology CLI ({e.filename}); it needs Node.js") from e


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
    dictionary = root / cfg["categoryDictionary"]
    try:
        categories = category_values(dictionary.read_text(encoding="utf-8"))
    except OSError as e:
        raise ConfigError(f"can't read the category dictionary: {dictionary}") from e
    result = scan(root, cfg, paths, [])
    issues = [Issue(i["code"], i["severity"], i.get("path", ""), i["message"]) for i in result["issues"]]
    issues += lint(result["notes"], categories)
    for i in issues:
        print(f"{i.severity} {i.code} {i.path}: {i.message}")
    errors = sum(i.severity == "error" for i in issues)
    print(f"{errors} error(s), {len(issues) - errors} warning(s)" if issues else "OK")
    return 1 if errors else 0


def cmd_find(
    root: Path, cfg: dict[str, str], prefix: str | None, filters: dict[str, str], include_archive: bool
) -> int:
    extra = [] if include_archive else ["--exclude", f"**/{cfg['projectArchive']}"]
    for path in find(scan(root, cfg, [], extra)["notes"], prefix, filters):
        print(path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tow", description="TOW vault convention checks")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="vault folder (default: current folder)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("config", help="print the settings in effect")
    p = sub.add_parser("lint", help="check classification fields and tag counts")
    p.add_argument("paths", nargs="*")
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

    root: Path = args.root.resolve()
    try:
        cfg = read_config(root)
        if args.command == "config":
            print(json.dumps(cfg, ensure_ascii=False, indent=2))
            return 0
        if args.command == "lint":
            return cmd_lint(root, cfg, args.paths)
        if args.command == "find":
            return cmd_find(root, cfg, args.prefix, filters, args.all)
        path_args: list[str] = args.cli_args if args.cli_command in PATH_COMMANDS else []
        excludes = scope_excludes(root, cfg, path_args)
        return run_cli(
            ontology_args(args.cli_command, args.cli_args, str(root), cfg, excludes), capture=False
        ).returncode
    except (ConfigError, CliError) as e:
        print(f"tow: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
