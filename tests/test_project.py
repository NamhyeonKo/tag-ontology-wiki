import json
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

import tow
import tow_project


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def git_path(cwd: Path, *args: str) -> Path:
    path = Path(git(cwd, *args))
    return (cwd / path).resolve() if not path.is_absolute() else path


@pytest.fixture(autouse=True)
def isolate_git_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    global_config = tmp_path / "empty-gitconfig"
    global_config.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init")
    git(path, "config", "user.name", "TOW Test")
    git(path, "config", "user.email", "tow-test@example.invalid")
    git(path, "config", "commit.gpgsign", "false")
    return path


def make_vault(path: Path) -> Path:
    (path / ".tow").mkdir(parents=True)
    (path / ".tow" / "tags.md").write_text("# Vault tag rules\n", encoding="utf-8")
    return path


def test_project_init_shared_creates_files_and_excludes_only_the_local_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = init_repo(tmp_path / "project")
    vault = make_vault(tmp_path / "vault")
    monkeypatch.chdir(project)

    assert (
        tow.main(["--root", str(vault), "project", "init", "--mode", "shared", "--exclude", "vendor", "--apply"]) == 0
    )

    project_tow = project / ".tow"
    assert json.loads((project_tow / "config.json").read_text(encoding="utf-8")) == {
        "kind": "project",
        "exclude": ["vendor"],
    }
    assert (project_tow / "tags.md").read_bytes() == b"# Vault tag rules\n"
    assert (project_tow / "documents.json").read_text(encoding="utf-8") == "{\n}\n"
    assert (project_tow / "tag-dictionary.json").read_text(encoding="utf-8") == "{\n}\n"
    exclude = git_path(project, "rev-parse", "--git-path", "info/exclude")
    assert exclude.read_text(encoding="utf-8").splitlines()[-1] == "/.tow/documents.local.json"
    assert git(project, "check-ignore", "-q", ".tow/documents.local.json") == ""
    assert tow_project.project_mode(project) == "shared"


def test_project_init_local_excludes_the_whole_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = init_repo(tmp_path / "project")
    vault = make_vault(tmp_path / "vault")
    monkeypatch.chdir(project)

    assert tow.main(["--root", str(vault), "project", "init", "--mode", "local", "--apply"]) == 0

    exclude = git_path(project, "rev-parse", "--git-path", "info/exclude")
    assert exclude.read_text(encoding="utf-8").splitlines()[-1] == "/.tow/"
    assert git(project, "check-ignore", "-q", ".tow/config.json") == ""
    assert tow_project.project_mode(project) == "local"


def test_project_init_in_a_nested_project_uses_a_toplevel_relative_pattern(tmp_path: Path) -> None:
    repository = init_repo(tmp_path / "repository")
    project = repository / "work" / "nested"
    project.mkdir(parents=True)
    vault = make_vault(tmp_path / "vault")

    assert tow_project.cmd_project_init(project, vault, {}, "local", [], True) == 0

    exclude = git_path(repository, "rev-parse", "--git-path", "info/exclude")
    assert exclude.read_text(encoding="utf-8").splitlines()[-1] == "/work/nested/.tow/"
    assert git(repository, "check-ignore", "-q", "work/nested/.tow/config.json") == ""


def test_project_init_in_a_worktree_uses_git_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repository = init_repo(tmp_path / "repository")
    (repository / "README.md").write_text("repo\n", encoding="utf-8")
    git(repository, "add", "README.md")
    git(repository, "commit", "-m", "initial")
    worktree = tmp_path / "worktree"
    git(repository, "worktree", "add", str(worktree), "-b", "test-worktree")
    linked_git_dir = Path(git(worktree, "rev-parse", "--git-dir"))
    if not linked_git_dir.is_absolute():
        linked_git_dir = worktree / linked_git_dir
    assert linked_git_dir.resolve() != (repository / ".git").resolve()
    worktree_exclude = Path(git(worktree, "rev-parse", "--git-path", "info/exclude"))
    if not worktree_exclude.is_absolute():
        worktree_exclude = worktree / worktree_exclude
    repository_exclude = git_path(repository, "rev-parse", "--git-path", "info/exclude")
    assert worktree_exclude == repository_exclude
    vault = make_vault(tmp_path / "vault")
    monkeypatch.chdir(worktree)

    assert tow.main(["--root", str(vault), "project", "init", "--mode", "local", "--apply"]) == 0

    exclude = git_path(worktree, "rev-parse", "--git-path", "info/exclude")
    assert exclude == worktree_exclude
    assert "/.tow/" in exclude.read_text(encoding="utf-8").splitlines()
    assert git(worktree, "check-ignore", "-q", ".tow/config.json") == ""


def test_project_init_refuses_local_mode_when_dot_tow_is_tracked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = init_repo(tmp_path / "project")
    (project / ".tow").mkdir()
    (project / ".tow" / "tracked.json").write_text("{}\n", encoding="utf-8")
    git(project, "add", ".tow/tracked.json")
    git(project, "commit", "-m", "track project metadata")
    vault = make_vault(tmp_path / "vault")
    monkeypatch.chdir(project)

    assert tow.main(["--root", str(vault), "project", "init", "--mode", "local", "--apply"]) == 2

    assert "tracked" in capsys.readouterr().err
    assert not (project / ".tow" / "config.json").exists()
    assert (
        "/.tow/"
        not in git_path(project, "rev-parse", "--git-path", "info/exclude").read_text(encoding="utf-8").splitlines()
    )


