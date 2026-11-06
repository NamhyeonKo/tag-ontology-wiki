import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Literal, cast

import pytest
from conftest import fake_cli

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


@pytest.mark.parametrize("legacy", [False, True], ids=["tow-vault", "legacy-vault"])
def test_project_init_refuses_to_register_a_vault_as_a_project(
    tmp_path: Path, legacy: bool, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "vault"
    project.mkdir()
    if legacy:
        (project / "tow.json").write_text("{}\n", encoding="utf-8")
    else:
        (project / ".tow").mkdir()
        (project / ".tow" / "config.json").write_text('{"kind": "vault"}\n', encoding="utf-8")
    vault = make_vault(tmp_path / "connected-vault")
    monkeypatch.chdir(project)

    assert tow.main(["--root", str(vault), "project", "init", "--mode", "shared"]) == 2

    assert "project root is a vault" in capsys.readouterr().err
    assert not (project / ".tow" / "documents.json").exists()


def test_project_init_refuses_to_register_home_as_a_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    vault = make_vault(tmp_path / "vault")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(home)

    assert tow.main(["--root", str(vault), "project", "init", "--mode", "shared"]) == 2

    assert "project root must not be the home directory" in capsys.readouterr().err
    assert not (home / ".tow").exists()


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


def test_exclude_target_fails_closed_for_project_outside_git_toplevel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    def git_root(_project: Path) -> Path:
        return repository

    def git_exclude(_cwd: Path, *_args: str) -> str:
        return "info/exclude"

    monkeypatch.setattr(tow_project, "_git_root", git_root)
    monkeypatch.setattr(tow_project, "git", git_exclude)

    with pytest.raises(tow.ConfigError, match="outside its Git repository"):
        tow_project.exclude_target(outside)


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
    real_git_run = tow_project.git.__globals__["_git_run"]

    def fail_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
        if "ls-files" in args:
            return subprocess.CompletedProcess(args, 128, "", "simulated Git failure")
        return real_git_run(cwd, *args)

    monkeypatch.setattr(tow_project, "_git_run", fail_git)

    with pytest.raises(tow.ConfigError, match="Git failed while determining project file status"):
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


@pytest.mark.parametrize("mode", ["local", "shared"])
def test_project_init_refuses_when_git_check_ignore_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: Literal["local", "shared"]
) -> None:
    project = init_repo(tmp_path / "project")
    vault = make_vault(tmp_path / "vault")
    real_git_run = tow_project.git.__globals__["_git_run"]

    def fail_check_ignore(cwd: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
        if "check-ignore" in args:
            return subprocess.CompletedProcess(args, 128, "", "simulated Git failure")
        return real_git_run(cwd, *args)

    monkeypatch.setattr(tow_project, "_git_run", fail_check_ignore)

    with pytest.raises(tow.ConfigError, match="Git failed while checking project metadata ignores"):
        tow_project.cmd_project_init(project, vault, {}, mode, [], True)


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


def test_project_files_lists_every_document_as_untracked_outside_git(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".tow").mkdir(parents=True)
    (project / ".tow" / "config.json").write_text('{"kind": "project"}\n', encoding="utf-8")
    (project / "note.md").write_text("note\n", encoding="utf-8")
    (project / "private.md").write_text("private\n", encoding="utf-8")
    (project / ".gitignore").write_text("private.md\n", encoding="utf-8")

    assert tow_project.project_files(project) == [("untracked", "note.md"), ("untracked", "private.md")]


def test_project_commands_fail_closed_when_git_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    (project / "note.md").write_text("note\n", encoding="utf-8")
    changes = write_changes(tmp_path, {"note.md": ["used"]})
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", "")

    assert tow.main(["--root", str(vault), "project", "tag", str(changes)]) == 2
    assert "Git" in capsys.readouterr().err
    assert tow.main(["project", "files"]) == 2
    assert "Git" in capsys.readouterr().err


def test_project_init_fails_closed_when_git_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = init_repo(tmp_path / "project")
    vault = make_vault(tmp_path / "vault")
    monkeypatch.chdir(project)
    monkeypatch.setenv("PATH", "")

    assert tow.main(["--root", str(vault), "project", "init", "--mode", "shared", "--apply"]) == 2

    assert "Git failed" in capsys.readouterr().err
    assert not (project / ".tow").exists()


# project tag

VAULT_TAGS: dict[str, dict[str, Any]] = {
    "other": {"description": "Other", "aliases": [], "broader": []},
    "parent": {"description": "Parent", "aliases": [], "broader": []},
    "root": {"description": "Root", "aliases": [], "broader": []},
    "used": {"description": "Used", "aliases": ["in-use"], "broader": ["parent"]},
}
TAG_CFG = {"tagDictionary": ".tow/tag-dictionary.json"}


def envelope(command: str, **fields: Any) -> str:
    return json.dumps({"schemaVersion": 1, "command": command, "ok": True, "issues": [], **fields})


def tag_setup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    subset: dict[str, Any] | None = None,
    check: str | None = None,
    mode: Literal["local", "shared"] = "shared",
) -> tuple[Path, Path]:
    """A project in `mode` and a vault holding VAULT_TAGS; the fake CLI answers `subset` with `subset`."""
    vault = make_vault(tmp_path / "vault")
    (vault / ".tow" / "config.json").write_text('{"kind": "vault"}\n', encoding="utf-8")
    (vault / ".tow" / "tag-dictionary.json").write_text(json.dumps(VAULT_TAGS), encoding="utf-8")
    project = init_repo(tmp_path / "project")
    assert tow_project.cmd_project_init(project, vault, TAG_CFG, mode, [], True) == 0
    outputs = {"subset": envelope("subset", dictionary=VAULT_TAGS if subset is None else subset)}
    outputs["check"] = check or envelope("check")
    fake_cli(tmp_path, monkeypatch, {}, outputs)
    return project, vault


