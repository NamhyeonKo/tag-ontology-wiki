import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

import tow
from tow import Issue, Note

CATEGORIES = {"ai", "ai/rag", "my-project"}


def note(path: str, fm: dict[str, Any] | None, headings: Sequence[str] = ()) -> Note:
    tags: list[str] = fm.get("tags", []) if fm else []
    return {
        "path": path,
        "frontmatter": fm,
        "tags": tags,
        "headings": [{"level": 2, "text": h} for h in headings],
    }


def codes(issues: list[Issue]) -> list[str]:
    return [i.code for i in issues]


# lint


def test_lint_accepts_a_conforming_note() -> None:
    fm = {"type": "resource", "category": ["ai/rag", "ai"], "tags": ["rag"]}
    assert tow.lint([note("r.md", fm)], CATEGORIES) == []


def test_lint_skips_notes_without_frontmatter() -> None:
    assert tow.lint([note("inbox.md", None)], CATEGORIES) == []


def test_lint_rejects_values_outside_the_allowed_set() -> None:
    fm = {"type": "resources", "status": "done", "kind": "memo"}
    issues = tow.lint([note("p.md", fm)], CATEGORIES)
    assert [(i.code, i.severity) for i in issues if i.code == "invalid-value"] == [("invalid-value", "error")] * 3


def test_lint_ignores_an_empty_classification_value() -> None:
    assert tow.lint([note("r.md", {"type": None})], CATEGORIES) == []


def test_lint_allows_status_and_kind_only_on_project_notes() -> None:
    project = note("p.md", {"type": "project", "status": "draft", "kind": "idea", "category": ["my-project"]})
    resource = note("r.md", {"type": "resource", "status": "draft", "kind": "idea"})
    issues = tow.lint([project, resource], CATEGORIES)
    assert [(i.path, i.code) for i in issues] == [("r.md", "project-only"), ("r.md", "project-only")]


def test_lint_reports_retired_properties() -> None:
    fm = {"type": "resource", "confidence": "high", "stage": "idea", "related": ["[[x]]"]}
    issues = tow.lint([note("r.md", fm)], CATEGORIES)
    assert codes(issues) == ["retired-property"] * 3


def test_lint_reports_unregistered_categories_in_lists_and_strings() -> None:
    listed = note("a.md", {"type": "resource", "category": ["ai", "ai/llm"]})
    single = note("b.md", {"type": "resource", "category": "web"})
    issues = tow.lint([listed, single], CATEGORIES)
    assert [(i.path, i.code) for i in issues] == [("a.md", "unknown-category"), ("b.md", "unknown-category")]
    assert "ai/llm" in issues[0].message


def test_lint_reports_duplicate_tags() -> None:
    issues = tow.lint([note("r.md", {"type": "resource", "tags": ["rag", "rag"]})], CATEGORIES)
    assert codes(issues) == ["duplicate-tag"]


def test_lint_flags_legacy_notes_and_skips_their_other_checks() -> None:
    fm = {
        "tags": ["type/resource", "ai/unknown", "ai/unknown"],
        "status": "draft",
        "category": ["web"],
        "confidence": "high",
    }
    issues = tow.lint([note("old.md", fm)], CATEGORIES)
    assert [(i.code, i.severity) for i in issues] == [("retired-property", "error"), ("legacy", "warning")]


def test_lint_warns_when_a_note_has_more_than_15_tags() -> None:
    fm = {"type": "resource", "tags": [f"t{i}" for i in range(16)]}
    issues = tow.lint([note("r.md", fm)], CATEGORIES)
    assert [(i.code, i.severity) for i in issues] == [("too-many-tags", "warning")]
    assert tow.lint([note("r.md", {**fm, "tags": fm["tags"][:15]})], CATEGORIES) == []


def test_lint_allows_20_tags_on_an_overview_note() -> None:
    sections = ["1.1. A", "1.2. B", "2.1. C"]
    fm = {"type": "resource", "tags": [f"t{i}" for i in range(20)]}
    assert tow.lint([note("r.md", fm, sections)], CATEGORIES) == []
    fm21 = {**fm, "tags": [f"t{i}" for i in range(21)]}
    assert codes(tow.lint([note("r.md", fm21, sections)], CATEGORIES)) == ["too-many-tags"]


def test_lint_needs_three_numbered_sections_for_an_overview_note() -> None:
    fm = {"type": "resource", "tags": [f"t{i}" for i in range(16)]}
    assert codes(tow.lint([note("r.md", fm, ["1.1. A", "1.2. B", "Summary"])], CATEGORIES)) == ["too-many-tags"]


