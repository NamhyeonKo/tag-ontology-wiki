from pathlib import Path

import pytest

import tow


def test_send_previews_then_creates_a_new_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"
    vault = tmp_path / "vault"
    project.mkdir()
    vault.mkdir()
    monkeypatch.chdir(project)
    source = project / "selection.txt"
    source.write_bytes(b"# Selected text\r\n\r\nKeep $x_1 + y$.\r\n")
    draft = project / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\n" + source.read_bytes())
    dest = "01_Projects/topic/note.md"
    target = vault / dest

    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--source", str(source)]) == 0
    assert capsys.readouterr().out == f"would create {dest}\n"
    assert not target.exists()

    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--source", str(source), "--apply"]) == 0
    assert capsys.readouterr().out == f"created {dest}\n"
    assert target.read_bytes() == draft.read_bytes()


def test_send_accepts_source_frontmatter_when_bodies_match(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    draft = tmp_path / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\n# Selected\nBody.\n")
    source = tmp_path / "source.md"
    source.write_bytes(b"---\ntags: [rag]\nprivate: note\n---\n# Selected\nBody.\n")
    dest = "03_Resources/selected.md"

    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--source", str(source), "--apply"]) == 0

    assert capsys.readouterr().out == f"created {dest}\n"
    assert (vault / dest).read_bytes() == draft.read_bytes()
    assert b"private: note" not in (vault / dest).read_bytes()


def test_send_never_overwrites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = tmp_path / "vault"
    target = vault / "01_Projects" / "existing.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"original\n")
    draft = tmp_path / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\nnew\n")
    source = tmp_path / "source.txt"
    source.write_bytes(b"new\n")
    monkeypatch.chdir(tmp_path)

    assert (
        tow.main(
            ["--root", str(vault), "send", str(draft), "01_Projects/existing.md", "--source", str(source), "--apply"]
        )
        == 2
    )
    assert "File exists" in capsys.readouterr().err
    assert target.read_bytes() == b"original\n"


@pytest.mark.parametrize("dest", ["01_Projects/note.txt", "01_Projects/.private/note.md", "01_Projects/.hidden.md"])
def test_send_refuses_non_markdown_or_hidden_destination_segments(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], dest: str
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    draft = tmp_path / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\nbody\n")
    source = tmp_path / "source.txt"
    source.write_bytes(b"body\n")

    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--source", str(source)]) == 2

    assert "destination" in capsys.readouterr().err
    assert not (vault / "01_Projects").exists()


def test_send_refuses_a_destination_outside_the_note_folders(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    draft = tmp_path / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\nbody\n")
    source = tmp_path / "source.txt"
    source.write_bytes(b"body\n")

    assert (
        tow.main(["--root", str(vault), "send", str(draft), "outside/note.md", "--source", str(source), "--apply"]) == 2
    )
    assert "configured note folder" in capsys.readouterr().err
    assert not (vault / "outside").exists()


def test_send_refuses_a_symlinked_folder_that_leaves_the_vault(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (vault / "01_Projects").symlink_to(outside, target_is_directory=True)
    draft = tmp_path / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\nbody\n")
    source = tmp_path / "source.txt"
    source.write_bytes(b"body\n")

    assert (
        tow.main(["--root", str(vault), "send", str(draft), "01_Projects/note.md", "--source", str(source), "--apply"])
        == 2
    )
    assert not (outside / "note.md").exists()


def test_send_refuses_an_in_vault_symlink_to_another_note_folder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = tmp_path / "vault"
    projects = vault / "01_Projects"
    resources = vault / "03_Resources"
    projects.mkdir(parents=True)
    resources.mkdir()
    (projects / "link").symlink_to(resources, target_is_directory=True)
    draft = tmp_path / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\nbody\n")
    source = tmp_path / "source.txt"
    source.write_bytes(b"body\n")

    assert (
        tow.main(
            ["--root", str(vault), "send", str(draft), "01_Projects/link/note.md", "--source", str(source), "--apply"]
        )
        == 2
    )
    assert "note folder" in capsys.readouterr().err
    assert not (resources / "note.md").exists()


def test_send_cleans_up_a_partial_write_and_allows_retry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    draft = tmp_path / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\nbody\n")
    source = tmp_path / "source.txt"
    source.write_bytes(b"body\n")
    dest = "01_Projects/nested/note.md"
    target = vault / dest
    original_read_bytes = Path.read_bytes
    failed = False

    def fail_first_readback(path: Path) -> bytes:
        nonlocal failed
        if path == target and not failed:
            failed = True
            raise OSError("simulated read-back failure")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_first_readback)
    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--source", str(source), "--apply"]) == 2
    assert not target.exists()
    assert not (vault / "01_Projects").exists()

    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--source", str(source), "--apply"]) == 0
    assert target.read_bytes() == draft.read_bytes()


def test_send_requires_the_body_to_equal_the_source_unless_transformed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    draft = tmp_path / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\ntransformed body\n")
    source = tmp_path / "source.txt"
    source.write_bytes(b"---\ntags: [rag]\n---\noriginal body\n")
    dest = "03_Resources/note.md"

    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--apply"]) == 2
    assert "requires --source" in capsys.readouterr().err
    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--transformed", "--apply"]) == 2
    assert "requires --source" in capsys.readouterr().err
    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--source", str(source), "--apply"]) == 2
    assert "does not match the source" in capsys.readouterr().err
    assert not (vault / dest).exists()

    assert (
        tow.main(["--root", str(vault), "send", str(draft), dest, "--source", str(source), "--transformed", "--apply"])
        == 0
    )
    assert (vault / dest).read_bytes() == draft.read_bytes()


def test_send_creates_missing_folders_inside_the_note_folder(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    draft = tmp_path / "draft.md"
    draft.write_bytes(b"---\ntype: resource\n---\nbody\n")
    source = tmp_path / "source.txt"
    source.write_bytes(b"body\n")
    dest = "02_Areas/topic/subtopic/note.md"

    assert tow.main(["--root", str(vault), "send", str(draft), dest, "--source", str(source), "--apply"]) == 0
    assert (vault / dest).read_bytes() == draft.read_bytes()