def write_changes(
    tmp_path: Path, documents: dict[str, list[str]], concepts: dict[str, dict[str, Any]] | None = None
) -> Path:
    changes = tmp_path / "changes.json"
    changes.write_text(json.dumps({"documents": documents, "concepts": concepts or {}}), encoding="utf-8")
    return changes


def project_tag(project: Path, vault: Path, changes: Path, apply: bool = True) -> int:
    return tow_project.cmd_project_tag(project, vault, TAG_CFG, changes, apply)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_project_tag_writes_tracked_entries_to_documents_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    subset = {key: VAULT_TAGS[key] for key in ("parent", "used")}
    project, vault = tag_setup(tmp_path, monkeypatch, subset)
    document = project / "proposal.md"
    document.write_bytes(b"# Proposal\r\n\r\nText.\r\n")
    git(project, "add", "proposal.md")
    changes = write_changes(tmp_path, {"proposal.md": ["used"]})
    monkeypatch.chdir(project)
    before = snapshot(project)
    capsys.readouterr()

    assert tow.main(["--root", str(vault), "project", "tag", str(changes)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "would add proposal.md to .tow/documents.json",
        "would add parent to .tow/tag-dictionary.json",
        "would add used to .tow/tag-dictionary.json",
    ]
    assert snapshot(project) == before

    assert tow.main(["--root", str(vault), "project", "tag", str(changes), "--apply"]) == 0
    assert capsys.readouterr().out.splitlines() == ["updated .tow/tag-dictionary.json", "updated .tow/documents.json"]
    bundle = project / ".tow"
    assert read_json(bundle / "documents.json") == {"proposal.md": {"tags": ["used"], "sha256": sha256(document)}}
    assert (bundle / "documents.json").read_text(encoding="utf-8").count("\n") == 3
    assert read_json(bundle / "tag-dictionary.json") == subset
    assert not (bundle / "documents.local.json").exists()

    assert tow.main(["--root", str(vault), "project", "tag", str(changes), "--apply"]) == 0
    assert capsys.readouterr().out.splitlines() == ["no changes"]


def test_project_tag_routes_untracked_files_to_the_local_file_in_shared_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch, {key: VAULT_TAGS[key] for key in ("parent", "used")})
    for name in ("tracked.md", "draft.md", "private.md"):
        (project / name).write_text(f"{name}\n", encoding="utf-8")
    (project / ".gitignore").write_text("private.md\n", encoding="utf-8")
    git(project, "add", "tracked.md")
    bundle = project / ".tow"
    stale = {"tags": ["used"], "sha256": "0"}
    (bundle / "documents.json").write_text(json.dumps({"draft.md": stale, "gone.md": stale}), encoding="utf-8")
    documents = {"tracked.md": ["used"], "draft.md": ["used"], "private.md": ["parent"], "gone.md": []}

    assert project_tag(project, vault, write_changes(tmp_path, documents)) == 0

    assert read_json(bundle / "documents.json") == {
        "tracked.md": {"tags": ["used"], "sha256": sha256(project / "tracked.md")}
    }
    assert read_json(bundle / "documents.local.json") == {
        "draft.md": {"tags": ["used"], "sha256": sha256(project / "draft.md")},
        "private.md": {"tags": ["parent"], "sha256": sha256(project / "private.md")},
    }
    assert git(project, "check-ignore", ".tow/documents.local.json") == ".tow/documents.local.json"


def test_project_tag_refuses_a_local_file_that_git_does_not_ignore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    exclude = git_path(project, "rev-parse", "--git-path", "info/exclude")
    exclude.write_text("", encoding="utf-8")  # a fresh clone of a shared project has no exclude entry
    (project / "draft.md").write_text("draft\n", encoding="utf-8")
    before = snapshot(project)

    with pytest.raises(tow.ConfigError, match="not ignored by Git"):
        project_tag(project, vault, write_changes(tmp_path, {"draft.md": ["used"]}))

    assert snapshot(project) == before


