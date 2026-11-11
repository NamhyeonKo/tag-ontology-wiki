from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from conftest import fake_cli

import tow
import tow_search

CFG = {
    "projects": "projects",
    "areas": "areas",
    "resources": "resources",
    "archives": "archives",
    "projectArchive": "archive",
    "tagDictionary": ".tow/tag-dictionary.json",
    "categoryDictionary": ".tow/category-dictionary.json",
    "inbox": "inbox",
    "attachments": "attachments",
    "dailyNotes": "daily-notes",
    "misc": "misc",
    "scope": "para",
}


def make_vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    (root / ".tow").mkdir(parents=True)
    (root / ".tow/config.json").write_text(json.dumps({"kind": "vault", **CFG}), encoding="utf-8")
    (root / ".tow/tag-dictionary.json").write_text(
        json.dumps({"rag": {"aliases": ["retrieval-augmented-generation"]}}), encoding="utf-8"
    )
    for folder in ("projects", "areas", "resources"):
        (root / folder).mkdir()
    return root


def write_note(root: Path, relative: str, text: str) -> None:
    (root / relative).write_text(text, encoding="utf-8")


def scan_notes(*items: tuple[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "ok": True,
        "notes": [
            {
                "path": path,
                "frontmatter": frontmatter,
                "tags": frontmatter.get("tags", []),
                "bodyTags": [],
                "headings": [],
            }
            for path, frontmatter in items
        ],
    }


def test_search_evaluates_and_or_not_and_reports_matching_clause_reasons(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_vault(tmp_path)
    write_note(root, "projects/graph.md", "---\ntype: project\n---\n# Graph\nGenerator retrieved passages.\n")
    write_note(root, "resources/overview.md", "# Overview\nA reference note.\n")
    write_note(root, "areas/hidden.md", "# Overview\nGenerator retrieved passages.\n")
    notes = [
        ("projects/graph.md", {"type": "project"}),
        ("resources/overview.md", {"type": "resource"}),
        ("areas/hidden.md", {"type": "area"}),
    ]
    fake_cli(tmp_path, monkeypatch, scan_notes(*notes))
    monkeypatch.chdir(root)
    capsys.readouterr()

    assert tow.main(["--root", str(root), "search", "title:graph text:generator OR heading:overview -path:areas"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "query": {
            "input": "title:graph text:generator OR heading:overview -path:areas",
            "interpreted": "title:graph text:generator OR heading:overview -path:areas",
        },
        "scope": ["projects", "areas", "resources"],
        "results": [
            {
                "path": "projects/graph.md",
                "title": "graph",
                "source": "vault",
                "reasons": [
                    {"clause": "title:graph", "kind": "title"},
                    {"clause": "text:generator", "kind": "text"},
                ],
            },
            {
                "path": "resources/overview.md",
                "title": "overview",
                "source": "vault",
                "reasons": [{"clause": "heading:overview", "kind": "heading"}],
            },
        ],
        "warnings": [],
        "unavailable": [],
    }


def test_search_field_clauses_use_scan_frontmatter_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_vault(tmp_path)
    write_note(root, "projects/graph.md", "---\ntype: project\n---\n")
    write_note(root, "resources/other.md", "---\ntype: resource\n---\n")
    fake_dir = fake_cli(
        tmp_path,
        monkeypatch,
        scan_notes(
            ("projects/graph.md", {"category": ["ai/rag"], "type": "project", "status": "active"}),
            ("resources/other.md", {"category": ["web"], "type": "resource", "status": "active"}),
        ),
    )
    monkeypatch.chdir(root)
    capsys.readouterr()

    assert tow.main(["--root", str(root), "search", "category:ai type:project status:active"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert [(item["path"], item["reasons"]) for item in output["results"]] == [
        (
            "projects/graph.md",
            [
                {"clause": "category:ai", "kind": "category"},
                {"clause": "type:project", "kind": "type"},
                {"clause": "status:active", "kind": "status"},
            ],
        )
    ]
    calls = json.loads((fake_dir / "calls.json").read_text(encoding="utf-8"))
    assert sum(call[0] == "scan" for call in calls) == 1


def test_search_unknown_tag_warns_with_cli_suggestions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_vault(tmp_path)
    fake_cli(
        tmp_path,
        monkeypatch,
        {"ok": True, "notes": []},
    )

    suggestion_calls: list[str] = []

    def prefix_suggestions(arguments: list[str]) -> dict[str, Any]:
        term = arguments[1]
        suggestion_calls.append(term)
        return {"matched": "onto", "suggestions": [{"tag": "ontology"}]}

    def run_suggest(arguments: list[str], capture: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=arguments, returncode=0, stdout=json.dumps(prefix_suggestions(arguments)), stderr=""
        )

    monkeypatch.setattr(tow_search, "run_cli", run_suggest)
    monkeypatch.chdir(root)
    capsys.readouterr()

    assert tow.main(["--root", str(root), "search", "tag:ontolgy OR title:other"]) == 1

    output = json.loads(capsys.readouterr().out)
    assert output["warnings"] == [
        {
            "code": "unknown-tag",
            "message": "Unknown tag 'ontolgy'. Similar dictionary tags: ontology. retry uses ontology.",
            "retry": "tag:ontology OR title:other",
        }
    ]
    assert output["results"] == []
    assert suggestion_calls == ["ontolgy"]


def test_search_unknown_tag_without_similar_tags_retries_as_a_bare_term(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_vault(tmp_path)
    fake_cli(tmp_path, monkeypatch, {"ok": True, "notes": []})

    def run_suggest(arguments: list[str], capture: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=arguments, returncode=0, stdout='{"suggestions": []}', stderr="")

    monkeypatch.setattr(tow_search, "run_cli", run_suggest)
    monkeypatch.chdir(root)
    capsys.readouterr()

    assert tow.main(["--root", str(root), "search", "tag:xyz OR title:other"]) == 1

    warning = json.loads(capsys.readouterr().out)["warnings"][0]
    assert warning == {
        "code": "unknown-tag",
        "message": (
            "Unknown tag 'xyz'. No similar dictionary tag; retry searches 'xyz' as a word in titles, headings and text."
        ),
        "retry": "xyz OR title:other",
    }


def test_search_keeps_text_results_when_concept_cli_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_vault(tmp_path)
    write_note(root, "projects/generator.md", "Generator text remains searchable.\n")
    fake_cli(
        tmp_path,
        monkeypatch,
        {"ok": True, "notes": []},
        {"show": json.dumps({"ok": False, "issues": [{"severity": "error", "message": "offline"}]})},
    )
    monkeypatch.chdir(root)
    capsys.readouterr()

    assert tow.main(["--root", str(root), "search", "tag:rag OR text:generator"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert [item["path"] for item in output["results"]] == ["projects/generator.md"]
    assert output["results"][0]["reasons"] == [{"clause": "text:generator", "kind": "text"}]
    assert output["unavailable"] == ["concepts: vault: offline"]


def test_search_reports_interpreted_query_and_exit_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_vault(tmp_path)
    write_note(root, "projects/graph.md", "Graph note.\n")
    fake_cli(tmp_path, monkeypatch, {"ok": True, "notes": []})
    monkeypatch.chdir(root)
    capsys.readouterr()

    assert tow.main(["--root", str(root), "search", "(title:graph OR"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["query"] == {"input": "(title:graph OR", "interpreted": "title:graph"}
    assert output["warnings"][0]["code"] == "unclosed-group"
    assert output["warnings"][0]["retry"] == "title:graph"

    assert tow.main(["--root", str(root), "search", "title:absent"]) == 1
    assert json.loads(capsys.readouterr().out)["results"] == []

    with pytest.raises(SystemExit) as error:
        tow.main(["--root", str(root), "search"])
    assert error.value.code == 2
    assert "search needs a query" in capsys.readouterr().err


def test_project_path_clause_does_not_match_absolute_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_vault(tmp_path)
    project = tmp_path / "project"
    (project / ".tow").mkdir(parents=True)
    (project / ".tow" / "config.json").write_text('{"kind": "project"}\n', encoding="utf-8")
    (project / "notes").mkdir()
    (project / "notes" / "graph.md").write_text("# Graph\n", encoding="utf-8")
    monkeypatch.chdir(project)
    capsys.readouterr()

    assert tow.main(["--root", str(root), "search", f"path:{project}"]) == 1

    assert json.loads(capsys.readouterr().out)["results"] == []


@pytest.mark.parametrize(
    ("query_arguments", "expected"),
    [(["-tag:rag"], "-tag:rag"), (["a", "-b"], "a -b"), (["--", "-x"], "-x")],
)
def test_search_passes_remaining_arguments_as_one_query(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    query_arguments: list[str],
    expected: str,
) -> None:
    root = make_vault(tmp_path)
    monkeypatch.chdir(root)
    capsys.readouterr()
    observed: list[str] = []

    def record_query(vault: Path, cfg: dict[str, str], project: Path | None, query: str, vault_args: list[str]) -> int:
        observed.append(query)
        return 0

    monkeypatch.setattr(tow, "cmd_search", record_query)

    assert tow.main(["search", *query_arguments]) == 0
    assert observed == [expected]


def test_search_help_is_not_treated_as_query() -> None:
    with pytest.raises(SystemExit) as error:
        tow.main(["search", "-h"])

    assert error.value.code == 0


def test_search_accepts_a_leading_not_clause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_vault(tmp_path)
    write_note(root, "projects/graph.md", "Graph note.\n")
    monkeypatch.chdir(root)
    capsys.readouterr()

    assert tow.main(["--root", str(root), "search", "--", "-path:absent"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert [(item["path"], item["reasons"]) for item in output["results"]] == [("projects/graph.md", [])]