# category dictionary


def test_category_values_reads_bullets_and_h3_headers() -> None:
    text = (
        "# Title\n\n### `ai` — AI\n- `ai/rag` : RAG, not `ai/llm`\n"
        "  - `ai/nested` : indented\nText `web`\n## `section`\n"
    )
    assert tow.category_values(text) == {"ai", "ai/rag"}


# find


def test_find_matches_a_category_and_its_children() -> None:
    notes = [
        note("a.md", {"category": ["ai"]}),
        note("b.md", {"category": ["web", "ai/rag"]}),
        note("c.md", {"category": ["aix"]}),
        note("d.md", None),
    ]
    assert tow.find(notes, "ai") == ["a.md", "b.md"]


# config


def test_load_config_fills_in_defaults() -> None:
    assert tow.load_config({"projects": "Projects"}) == {**tow.DEFAULTS, "projects": "Projects"}


@pytest.mark.parametrize(
    "raw",
    [[], {"project": "P"}, {"areas": 2}, {"areas": ""}, {"resources": "Notes/Resources"}, {"projectArchive": "a/b"}],
)
def test_load_config_rejects_bad_files(raw: object) -> None:
    with pytest.raises(tow.ConfigError):
        tow.load_config(raw)


def test_load_config_allows_dictionary_paths_with_folders() -> None:
    assert tow.load_config({"tagDictionary": "meta/tags.json"})["tagDictionary"] == "meta/tags.json"


# tag-ontology arguments


def test_scope_excludes_everything_at_the_root_but_para_folders(tmp_path: Path) -> None:
    for d in ["01_Projects", "02_Areas", "03_Resources", "04_Archives", "00_Inbox", "99_Etc", ".obsidian"]:
        (tmp_path / d).mkdir()
    for f in ["AGENTS.md", "Tag-Dictionary.json", "tow.json"]:
        (tmp_path / f).write_text("")
    assert tow.scope_excludes(tmp_path, tow.DEFAULTS, []) == [
        "--exclude", "00_Inbox", "--exclude", "99_Etc", "--exclude", "AGENTS.md",
    ]  # fmt: skip


def test_scope_excludes_keeps_folders_named_in_the_arguments(tmp_path: Path) -> None:
    (tmp_path / "00_Inbox").mkdir()
    (tmp_path / "99_Etc").mkdir()
    args = ["00_Inbox/a.md", "--exclude", "99_Etc"]
    assert tow.scope_excludes(tmp_path, tow.DEFAULTS, args) == ["--exclude", "99_Etc"]


def test_scope_excludes_normalizes_relative_and_absolute_paths(tmp_path: Path) -> None:
    (tmp_path / "00_Inbox").mkdir()
    (tmp_path / "99_Etc").mkdir()
    args = ["./00_Inbox/a.md", str(tmp_path / "99_Etc" / "b.md")]
    assert tow.scope_excludes(tmp_path, tow.DEFAULTS, args) == []


def test_ontology_args_for_show_add_settings_and_skip_project_archives() -> None:
    args = tow.ontology_args("show", ["rag", "--notes"], "/v", tow.DEFAULTS, ["--exclude", "00_Inbox"])
    assert args == [
        "show", "rag", "--notes", "--root", "/v",
        "--dictionary", "Tag-Dictionary.json", "--names", "kebab",
        "--exclude", "00_Inbox", "--exclude", "**/archive",
    ]  # fmt: skip


def test_ontology_args_all_keeps_project_archives_and_is_not_passed_on() -> None:
    args = tow.ontology_args("show", ["rag", "--all"], "/v", tow.DEFAULTS, [])
    assert "--all" not in args
    assert "**/archive" not in args


def test_ontology_args_for_scan_have_no_dictionary_options() -> None:
    assert tow.ontology_args("scan", ["--json"], "/v", tow.DEFAULTS, ["--exclude", "x"]) == [
        "scan", "--json", "--root", "/v", "--exclude", "x",
    ]  # fmt: skip


def test_ontology_args_for_check_have_no_note_scope() -> None:
    assert tow.ontology_args("check", [], "/v", tow.DEFAULTS, ["--exclude", "x"]) == [
        "check", "--root", "/v", "--dictionary", "Tag-Dictionary.json", "--names", "kebab",
    ]  # fmt: skip


# command line, against a stand-in for the tag-ontology CLI