def test_project_tag_keeps_project_only_concepts_across_a_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    subset = {key: VAULT_TAGS[key] for key in ("parent", "used")}
    project, vault = tag_setup(tmp_path, monkeypatch, subset)
    (project / "note.md").write_text("note\n", encoding="utf-8")
    git(project, "add", "note.md")
    project_only = {"description": "Project concept", "aliases": ["po"], "broader": ["parent"], "facet": "x"}
    old: dict[str, Any] = {
        "project-only": project_only,
        "used": {"description": "Stale copy", "broader": []},
        "other": VAULT_TAGS["other"],
    }
    (project / ".tow" / "tag-dictionary.json").write_text(json.dumps(old, indent=2), encoding="utf-8")
    capsys.readouterr()

    assert project_tag(project, vault, write_changes(tmp_path, {"note.md": ["used"]}), apply=False) == 0
    assert capsys.readouterr().out.splitlines() == [
        "would add note.md to .tow/documents.json",
        "would remove other from .tow/tag-dictionary.json",
        "would add parent to .tow/tag-dictionary.json",
        "would update used in .tow/tag-dictionary.json",
    ]
    assert project_tag(project, vault, write_changes(tmp_path, {"note.md": ["used"]})) == 0

    assert read_json(project / ".tow" / "tag-dictionary.json") == {**subset, "project-only": project_only}


def test_project_tag_asks_subset_for_vault_tags_and_project_broader_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    (project / "note.md").write_text("note\n", encoding="utf-8")
    git(project, "add", "note.md")
    bundle = project / ".tow"
    (bundle / "tag-dictionary.json").write_text(
        json.dumps({"project-only": {"description": "P", "broader": ["root"]}}), encoding="utf-8"
    )
    (bundle / "documents.json").write_text(
        json.dumps({"old.md": {"tags": ["other", "project-only"], "sha256": "0"}}), encoding="utf-8"
    )
    concept = {"description": "New", "broader": ["parent", "project-only"]}
    changes = write_changes(tmp_path, {"note.md": ["used", "new-concept"]}, {"new-concept": concept})

    assert project_tag(project, vault, changes) == 0

    subset_call, check_call = read_json(tmp_path / "calls.json")
    assert subset_call == [
        "subset", "other", "parent", "root", "used",
        "--root", str(vault), "--dictionary", ".tow/tag-dictionary.json", "--names", "kebab", "--json",
    ]  # fmt: skip
    assert check_call[:3] == ["check", "--root", str(project)]
    assert check_call[3] == "--dictionary" and check_call[5:] == ["--json"]
    assert Path(check_call[4]).is_absolute() and not Path(check_call[4]).exists()
    assert read_json(bundle / "tag-dictionary.json") == {
        **VAULT_TAGS,
        "project-only": {"description": "P", "broader": ["root"]},
        "new-concept": concept,
    }


@pytest.mark.parametrize(
    ("documents", "concepts", "message"),
    [
        ({"note.md": ["missing"]}, {}, "unknown tag 'missing'"),
        ({"../outside.md": ["used"]}, {}, "inside the project"),
        ({"link.md": ["used"]}, {}, "inside the project"),
        ({"./note.md": ["used"]}, {}, "inside the project"),
        ({"notes.txt": ["used"]}, {}, r"\.md"),
        ({"absent.md": ["used"]}, {}, "not found"),
        ({"Note.md": ["used"]}, {}, "exact path and case"),
        ({"note.md": ["used"]}, {"used": {"description": "Mine", "broader": []}}, "already in the vault"),
        ({"note.md": ["used"]}, {"In-Use": {"description": "Alias", "broader": []}}, "already in the vault"),
        ({"note.md": "used"}, {}, "changes file"),
    ],
)
def test_project_tag_rejects_unknown_tags_and_paths_outside_the_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    documents: dict[str, list[str]],
    concepts: dict[str, dict[str, Any]],
    message: str,
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    (project / "note.md").write_text("note\n", encoding="utf-8")
    (project / "notes.txt").write_text("text\n", encoding="utf-8")
    (tmp_path / "outside.md").write_text("outside\n", encoding="utf-8")
    (project / "link.md").symlink_to(tmp_path / "outside.md")
    before = snapshot(project)

    with pytest.raises(tow.ConfigError, match=message):
        project_tag(project, vault, write_changes(tmp_path, documents, concepts))

    assert snapshot(project) == before
    assert not (tmp_path / "calls.json").exists()


def test_project_tag_validates_the_new_dictionary_before_replacing_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    issue = {"code": "unknown-reference", "severity": "error", "message": "new-concept.broader: unknown tag nowhere"}
    check = json.dumps({"schemaVersion": 1, "command": "check", "ok": False, "issues": [issue]})
    project, vault = tag_setup(tmp_path, monkeypatch, {}, check)
    (project / "note.md").write_text("note\n", encoding="utf-8")
    git(project, "add", "note.md")
    changes = write_changes(
        tmp_path, {"note.md": ["new-concept"]}, {"new-concept": {"description": "N", "broader": ["nowhere"]}}
    )
    before = snapshot(project)

    with pytest.raises(tow.ConfigError, match="unknown tag nowhere"):
        project_tag(project, vault, changes)

    assert snapshot(project) == before


def test_project_tag_never_edits_project_documents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch, {key: VAULT_TAGS[key] for key in ("parent", "used")})
    (project / "note.md").write_bytes(b"\xef\xbb\xbf---\r\ntags: [old]\r\n---\r\n# Before\r\nContent")
    (project / "docs").mkdir()
    (project / "docs" / "plain.md").write_bytes(b"No frontmatter, no newline")
    git(project, "add", "note.md", "docs/plain.md")
    documents_before = {path: path.read_bytes() for path in project.rglob("*.md")}
    vault_before = snapshot(vault)
    changes = write_changes(tmp_path, {"note.md": ["used"], "docs/plain.md": ["parent"]})

    assert project_tag(project, vault, changes) == 0

    assert {path: path.read_bytes() for path in project.rglob("*.md")} == documents_before
    assert snapshot(vault) == vault_before
    assert set(read_json(project / ".tow" / "documents.json")) == {"docs/plain.md", "note.md"}


