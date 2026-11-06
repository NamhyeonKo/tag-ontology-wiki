import errno
import json
import subprocess
from pathlib import Path

import pytest

import tow
import tow_core
from tow_core import (
    ConfigError,
    is_legacy_vault,
    read_user_config,
    resolve_project,
    resolve_vault,
    serialize_entries,
    tow_kind,
    upward,
    user_config_file,
)


def set_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("TOW_VAULT", raising=False)
    return home


def write_user_config(home: Path, vault: Path) -> None:
    config = home / ".tow" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"kind": "user", "vault": str(vault)}), encoding="utf-8")


def test_root_argument_wins_over_env_and_user_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = set_home(tmp_path, monkeypatch)
    root = tmp_path / "root"
    env_vault = tmp_path / "env"
    user_vault = tmp_path / "user"
    for path in (root, env_vault, user_vault):
        path.mkdir()
    write_user_config(home, user_vault)
    monkeypatch.setenv("TOW_VAULT", str(env_vault))

    assert resolve_vault(tmp_path, root, {"TOW_VAULT": str(env_vault)}).source == "--root"


def test_env_wins_over_user_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = set_home(tmp_path, monkeypatch)
    env_vault = tmp_path / "env"
    user_vault = tmp_path / "user"
    env_vault.mkdir()
    user_vault.mkdir()
    write_user_config(home, user_vault)

    resolved = resolve_vault(tmp_path, None, {"TOW_VAULT": str(env_vault)})

    assert resolved.root == env_vault
    assert resolved.source == "TOW_VAULT"


def test_nearest_vault_beats_environment_connection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    set_home(tmp_path, monkeypatch)
    current = tmp_path / "current"
    (current / ".tow").mkdir(parents=True)
    (current / ".tow/config.json").write_text('{"kind": "vault"}', encoding="utf-8")
    connected = tmp_path / "connected"
    (connected / ".tow").mkdir(parents=True)
    (connected / ".tow/config.json").write_text('{"kind": "vault"}', encoding="utf-8")

    resolved = resolve_vault(current, None, {"TOW_VAULT": str(connected)})

    assert (resolved.root, resolved.source) == (current, "ancestor")


def test_nearest_vault_beats_user_connection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = set_home(tmp_path, monkeypatch)
    current = tmp_path / "current"
    (current / ".tow").mkdir(parents=True)
    (current / ".tow/config.json").write_text('{"kind": "vault"}', encoding="utf-8")
    connected = tmp_path / "connected"
    connected.mkdir()
    write_user_config(home, connected)

    resolved = resolve_vault(current, None, {})

    assert (resolved.root, resolved.source) == (current, "ancestor")


def test_user_file_names_the_vault_with_spaces_and_korean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = set_home(tmp_path, monkeypatch)
    vault = tmp_path / "내 vault 2"
    project_dir = tmp_path / "project"
    vault.mkdir()
    project_dir.mkdir()
    write_user_config(home, vault)

    resolved = resolve_vault(project_dir, None, {})

    assert resolved.root == vault
    assert resolved.source == "user"
    assert user_config_file() == home / ".tow" / "config.json"
    assert read_user_config() == str(vault)


def test_ancestor_tow_vault_is_found_from_a_subfolder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    set_home(tmp_path, monkeypatch)
    vault = tmp_path / "vault"
    project_dir = vault / "projects" / "one"
    (vault / ".tow").mkdir(parents=True)
    project_dir.mkdir(parents=True)
    (vault / ".tow" / "config.json").write_text('{"kind": "vault"}', encoding="utf-8")

    resolved = resolve_vault(project_dir, None, {})

    assert resolved.root == vault
    assert resolved.layout == "tow"
    assert resolved.source == "ancestor"
    assert tow_kind(vault) == "vault"


@pytest.mark.parametrize("marker", ["tow.json", "Tag-Dictionary.json", "Category-Dictionary.md"])
def test_legacy_markers_count_as_a_vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, marker: str) -> None:
    set_home(tmp_path, monkeypatch)
    vault = tmp_path / "vault"
    project_dir = vault / "nested"
    project_dir.mkdir(parents=True)
    (vault / marker).write_text('{"tag": {}}' if marker == "Tag-Dictionary.json" else "{}", encoding="utf-8")

    resolved = resolve_vault(project_dir, None, {})

    assert resolved.root == vault
    assert resolved.layout == "legacy"
    assert resolved.source == "ancestor"
    assert is_legacy_vault(vault)


def test_empty_plugin_starter_dictionary_is_not_a_legacy_vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    set_home(tmp_path, monkeypatch)
    vault = tmp_path / "vault"
    nested = vault / "nested"
    nested.mkdir(parents=True)
    (vault / "Tag-Dictionary.json").write_text("{\n}\n", encoding="utf-8")

    assert not is_legacy_vault(vault)
    with pytest.raises(ConfigError, match="no vault found"):
        resolve_vault(nested, None, {})


