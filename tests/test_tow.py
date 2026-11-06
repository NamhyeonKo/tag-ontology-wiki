import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from conftest import fake_cli

import tow
import tow_core
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


def test_lint_treats_tags_that_differ_only_in_case_as_duplicates() -> None:
    issues = tow.lint([note("r.md", {"type": "resource", "tags": ["Python", "python"]})], CATEGORIES)
    assert codes(issues) == ["duplicate-tag"]
    assert "Python" in issues[0].message
    assert "python" in issues[0].message


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


def test_category_entries_reads_descriptions() -> None:
    assert tow.category_entries('{"ai": {"description": "Artificial intelligence"}}') == {
        "ai": {"description": "Artificial intelligence"}
    }


@pytest.mark.parametrize(
    "text",
    [
        "[]",
        '"ai"',
        '{"ai": "description"}',
        '{"ai": {"description": 1}}',
        '{"ai": {"description": "x", "other": "y"}}',
        '{"ai": {"description": "x", "0": "y"}}',
        "not json",
    ],
)
def test_category_entries_rejects_invalid_shapes(text: str) -> None:
    with pytest.raises(tow.ConfigError):
        tow.category_entries(text)


def test_load_categories_supports_json_and_markdown(tmp_path: Path) -> None:
    json_path = tmp_path / "categories.json"
    json_path.write_text('{"ai/rag": {"description": "RAG"}}\n')
    markdown_path = tmp_path / "categories.md"
    markdown_path.write_text("### `ai` — artificial intelligence\n")

    assert tow.load_categories(tmp_path, {"categoryDictionary": "categories.json"}) == {"ai/rag"}
    assert tow.load_categories(tmp_path, {"categoryDictionary": "categories.md"}) == {"ai"}


# find


def test_find_matches_a_category_and_its_children() -> None:
    notes = [
        note("a.md", {"category": ["ai"]}),
        note("b.md", {"category": ["web", "ai/rag"]}),
        note("c.md", {"category": ["aix"]}),
        note("d.md", None),
    ]
    assert tow.find(notes, "ai") == ["a.md", "b.md"]


def test_find_filters_by_frontmatter_fields_and_tags() -> None:
    notes = [
        note("p.md", {"type": "project", "status": "draft", "category": ["ai/rag"], "tags": ["RAG"]}),
        note("q.md", {"type": "project", "category": ["web"], "tags": ["rag"]}),
        note("r.md", {"type": "resource", "category": ["ai/rag"], "tags": ["rag"]}),
    ]
    assert tow.find(notes, None, {"type": "project"}) == ["p.md", "q.md"]
    assert tow.find(notes, None, {"status": "draft"}) == ["p.md"]
    assert tow.find(notes, "ai", {"type": "project", "tag": "rag"}) == ["p.md"]


# config


def test_write_text_atomic_refuses_existing_targets_when_exclusive(tmp_path: Path) -> None:
    path = tmp_path / "kept.txt"
    path.write_text("original")

    with pytest.raises(FileExistsError):
        tow_core.write_text_atomic(path, "replacement", exclusive=True)

    assert path.read_text() == "original"
    assert list(tmp_path.iterdir()) == [path]


def test_load_config_fills_in_defaults() -> None:
    assert tow.load_config({"projects": "Projects"}) == {**tow.DEFAULTS, "projects": "Projects"}


def test_read_config_prefers_dot_tow_config_with_tow_defaults(tmp_path: Path) -> None:
    config = tmp_path / ".tow" / "config.json"
    config.parent.mkdir()
    config.write_text('{"kind": "vault", "projects": "Projects"}')
    (tmp_path / "tow.json").write_text('{"areas": "Legacy Areas"}')

    assert tow.read_config(tmp_path) == {**tow.TOW_DEFAULTS, "projects": "Projects"}


def test_read_config_keeps_tow_json_defaults_for_legacy_vaults(tmp_path: Path) -> None:
    (tmp_path / "tow.json").write_text('{"areas": "Areas"}')

    assert tow.read_config(tmp_path) == {**tow.DEFAULTS, "areas": "Areas"}


def test_load_config_accepts_only_kind_vault() -> None:
    config = tow.load_config({"kind": "vault", "projects": "Projects"}, tow.TOW_DEFAULTS)
    assert config == {**tow.TOW_DEFAULTS, "projects": "Projects"}
    assert "kind" not in config
    with pytest.raises(tow.ConfigError, match="kind"):
        tow.load_config({"kind": "project"}, tow.TOW_DEFAULTS)