def test_project_tag_keeps_tags_of_local_files_out_of_the_shared_dictionary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    subset = {key: VAULT_TAGS[key] for key in ("parent", "root", "used")}
    project, vault = tag_setup(tmp_path, monkeypatch, subset)
    for name in ("tracked.md", "draft.md"):
        (project / name).write_text(f"{name}\n", encoding="utf-8")
    git(project, "add", "tracked.md")
    chain = {
        "po-child": {"description": "Child", "broader": ["po-root"]},
        "po-root": {"description": "Root", "broader": ["root"]},
    }
    others: dict[str, Any] = {
        "po-local": {"description": "Local only", "broader": []},
        "po-unused": {"description": "Unused", "broader": ["parent"]},
    }
    (project / ".tow" / "tag-dictionary.json").write_text(json.dumps({**chain, **others}), encoding="utf-8")
    documents = {"tracked.md": ["used", "po-child"], "draft.md": ["used", "other", "po-local"]}

    assert project_tag(project, vault, write_changes(tmp_path, documents)) == 0

    assert read_json(tmp_path / "calls.json")[0][:5] == ["subset", "parent", "root", "used", "--root"]
    assert read_json(project / ".tow" / "tag-dictionary.json") == {**subset, **chain, **others}
    assert read_json(project / ".tow" / "documents.local.json")["draft.md"]["tags"] == ["used", "other", "po-local"]


def test_project_tag_refuses_a_new_concept_used_only_by_local_files_in_shared_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch, {})
    (project / "draft.md").write_text("draft\n", encoding="utf-8")
    changes = write_changes(tmp_path, {"draft.md": ["new-local"]}, {"new-local": {"description": "N", "broader": []}})
    before = snapshot(project)

    with pytest.raises(tow.ConfigError, match="tag a tracked document with it, or register it in the vault"):
        project_tag(project, vault, changes)

    assert snapshot(project) == before


def test_project_tag_accepts_a_new_concept_on_untracked_files_in_local_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch, {}, mode="local")
    (project / "draft.md").write_text("draft\n", encoding="utf-8")
    concept: dict[str, Any] = {"description": "N", "broader": []}

    assert (
        project_tag(project, vault, write_changes(tmp_path, {"draft.md": ["new-local"]}, {"new-local": concept})) == 0
    )

    assert read_json(project / ".tow" / "tag-dictionary.json") == {"new-local": concept}
    assert set(read_json(project / ".tow" / "documents.json")) == {"draft.md"}
    assert not (project / ".tow" / "documents.local.json").exists()


@pytest.mark.parametrize("tracked", [False, True], ids=["to-local", "to-shared"])
def test_project_tag_writes_a_moved_entry_to_its_new_file_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tracked: bool
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch, {key: VAULT_TAGS[key] for key in ("parent", "used")})
    (project / "draft.md").write_text("draft\n", encoding="utf-8")
    if tracked:
        git(project, "add", "draft.md")
    source = project / ".tow" / ("documents.local.json" if tracked else "documents.json")
    source.write_text(json.dumps({"draft.md": {"tags": ["used"], "sha256": "0"}}), encoding="utf-8")
    real_write = tow_project.write_text_atomic
    document_writes: list[str] = []

    def fail_second_documents_write(path: Path, text: str, *, exclusive: bool = False) -> None:
        if path.name.startswith("documents"):
            document_writes.append(path.name)
            if len(document_writes) == 2:
                raise OSError("disk full")
        real_write(path, text, exclusive=exclusive)

    monkeypatch.setattr(tow_project, "write_text_atomic", fail_second_documents_write)

    with pytest.raises(OSError, match="disk full"):
        project_tag(project, vault, write_changes(tmp_path, {"draft.md": ["used"]}))

    files = [project / ".tow" / name for name in ("documents.json", "documents.local.json")]
    assert any("draft.md" in read_json(path) for path in files if path.exists())


def test_project_status_reports_untracked_documents_json_entries_as_local_in_shared_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch, mode="shared")
    capsys.readouterr()
    note = project / "leftover.md"
    note.write_text("leftover\n", encoding="utf-8")
    (project / ".tow" / "documents.json").write_text(
        json.dumps({"leftover.md": {"tags": ["used"], "sha256": sha256(note)}}), encoding="utf-8"
    )
    (project / ".tow" / "documents.local.json").write_text("{}\n", encoding="utf-8")

    assert tow_project.cmd_project_status(project, vault, TAG_CFG) == 0

    assert capsys.readouterr().out.splitlines() == ["local-entry-in-shared leftover.md"]


def test_project_status_does_not_mark_missing_shared_files_as_local_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch, mode="shared")
    (project / ".tow" / "documents.json").write_text(
        json.dumps({"missing.md": {"tags": ["used"], "sha256": "bad"}}), encoding="utf-8"
    )
    capsys.readouterr()

    assert tow_project.cmd_project_status(project, vault, TAG_CFG) == 0

    assert capsys.readouterr().out.splitlines() == ["missing missing.md"]