def test_obsidian_folder_alone_is_not_a_vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    set_home(tmp_path, monkeypatch)
    project = tmp_path / "project"
    (project / ".obsidian").mkdir(parents=True)

    with pytest.raises(ConfigError, match="run tow-setup"):
        resolve_vault(project, None, {})


def test_upward_search_never_examines_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = set_home(tmp_path, monkeypatch)
    project = home / "projects" / "one"
    project.mkdir(parents=True)
    vault = tmp_path / "vault"
    vault.mkdir()
    write_user_config(home, vault)

    assert home not in list(upward(project))
    assert resolve_vault(project, None, {}).source == "user"


def test_a_missing_configured_vault_is_an_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = set_home(tmp_path, monkeypatch)
    write_user_config(home, tmp_path / "deleted-vault")

    with pytest.raises(ConfigError, match="does not exist"):
        resolve_vault(tmp_path, None, {})


def test_user_config_must_name_an_absolute_vault_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = set_home(tmp_path, monkeypatch)
    config = home / ".tow" / "config.json"
    config.parent.mkdir()
    config.write_text('{"kind": "user", "vault": "relative"}', encoding="utf-8")

    with pytest.raises(ConfigError):
        read_user_config()


def test_cwd_inside_the_vault_has_no_project_including_through_a_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    set_home(tmp_path, monkeypatch)
    vault = tmp_path / "vault"
    subfolder = vault / "notes"
    subfolder.mkdir(parents=True)
    alias = tmp_path / "vault-alias"
    alias.symlink_to(vault, target_is_directory=True)

    assert resolve_project(subfolder, vault) is None
    assert resolve_project(alias / "notes", vault) is None


def test_project_prefers_a_tow_project_folder_then_git_toplevel_then_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    set_home(tmp_path, monkeypatch)
    project = tmp_path / "project"
    nested = project / "nested"
    (project / ".tow").mkdir(parents=True)
    nested.mkdir()
    (project / ".tow" / "config.json").write_text('{"kind": "project"}', encoding="utf-8")

    assert resolve_project(nested, None) == project

    git_root = tmp_path / "git-root"
    git_nested = git_root / "src" / "app"
    git_nested.mkdir(parents=True)
    subprocess.run(["git", "init", str(git_root)], check=True, capture_output=True)
    assert resolve_project(git_nested, None) == git_root

    standalone = tmp_path / "standalone"
    standalone.mkdir()
    assert resolve_project(standalone, None) == standalone


def test_serialize_entries_matches_the_dictionary_layout() -> None:
    assert serialize_entries({"b": {"x": 1}, "a": {}}) == '{\n"a": {},\n"b": {"x": 1}\n}\n'
    assert serialize_entries({}) == "{\n}\n"


def test_connect_shows_the_current_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = set_home(tmp_path, monkeypatch)
    monkeypatch.chdir(tmp_path)

    assert tow.main(["connect"]) == 0
    assert capsys.readouterr().out == "not connected\n"

    vault = tmp_path / "personal-vault"
    vault.mkdir()
    write_user_config(home, vault)

    assert tow.main(["connect"]) == 0
    assert capsys.readouterr().out == f"connected: {vault} (from ~/.tow/config.json)\n"


def test_connect_shows_environment_connection_without_user_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = set_home(tmp_path, monkeypatch)
    env_vault = tmp_path / "environment-vault"
    env_vault.mkdir()
    monkeypatch.setenv("TOW_VAULT", str(env_vault))
    monkeypatch.chdir(tmp_path)

    assert tow.main(["connect"]) == 0
    assert capsys.readouterr().out == (f"connected: {env_vault} (from TOW_VAULT; overrides ~/.tow/config.json)\n")
    assert not (home / ".tow" / "config.json").exists()


def test_connect_warns_that_environment_overrides_user_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = set_home(tmp_path, monkeypatch)
    env_vault = tmp_path / "environment-vault"
    env_vault.mkdir()
    old_vault = tmp_path / "old-vault"
    old_vault.mkdir()
    new_vault = tmp_path / "new-vault"
    (new_vault / ".tow").mkdir(parents=True)
    (new_vault / ".tow" / "config.json").write_text('{"kind": "vault"}', encoding="utf-8")
    write_user_config(home, old_vault)
    monkeypatch.setenv("TOW_VAULT", str(env_vault))
    monkeypatch.chdir(tmp_path)

    assert tow.main(["connect"]) == 0
    assert capsys.readouterr().out == (f"connected: {env_vault} (from TOW_VAULT; overrides ~/.tow/config.json)\n")

    assert tow.main(["connect", "new-vault"]) == 0
    preview = capsys.readouterr()
    assert preview.out == f"would connect {env_vault} → {new_vault.resolve()}\n"
    assert "TOW_VAULT still overrides ~/.tow/config.json" in preview.err

    assert tow.main(["connect", "new-vault", "--apply"]) == 0
    applied = capsys.readouterr()
    assert "TOW_VAULT still overrides ~/.tow/config.json" in applied.err
    config = home / ".tow" / "config.json"
    assert json.loads(config.read_text(encoding="utf-8")) == {"kind": "user", "vault": str(new_vault.resolve())}


