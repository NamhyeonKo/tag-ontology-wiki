from pathlib import Path

import pytest

import tow


def test_verify_body_accepts_only_frontmatter_changes_without_cli_or_config(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    body = b"# Note\r\n\r\nKeep $x_1 + y$, `a  b`, and 1.00 kg.\r\n"
    (tmp_path / "before.md").write_bytes(b"---\r\nstatus: reading\r\n---\r\n" + body)
    (tmp_path / "after.md").write_bytes(b"---\nstatus: done\ncustom: [value]\n---\n" + body)
    (tmp_path / "tow.json").write_text("not valid JSON")
    assert tow.main(["--root", str(tmp_path), "verify-body", "before.md", "after.md"]) == 0
    assert "body unchanged" in capsys.readouterr().out


@pytest.mark.parametrize(
    "body",
    [
        b"# Note\nChanged prose.\n",
        b"# Note\n$x - y$\n",
        b'# Note\n```python\nemit("a b")\n```\n',
        b"# Note\n| Value |\n| --- |\n| 1.0 kg |\n",
        b"# Note\r\nOriginal.\r\n",
        b"# Note\nOriginal.",
    ],
)
def test_verify_body_rejects_every_body_byte_change(tmp_path: Path, body: bytes) -> None:
    (tmp_path / "before.md").write_bytes(b"---\nstatus: reading\n---\n# Note\nOriginal.\n")
    (tmp_path / "after.md").write_bytes(b"---\nstatus: done\n---\n" + body)
    assert tow.main(["--root", str(tmp_path), "verify-body", "before.md", "after.md"]) == 1


def test_verify_body_handles_absent_frontmatter_and_thematic_breaks(tmp_path: Path) -> None:
    body = b"# Note\n\n---\n\nThis remains body text.\n"
    (tmp_path / "before.md").write_bytes(body)
    (tmp_path / "after.md").write_bytes(b"---\ntags: []\n---\n" + body)
    assert tow.main(["--root", str(tmp_path), "verify-body", "before.md", "after.md"]) == 0


def test_verify_body_handles_bom_and_a_closing_delimiter_at_eof(tmp_path: Path) -> None:
    (tmp_path / "before.md").write_bytes(b"\xef\xbb\xbf---\nstatus: reading\n---")
    (tmp_path / "after.md").write_bytes(b"---\nstatus: done\n---\n")
    assert tow.main(["--root", str(tmp_path), "verify-body", "before.md", "after.md"]) == 0


def test_verify_body_fails_closed_on_an_unclosed_frontmatter_block(tmp_path: Path) -> None:
    (tmp_path / "before.md").write_bytes(b"---\nstatus: reading\n")
    (tmp_path / "after.md").write_bytes(b"---\nstatus: done\n")
    assert tow.main(["--root", str(tmp_path), "verify-body", "before.md", "after.md"]) == 2


def test_verify_body_rejects_a_self_comparison_and_hard_linked_snapshot(tmp_path: Path) -> None:
    (tmp_path / "note.md").write_text("# Note\n")
    (tmp_path / "copy.md").hardlink_to(tmp_path / "note.md")
    for before in ("note.md", "copy.md"):
        assert tow.main(["--root", str(tmp_path), "verify-body", before, "note.md"]) == 2


def test_verify_body_rejects_outside_paths_and_symlinks(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    (root / "note.md").write_text("# Note\n")
    outside = tmp_path / "outside.md"
    outside.write_text("# Note\n")
    (root / "link.md").symlink_to(outside)
    for path in ("../outside.md", str(outside), "link.md"):
        assert tow.main(["--root", str(root), "verify-body", path, "note.md"]) == 2


def test_verify_body_reports_missing_snapshots(tmp_path: Path) -> None:
    (tmp_path / "note.md").write_text("# Note\n")
    assert tow.main(["--root", str(tmp_path), "verify-body", "missing.md", "note.md"]) == 2
