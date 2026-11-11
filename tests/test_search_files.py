import subprocess
from pathlib import Path

import pytest

import tow_search


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init")
    return path


def make_vault(path: Path) -> Path:
    (path / ".tow").mkdir(parents=True)
    (path / ".tow" / "config.json").write_text('{"kind": "vault"}\n', encoding="utf-8")
    return path


def write_note(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Note\n", encoding="utf-8")


def para_config() -> dict[str, str]:
    return {
        "projects": "projects",
        "areas": "areas",
        "resources": "resources",
        "archives": "archives",
        "projectArchive": "archive",
        "scope": "para",
    }


def test_candidates_in_para_scope_skip_non_para_and_hidden_folders(tmp_path: Path) -> None:
    root = init_repo(tmp_path / "vault")
    for relative in (
        "projects/keep.md",
        "projects/readme.txt",
        "projects/Example/archive/old.md",
        "areas/keep.md",
        "archives/keep.md",
        "outside/drop.md",
        "projects/tow/kept.md",
        "tow/tags.md",
        ".obsidian/private.md",
        ".tow/private.md",
    ):
        write_note(root, relative)

    result = tow_search.vault_candidates(root, para_config())

    assert result.paths == ["archives/keep.md", "areas/keep.md", "projects/keep.md", "projects/tow/kept.md"]
    assert result.contents_ok is True
    assert result.unavailable == []


def test_candidates_use_git_ignore_rules_and_keep_untracked_notes(tmp_path: Path) -> None:
    root = init_repo(tmp_path / "vault")
    write_note(root, "projects/tracked.md")
    write_note(root, "projects/untracked.md")
    write_note(root, "projects/ignored/hidden.md")
    (root / ".gitignore").write_text("projects/ignored/\n", encoding="utf-8")
    git(root, "add", "projects/tracked.md", ".gitignore")

    result = tow_search.vault_candidates(root, para_config())

    assert result.paths == ["projects/tracked.md", "projects/untracked.md"]
    assert result.contents_ok is True
    assert result.unavailable == []


def test_candidates_outside_git_do_not_apply_gitignore(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    write_note(root, "projects/ignored-looking.md")
    (root / ".gitignore").write_text("projects/ignored-looking.md\n", encoding="utf-8")

    result = tow_search.vault_candidates(root, para_config())

    assert result.paths == ["projects/ignored-looking.md"]
    assert result.contents_ok is True
    assert result.unavailable == []


def test_candidates_vault_scope_includes_every_visible_note_except_tow(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    for relative in (
        "root.md",
        "projects/project.md",
        "outside/note.md",
        "tow/tags.md",
        ".obsidian/private.md",
        ".tow/private.md",
    ):
        write_note(root, relative)

    result = tow_search.vault_candidates(root, {**para_config(), "scope": "vault"})

    assert result.paths == ["outside/note.md", "projects/project.md", "root.md"]
    assert result.contents_ok is True
    assert result.unavailable == []


def test_candidates_fall_back_to_walk_when_git_is_missing_for_git_vault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = init_repo(tmp_path / "vault")
    write_note(root, "projects/visible.md")
    write_note(root, "projects/ignored/visible-too.md")
    (root / ".gitignore").write_text("projects/ignored/\n", encoding="utf-8")
    monkeypatch.setenv("PATH", "")

    result = tow_search.vault_candidates(root, para_config())

    assert result.paths == ["projects/ignored/visible-too.md", "projects/visible.md"]
    assert result.contents_ok is False
    assert result.unavailable == [
        "vault: git is not available, so .gitignore rules can't be applied; body and heading search skipped"
    ]