def test_config_reports_the_vault_source_on_stderr(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = vault(tmp_path)
    (root / "tow.json").write_text('{"areas": "Areas"}')
    plugin = root / ".obsidian/plugins/tag-ontology/data.json"
    plugin.parent.mkdir(parents=True)
    plugin.write_text('{"dictionaryPath": "Tag-Dictionary.json"}')

    assert tow.main(["--root", str(root), "config"]) == 0

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {**tow.DEFAULTS, "areas": "Areas"}
    assert f"tow: vault {root} (from --root, legacy)" in captured.err


def test_main_without_any_vault_exits_2_with_setup_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert tow.main(["config"]) == 2
    assert "run tow-setup" in capsys.readouterr().err


def test_config_warns_when_the_plugin_uses_another_dictionary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = {**tow.TOW_DEFAULTS}
    assert tow.plugin_dictionary_warning(tmp_path, config) == (
        "plugin settings not checked (no .obsidian/plugins/tag-ontology/data.json)"
    )
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/config.json").write_text('{"kind": "vault"}')
    (tmp_path / ".tow/tag-dictionary.json").write_text("{}")
    plugin = tmp_path / ".obsidian/plugins/tag-ontology/data.json"
    plugin.parent.mkdir(parents=True)
    plugin.write_text('{"dictionaryPath": "custom/tags.json", "dictionaryPathExplicit": true}')

    assert tow.main(["--root", str(tmp_path), "config"]) == 0
    captured = capsys.readouterr()
    assert "plugin dictionary path differs" in captured.err
    assert "custom/tags.json" in captured.err

    plugin.write_text('{"dictionaryPath": "Tag-Dictionary.json"}')
    assert tow.plugin_dictionary_warning(tmp_path, config) is None
    assert tow.main(["--root", str(tmp_path), "config"]) == 0
    assert "plugin dictionary path differs" not in capsys.readouterr().err


def test_plugin_dictionary_warning_honors_an_explicit_false_flag(tmp_path: Path) -> None:
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/tag-dictionary.json").write_text("{}")
    plugin = tmp_path / ".obsidian/plugins/tag-ontology/data.json"
    plugin.parent.mkdir(parents=True)
    plugin.write_text('{"dictionaryPath": "custom/tags.json", "dictionaryPathExplicit": false}')

    assert tow.plugin_dictionary_warning(tmp_path, tow.TOW_DEFAULTS) is None


def test_plugin_dictionary_warning_treats_unflagged_custom_path_as_explicit(tmp_path: Path) -> None:
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/tag-dictionary.json").write_text("{}")
    plugin = tmp_path / ".obsidian/plugins/tag-ontology/data.json"
    plugin.parent.mkdir(parents=True)
    plugin.write_text('{"dictionaryPath": "custom/tags.json"}')

    assert tow.plugin_dictionary_warning(tmp_path, tow.TOW_DEFAULTS) == (
        "plugin dictionary path differs: TOW uses .tow/tag-dictionary.json, Tag Ontology plugin uses custom/tags.json"
    )


@pytest.mark.parametrize(
    ("tow_dictionary", "make_tow_dictionary"),
    [(".tow/tag-dictionary.json", True), ("Tag-Dictionary.json", False)],
)
def test_plugin_dictionary_warning_uses_automatic_default_without_flag(
    tmp_path: Path, tow_dictionary: str, make_tow_dictionary: bool
) -> None:
    if make_tow_dictionary:
        (tmp_path / ".tow").mkdir()
        (tmp_path / ".tow/tag-dictionary.json").write_text("{}")
    plugin = tmp_path / ".obsidian/plugins/tag-ontology/data.json"
    plugin.parent.mkdir(parents=True)
    plugin.write_text('{"dictionaryPath": "Tag-Dictionary.json"}')

    assert tow.plugin_dictionary_warning(tmp_path, {**tow.DEFAULTS, "tagDictionary": tow_dictionary}) is None


@pytest.mark.parametrize(
    "raw",
    [[], {"project": "P"}, {"areas": 2}, {"areas": ""}, {"resources": "Notes/Resources"}, {"projectArchive": "a/b"}],
)
def test_load_config_rejects_bad_files(raw: object) -> None:
    with pytest.raises(tow.ConfigError):
        tow.load_config(raw)


def test_tow_init_uses_configured_dictionary_paths_and_freeform_opt_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow" / "config.json").write_text(
        '{"kind": "vault", "scope": "vault", "tagDictionary": "meta/tags.json", '
        '"categoryDictionary": "meta/categories.json"}\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert tow.main(["init"]) == 0
    preview = capsys.readouterr().out
    assert "would create meta/tags.json" not in preview
    assert "would create meta/categories.json" not in preview
    assert ".tow/tags.md" in preview and ".tow/categories.md" in preview

    assert tow.main(["init", "--dictionaries"]) == 0
    preview = capsys.readouterr().out
    assert "would create meta/tags.json" in preview
    assert "would create meta/categories.json" in preview


def test_load_config_accepts_a_whole_vault_scope_and_rejects_others() -> None:
    assert tow.load_config({"scope": "vault"})["scope"] == "vault"
    with pytest.raises(tow.ConfigError, match="scope"):
        tow.load_config({"scope": "everything"})


def test_load_config_allows_dictionary_paths_with_folders() -> None:
    assert tow.load_config({"tagDictionary": "meta/tags.json"})["tagDictionary"] == "meta/tags.json"


def test_load_config_accepts_portable_workflow_locations() -> None:
    locations = {
        "inbox": "Capture",
        "attachments": "Support/media",
        "dailyNotes": "Life/journal",
        "misc": "Support",
    }
    assert tow.load_config(locations) == {**tow.DEFAULTS, **locations}


@pytest.mark.parametrize("key", ["attachments", "dailyNotes"])
@pytest.mark.parametrize("value", ["/outside", "../outside", "inside/../outside", "."])
def test_workflow_storage_paths_stay_relative_to_the_vault(key: str, value: str) -> None:
    with pytest.raises(tow.ConfigError, match=f"{key}:.*vault-relative"):
        tow.load_config({key: value})


@pytest.mark.parametrize("key", ["inbox", "misc"])
@pytest.mark.parametrize("value", ["nested/folder", ".", ".."])
def test_workflow_root_folders_reject_nested_paths(key: str, value: str) -> None:
    with pytest.raises(tow.ConfigError, match="single folder"):
        tow.load_config({key: value})


# tag-ontology arguments


def test_default_cli_is_pinned_to_tag_ontology_0_2_0() -> None:
    assert tow_core.DEFAULT_CLI == "npx --yes tag-ontology@0.2.0"


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


def test_vault_scope_keeps_inbox_and_misc_notes_and_excludes_only_the_dictionary(tmp_path: Path) -> None:
    for d in ["notes", "journal", "00_Inbox", "99_Etc"]:
        (tmp_path / d).mkdir()
    (tmp_path / "Category-Dictionary.md").write_text("")
    cfg = {**tow.DEFAULTS, "scope": "vault"}
    assert tow.scope_excludes(tmp_path, cfg, []) == ["--exclude", "Category-Dictionary.md"]
    assert tow.scope_excludes(tmp_path, cfg, ["Category-Dictionary.md"]) == []


def test_vault_scope_keeps_archive_named_notes_in_ontology_queries() -> None:
    cfg = {**tow.DEFAULTS, "scope": "vault"}
    assert "--exclude" not in tow.ontology_args("show", ["rag", "--notes"], "/v", cfg, [])


def test_vault_scan_keeps_an_explicitly_selected_nested_category_dictionary(tmp_path: Path) -> None:
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta/categories.md").write_text("# Categories\n")
    cfg = {**tow.DEFAULTS, "scope": "vault", "categoryDictionary": "meta/categories.md"}
    assert tow.scope_excludes(tmp_path, cfg, []) == ["--exclude", "meta/categories.md"]
    assert tow.scope_excludes(tmp_path, cfg, ["meta/categories.md"]) == []
    assert tow.scope_excludes(tmp_path, cfg, ["./meta/categories.md"]) == []
    assert tow.scope_excludes(tmp_path, cfg, [str(tmp_path / "meta/categories.md")]) == []


def test_vault_scope_does_not_exclude_a_json_category_dictionary(tmp_path: Path) -> None:
    dictionary = tmp_path / ".tow/category-dictionary.json"
    dictionary.parent.mkdir()
    dictionary.write_text("{}\n")
    cfg = {**tow.DEFAULTS, "scope": "vault", "categoryDictionary": ".tow/category-dictionary.json"}

    assert tow.scope_excludes(tmp_path, cfg, []) == []


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


def test_ontology_args_passes_tags_file_and_subset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = vault(tmp_path)
    (root / "00_Inbox").mkdir()
    fake = fake_cli(tmp_path, monkeypatch, scan_of())
    monkeypatch.chdir(root)

    assert tow.main(["--root", str(root), "ontology", "usage", "--tags-file", "00_Inbox/overlay.json", "--json"]) == 0
    usage_args = json.loads((fake / "args.json").read_text())
    assert "--tags-file 00_Inbox/overlay.json" in " ".join(usage_args)
    assert any(usage_args[index : index + 2] == ["--exclude", "00_Inbox"] for index in range(len(usage_args) - 1))

    assert tow.main(["--root", str(root), "ontology", "subset", "rag", "--json"]) == 0
    subset_args = json.loads((fake / "args.json").read_text())
    assert subset_args == [
        "subset", "rag", "--json", "--root", str(root),
        "--dictionary", "Tag-Dictionary.json", "--names", "kebab",
    ]  # fmt: skip


@pytest.mark.parametrize(
    ("command", "setup"),
    [
        ("init --apply", "legacy"),
        ("migrate --apply", "legacy"),
        ("migrate --remove-legacy --apply", "migrated"),
        ("category add web Web --apply", "tow"),
        ("ontology apply changes.json --base abc", "tow"),
    ],
)
def test_maintenance_writes_refuse_outside_the_vault(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: str,
    setup: str,
) -> None:
    root = tmp_path / "vault"
    project = tmp_path / "project"
    project.mkdir()
    if setup in ("legacy", "migrated"):
        (root / "tow.json").parent.mkdir(parents=True)
        (root / "tow.json").write_text("{}")
        (root / "Tag-Dictionary.json").write_text("{}\n")
        (root / "Category-Dictionary.md").write_text("- `ai` : AI\n")
    if setup in ("migrated", "tow"):
        (root / ".tow").mkdir(parents=True, exist_ok=True)
        (root / ".tow/config.json").write_text('{"kind": "vault"}')
        (root / ".tow/tag-dictionary.json").write_text("{}\n")
        (root / ".tow/category-dictionary.json").write_text("{}\n")

    before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    monkeypatch.chdir(project)
    args = command.split()

    assert tow.main(["--root", str(root), *args]) == 2
    captured = capsys.readouterr()
    assert "changes the vault" in captured.err
    assert f"run it inside {root}" in captured.err
    assert {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()} == before


def test_maintenance_write_location_guard_resolves_symlinks(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    root_alias = tmp_path / "vault-alias"
    root_alias.symlink_to(root, target_is_directory=True)
    cwd_alias = tmp_path / "outside-alias"
    cwd_alias.symlink_to(outside, target_is_directory=True)

    with pytest.raises(tow.ConfigError, match="init --apply changes the vault"):
        tow.require_inside(root_alias, cwd_alias, "init --apply")


@pytest.mark.parametrize("command", ["config", "lint", "find"])
def test_read_commands_work_from_another_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    (root / "tow.json").write_text('{"scope": "vault"}')
    (root / "Category-Dictionary.md").write_text("- `ai` : AI\n")
    (root / "Tag-Dictionary.json").write_text("{}\n")
    monkeypatch.chdir(project)
    fake_cli(tmp_path, monkeypatch, scan_of())

    args = ["--root", str(root), command]
    if command == "find":
        args.append("ai")

    assert tow.main(args) == 0
    capsys.readouterr()


def test_project_status_inside_vault_uses_normal_project_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    vault_root = tmp_path / "vault"
    (vault_root / ".tow").mkdir(parents=True)
    (vault_root / ".tow/config.json").write_text('{"kind": "vault"}', encoding="utf-8")
    monkeypatch.chdir(vault_root)

    assert tow.main(["project", "status"]) == 2

    assert "not a TOW project" in capsys.readouterr().err


def test_lookup_inside_another_git_vault_has_no_project_unavailable_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    current_vault = tmp_path / "current-vault"
    (current_vault / ".tow").mkdir(parents=True)
    (current_vault / ".tow/config.json").write_text('{"kind": "vault"}', encoding="utf-8")
    (current_vault / ".tow/tag-dictionary.json").write_text('{"rag": {}}', encoding="utf-8")
    connected_vault = tmp_path / "connected-vault"
    (connected_vault / ".tow").mkdir(parents=True)
    (connected_vault / ".tow/config.json").write_text('{"kind": "vault"}', encoding="utf-8")
    subprocess.run(["git", "init", str(current_vault)], check=True, capture_output=True)
    fake_cli(
        tmp_path,
        monkeypatch,
        scan_of(),
        {"show": json.dumps({"schemaVersion": 1, "command": "show", "ok": True, "tag": "rag", "noteMatches": []})},
    )
    monkeypatch.chdir(current_vault)
    monkeypatch.setenv("TOW_VAULT", str(connected_vault))

    assert tow.main(["lookup", "rag"]) == 0

    assert json.loads(capsys.readouterr().out)["unavailable"] == []


# command line, against a stand-in for the tag-ontology CLI


def vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    (root / "03_Resources").mkdir(parents=True)
    (root / "Category-Dictionary.md").write_text("### `ai` — AI\n- `ai/rag` : RAG\n")
    (root / "Tag-Dictionary.json").write_text("{}\n")
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


def test_lint_reads_a_json_category_dictionary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "vault"
    (root / ".tow").mkdir(parents=True)
    (root / ".tow/config.json").write_text('{"kind": "vault"}')
    (root / ".tow/category-dictionary.json").write_text(
        '{"ai": {"description": "Artificial intelligence"}, "ai/rag": {"description": "RAG"}}\n'
    )
    (root / ".tow/tag-dictionary.json").write_text("{}\n")
    fake_cli(tmp_path, monkeypatch, scan_of(note("a.md", {"type": "resource", "category": ["ai/rag"]})))

    assert tow.main(["--root", str(root), "lint"]) == 0
    assert capsys.readouterr().out.strip() == "OK"


def test_lint_still_reads_a_markdown_category_dictionary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = vault(tmp_path)
    fake_cli(tmp_path, monkeypatch, scan_of(note("03_Resources/a.md", {"type": "resource", "category": ["ai/rag"]})))

    assert tow.main(["--root", str(root), "lint"]) == 0
    assert capsys.readouterr().out.strip() == "OK"


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


def test_main_find_filters_without_a_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = vault(tmp_path)
    notes = [note("03_Resources/a.md", {"type": "project"}), note("03_Resources/b.md", {"type": "resource"})]
    fake_cli(tmp_path, monkeypatch, scan_of(*notes))
    assert tow.main(["--root", str(root), "find", "--type", "project"]) == 0
    assert capsys.readouterr().out.strip() == "03_Resources/a.md"


def test_main_find_needs_a_prefix_or_a_filter(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        tow.main(["--root", str(vault(tmp_path)), "find"])


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


def test_category_add_previews_then_writes_one_entry_per_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "vault"
    dictionary = root / ".tow/category-dictionary.json"
    dictionary.parent.mkdir(parents=True)
    dictionary.write_text('{"ai": {"description": "Artificial intelligence"}}\n')
    (root / ".tow/config.json").write_text('{"kind": "vault"}')
    monkeypatch.chdir(root)
    assert tow.main(["--root", str(root), "category", "add", "ai/rag", "Retrieval-augmented generation"]) == 0
    assert capsys.readouterr().out == 'would add "ai/rag": Retrieval-augmented generation\n'
    assert json.loads(dictionary.read_text()) == {"ai": {"description": "Artificial intelligence"}}

    assert (
        tow.main(["--root", str(root), "category", "add", "ai/rag", "Retrieval-augmented generation", "--apply"]) == 0
    )
    assert capsys.readouterr().out == 'added "ai/rag"\n'
    assert dictionary.read_text() == (
        '{\n"ai": {"description": "Artificial intelligence"},\n'
        '"ai/rag": {"description": "Retrieval-augmented generation"}\n}\n'
    )


def test_category_add_accepts_korean_category_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "vault"
    (root / ".tow").mkdir(parents=True)
    (root / ".tow" / "config.json").write_text('{"kind": "vault"}\n', encoding="utf-8")
    (root / ".tow" / "category-dictionary.json").write_text("{\n}\n", encoding="utf-8")
    monkeypatch.chdir(root)

    assert tow.main(["category", "add", "인공지능/검색_증강", "검색 기반 생성"]) == 0

    assert 'would add "인공지능/검색_증강": 검색 기반 생성' in capsys.readouterr().out


def test_category_add_refuses_duplicates_invalid_values_and_markdown_dictionaries(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    json_path = root / ".tow/category-dictionary.json"
    json_path.parent.mkdir()
    json_path.write_text('{"ai": {"description": "Artificial intelligence"}}\n')
    (root / ".tow/config.json").write_text('{"kind": "vault"}')

    assert tow.main(["--root", str(root), "category", "add", "ai", "Duplicate"]) == 2
    assert "already registered" in capsys.readouterr().err
    assert tow.main(["--root", str(root), "category", "add", "ai/with space", "Invalid"]) == 2
    assert "invalid category" in capsys.readouterr().err

    (root / ".tow/config.json").unlink()
    (root / "tow.json").write_text('{"categoryDictionary": "Category-Dictionary.md"}')
    (root / "Category-Dictionary.md").write_text("- `ai` : AI\n")
    assert tow.main(["--root", str(root), "category", "add", "web", "Web"]) == 2
    assert 'run "tow migrate"' in capsys.readouterr().err


def test_config_uses_the_current_vault_without_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    connected = tmp_path / "connected"
    current = tmp_path / "current"
    (connected / ".tow").mkdir(parents=True)
    (connected / ".tow" / "config.json").write_text('{"kind": "vault"}\n', encoding="utf-8")
    (current / ".tow").mkdir(parents=True)
    (current / ".tow" / "config.json").write_text('{"kind": "vault"}\n', encoding="utf-8")
    monkeypatch.setenv("TOW_VAULT", str(connected))
    monkeypatch.chdir(current)

    assert tow.main(["config"]) == 0

    output = capsys.readouterr()
    assert json.loads(output.out) == tow.TOW_DEFAULTS
    assert f"tow: vault {current} (from ancestor, tow)" in output.err
    assert "warning: the current folder is inside the vault" not in output.err


def test_main_config_prints_the_merged_settings(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = vault(tmp_path)
    (root / "tow.json").write_text('{"areas": "Areas"}')
    assert tow.main(["--root", str(root), "config"]) == 0
    assert json.loads(capsys.readouterr().out) == {**tow.DEFAULTS, "areas": "Areas"}


def test_tow_py_runs_as_a_single_path(tmp_path: Path) -> None:
    """`tow` is just the script's path, so it still works when an agent keeps it in a shell variable."""
    script = Path(tow.__file__)
    result = subprocess.run([str(script), "--root", str(vault(tmp_path)), "config"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == tow.DEFAULTS


def test_main_reports_a_broken_config_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = vault(tmp_path)
    (root / "tow.json").write_text("{not json")
    assert tow.main(["--root", str(root), "config"]) == 2
    assert "tow.json" in capsys.readouterr().err


# first-time setup


@pytest.mark.parametrize("key", ["categoryDictionary", "tagDictionary"])
@pytest.mark.parametrize("path", ["../outside.json", "/tmp/outside.json", "."])
def test_dictionary_setup_paths_must_be_inside_the_vault(key: str, path: str) -> None:
    with pytest.raises(tow.ConfigError):
        tow.load_config({key: path})


@pytest.mark.parametrize("key", ["categoryDictionary", "tagDictionary"])
@pytest.mark.parametrize("scope", ["para", "vault"])
def test_init_rejects_dictionary_directory_syntax_before_writes(
    tmp_path: Path, key: str, scope: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "tow.json"
    config.write_text(json.dumps({"scope": scope, key: "meta/Dictionary.md/"}))
    before = config.read_bytes()

    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--dictionaries", "--apply"]) == 2
    assert list(tmp_path.iterdir()) == [config]
    assert config.read_bytes() == before


def test_init_rejects_dictionary_parent_symlinks_before_creating_any_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "meta").symlink_to(outside, target_is_directory=True)
    (root / "tow.json").write_text('{"categoryDictionary": "meta/categories.md"}')
    monkeypatch.chdir(root)
    assert tow.main(["--root", str(root), "init", "--apply"]) == 2
    assert list(outside.iterdir()) == []
    assert not (root / "01_Projects").exists()


@pytest.mark.parametrize(
    "settings",
    [
        {"categoryDictionary": "meta/dict.md", "tagDictionary": "meta/dict.md"},
        {"categoryDictionary": "01_Projects"},
        {"categoryDictionary": "meta", "tagDictionary": "meta/tags.json"},
        {},
    ],
)
def test_init_rejects_conflicting_or_wrong_type_targets_before_writes(
    tmp_path: Path, settings: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "tow.json").write_text(json.dumps(settings))
    if not settings:
        (tmp_path / "Category-Dictionary.md").mkdir()
    before = set(tmp_path.rglob("*"))
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--apply"]) == 2
    assert set(tmp_path.rglob("*")) == before


def test_init_reports_filesystem_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def denied(*args: object, **kwargs: object) -> None:
        raise PermissionError("fixture permission denied")

    monkeypatch.setattr(Path, "mkdir", denied)
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--apply"]) == 2
    assert "fixture permission denied" in capsys.readouterr().err


def test_init_creates_a_json_category_dictionary_for_tow_vaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/config.json").write_text('{"kind": "vault", "scope": "vault"}')
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--dictionaries", "--apply"]) == 0
    capsys.readouterr()
    assert (tmp_path / ".tow/category-dictionary.json").read_text() == "{\n}\n"
    assert not (tmp_path / "01_Projects").exists()


def test_init_lists_missing_paths_and_creates_them_only_with_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}")
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init"]) == 0
    captured = capsys.readouterr()
    assert "would create 03_Resources/" in captured.out
    assert 'run "tow migrate"' in captured.err
    assert [path.name for path in tmp_path.iterdir()] == ["tow.json"]
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--apply"]) == 0
    for folder in ["01_Projects", "02_Areas", "03_Resources", "04_Archives", "00_Inbox"]:
        assert (tmp_path / folder).is_dir()
    categories = (tmp_path / "Category-Dictionary.md").read_text()
    assert tow.category_values(categories) == set()
    assert json.loads((tmp_path / "Tag-Dictionary.json").read_text()) == {}
    capsys.readouterr()
    tow.main(["--root", str(tmp_path), "init"])
    assert capsys.readouterr().out.strip() == "nothing to create"


def test_vault_init_creates_nothing_without_explicit_dictionary_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text('{"scope": "vault", "tagDictionary": "meta/tags.json"}')
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--apply"]) == 0
    assert capsys.readouterr().out.strip() == "nothing to create"
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_init_creates_para_folders_for_tow_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/config.json").write_text('{"kind": "vault", "scope": "para"}')
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--apply"]) == 0
    capsys.readouterr()
    for folder in ("01_Projects", "02_Areas", "03_Resources", "04_Archives", "00_Inbox"):
        assert (tmp_path / folder).is_dir()


def test_init_creates_para_folders_for_plain_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--apply"]) == 0
    capsys.readouterr()
    for folder in ("01_Projects", "02_Areas", "03_Resources", "04_Archives", "00_Inbox"):
        assert (tmp_path / folder).is_dir()


@pytest.mark.parametrize("tag_path", ["./meta/tags.json", "meta\\\\tags.json"])
def test_init_normalizes_configured_dictionary_paths_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tag_path: str
) -> None:
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/config.json").write_text(
        json.dumps({"kind": "vault", "scope": "vault", "tagDictionary": tag_path}), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "init", "--dictionaries", "--apply"]) == 0

    capsys.readouterr()
    assert (tmp_path / "meta/tags.json").read_text(encoding="utf-8") == "{\n}\n"


def test_init_uses_markdown_starter_for_a_configured_markdown_dictionary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/config.json").write_text(
        '{"kind": "vault", "scope": "vault", "categoryDictionary": "meta/categories.md"}', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "init", "--dictionaries", "--apply"]) == 0

    capsys.readouterr()
    content = (tmp_path / "meta/categories.md").read_text(encoding="utf-8")
    assert content.startswith("---\nupdated: ")
    assert "# Category Dictionary" in content


def test_init_uses_configured_dictionary_paths_in_tow_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/config.json").write_text(
        '{"kind": "vault", "scope": "vault", "tagDictionary": "meta/tags.json", '
        '"categoryDictionary": "meta/categories.json"}',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "init", "--dictionaries"]) == 0

    output = capsys.readouterr().out
    assert "would create meta/tags.json" in output
    assert "would create meta/categories.json" in output
    assert "would create .tow/tag-dictionary.json" not in output
    assert "would create .tow/category-dictionary.json" not in output


