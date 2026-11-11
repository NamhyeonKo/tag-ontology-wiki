"""Query grammar, candidate discovery, and evaluation for ``tow search``."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal, TypedDict, cast

from tow_core import CliError, ConfigError, body_bytes, run_cli

FIELDS = ("tag", "title", "heading", "text", "path", "category", "type", "status", "kind", "source")
PARA = ("projects", "areas", "resources", "archives")
GIT_UNAVAILABLE = "vault: git is not available, so .gitignore rules can't be applied; body and heading search skipped"


@dataclass
class Candidates:
    paths: list[str]
    contents_ok: bool
    unavailable: list[str]


def vault_candidates(root: Path, cfg: Mapping[str, str]) -> Candidates:
    """List visible Markdown paths in the configured vault scope."""
    root = root.resolve()
    folders = [cfg[key] for key in PARA if (root / cfg[key]).is_dir()] if cfg["scope"] == "para" else ["."]

    def visible(path: str) -> bool:
        parts = PurePosixPath(path).parts
        return (
            bool(parts)
            and not any(part.startswith(".") for part in parts)
            and parts[0] != "tow"
            and (cfg["scope"] != "para" or parts[0] in folders)
            and not (cfg["scope"] == "para" and cfg["projectArchive"] in parts[1:-1])
            and path.endswith(".md")
        )

    def walk() -> list[str]:
        paths: list[str] = []
        for directory, names, files in os.walk(root):
            current = Path(directory)
            names[:] = [name for name in names if not name.startswith(".") and (current != root or name != "tow")]
            if cfg["scope"] == "para" and current == root:
                names[:] = [name for name in names if name in folders]
            for name in files:
                relative = (current / name).relative_to(root).as_posix()
                if visible(relative):
                    paths.append(relative)
        return sorted(set(paths))

    git_present = any((directory / ".git").exists() for directory in (root, *root.parents))
    try:
        check = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        paths = walk()
        return Candidates(paths, not git_present, [] if not git_present else [GIT_UNAVAILABLE])

    if check.returncode == 0 and check.stdout.strip() == "true":
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *folders],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return Candidates(sorted({path for path in result.stdout.split("\0") if path and visible(path)}), True, [])

    return Candidates(walk(), True, [])


@dataclass(frozen=True)
class Term:
    field: str | None
    value: str
    exact: bool = False


@dataclass(frozen=True)
class Not:
    node: Node


@dataclass(frozen=True)
class And:
    nodes: tuple[Node, ...]


@dataclass(frozen=True)
class Or:
    nodes: tuple[Node, ...]


Node = Term | Not | And | Or


class QueryWarning(TypedDict):
    code: str
    message: str
    retry: str | None


TokenKind = Literal["word", "or", "minus", "open", "close"]


@dataclass(frozen=True)
class _Token:
    kind: TokenKind
    value: str
    position: int
    term: Term | None = None


def _warn(warnings: list[tuple[int, str, str]], position: int, code: str, message: str) -> None:
    warnings.append((position, code, message))


def tokenize(text: str, warnings: list[tuple[int, str, str]]) -> list[_Token]:
    """Split query syntax while preserving quoted text and source positions."""
    tokens: list[_Token] = []
    index = 0
    while index < len(text):
        if text[index].isspace():
            index += 1
            continue
        if text[index] == "(":
            tokens.append(_Token("open", "(", index))
            index += 1
            continue
        if text[index] == ")":
            tokens.append(_Token("close", ")", index))
            index += 1
            continue
        if text[index] == "-":
            tokens.append(_Token("minus", "-", index))
            index += 1
            continue

        start = index
        quote_position: int | None = None
        quoted = False
        value: list[str] = []
        while index < len(text):
            character = text[index]
            if quoted:
                if character == "\\" and index + 1 < len(text):
                    value.extend((character, text[index + 1]))
                    index += 2
                    continue
                if character == '"':
                    quoted = False
                value.append(character)
                index += 1
                continue
            if character.isspace() or character in "()":
                break
            if character == '"':
                quoted = True
                quote_position = index
            if character == "\\" and index + 1 < len(text) and text[index + 1] in ('"', "\\"):
                value.extend((character, text[index + 1]))
                index += 2
                continue
            value.append(character)
            index += 1

        if quoted:
            position = quote_position if quote_position is not None else start
            _warn(
                warnings,
                position,
                "unclosed-quote",
                f"Closed the quote opened at position {position} at the end of the query.",
            )
            value.append('"')
        raw = "".join(value)
        kind: TokenKind = "or" if raw == "OR" and not raw.startswith('"') else "word"
        tokens.append(_Token(kind, raw, start))
    return tokens


def _decode(raw: str) -> str:
    value: list[str] = []
    quoted = False
    index = 0
    while index < len(raw):
        character = raw[index]
        if quoted and character == "\\" and index + 1 < len(raw) and raw[index + 1] in ("\\", '"'):
            value.append(raw[index + 1])
            index += 2
            continue
        if character == '"':
            quoted = not quoted
        else:
            value.append(character)
        index += 1
    return "".join(value)


def _term_from_token(token: _Token, warnings: list[tuple[int, str, str]]) -> Term | None:
    prefix, separator, raw_value = token.value.partition(":")
    is_field = (
        not token.value.startswith('"')
        and bool(separator)
        and prefix.isascii()
        and prefix.replace("_", "a").replace("-", "a").isalnum()
    )
    field: str | None = None
    exact = False
    if is_field:
        if prefix == "tag" and raw_value.startswith("="):
            raw_value = raw_value[1:]
            exact = True
        value = _decode(raw_value)
        if prefix == "tag":
            value = value.removeprefix("#")  # Obsidian writes tag:#work
        if not value:
            _warn(
                warnings,
                token.position,
                "empty-value",
                f"Dropped empty field value at position {token.position}.",
            )
            return None
        if prefix in FIELDS:
            field = prefix
        else:
            _warn(
                warnings,
                token.position,
                "unknown-field",
                f"Treated unknown field {prefix!r} as a bare term at position {token.position}.",
            )
            return Term(None, _decode(token.value))
        return Term(field, value, exact)

    value = _decode(token.value)
    if not value:
        _warn(
            warnings,
            token.position,
            "empty-value",
            f"Dropped empty value at position {token.position}.",
        )
        return None
    return Term(None, value)


def _prepare_tokens(tokens: list[_Token], text_length: int, warnings: list[tuple[int, str, str]]) -> list[_Token]:
    balanced: list[_Token] = []
    opens: list[_Token] = []
    for token in tokens:
        if token.kind == "open":
            opens.append(token)
            balanced.append(token)
        elif token.kind == "close":
            if opens:
                opens.pop()
                balanced.append(token)
            else:
                _warn(
                    warnings,
                    token.position,
                    "unmatched-close",
                    f"Dropped unmatched closing parenthesis at position {token.position}.",
                )
        else:
            balanced.append(token)
    for token in opens:
        _warn(
            warnings,
            token.position,
            "unclosed-group",
            f"Closed the group opened at position {token.position} at the end of the query.",
        )
        balanced.append(_Token("close", ")", text_length))

    classified: list[_Token] = []
    for token in balanced:
        if token.kind == "word":
            term = _term_from_token(token, warnings)
            if term is not None:
                classified.append(_Token(token.kind, token.value, token.position, term))
        else:
            classified.append(token)

    while True:
        changed = False
        for index in range(len(classified) - 1):
            if classified[index].kind == "open" and classified[index + 1].kind == "close":
                token = classified[index]
                _warn(
                    warnings,
                    token.position,
                    "empty-value",
                    f"Dropped empty group at position {token.position}.",
                )
                del classified[index : index + 2]
                changed = True
                break
        if changed:
            continue

        for index, token in enumerate(classified):
            if token.kind != "minus":
                continue
            end = index
            while end < len(classified) and classified[end].kind == "minus":
                end += 1
            if end == len(classified) or classified[end].kind not in ("word", "open"):
                for dangling in classified[index:end]:
                    _warn(
                        warnings,
                        dangling.position,
                        "dangling-operator",
                        f"Dropped dangling '-' at position {dangling.position}.",
                    )
                del classified[index:end]
                changed = True
                break
        if changed:
            continue

        for index, token in enumerate(classified):
            if token.kind != "or":
                continue
            has_left = index > 0 and classified[index - 1].kind in ("word", "close")
            has_right = index + 1 < len(classified) and classified[index + 1].kind in ("word", "open", "minus")
            if not has_left or not has_right:
                _warn(
                    warnings,
                    token.position,
                    "dangling-operator",
                    f"Dropped dangling OR at position {token.position}.",
                )
                del classified[index]
                changed = True
                break
        if not changed:
            break

    return classified


class _Parser:
    def __init__(self, tokens: list[_Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def _peek(self) -> _Token | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def parse_or(self) -> Node | None:
        first = self.parse_and()
        if first is None:
            return None
        nodes: list[Node] = list(first.nodes) if isinstance(first, Or) else [first]
        while (token := self._peek()) is not None and token.kind == "or":
            self.index += 1
            right = self.parse_and()
            if isinstance(right, Or):
                nodes.extend(right.nodes)
            elif right is not None:
                nodes.append(right)
        return Or(tuple(nodes)) if len(nodes) > 1 else nodes[0]

    def parse_and(self) -> Node | None:
        first = self.parse_unary()
        if first is None:
            return None
        nodes: list[Node] = list(first.nodes) if isinstance(first, And) else [first]
        while (token := self._peek()) is not None and token.kind in ("word", "open", "minus"):
            right = self.parse_unary()
            if isinstance(right, And):
                nodes.extend(right.nodes)
            elif right is not None:
                nodes.append(right)
        return And(tuple(nodes)) if len(nodes) > 1 else nodes[0]

    def parse_unary(self) -> Node | None:
        negations = 0
        while (token := self._peek()) is not None and token.kind == "minus":
            self.index += 1
            negations += 1
        node = self.parse_primary()
        for _ in range(negations):
            if node is not None:
                node = Not(node)
        return node

    def parse_primary(self) -> Node | None:
        token = self._peek()
        if token is None:
            return None
        if token.kind == "word":
            self.index += 1
            return token.term or Term(None, _decode(token.value))
        if token.kind == "open":
            self.index += 1
            node = self.parse_or()
            if (closing := self._peek()) is not None and closing.kind == "close":
                self.index += 1
            return node
        return None


def _quote_value(value: str) -> str:
    if (
        value == "OR"
        or value.startswith("-")
        or ":" in value
        or any(character.isspace() or character in '()"' for character in value)
    ):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _render(node: Node, parent_precedence: int = 0) -> str:
    if isinstance(node, Term):
        value = _quote_value(node.value)
        field = f"{node.field}:" if node.field is not None else ""
        exact = "=" if node.exact else ""
        return f"{field}{exact}{value}"
    if isinstance(node, Not):
        rendered = f"-{_render(node.node)}" if isinstance(node.node, (Term, Not)) else f"-({_render(node.node)})"
        precedence = 3
    elif isinstance(node, And):
        rendered = " ".join(_render(child, 2) for child in node.nodes)
        precedence = 2
    else:
        rendered = " OR ".join(_render(child, 1) for child in node.nodes)
        precedence = 1
    return f"({rendered})" if precedence < parent_precedence else rendered


def render(node: Node) -> str:
    """Render an AST in canonical query syntax."""
    return _render(node)


def parse_query(text: str) -> tuple[Node | None, list[QueryWarning], str]:
    """Parse a query, repairing malformed syntax into a searchable expression."""
    repairs: list[tuple[int, str, str]] = []
    tokens = _prepare_tokens(tokenize(text, repairs), len(text), repairs)
    node = _Parser(tokens).parse_or()
    interpreted = render(node) if node is not None else ""
    warnings: list[QueryWarning] = [
        {"code": code, "message": message, "retry": interpreted}
        for _, code, message in sorted(repairs, key=lambda repair: repair[0])
    ]
    return node, warnings, interpreted


def _replace_tag(node: Node, original: str, replacement: Term) -> Node:
    if isinstance(node, Term):
        if node.field == "tag" and node.value == original:
            return replacement
        return node
    if isinstance(node, Not):
        return Not(_replace_tag(node.node, original, replacement))
    children = tuple(_replace_tag(child, original, replacement) for child in node.nodes)
    return And(children) if isinstance(node, And) else Or(children)


def _flatten(node: Node) -> list[Term]:
    if isinstance(node, Term):
        return [node]
    if isinstance(node, Not):
        return _flatten(node.node)
    return [term for child in node.nodes for term in _flatten(child)]


def _title(path: str) -> str:
    return PurePosixPath(path).stem


def _headings(text: str) -> list[str]:
    result: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("#"):
            result.append(line)
    return result


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in cast(list[object], value) if isinstance(item, str)]
    return []


def find_query(prefix: str | None, filters: Mapping[str, str]) -> str:
    """Render the search query corresponding to legacy find options."""
    terms = [Term("category", prefix)] if prefix is not None else []
    terms.extend(
        Term(key, filters[key], exact=key == "tag") for key in ("type", "status", "kind", "tag") if key in filters
    )
    if not terms:
        return ""
    return render(And(tuple(terms)) if len(terms) > 1 else terms[0])


def matches_scan_query(node: Node, note: Mapping[str, Any]) -> bool:
    """Evaluate a find query against scan metadata using find's legacy matching rules."""
    raw_frontmatter = note.get("frontmatter")
    if not isinstance(raw_frontmatter, dict) or not raw_frontmatter:
        return False
    frontmatter = cast(dict[str, Any], raw_frontmatter)
    tags = _strings(note.get("tags"))

    def matches(current: Node) -> bool:
        if isinstance(current, Term):
            field = current.field
            if field == "tag":
                return current.value.casefold() in {tag.casefold() for tag in tags}
            values = _strings(frontmatter.get(field)) if field is not None else []
            if field == "category":
                return any(item == current.value or item.startswith(current.value + "/") for item in values)
            return current.value in values
        if isinstance(current, Not):
            return not matches(current.node)
        if isinstance(current, And):
            return all(matches(child) for child in current.nodes)
        return any(matches(child) for child in current.nodes)

    return matches(node)