def test_project_status_reports_stale_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, _ = tag_setup(tmp_path, monkeypatch)
    document = project / "note.md"
    document.write_text("before\n", encoding="utf-8")
    git(project, "add", "note.md")
    (project / ".tow" / "documents.json").write_text(
        json.dumps({"note.md": {"tags": ["used"], "sha256": sha256(document)}}), encoding="utf-8"
    )
    (project / ".tow" / "tag-dictionary.json").write_text(json.dumps({"used": VAULT_TAGS["used"]}), encoding="utf-8")
    document.write_text("after\n", encoding="utf-8")
    capsys.readouterr()

    assert tow_project.cmd_project_status(project, tmp_path / "vault", TAG_CFG) == 0

    assert capsys.readouterr().out.splitlines() == ["stale note.md"]


def test_project_status_suggests_a_renamed_file_by_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    document = project / "renamed.md"
    document.write_bytes(b"identical bytes\n")
    (project / ".tow" / "documents.json").write_text(
        json.dumps({"old.md": {"tags": ["used"], "sha256": sha256(document)}}), encoding="utf-8"
    )
    (project / ".tow" / "tag-dictionary.json").write_text(json.dumps({"used": VAULT_TAGS["used"]}), encoding="utf-8")
    capsys.readouterr()

    assert tow_project.cmd_project_status(project, vault, TAG_CFG) == 0

    assert capsys.readouterr().out.splitlines() == ["missing old.md", "  moved? renamed.md"]


def test_project_status_reports_tags_missing_from_the_project_dictionary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    document = project / "note.md"
    document.write_text("note\n", encoding="utf-8")
    entry = {"tags": ["vault-known", "missing"], "sha256": sha256(document)}
    (project / ".tow" / "documents.json").write_text(json.dumps({"note.md": entry}), encoding="utf-8")
    (project / ".tow" / "tag-dictionary.json").write_text("{}\n", encoding="utf-8")
    (vault / ".tow" / "tag-dictionary.json").write_text(
        json.dumps({"vault-known": VAULT_TAGS["used"]}), encoding="utf-8"
    )
    capsys.readouterr()

    assert tow_project.cmd_project_status(project, vault, TAG_CFG) == 0

    assert capsys.readouterr().out.splitlines() == [
        "local-entry-in-shared note.md",
        "unknown-tag note.md missing",
    ]


def test_project_status_is_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    (project / "note.md").write_text("note\n", encoding="utf-8")
    before = snapshot(project)
    vault_before = snapshot(vault)
    capsys.readouterr()

    assert tow_project.cmd_project_status(project, vault, TAG_CFG) == 0

    assert snapshot(project) == before
    assert snapshot(vault) == vault_before
    assert capsys.readouterr().out.splitlines() == ["OK"]


def test_project_files_lists_tracked_untracked_and_ignored_names(
    tmp_path: Path,
) -> None:
    project = init_repo(tmp_path / "project")
    for name in ("tracked.md", "draft.md", "private.md"):
        (project / name).write_text(f"{name}\n", encoding="utf-8")
    (project / ".gitignore").write_text("private.md\n", encoding="utf-8")
    git(project, "add", "tracked.md", ".gitignore")
    (project / ".tow").mkdir()
    (project / ".tow" / "config.json").write_text('{"kind": "project"}\n', encoding="utf-8")

    assert tow_project.project_files(project) == [
        ("tracked", "tracked.md"),
        ("untracked", "draft.md"),
        ("ignored", "private.md"),
    ]


def test_project_files_preserves_non_ascii_names_for_each_git_status(tmp_path: Path) -> None:
    project = init_repo(tmp_path / "project")
    names = {
        "tracked": "docs/설계 노트.md",
        "untracked": "drafts/미완성 노트.md",
        "ignored": "private/비공개 노트.md",
    }
    for name in names.values():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content\n", encoding="utf-8")
    (project / ".gitignore").write_text("private/\n", encoding="utf-8")
    git(project, "add", names["tracked"], ".gitignore")
    (project / ".tow").mkdir()
    (project / ".tow" / "config.json").write_text('{"kind": "project"}\n', encoding="utf-8")

    assert tow_project.project_files(project) == [
        ("tracked", names["tracked"]),
        ("untracked", names["untracked"]),
        ("ignored", names["ignored"]),
    ]


def test_project_files_reports_status_relative_to_nested_project_root(tmp_path: Path) -> None:
    repository = init_repo(tmp_path / "repository")
    project = repository / "work" / "nested"
    project.mkdir(parents=True)
    names = {"tracked": "tracked.md", "untracked": "draft.md", "ignored": "private.md"}
    for name in names.values():
        (project / name).write_text(f"{name}\n", encoding="utf-8")
    (project / ".gitignore").write_text("private.md\n", encoding="utf-8")
    git(repository, "add", "work/nested/tracked.md", "work/nested/.gitignore")
    (project / ".tow").mkdir()
    (project / ".tow" / "config.json").write_text('{"kind": "project"}\n', encoding="utf-8")

    assert tow_project.project_files(project) == [
        ("tracked", names["tracked"]),
        ("untracked", names["untracked"]),
        ("ignored", names["ignored"]),
    ]