def test_init_uses_tow_layout_for_an_empty_plugin_dictionary_without_deleting_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    plugin_dictionary = tmp_path / "Tag-Dictionary.json"
    plugin_dictionary.write_text("{\n}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "init", "--apply"]) == 0

    output = capsys.readouterr()
    assert output.err.strip() == (
        "tow: Tag-Dictionary.json is the plugin's empty starter; the plugin switches to "
        ".tow/tag-dictionary.json once it exists, and you can delete the root file"
    )
    assert (tmp_path / ".tow/config.json").is_file()
    assert (tmp_path / ".tow/tag-dictionary.json").read_text(encoding="utf-8") == "{\n}\n"
    assert plugin_dictionary.read_text(encoding="utf-8") == "{\n}\n"


def test_init_creates_the_dot_tow_starter_bundle_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init"]) == 0
    preview = capsys.readouterr().out
    for name in (
        ".tow/config.json",
        ".tow/tags.md",
        ".tow/tag-dictionary.json",
        ".tow/categories.md",
        ".tow/category-dictionary.json",
    ):
        assert f"would create {name}" in preview
    assert list(tmp_path.iterdir()) == []

    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--apply"]) == 0
    capsys.readouterr()
    assert (tmp_path / ".tow/config.json").read_text() == '{"kind": "vault"}\n'
    assert (tmp_path / ".tow/tag-dictionary.json").read_text() == "{\n}\n"
    assert (tmp_path / ".tow/category-dictionary.json").read_text() == "{\n}\n"
    assert (tmp_path / ".tow/tags.md").read_text() == (Path(tow.__file__).parent / "starters/tags.md").read_text()
    assert (tmp_path / ".tow/categories.md").read_text() == (
        Path(tow.__file__).parent / "starters/categories.md"
    ).read_text()
    assert tow.main(["--root", str(tmp_path), "init"]) == 0
    assert capsys.readouterr().out.strip() == "nothing to create"


@pytest.mark.parametrize("missing", ["Tag-Dictionary.json", "Category-Dictionary.md"])
def test_migrate_creates_empty_dictionary_when_a_legacy_dictionary_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], missing: str
) -> None:
    (tmp_path / "tow.json").write_text("{}\n", encoding="utf-8")
    if missing != "Tag-Dictionary.json":
        (tmp_path / "Tag-Dictionary.json").write_text('{"tag": {"description": "Tag"}}\n', encoding="utf-8")
    if missing != "Category-Dictionary.md":
        (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0

    output = capsys.readouterr().out
    target = ".tow/tag-dictionary.json" if missing == "Tag-Dictionary.json" else ".tow/category-dictionary.json"
    assert f"missing; created empty dictionary {target}" in output
    assert json.loads((tmp_path / ".tow/tag-dictionary.json").read_text()) == (
        {} if missing == "Tag-Dictionary.json" else {"tag": {"description": "Tag"}}
    )
    assert json.loads((tmp_path / ".tow/category-dictionary.json").read_text()) == (
        {} if missing == "Category-Dictionary.md" else {"ai": {"description": "AI"}}
    )
    assert (tmp_path / ".tow/tag-dictionary.json").read_text() == (
        "{\n}\n" if missing == "Tag-Dictionary.json" else (tmp_path / "Tag-Dictionary.json").read_text()
    )


def test_migrate_remove_legacy_does_not_report_missing_default_dictionary_as_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    (tmp_path / ".tow/tag-dictionary.json").write_text('{\n"custom": {"description": "Custom"}\n}\n', encoding="utf-8")

    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy"]) == 0
    output = capsys.readouterr().out

    assert "kept legacy original Tag-Dictionary.json" not in output
    assert "Tag-Dictionary.json because it differs" not in output


def test_migrate_reports_only_sources_created_during_this_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    output = capsys.readouterr().out

    assert "Tag-Dictionary.json" not in output
    assert not (tmp_path / "Tag-Dictionary.json").exists()


def test_migrate_does_not_report_an_existing_target_as_created_for_a_missing_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n", encoding="utf-8")
    existing_tag_target = tmp_path / ".tow/tag-dictionary.json"
    existing_tag_target.parent.mkdir()
    existing_tag_target.write_text("{\n}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0

    assert "missing; created empty dictionary .tow/tag-dictionary.json" not in capsys.readouterr().out


def test_migrate_does_not_claim_a_dictionary_was_created_when_its_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def fail_dictionary_write(path: Path, text: str, *, exclusive: bool = False) -> None:
        if path == tmp_path / ".tow/tag-dictionary.json":
            raise OSError("simulated write failure")
        tow_core.write_text_atomic(path, text, exclusive=exclusive)

    monkeypatch.setattr(tow, "write_text_atomic", fail_dictionary_write)

    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 2

    assert "missing; created empty dictionary" not in capsys.readouterr().out


def test_migrate_previews_then_copies_and_converts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text(
        '{"scope": "vault", "tagDictionary": "Tag-Dictionary.json", '
        '"categoryDictionary": "Category-Dictionary.md", "areas": "Knowledge"}'
    )
    (tmp_path / "Tag-Dictionary.json").write_bytes(b'{"alpha": {"description": "A"}}\r\n')
    (tmp_path / "Category-Dictionary.md").write_text(
        "# Categories\n### `ai` — artificial intelligence\n- `ai/rag` : retrieval augmented generation\n"
    )

    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate"]) == 0
    assert "would create .tow/config.json" in capsys.readouterr().out
    assert not (tmp_path / ".tow").exists()

    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    assert json.loads((tmp_path / ".tow/config.json").read_text()) == {
        "kind": "vault",
        "scope": "vault",
        "areas": "Knowledge",
        "categoryDictionary": ".tow/category-dictionary.json",
    }
    assert (tmp_path / ".tow/tag-dictionary.json").read_bytes() == b'{"alpha": {"description": "A"}}\r\n'
    assert json.loads((tmp_path / ".tow/category-dictionary.json").read_text()) == {
        "ai": {"description": "artificial intelligence"},
        "ai/rag": {"description": "retrieval augmented generation"},
    }
    assert (tmp_path / "tow.json").exists()
    assert (tmp_path / "Tag-Dictionary.json").exists()
    assert (tmp_path / "Category-Dictionary.md").exists()


def test_migrate_refuses_when_existing_target_bytes_differ(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}")
    (tmp_path / "Tag-Dictionary.json").write_text("{}\n")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n")
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/config.json").write_text('{"kind": "vault"}')
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 2
    assert "already exists" in capsys.readouterr().err
    assert list((tmp_path / ".tow").iterdir()) == [tmp_path / ".tow/config.json"]


def test_migrate_resumes_after_a_later_target_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}")
    (tmp_path / "Tag-Dictionary.json").write_text("{}\n")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n")
    monkeypatch.chdir(tmp_path)
    real_write = tow.write_text_atomic
    failed_path = tmp_path / ".tow/category-dictionary.json"

    def fail_once(path: Path, text: str, *, exclusive: bool = False) -> None:
        if path == failed_path:
            raise OSError("simulated write failure")
        real_write(path, text, exclusive=exclusive)

    monkeypatch.setattr(tow, "write_text_atomic", fail_once)
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 2
    assert "simulated write failure" in capsys.readouterr().err
    assert not (tmp_path / ".tow/config.json").exists()
    assert tow_core.resolve_vault(tmp_path, None, {}).layout == "legacy"

    monkeypatch.setattr(tow, "write_text_atomic", real_write)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    assert json.loads((tmp_path / ".tow/config.json").read_text()) == {
        "kind": "vault",
        "categoryDictionary": ".tow/category-dictionary.json",
    }
    assert json.loads((tmp_path / ".tow/category-dictionary.json").read_text()) == {"ai": {"description": "AI"}}


def test_migrate_accepts_existing_targets_with_expected_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}")
    (tmp_path / "Tag-Dictionary.json").write_text("{}\n")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n")
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    assert capsys.readouterr().out.strip() == "nothing to migrate"


