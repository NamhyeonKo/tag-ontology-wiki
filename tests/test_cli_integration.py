"""Opt-in tests against a real CLI selected by TOW_TAG_ONTOLOGY."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "vault"
TOW = Path(__file__).parents[1] / "scripts" / "tow.py"
pytestmark = pytest.mark.skipif(not os.environ.get("TOW_TAG_ONTOLOGY"), reason="set TOW_TAG_ONTOLOGY to a real CLI")


@pytest.fixture
def real_vault(tmp_path: Path) -> Path:
    return Path(shutil.copytree(FIXTURE, tmp_path / "vault"))


def run(root: Path, *args: str, code: int = 0) -> str:
    result = subprocess.run(
        [sys.executable, str(TOW), "--root", str(root), *args], capture_output=True, text=True, check=False
    )
    assert result.returncode == code, (args, result.returncode, result.stdout, result.stderr)
    return result.stdout


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_real_cli_finds_only_matching_fields_in_configured_folders(real_vault: Path) -> None:
    before = snapshot(real_vault)
    assert json.loads(run(real_vault, "config"))["tagDictionary"] == "meta/Tag-Dictionary.json"
    assert run(real_vault, "lint").strip() == "OK"
    assert run(real_vault, "find", "ai/rag", "--type", "project").splitlines() == ["Projects/Category Project.md"]
    assert run(real_vault, "find", "--type", "project", "--tag", "RAG").splitlines() == ["Projects/Search.md"]
    assert run(real_vault, "find", "--status", "in-progress", "--kind", "design").splitlines() == ["Projects/Search.md"]
    assert run(real_vault, "find", "--type", "project", "--all").splitlines() == [
        "Projects/Category Project.md",
        "Projects/Search.md",
        "Projects/superseded/Old Search.md",
    ]
    assert snapshot(real_vault) == before


def test_real_cli_usage_and_show_respect_aliases_hierarchy_and_scope(real_vault: Path) -> None:
    before = snapshot(real_vault)
    usage = json.loads(run(real_vault, "ontology", "usage", "--json"))
    assert usage["scanned"] == 6
    assert usage["unregistered"] == []
    assert usage["nonCanonical"] == [
        {"path": "Resources/Pipeline.md", "tag": "retrieval-augmented-generation", "canonical": "rag"}
    ]
    direct = json.loads(run(real_vault, "ontology", "show", "information-retrieval", "--notes", "--exact", "--json"))
    assert direct["notePaths"] == ["Resources/Chunking.md", "Resources/Pipeline.md"]
    rollup = json.loads(run(real_vault, "ontology", "show", "information-retrieval", "--notes", "--json"))
    assert rollup["notePaths"] == [
        "Projects/Category Project.md",
        "Projects/Search.md",
        "Resources/Chunking.md",
        "Resources/Example.md",
        "Resources/Pipeline.md",
    ]
    alias = json.loads(run(real_vault, "ontology", "show", "retrieval-augmented-generation", "--json"))
    assert alias["tag"] == "rag"
    assert snapshot(real_vault) == before


def test_real_cli_checks_explicit_paths_without_treating_show_tags_as_paths(real_vault: Path) -> None:
    for path in ["./Inbox/Draft.md", str(real_vault / "Inbox" / "Draft.md")]:
        assert "unknown-category Inbox/Draft.md" in run(real_vault, "lint", path, code=1)
        scan = json.loads(run(real_vault, "ontology", "scan", path, "--json"))
        assert [n["path"] for n in scan["notes"]] == ["Inbox/Draft.md"]
    show = json.loads(run(real_vault, "ontology", "show", "Inbox", "--notes", "--json"))
    assert show["notePaths"] == []


def test_real_cli_plan_apply_and_stale_base_preserve_write_boundaries(real_vault: Path, tmp_path: Path) -> None:
    before = snapshot(real_vault)
    draft = json.loads(run(real_vault, "ontology", "show", "rag", "--json"))["draft"]
    draft["description"] = "An answer-generation method that retrieves supporting material before generating an answer."
    changes = tmp_path / "changes.json"
    changes.write_text(json.dumps({"schemaVersion": 1, "changes": [{"kind": "edit", "tag": "rag", "draft": draft}]}))
    assert run(real_vault, "ontology", "plan", str(changes), "--json", code=2) == ""
    assert snapshot(real_vault) == before
    scratch = real_vault / ".tow-tmp"
    scratch.mkdir()
    changes = Path(shutil.copy2(changes, scratch / "changes.json"))
    before = snapshot(real_vault)
    plan = json.loads(run(real_vault, "ontology", "plan", str(changes), "--json"))
    assert plan["ok"] and [d["tag"] for d in plan["diff"]] == ["rag"]
    assert snapshot(real_vault) == before
    applied = json.loads(run(real_vault, "ontology", "apply", str(changes), "--base", plan["base"], "--json"))
    assert applied["written"] is True
    after = snapshot(real_vault)
    assert {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)} == {"meta/Tag-Dictionary.json"}
    dictionary = json.loads((real_vault / "meta" / "Tag-Dictionary.json").read_text())
    assert dictionary["rag"]["description"] == draft["description"]
    conflict = json.loads(run(real_vault, "ontology", "apply", str(changes), "--base", plan["base"], "--json", code=3))
    assert conflict["conflict"]["current"] == applied["hash"]
    assert snapshot(real_vault) == after