def _add_unavailable(unavailable: list[str], item: str) -> None:
    group = item.partition(":")[0]
    if not any(existing.partition(":")[0] == group for existing in unavailable):
        unavailable.append(item)


def cmd_search(vault: Path, cfg: Mapping[str, str], project: Path | None, query: str, vault_args: list[str]) -> int:
    """Evaluate a query over visible vault notes and documents in the current TOW project."""
    from tow import PARA as TOW_PARA
    from tow import scan as scan_notes
    from tow import scope_is_empty
    from tow_project import lookup_results, project_files, tag_is_known

    node, warnings, interpreted = parse_query(query)
    scope = [cfg[key] for key in TOW_PARA if (vault / cfg[key]).is_dir()] if cfg["scope"] == "para" else ["."]
    candidates = vault_candidates(vault, cfg)
    unavailable = list(candidates.unavailable)
    vault_skipped = (
        "search scope is empty (no PARA folders); no vault notes were searched" if scope_is_empty(vault, cfg) else None
    )
    if not query.strip() or node is None:
        print(
            json.dumps(
                {
                    "query": {"input": query, "interpreted": interpreted},
                    "scope": scope,
                    "results": [],
                    "warnings": warnings,
                    "unavailable": unavailable,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    project_paths: list[str] = []
    project_tracked: set[str] = set()
    if project is not None:
        try:
            project_root = project.resolve()
            files = project_files(project_root)
            project_paths = [path for _, path in files]
            project_tracked = {path for status, path in files if status == "tracked"}
            project = project_root
        except (ConfigError, OSError, ValueError) as error:
            _add_unavailable(unavailable, f"project: {error}")
            project = None

    sources_paths = [("vault", path) for path in candidates.paths] + [("project", path) for path in project_paths]
    results: dict[tuple[str, str], dict[str, Any]] = {
        (source, path): {
            "path": path,
            "title": _title(path),
            "source": source,
            "reasons": [],
        }
        for source, path in sources_paths
    }
    terms = _flatten(node)

    def lookup_concept(tag: str, exact: bool) -> dict[tuple[str, str], str]:
        args = [vault_args[0], tag]
        if exact:
            args.append("--exact")
        args.extend(vault_args[1:])
        try:
            matched, failures = lookup_results(
                vault,
                cfg,
                project,
                tag,
                exact,
                args,
                vault_skipped if scope_is_empty(vault, cfg) else None,
            )
            for failure in failures:
                _add_unavailable(unavailable, f"concepts: {failure}")
        except (CliError, ConfigError, OSError, ValueError) as error:
            _add_unavailable(unavailable, f"concepts: {error}")
            return {}
        matches: dict[tuple[str, str], str] = {}
        for item in matched:
            source = item.get("source")
            path = item.get("path")
            raw_matches = item.get("matches")
            if source not in ("vault", "project") or not isinstance(path, str) or not isinstance(raw_matches, list):
                continue
            kinds = [
                cast(str, cast(dict[str, Any], match)["kind"])
                for match in cast(list[object], raw_matches)
                if isinstance(match, dict) and cast(dict[str, Any], match).get("kind") in ("exact", "narrower")
            ]
            if kinds:
                matches[(cast(str, source), path)] = "exact" if "exact" in kinds else "narrower"
        return matches

    concept_cache: dict[tuple[str, bool], dict[tuple[str, str], str]] = {}
    warning_values: set[str] = set()
    for term in terms:
        if term.field == "tag" or term.field is None:
            cache_key = (term.value, term.exact if term.field == "tag" else False)
            if cache_key not in concept_cache:
                concept_cache[cache_key] = lookup_concept(*cache_key)
            if (
                term.field == "tag"
                and not concept_cache[cache_key]
                and not any(failure.startswith("concepts:") for failure in unavailable)
            ):
                try:
                    known = tag_is_known(vault, cfg, project, term.value)
                except (CliError, ConfigError, OSError, ValueError) as error:
                    _add_unavailable(unavailable, f"concepts: {error}")
                    known = True
                if not known and term.value not in warning_values:
                    suggestion_args = [
                        "suggest",
                        term.value,
                        "--json",
                        "--limit",
                        "5",
                        "--root",
                        str(vault),
                        "--dictionary",
                        cfg["tagDictionary"],
                        "--names",
                        "kebab",
                    ]
                    labels: list[str] = []
                    try:
                        suggestion_result = run_cli(suggestion_args, capture=True)
                        if suggestion_result.returncode not in (0, 1):
                            raise CliError(suggestion_result.stderr.strip() or "tag-ontology suggest failed")
                        suggestion_data: object = json.loads(suggestion_result.stdout)
                        suggestions: object = (
                            cast(dict[str, Any], suggestion_data).get("suggestions", [])
                            if isinstance(suggestion_data, dict)
                            else []
                        )
                        for suggestion in cast(list[object], suggestions):
                            if not isinstance(suggestion, dict):
                                continue
                            suggestion = cast(dict[str, Any], suggestion)
                            if not isinstance(suggestion.get("tag"), str):
                                continue
                            label = cast(str, suggestion["tag"])
                            alias = suggestion.get("alias")
                            labels.append(f"{label} (alias: {alias})" if isinstance(alias, str) else label)
                    except (CliError, OSError, ValueError) as error:
                        _add_unavailable(unavailable, f"concepts: {error}")
                    similar = labels[0].split(" (alias:", 1)[0] if labels else None
                    replacement_term = (
                        Term("tag", similar, term.exact) if similar is not None else Term(None, term.value)
                    )
                    repaired = render(_replace_tag(node, term.value, replacement_term))
                    if similar is not None:
                        message = (
                            f"Unknown tag '{term.value}'. Similar dictionary tags: {', '.join(labels)}. "
                            f"retry uses {similar}."
                        )
                    else:
                        message = (
                            f"Unknown tag '{term.value}'. No similar dictionary tag; retry searches '{term.value}' "
                            "as a word in titles, headings and text."
                        )
                    warnings.append({"code": "unknown-tag", "message": message, "retry": repaired})
                    warning_values.add(term.value)

    needs_fields = any(term.field in {"category", "type", "status", "kind"} for term in terms)
    metadata: dict[str, dict[str, Any]] = {}
    if needs_fields and candidates.paths:
        extra = [] if cfg["scope"] == "vault" else ["--exclude", f"**/{cfg['projectArchive']}"]
        try:
            data = scan_notes(vault, dict(cfg), candidates.paths, extra)
            notes = data.get("notes")
            if not isinstance(notes, list):
                raise CliError("invalid tag-ontology scan result")
            for raw_note in cast(list[object], notes):
                if isinstance(raw_note, dict) and isinstance(cast(dict[str, Any], raw_note).get("path"), str):
                    metadata[cast(str, cast(dict[str, Any], raw_note)["path"])] = cast(dict[str, Any], raw_note)
        except (CliError, OSError, ValueError) as error:
            _add_unavailable(unavailable, f"fields: {error}")

    needs_body = any(term.field in (None, "heading", "text") for term in terms)
    if needs_body and not candidates.contents_ok:
        _add_unavailable(unavailable, GIT_UNAVAILABLE)
    contents: dict[tuple[str, str], str] = {}
    if needs_body:
        for source, path in sources_paths:
            if source == "vault" and not candidates.contents_ok:
                continue
            if source == "project" and path not in project_tracked:
                continue
            base = vault if source == "vault" else project
            if base is None:
                continue
            try:
                contents[(source, path)] = (base / path).read_text(encoding="utf-8", errors="replace")
            except OSError:
                contents[(source, path)] = ""
            else:
                if source == "vault":
                    try:
                        raw_contents = contents[(source, path)].encode("utf-8", errors="replace")
                        contents[(source, path)] = body_bytes(raw_contents).decode("utf-8", errors="replace")
                    except ConfigError:
                        contents[(source, path)] = ""

    field_values: dict[tuple[str, str], dict[str, list[str]]] = {}
    for source, path in sources_paths:
        if source == "project":
            field_values[(source, path)] = {}
            continue
        raw_note = metadata.get(path, {})
        raw_frontmatter = raw_note.get("frontmatter")
        frontmatter = cast(dict[str, Any], raw_frontmatter) if isinstance(raw_frontmatter, dict) else {}
        field_values[(source, path)] = {
            "category": _strings(frontmatter.get("category")),
            "type": _strings(frontmatter.get("type")),
            "status": _strings(frontmatter.get("status")),
            "kind": _strings(frontmatter.get("kind")),
        }

    def evaluate(term: Term, source: str, path: str) -> tuple[bool, str | None]:
        key = (source, path)
        field = term.field
        folded = term.value.casefold()
        if field == "source":
            if term.value.casefold() in ("vault", "project"):
                return term.value.casefold() == source, "source"
            return False, None
        if field == "path":
            return folded in path.casefold(), "path"
        if field == "title":
            return folded in _title(path).casefold(), "title"
        if field == "heading":
            text = contents.get(key)
            return (text is not None and any(folded in heading.casefold() for heading in _headings(text)), "heading")
        if field == "text":
            text = contents.get(key)
            return (text is not None and folded in text.casefold(), "text")
        if field == "category":
            categories = field_values[key].get("category", [])
            matched = any(item.casefold() == folded or item.casefold().startswith(folded + "/") for item in categories)
            return matched, "category"
        if field in {"type", "status", "kind"}:
            return any(item.casefold() == folded for item in field_values[key].get(field, [])), field
        if field == "tag":
            kind = concept_cache.get((term.value, term.exact), {}).get(key)
            return kind is not None, kind
        if field is None:
            kind = concept_cache.get((term.value, False), {}).get(key)
            if kind is not None:
                return True, kind
            title = _title(path).casefold()
            if folded in title:
                return True, "title"
            text = contents.get(key)
            if text is not None:
                if any(folded in heading.casefold() for heading in _headings(text)):
                    return True, "heading"
                if folded in text.casefold():
                    return True, "text"
        return False, None

    def matches(current: Node, source: str, path: str) -> tuple[bool, list[dict[str, str]]]:
        if isinstance(current, Term):
            matched, kind = evaluate(current, source, path)
            clause = f"{current.field + ':' if current.field else ''}{'=' if current.exact else ''}{current.value}"
            return matched, [{"clause": clause, "kind": kind or current.field or "term"}] if matched else []
        if isinstance(current, Not):
            matched, _ = matches(current.node, source, path)
            return not matched, []
        if isinstance(current, And):
            reasons: list[dict[str, str]] = []
            for child in current.nodes:
                matched, child_reasons = matches(child, source, path)
                if not matched:
                    return False, []
                reasons.extend(child_reasons)
            return True, reasons
        reasons = []
        matched_any = False
        for child in current.nodes:
            matched, child_reasons = matches(child, source, path)
            if matched:
                matched_any = True
                reasons.extend(child_reasons)
        return matched_any, reasons

    matching_keys: set[tuple[str, str]] = set()
    for source, path in sources_paths:
        matched, reasons = matches(node, source, path)
        if matched:
            matching_keys.add((source, path))
            results[(source, path)]["reasons"] = reasons

    ordered = sorted(
        (results[key] for key in matching_keys),
        key=lambda item: (item["source"], item["path"]),
    )
    print(
        json.dumps(
            {
                "query": {"input": query, "interpreted": interpreted},
                "scope": scope,
                "results": ordered,
                "warnings": warnings,
                "unavailable": unavailable,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ordered else 1