def test_migrate_remove_legacy_requires_verified_copies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text('{"areas": "Knowledge"}')
    (tmp_path / "Tag-Dictionary.json").write_text("{}\n")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n")
    (tmp_path / ".tow").mkdir()
    (tmp_path / ".tow/config.json").write_text('{"kind": "vault", "areas": "Knowledge"}')
    (tmp_path / ".tow/tag-dictionary.json").write_text("tampered\n")
    (tmp_path / ".tow/category-dictionary.json").write_text('{\n"ai": {"description": "AI"}\n}\n')

    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy", "--apply"]) == 2
    assert "verification" in capsys.readouterr().err
    assert all((tmp_path / name).exists() for name in ("tow.json", "Tag-Dictionary.json", "Category-Dictionary.md"))


def test_migrate_remove_legacy_keeps_customized_manual_and_reports_changed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}")
    (tmp_path / "Tag-Dictionary.json").write_text("{}\n")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n")

    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    (tmp_path / ".tow/tags.md").write_text("custom tags manual\n")
    (tmp_path / ".tow/categories.md").write_text("custom categories manual\n")
    (tmp_path / ".tow/tag-dictionary.json").write_text('{\n"custom": {"description": "Custom"}\n}\n')
    (tmp_path / ".tow/category-dictionary.json").write_text('{\n"web": {"description": "Web"}\n}\n')

    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy"]) == 0
    output = capsys.readouterr()
    assert "would delete tow.json" in output.out
    assert "would delete Tag-Dictionary.json" not in output.out
    assert "changed .tow/tag-dictionary.json; kept legacy original Tag-Dictionary.json because it differs" in output.out
    assert (
        "changed .tow/category-dictionary.json; kept legacy original Category-Dictionary.md because it differs"
        in output.out
    )
    assert "changed .tow/tags.md" not in output.out
    assert "changed .tow/categories.md" not in output.out
    assert "verification failed: migration verification failed:" not in output.err
    assert all((tmp_path / name).exists() for name in ("tow.json", "Tag-Dictionary.json", "Category-Dictionary.md"))


