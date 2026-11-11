"""Query grammar: OR < AND (implicit space) < unary NOT, with fields and groups."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, TypedDict

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