def test_project_files_applies_docs_and_exclude(tmp_path: Path) -> None:
    project = init_repo(tmp_path / "project")
    for name in ("docs/keep.md", "docs/vendor/drop.md", "other.md", ".hidden/secret.md"):
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content\n", encoding="utf-8")
    (project / ".tow").mkdir()
    (project / ".tow" / "config.json").write_text(
        json.dumps({"kind": "project", "docs": ["docs"], "exclude": ["**/vendor"]}) + "\n", encoding="utf-8"
    )

    assert tow_project.project_files(project) == [("untracked", "docs/keep.md")]


def test_project_files_cli_lists_document_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = init_repo(tmp_path / "project")
    (project / "note.md").write_text("note\n", encoding="utf-8")
    (project / ".tow").mkdir()
    (project / ".tow" / "config.json").write_text('{"kind": "project"}\n', encoding="utf-8")
    vault = make_vault(tmp_path / "vault")
    monkeypatch.chdir(project)

    assert tow.main(["--root", str(vault), "project", "files"]) == 0
    assert capsys.readouterr().out.splitlines() == ["untracked note.md"]


def test_project_files_lists_names_without_reading_markdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = init_repo(tmp_path / "project")
    document = project / "note.md"
    document.write_text("must not be read", encoding="utf-8")
    (project / ".tow").mkdir()
    (project / ".tow" / "config.json").write_text('{"kind": "project"}\n', encoding="utf-8")
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text

    def reject_markdown_reads(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".md":
            raise AssertionError(f"read Markdown contents: {path}")
        return original_read_bytes(path, *args, **kwargs)

    def reject_markdown_text_reads(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".md":
            raise AssertionError(f"read Markdown contents: {path}")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", reject_markdown_reads)
    monkeypatch.setattr(Path, "read_text", reject_markdown_text_reads)

    assert tow_project.project_files(project) == [("untracked", "note.md")]


def test_project_concepts_cli_emits_import_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    (project / ".tow").mkdir(parents=True)
    (project / ".tow" / "config.json").write_text('{"kind": "project"}\n', encoding="utf-8")
    (project / ".tow" / "tag-dictionary.json").write_text("{}\n", encoding="utf-8")
    vault = make_vault(tmp_path / "vault")
    (vault / ".tow" / "config.json").write_text('{"kind": "vault"}\n', encoding="utf-8")
    (vault / ".tow" / "tag-dictionary.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.chdir(vault)

    assert tow.main(["--root", str(vault), "project", "concepts", str(project)]) == 0
    assert json.loads(capsys.readouterr().out) == {"changes": []}


def test_project_concepts_emits_additions_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    (project / ".tow").mkdir(parents=True)
    (project / ".tow" / "config.json").write_text('{"kind": "project"}\n', encoding="utf-8")
    vault = make_vault(tmp_path / "vault")
    monkeypatch.chdir(vault)
    vault_entry = {
        "description": "Vault concept",
        "aliases": ["v"],
        "broader": [],
        "related": ["project-only"],
    }
    project_entry = {
        "description": "Vault concept",
        "aliases": ["v"],
        "broader": [],
    }  # project subset prunes the vault's related link
    project_only = {"description": "Project concept", "aliases": ["pc"], "broader": ["vault-tag"]}
    project_child = {"description": "Project child", "broader": ["project-only"], "related": []}
    (vault / ".tow" / "tag-dictionary.json").write_text(json.dumps({"vault-tag": vault_entry}), encoding="utf-8")
    (project / ".tow" / "tag-dictionary.json").write_text(
        json.dumps({"vault-tag": project_entry, "project-only": project_only, "project-child": project_child}),
        encoding="utf-8",
    )

    before = snapshot(project)
    vault_before = snapshot(vault)

    assert tow_project.cmd_project_concepts(project, vault, TAG_CFG) == 0

    assert snapshot(project) == before
    assert snapshot(vault) == vault_before
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "changes": [
            {
                "kind": "add",
                "draft": {
                    "name": "project-child",
                    "description": "Project child",
                    "aliases": [],
                    "parents": ["project-only"],
                    "children": [],
                    "related": [],
                },
            },
            {
                "kind": "add",
                "draft": {
                    "name": "project-only",
                    "description": "Project concept",
                    "aliases": ["pc"],
                    "parents": ["vault-tag"],
                    "children": [],
                    "related": [],
                },
            },
        ]
    }


def fake_lookup_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    responses: dict[str, dict[str, Any]],
) -> Path:
    responses_path = tmp_path / "lookup-responses.json"
    responses_path.write_text(json.dumps(responses), encoding="utf-8")
    script = tmp_path / "fake_lookup_cli.py"
    script.write_text(
        "import json, pathlib, sys\n"
        f"directory = pathlib.Path({str(tmp_path)!r})\n"
        "args = sys.argv[1:]\n"
        "root = args[args.index('--root') + 1]\n"
        "record = {'args': args}\n"
        "if '--dictionary' in args:\n"
        "    dictionary = pathlib.Path(args[args.index('--dictionary') + 1])\n"
        "    if not dictionary.is_absolute(): dictionary = pathlib.Path(root) / dictionary\n"
        "    record['dictionary'] = json.loads(dictionary.read_text())\n"
        "record['tags_files'] = [args[i + 1] for i, value in enumerate(args[:-1]) if value == '--tags-file']\n"
        "calls = directory / 'lookup-calls.json'\n"
        "calls.write_text(json.dumps([*(json.loads(calls.read_text()) if calls.exists() else []), record]))\n"
        "response = json.loads((directory / 'lookup-responses.json').read_text())[root]\n"
        "if 'stderr' in response:\n"
        "    sys.stderr.write(response['stderr'])\n"
        "    sys.exit(response['code'])\n"
        "print(json.dumps(response['json']))\n"
        "sys.exit(response.get('code', 0))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TOW_TAG_ONTOLOGY", f"{tow.sys.executable} {script}")
    return tmp_path / "lookup-calls.json"


def lookup_response(tag: str, *notes: dict[str, Any]) -> dict[str, Any]:
    return {"code": 0, "json": {"ok": True, "tag": tag, "noteMatches": list(notes)}}


def lookup_note(path: str, *matches: tuple[str, str]) -> dict[str, Any]:
    return {"path": path, "matches": [{"tag": tag, "source": source} for tag, source in matches]}


@pytest.mark.parametrize(
    ("broken", "contents"),
    [("config", "{"), ("dictionary", "[")],
)
def test_lookup_reports_malformed_project_data_but_keeps_vault_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    broken: str,
    contents: str,
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    (vault / ".tow" / "tag-dictionary.json").write_text(json.dumps(VAULT_TAGS), encoding="utf-8")
    (project / ".tow" / ("config.json" if broken == "config" else "tag-dictionary.json")).write_text(
        contents, encoding="utf-8"
    )
    calls_path = fake_lookup_cli(
        tmp_path,
        monkeypatch,
        {str(vault): lookup_response("used", lookup_note("vault.md", ("used", "tags")))},
    )
    monkeypatch.chdir(project)
    capsys.readouterr()

    assert tow.main(["--root", str(vault), "lookup", "used"]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["results"] == [
        {"source": "vault", "path": "vault.md", "matches": [{"tag": "used", "source": "tags", "kind": "exact"}]}
    ]
    assert result["unavailable"] and result["unavailable"][0].startswith("project: ")
    assert len(read_json(calls_path)) == 1


def test_lookup_merges_vault_then_project_results_sorted_by_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    project_entry = {"description": "Project override", "aliases": ["local-used"], "broader": []}
    project_dictionary: dict[str, Any] = {
        "used": project_entry,
        "project-only": {"description": "Only here", "broader": []},
    }
    vault_entry = {**VAULT_TAGS["used"], "broader": ["root"]}
    current_vault_dictionary = {**VAULT_TAGS, "used": vault_entry}
    (vault / ".tow" / "tag-dictionary.json").write_text(json.dumps(current_vault_dictionary), encoding="utf-8")
    (project / ".tow" / "tag-dictionary.json").write_text(json.dumps(project_dictionary), encoding="utf-8")
    (project / ".tow" / "config.json").write_text(
        json.dumps({"kind": "project", "docs": ["docs"], "exclude": ["docs/private"]}), encoding="utf-8"
    )
    (project / ".tow" / "documents.json").write_text("{}\n", encoding="utf-8")
    (project / "docs").mkdir()
    responses = {
        str(vault): lookup_response(
            "used", lookup_note("z-vault.md", ("used", "tags")), lookup_note("a-vault.md", ("used", "bodyTags"))
        ),
        str(project): lookup_response(
            "used",
            lookup_note("docs/z.md", ("used", "overlay")),
            lookup_note("docs/private/drop.md", ("used", "tags")),
            lookup_note("outside.md", ("used", "tags")),
            lookup_note("docs/a.md", ("used", "tags")),
        ),
    }
    calls_path = fake_lookup_cli(tmp_path, monkeypatch, responses)
    monkeypatch.chdir(project)
    capsys.readouterr()
    before_project, before_vault = snapshot(project), snapshot(vault)

    assert tow.main(["--root", str(vault), "lookup", "used"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "tag": "used",
        "results": [
            {
                "source": "vault",
                "path": "a-vault.md",
                "matches": [{"tag": "used", "source": "bodyTags", "kind": "exact"}],
            },
            {"source": "vault", "path": "z-vault.md", "matches": [{"tag": "used", "source": "tags", "kind": "exact"}]},
            {"source": "project", "path": "docs/a.md", "matches": [{"tag": "used", "source": "tags", "kind": "exact"}]},
            {
                "source": "project",
                "path": "docs/z.md",
                "matches": [{"tag": "used", "source": "overlay", "kind": "exact"}],
            },
        ],
        "unavailable": [],
    }
    calls = read_json(calls_path)
    project_call = next(call for call in calls if call["args"][call["args"].index("--root") + 1] == str(project))
    assert project_call["dictionary"] == {**project_dictionary, **current_vault_dictionary}
    assert project_call["tags_files"] == [str(project / ".tow" / "documents.json")]
    assert "--exclude" in project_call["args"] and "docs/private" in project_call["args"]
    assert snapshot(project) == before_project
    assert snapshot(vault) == before_vault


def test_lookup_marks_exact_and_narrower_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, vault = tag_setup(tmp_path, monkeypatch)
    responses = {
        str(vault): lookup_response(
            "used",
            lookup_note("note.md", ("child", "bodyTags"), ("used", "tags")),
        )
    }
    calls_path = fake_lookup_cli(tmp_path, monkeypatch, responses)
    monkeypatch.chdir(vault)
    capsys.readouterr()

    assert tow.main(["--root", str(vault), "lookup", "IN-USE"]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["results"] == [
        {
            "source": "vault",
            "path": "note.md",
            "matches": [
                {"tag": "child", "source": "bodyTags", "kind": "narrower"},
                {"tag": "used", "source": "tags", "kind": "exact"},
            ],
        }
    ]
    assert "--exact" not in read_json(calls_path)[0]["args"]


def test_lookup_exact_option_is_passed_to_each_known_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    responses = {
        str(vault): lookup_response("used", lookup_note("vault.md", ("used", "tags"))),
        str(project): lookup_response("used", lookup_note("project.md", ("used", "overlay"))),
    }
    calls_path = fake_lookup_cli(tmp_path, monkeypatch, responses)
    monkeypatch.chdir(project)
    capsys.readouterr()

    assert tow.main(["--root", str(vault), "lookup", "used", "--exact"]) == 0

    assert ["--exact" in call["args"] for call in read_json(calls_path)] == [True, True]


def test_lookup_inside_the_vault_returns_only_vault_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    responses = {str(vault): lookup_response("used", lookup_note("vault.md", ("used", "tags")))}
    calls_path = fake_lookup_cli(tmp_path, monkeypatch, responses)
    monkeypatch.chdir(vault)
    capsys.readouterr()

    assert tow.main(["--root", str(vault), "lookup", "used"]) == 0

    assert json.loads(capsys.readouterr().out)["results"] == [
        {"source": "vault", "path": "vault.md", "matches": [{"tag": "used", "source": "tags", "kind": "exact"}]}
    ]
    calls = read_json(calls_path)
    assert len(calls) == 1
    assert calls[0]["args"][calls[0]["args"].index("--root") + 1] == str(vault)
    assert project.is_dir()


def test_lookup_without_a_tow_project_returns_only_vault_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _, vault = tag_setup(tmp_path, monkeypatch)
    responses = {str(vault): lookup_response("used", lookup_note("vault.md", ("used", "tags")))}
    calls_path = fake_lookup_cli(tmp_path, monkeypatch, responses)
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    capsys.readouterr()

    assert tow.main(["--root", str(vault), "lookup", "used"]) == 0

    assert json.loads(capsys.readouterr().out)["results"] == [
        {"source": "vault", "path": "vault.md", "matches": [{"tag": "used", "source": "tags", "kind": "exact"}]}
    ]
    calls = read_json(calls_path)
    assert len(calls) == 1
    assert calls[0]["args"][calls[0]["args"].index("--root") + 1] == str(vault)


def test_lookup_treats_an_unknown_project_tag_as_no_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    calls_path = fake_lookup_cli(tmp_path, monkeypatch, {})
    monkeypatch.chdir(project)
    capsys.readouterr()

    assert tow.main(["--root", str(vault), "lookup", "not-registered"]) == 1

    assert json.loads(capsys.readouterr().out) == {
        "tag": "not-registered",
        "results": [],
        "unavailable": [],
    }
    assert not calls_path.exists()


def test_lookup_reports_an_unavailable_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    responses = {
        str(vault): {"code": 2, "stderr": "tag-ontology: ambiguous alias\n"},
        str(project): lookup_response("used", lookup_note("project.md", ("used", "overlay"))),
    }
    calls_path = fake_lookup_cli(tmp_path, monkeypatch, responses)
    monkeypatch.chdir(project)
    capsys.readouterr()

    assert tow.main(["--root", str(vault), "lookup", "used"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "tag": "used",
        "results": [
            {
                "source": "project",
                "path": "project.md",
                "matches": [{"tag": "used", "source": "overlay", "kind": "exact"}],
            }
        ],
        "unavailable": ["vault: tag-ontology: ambiguous alias"],
    }
    assert len(read_json(calls_path)) == 2


def test_lookup_finds_a_project_only_tag_without_querying_the_vault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, vault = tag_setup(tmp_path, monkeypatch)
    project_dictionary = {"project-only": {"description": "Only here", "aliases": ["po"], "broader": []}}
    (project / ".tow" / "tag-dictionary.json").write_text(json.dumps(project_dictionary), encoding="utf-8")
    responses = {str(project): lookup_response("project-only", lookup_note("only.md", ("project-only", "tags")))}
    calls_path = fake_lookup_cli(tmp_path, monkeypatch, responses)
    monkeypatch.chdir(project)
    capsys.readouterr()

    assert tow.main(["--root", str(vault), "lookup", "project-only"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "tag": "project-only",
        "results": [
            {
                "source": "project",
                "path": "only.md",
                "matches": [{"tag": "project-only", "source": "tags", "kind": "exact"}],
            }
        ],
        "unavailable": [],
    }
    calls = read_json(calls_path)
    assert len(calls) == 1
    assert calls[0]["args"][calls[0]["args"].index("--root") + 1] == str(project)
    assert calls[0]["dictionary"] == {**project_dictionary, **VAULT_TAGS}