def test_migrate_remove_legacy_reports_verification_failure_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "Tag-Dictionary.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    (tmp_path / ".tow/tags.md").unlink()

    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy", "--apply"]) == 2

    error = capsys.readouterr().err
    assert error.count("migration verification failed:") == 1
    assert "missing .tow/tags.md" in error
    assert all((tmp_path / name).exists() for name in ("tow.json", "Tag-Dictionary.json", "Category-Dictionary.md"))


def test_migrate_remove_legacy_succeeds_when_tow_json_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "Tag-Dictionary.json").write_text("{}\n")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n")

    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy", "--apply"]) == 0
    capsys.readouterr()
    assert not (tmp_path / "Tag-Dictionary.json").exists()
    assert not (tmp_path / "Category-Dictionary.md").exists()
    assert (tmp_path / ".tow/config.json").exists()


def test_migrate_remove_legacy_keeps_customized_default_category_markdown_dictionary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "Tag-Dictionary.json").write_text('{"tag": {"description": "Tag"}}\n', encoding="utf-8")
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : AI\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    (tmp_path / ".tow/category-dictionary.json").write_text('{\n"web": {"description": "Web"}\n}\n')
    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy", "--apply"]) == 0
    output = capsys.readouterr().out

    assert (tmp_path / "Category-Dictionary.md").is_file()
    assert "deleted Category-Dictionary.md" not in output