def fake_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scan: dict[str, Any]) -> Path:
    """Point TOW_TAG_ONTOLOGY at a script that records its arguments and prints `scan`."""
    (tmp_path / "scan.json").write_text(json.dumps(scan))
    script = tmp_path / "fake_cli.py"
    script.write_text(
        "import json, pathlib, sys\n"
        f"d = pathlib.Path({str(tmp_path)!r})\n"
        "(d / 'args.json').write_text(json.dumps(sys.argv[1:]))\n"
        "print((d / 'scan.json').read_text())\n"
    )
    monkeypatch.setenv("TOW_TAG_ONTOLOGY", f"{sys.executable} {script}")
    return tmp_path


def vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    (root / "03_Resources").mkdir(parents=True)
    (root / "Category-Dictionary.md").write_text("### `ai` — AI\n- `ai/rag` : RAG\n")
    return root


def scan_of(*notes: Note) -> dict[str, Any]:
    return {"schemaVersion": 1, "command": "scan", "ok": True, "issues": [], "notes": list(notes)}


def test_main_lint_exits_1_and_prints_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = vault(tmp_path)
    fake = fake_cli(
        tmp_path, monkeypatch, scan_of(note("03_Resources/a.md", {"type": "resource", "category": ["web"]}))
    )
    assert tow.main(["--root", str(root), "lint"]) == 1
    out = capsys.readouterr().out
    assert "unknown-category" in out
    assert "03_Resources/a.md" in out
    assert json.loads((fake / "args.json").read_text())[:4] == ["scan", "--json", "--root", str(root)]


def test_main_lint_prints_ok_for_a_clean_vault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = vault(tmp_path)
    fake_cli(tmp_path, monkeypatch, scan_of(note("03_Resources/a.md", {"type": "resource", "category": ["ai/rag"]})))
    assert tow.main(["--root", str(root), "lint"]) == 0
    assert capsys.readouterr().out.strip() == "OK"


def test_main_lint_passes_on_scan_warnings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = vault(tmp_path)
    warning = {"code": "invalid-frontmatter", "severity": "warning", "path": "03_Resources/b.md", "message": "bad"}
    fake_cli(tmp_path, monkeypatch, {**scan_of(note("03_Resources/b.md", None)), "issues": [warning]})
    assert tow.main(["--root", str(root), "lint"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "warning invalid-frontmatter 03_Resources/b.md: bad",
        "0 error(s), 1 warning(s)",
    ]


def test_main_find_skips_project_archives_unless_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = vault(tmp_path)
    fake = fake_cli(tmp_path, monkeypatch, scan_of(note("03_Resources/a.md", {"category": ["ai/rag"]})))
    assert tow.main(["--root", str(root), "find", "ai"]) == 0
    assert capsys.readouterr().out.strip() == "03_Resources/a.md"
    assert "**/archive" in json.loads((fake / "args.json").read_text())
    tow.main(["--root", str(root), "find", "ai", "--all"])
    assert "**/archive" not in json.loads((fake / "args.json").read_text())


def test_main_ontology_reads_paths_only_for_commands_that_take_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = vault(tmp_path)
    (root / "00_Inbox").mkdir()
    fake = fake_cli(tmp_path, monkeypatch, scan_of())
    tow.main(["--root", str(root), "ontology", "show", "00_Inbox", "--notes"])
    assert "--exclude 00_Inbox" in " ".join(json.loads((fake / "args.json").read_text()))
    tow.main(["--root", str(root), "ontology", "usage", "00_Inbox/a.md"])
    assert "--exclude 00_Inbox" not in " ".join(json.loads((fake / "args.json").read_text()))


def test_main_reports_a_cli_that_prints_no_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = vault(tmp_path)
    script = tmp_path / "broken_cli.py"
    script.write_text("import sys\nsys.stderr.write('npm error 404\\n')\nsys.exit(1)\n")
    monkeypatch.setenv("TOW_TAG_ONTOLOGY", f"{sys.executable} {script}")
    assert tow.main(["--root", str(root), "lint"]) == 2
    assert "npm error 404" in capsys.readouterr().err


def test_main_config_prints_the_merged_settings(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = vault(tmp_path)
    (root / "tow.json").write_text('{"areas": "Areas"}')
    assert tow.main(["--root", str(root), "config"]) == 0
    assert json.loads(capsys.readouterr().out) == {**tow.DEFAULTS, "areas": "Areas"}


def test_main_reports_a_broken_config_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = vault(tmp_path)
    (root / "tow.json").write_text("{not json")
    assert tow.main(["--root", str(root), "config"]) == 2
    assert "tow.json" in capsys.readouterr().err