def test_project_init_refuses_local_mode_when_tracked_file_check_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = init_repo(tmp_path / "project")
    vault = make_vault(tmp_path / "vault")
    real_git = tow_project.git

    def fail_ls_files(cwd: Path, *args: str) -> str | None:
        if args == ("ls-files", ".tow"):
            return None
        return real_git(cwd, *args)

    monkeypatch.setattr(tow_project, "git", fail_ls_files)

    with pytest.raises(tow.ConfigError, match=r"can't determine whether \.tow contains tracked files"):
        tow_project.cmd_project_init(project, vault, {}, "local", [], True)

    assert not (project / ".tow" / "config.json").exists()


def test_project_init_shared_refuses_when_gitignore_hides_all_project_metadata(tmp_path: Path) -> None:
    project = init_repo(tmp_path / "project")
    (project / ".gitignore").write_text(".tow/\n", encoding="utf-8")
    vault = make_vault(tmp_path / "vault")

    with pytest.raises(tow.ConfigError, match="shared project metadata is ignored"):
        tow_project.cmd_project_init(project, vault, {}, "shared", [], True)

    assert not (project / ".tow" / "config.json").exists()
    assert (
        "/.tow/documents.local.json"
        not in git_path(project, "rev-parse", "--git-path", "info/exclude").read_text(encoding="utf-8").splitlines()
    )


def test_project_init_shared_refuses_when_a_project_metadata_file_is_ignored(tmp_path: Path) -> None:
    project = init_repo(tmp_path / "project")
    (project / ".gitignore").write_text("/.tow/documents.json\n", encoding="utf-8")
    vault = make_vault(tmp_path / "vault")

    with pytest.raises(tow.ConfigError, match="shared project metadata is ignored"):
        tow_project.cmd_project_init(project, vault, {}, "shared", [], True)

    assert not (project / ".tow" / "config.json").exists()
    assert not (project / ".tow" / "documents.json").exists()
    assert (
        "/.tow/documents.local.json"
        not in git_path(project, "rev-parse", "--git-path", "info/exclude").read_text(encoding="utf-8").splitlines()
    )


def test_project_init_rolls_back_created_files_when_exclude_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = init_repo(tmp_path / "project")
    vault = make_vault(tmp_path / "vault")
    exclude = git_path(project, "rev-parse", "--git-path", "info/exclude")
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text("original\n", encoding="utf-8")
    original_open = Path.open

    def fail_exclude_write(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == exclude and args and args[0] == "a":
            raise OSError("simulated exclude write failure")
        result = cast(Any, original_open)(path, *args, **kwargs)
        return result

    monkeypatch.setattr(Path, "open", fail_exclude_write)

    with pytest.raises(OSError, match="simulated exclude write failure"):
        tow_project.cmd_project_init(project, vault, {}, "shared", [], True)

    assert not (project / ".tow").exists()
    assert exclude.read_text(encoding="utf-8") == "original\n"


def test_project_init_never_overwrites(tmp_path: Path) -> None:
    project = init_repo(tmp_path / "project")
    vault = make_vault(tmp_path / "vault")
    project_tow = project / ".tow"
    project_tow.mkdir()
    (project_tow / "tags.md").write_text("keep this manual\n", encoding="utf-8")

    with pytest.raises(tow.ConfigError, match="already exists"):
        tow_project.cmd_project_init(project, vault, {}, "shared", [], True)

    assert (project_tow / "tags.md").read_text(encoding="utf-8") == "keep this manual\n"
    assert not (project_tow / "config.json").exists()
    assert not (project_tow / "documents.json").exists()


def test_project_init_skips_missing_vault_tags_manual(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = init_repo(tmp_path / "project")
    vault = tmp_path / "vault"
    vault.mkdir()

    assert tow_project.cmd_project_init(project, vault, {}, "shared", [], True) == 0

    assert "vault has no .tow/tags.md (run tow migrate)" in capsys.readouterr().out
    assert (project / ".tow" / "config.json").is_file()
    assert (project / ".tow" / "documents.json").read_text(encoding="utf-8") == "{\n}\n"
    assert (project / ".tow" / "tag-dictionary.json").read_text(encoding="utf-8") == "{\n}\n"
    assert not (project / ".tow" / "tags.md").exists()


def test_project_init_outside_git_reports_no_exclude_change(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = tmp_path / "project"
    project.mkdir()
    vault = make_vault(tmp_path / "vault")

    assert tow_project.cmd_project_init(project, vault, {}, "local", [], True) == 0

    assert "not in a Git repository" in capsys.readouterr().out
    assert tow_project.project_mode(project) == "none"


def test_project_mode_reports_none_outside_git(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    assert tow_project.project_mode(project) == "none"