def test_migrate_remove_legacy_keeps_custom_category_markdown_dictionary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "meta").mkdir()
    (tmp_path / "tow.json").write_text('{"categoryDictionary": "meta/categories.md"}', encoding="utf-8")
    (tmp_path / "Tag-Dictionary.json").write_text("{\n}\n", encoding="utf-8")
    (tmp_path / "meta/categories.md").write_text("- `ai` : AI\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy", "--apply"]) == 0
    output = capsys.readouterr().out

    assert (tmp_path / "meta/categories.md").is_file()
    assert "deleted Category-Dictionary.md" not in output


def test_migrate_remove_legacy_keeps_custom_dictionaries_after_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "meta").mkdir()
    (tmp_path / "tow.json").write_text(
        '{"tagDictionary": "meta/tags.json", "categoryDictionary": "meta/categories.md"}'
    )
    (tmp_path / "meta/tags.json").write_text('{"alpha": {"description": "A"}}\n')
    (tmp_path / "meta/categories.md").write_text("- `ai` : AI\n")

    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy", "--apply"]) == 0
    capsys.readouterr()
    assert not (tmp_path / "tow.json").exists()
    assert json.loads((tmp_path / ".tow/config.json").read_text()) == {
        "kind": "vault",
        "tagDictionary": "meta/tags.json",
        "categoryDictionary": ".tow/category-dictionary.json",
    }
    assert (tmp_path / "meta/tags.json").exists()
    assert (tmp_path / "meta/categories.md").is_file()


