from __future__ import annotations

import pytest

from tow_search import FIELDS, And, Node, Not, Or, Term, find_query, matches_scan_query, parse_query, render


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("a b", And((Term(None, "a"), Term(None, "b")))),
        ("a OR b c", Or((Term(None, "a"), And((Term(None, "b"), Term(None, "c")))))),
        ("-tag:x", Not(Term("tag", "x"))),
        ("tag:=x", Term("tag", "x", exact=True)),
        ('title:"graph rag"', Term("title", "graph rag")),
        ("(a OR b) -c", And((Or((Term(None, "a"), Term(None, "b"))), Not(Term(None, "c"))))),
        ("or", Term(None, "or")),
        ('"OR"', Term(None, "OR")),
        ('"-term"', Term(None, "-term")),
        ('"a(b)"', Term(None, "a(b)")),
        ('"a\\"b"', Term(None, 'a"b')),
        ('"foo:bar"', Term(None, "foo:bar")),
        ("graph-rag", Term(None, "graph-rag")),
        ("tag:graph-rag", Term("tag", "graph-rag")),
    ],
)
def test_parse_query_builds_the_expected_ast(query: str, expected: Node) -> None:
    node, warnings, interpreted = parse_query(query)

    assert node == expected
    assert warnings == []
    assert node is not None
    assert render(node) == interpreted


def test_find_query_uses_search_fields_and_exact_tag_semantics() -> None:
    query = find_query("ai", {"type": "project", "tag": "RAG"})

    assert query == "category:ai type:project tag:=RAG"
    node, warnings, interpreted = parse_query(query)
    assert warnings == []
    assert interpreted == query
    assert node is not None


def test_matches_scan_query_uses_legacy_find_matching() -> None:
    node, _, _ = parse_query("category:ai type:project tag:=RAG")
    assert node is not None
    matching = {
        "frontmatter": {"category": ["ai/rag"], "type": "project"},
        "tags": ["rag"],
    }
    outside = {**matching, "tags": ["ragged"]}

    assert matches_scan_query(node, matching)
    assert not matches_scan_query(node, outside)


def assert_retry_is_fixed_point(retry: str) -> None:
    _, warnings, interpreted = parse_query(retry)
    assert warnings == []
    assert interpreted == retry


@pytest.mark.parametrize(
    ("query", "codes", "interpreted"),
    [
        ("(tag:rag OR", ["unclosed-group", "dangling-operator"], "tag:rag"),
        ("a )", ["unmatched-close"], "a"),
        ("OR a", ["dangling-operator"], "a"),
        ("a OR", ["dangling-operator"], "a"),
        ("a OR OR b", ["dangling-operator"], "a OR b"),
        ('"graph rag', ["unclosed-quote"], '"graph rag"'),
        ("tag:", ["empty-value"], ""),
        ("()", ["empty-value"], ""),
        ("foo:bar", ["unknown-field"], '"foo:bar"'),
        ('foo:bar "graph rag', ["unknown-field", "unclosed-quote"], '"foo:bar" "graph rag"'),
    ],
)
def test_parse_query_repairs_invalid_input(query: str, codes: list[str], interpreted: str) -> None:
    node, warnings, actual_interpreted = parse_query(query)

    assert actual_interpreted == interpreted
    assert [warning["code"] for warning in warnings] == codes
    assert all(warning["retry"] == actual_interpreted for warning in warnings)
    assert all("position" in warning["message"] for warning in warnings)
    if node is None:
        assert actual_interpreted == ""
    else:
        assert render(node) == actual_interpreted
    retry_query, retry_warnings, retry_interpreted = parse_query(actual_interpreted)
    assert retry_warnings == []
    assert retry_interpreted == actual_interpreted
    assert retry_query is None if node is None else retry_query is not None


def test_parse_query_returns_none_when_only_repairs_remain() -> None:
    node, warnings, interpreted = parse_query(" OR () ")

    assert node is None
    assert [warning["code"] for warning in warnings] == ["dangling-operator", "empty-value"]
    assert all(warning["retry"] == "" for warning in warnings)
    assert interpreted == ""
    assert_retry_is_fixed_point(interpreted)


def test_parse_query_orders_warnings_by_input_position() -> None:
    _, warnings, _ = parse_query("OR tag: )")

    assert [warning["code"] for warning in warnings] == [
        "dangling-operator",
        "empty-value",
        "unmatched-close",
    ]
    assert [warning["message"].split("position ", 1)[1].split()[0].rstrip(".") for warning in warnings] == [
        "0",
        "3",
        "8",
    ]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("a OR b c", "a OR b c"),
        ("a OR (b c)", "a OR b c"),
        ("a (b OR c)", "a (b OR c)"),
        ("-(a OR b)", "-(a OR b)"),
        ('title:"graph rag"', 'title:"graph rag"'),
        ('"a\\"b"', '"a\\"b"'),
        ('"OR"', '"OR"'),
        ('"-term"', '"-term"'),
    ],
)
def test_render_emits_canonical_query(query: str, expected: str) -> None:
    node, warnings, interpreted = parse_query(query)

    assert warnings == []
    assert node is not None
    assert render(node) == expected
    assert interpreted == expected


def test_render_quotes_terms_containing_query_delimiters() -> None:
    assert render(Term(None, "a(b)")) == '"a(b)"'
    assert render(Term(None, 'a"b')) == '"a\\"b"'


def test_parse_query_keeps_term_case() -> None:
    node, warnings, interpreted = parse_query("Tag:GraphRAG")

    assert warnings == [
        {
            "code": "unknown-field",
            "message": "Treated unknown field 'Tag' as a bare term at position 0.",
            "retry": '"Tag:GraphRAG"',
        }
    ]
    assert node == Term(None, "Tag:GraphRAG")
    assert interpreted == '"Tag:GraphRAG"'


def test_declared_fields_match_the_query_contract() -> None:
    assert FIELDS == ("tag", "title", "heading", "text", "path", "category", "type", "status", "kind", "source")


def test_parse_query_handles_repeated_unary_not() -> None:
    node, warnings, interpreted = parse_query("--a")

    assert node == Not(Not(Term(None, "a")))
    assert warnings == []
    assert interpreted == "--a"