def test_connect_previews_without_apply_and_writes_with_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = set_home(tmp_path, monkeypatch)
    old_vault = tmp_path / "old-vault"
    old_vault.mkdir()
    new_vault = tmp_path / "new-vault"
    (new_vault / ".tow").mkdir(parents=True)
    (new_vault / ".tow" / "config.json").write_text('{"kind": "vault"}', encoding="utf-8")
    write_user_config(home, old_vault)
    monkeypatch.chdir(tmp_path)

    assert tow.main(["connect", "new-vault"]) == 0
    assert capsys.readouterr().out == f"would connect {old_vault} → {new_vault.resolve()}\n"
    config = home / ".tow" / "config.json"
    assert json.loads(config.read_text(encoding="utf-8")) == {"kind": "user", "vault": str(old_vault)}

    assert tow.main(["connect", "new-vault", "--apply"]) == 0
    assert json.loads(config.read_text(encoding="utf-8")) == {"kind": "user", "vault": str(new_vault.resolve())}


def test_user_config_write_preserves_existing_file_if_atomic_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = set_home(tmp_path, monkeypatch)
    vault = tmp_path / "vault"
    (vault / ".tow").mkdir(parents=True)
    (vault / ".tow" / "config.json").write_text('{"kind": "vault"}', encoding="utf-8")
    existing = home / ".tow" / "config.json"
    existing.parent.mkdir()
    existing.write_text('{"kind": "user", "vault": "old"}', encoding="utf-8")

    def fail_replace(source: str | Path, target: str | Path) -> None:
        assert Path(target) == existing
        assert existing.read_text(encoding="utf-8") == '{"kind": "user", "vault": "old"}'
        assert Path(source).is_file()
        raise OSError("replace failed")

    monkeypatch.setattr(tow_core.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        tow_core.write_user_config(vault)

    assert existing.read_text(encoding="utf-8") == '{"kind": "user", "vault": "old"}'
    assert list(existing.parent.iterdir()) == [existing]


def test_connect_refuses_a_folder_that_is_not_a_vault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    home = set_home(tmp_path, monkeypatch)
    not_a_vault = tmp_path / "plain-folder"
    not_a_vault.mkdir()
    monkeypatch.chdir(tmp_path)

    assert tow.main(["connect", str(not_a_vault)]) == 2
    assert "run setup inside the vault first" in capsys.readouterr().err
    assert not (home / ".tow" / "config.json").exists()


def test_exclusive_atomic_write_fallback_removes_partial_target_when_writing_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "created.txt"

    def unavailable_link(source: str | Path, target: str | Path) -> None:
        raise OSError(errno.ENOTSUP, "operation not supported")

    class FailingFile:
        def __enter__(self):
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def write(self, text: str) -> None:
            raise OSError("simulated write failure")

    monkeypatch.setattr(tow_core.os, "link", unavailable_link)

    def fail_fdopen(_fd: int, mode: str) -> FailingFile:
        assert mode == "wb"
        return FailingFile()

    monkeypatch.setattr(tow_core.os, "fdopen", fail_fdopen)

    with pytest.raises(OSError, match="simulated write failure"):
        tow_core.write_text_atomic(path, "created", exclusive=True)

    assert not path.exists()


def test_exclusive_atomic_write_falls_back_when_hard_links_are_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "created.txt"

    def unavailable_link(source: str | Path, target: str | Path) -> None:
        raise OSError(errno.ENOTSUP, "operation not supported")

    monkeypatch.setattr(tow_core.os, "link", unavailable_link)

    tow_core.write_text_atomic(path, "created", exclusive=True)

    assert path.read_text(encoding="utf-8") == "created"
    assert list(tmp_path.iterdir()) == [path]


def test_exclusive_atomic_write_fallback_refuses_a_target_created_after_the_initial_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "existing.txt"

    def create_target_then_disable_link(_source: str | Path, target: str | Path) -> None:
        Path(target).write_text("original", encoding="utf-8")
        raise OSError(errno.ENOTSUP, "operation not supported")

    monkeypatch.setattr(tow_core.os, "link", create_target_then_disable_link)

    with pytest.raises(FileExistsError):
        tow_core.write_text_atomic(path, "replacement", exclusive=True)

    assert path.read_text(encoding="utf-8") == "original"


def test_shared_plumbing_remains_importable_from_tow() -> None:
    from tow_core import DEFAULT_CLI, CliError, run_cli

    assert tow.ConfigError is ConfigError
    assert tow.CliError is CliError
    assert tow.DEFAULT_CLI == DEFAULT_CLI
    assert tow.run_cli is run_cli