def test_migrate_remove_legacy_deletes_only_after_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text(
        '{"areas": "Knowledge", "categoryDictionary": "Category-Dictionary.md", "tagDictionary": "Tag-Dictionary.json"}'
    )
    (tmp_path / "Tag-Dictionary.json").write_text('{"alpha": {"description": "A"}}\n')
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : artificial intelligence\n")

    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "migrate", "--apply"]) == 0
    capsys.readouterr()
    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy"]) == 0
    assert "would delete tow.json" in capsys.readouterr().out
    assert all((tmp_path / name).exists() for name in ("tow.json", "Tag-Dictionary.json", "Category-Dictionary.md"))

    assert tow.main(["--root", str(tmp_path), "migrate", "--remove-legacy", "--apply"]) == 0
    capsys.readouterr()
    assert all(not (tmp_path / name).exists() for name in ("tow.json", "Tag-Dictionary.json", "Category-Dictionary.md"))
    assert (tmp_path / ".tow/config.json").exists()


def test_vault_init_creates_only_requested_dictionaries_and_preserves_existing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tow.json").write_text('{"scope": "vault", "tagDictionary": "meta/tags.json"}')
    (tmp_path / "Category-Dictionary.md").write_text("- `ai` : mine\n")
    monkeypatch.chdir(tmp_path)
    assert tow.main(["--root", str(tmp_path), "init", "--dictionaries"]) == 0
    assert "would create meta/tags.json" in capsys.readouterr().out
    assert not (tmp_path / "meta").exists()
    assert tow.main(["--root", str(tmp_path), "init", "--dictionaries", "--apply"]) == 0
    assert capsys.readouterr().out.splitlines() == ["created meta/tags.json"]
    assert (tmp_path / "Category-Dictionary.md").read_text() == "- `ai` : mine\n"
    assert json.loads((tmp_path / "meta/tags.json").read_text()) == {}
    assert not (tmp_path / "00_Inbox").exists()


def test_main_warns_when_the_para_scope_has_no_folders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "notes").mkdir()
    fake_cli(tmp_path, monkeypatch, scan_of())
    assert tow.main(["--root", str(tmp_path), "find", "--tag", "rag"]) == 0
    assert '"scope": "vault"' in capsys.readouterr().err
    (tmp_path / "tow.json").write_text('{"scope": "vault"}')
    tow.main(["--root", str(tmp_path), "find", "--tag", "rag"])
    assert capsys.readouterr().err == ""


def test_main_points_to_init_when_the_tag_dictionary_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = vault(tmp_path)
    (root / "Tag-Dictionary.json").unlink()
    assert tow.main(["--root", str(root), "ontology", "check", "--json"]) == 2
    assert "tow init" in capsys.readouterr().err
