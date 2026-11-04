import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

import tow

ROOT = Path(__file__).parents[1]
SKILLS = {
    "tow-query",
    "tow-check",
    "tow-tag-suggest",
    "tow-tag-sync",
    "tow-classify",
    "tow-link",
    "tow-edit",
    "tow-merge",
    "tow-review",
    "tow-ingest",
    "tow-setup",
}


def test_hosts_share_the_same_package_identity() -> None:
    portable = json.loads((ROOT / "plugin.json").read_text())
    for name in (".claude-plugin", ".antigravity-plugin"):
        manifest = json.loads((ROOT / name / "plugin.json").read_text())
        for key in ("name", "version", "author", "repository", "license"):
            assert portable[key] == manifest[key]
    assert {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")} == SKILLS


def test_workflows_have_no_private_vault_dependencies() -> None:
    documents = [ROOT / "docs/methodology.md", *(ROOT / "skills").rglob("*.md")]
    for document in documents:
        text = document.read_text()
        for private in ("/Users/", "oh-my-obsidian", "vault_meta.py", "../../../AGENTS.md"):
            assert private not in text, (document, private)


def test_distribution_declares_local_execution_and_bundles_a_valid_icon() -> None:
    portable = json.loads((ROOT / "plugin.json").read_text())
    openai = portable["extensions"]["com.openai"]
    assert openai["requires_local_executor"] is True
    interface = openai["interface"]
    assert 0 < len(interface["displayName"]) <= 30
    assert 0 < len(interface["shortDescription"]) <= 30
    assert interface["longDescription"] and interface["developerName"]
    assert interface["logo"] == interface["composerIcon"]
    image = (ROOT / interface["logo"]).read_bytes()
    assert image[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", image[16:24])
    assert width == height and 512 <= width <= 2048 and len(image) < 2 * 1024 * 1024
    for name, key in ((".claude-plugin", "icon"), (".antigravity-plugin", "logo")):
        manifest = json.loads((ROOT / name / "plugin.json").read_text())
        assert (ROOT / manifest[key]).read_bytes() == image


def test_distribution_pins_an_exact_published_cli_version() -> None:
    assert re.fullmatch(r"npx --yes tag-ontology@\d+\.\d+\.\d+", tow.DEFAULT_CLI)


def test_codex_marketplace_points_at_the_complete_package() -> None:
    catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
    claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert catalog["name"] == claude["name"]
    (entry,) = catalog["plugins"]
    assert entry["name"] == json.loads((ROOT / "plugin.json").read_text())["name"]
    assert entry["source"]["source"] == "local"
    assert (ROOT / entry["source"]["path"]).resolve() == ROOT


def test_relocated_package_keeps_references_and_executable_without_host_variables(tmp_path: Path) -> None:
    package = tmp_path / "installed plugin with spaces"
    package.mkdir()
    shutil.copy2(ROOT / "plugin.json", package / "plugin.json")
    for name in ("skills", "docs", "scripts", "assets"):
        shutil.copytree(ROOT / name, package / name, ignore=shutil.ignore_patterns("__pycache__"))
    for document in (package / "skills").rglob("*.md"):
        for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            if href.startswith(("https://", "http://", "#")):
                continue
            target = (document.parent / href.split("#", 1)[0]).resolve()
            assert target.is_relative_to(package), (document, href)
            assert target.is_file(), (document, href)
    env = {key: value for key, value in os.environ.items() if key not in {"CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT"}}
    vault = Path(shutil.copytree(ROOT / "tests/fixtures/vault", tmp_path / "vault"))
    result = subprocess.run(
        [str(package / "scripts/tow.py"), "--root", str(vault), "config"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == {**tow.DEFAULTS, **json.loads((vault / "tow.json").read_text())}


def test_skill_descriptions_list_english_triggers_only() -> None:
    for skill in SKILLS:
        frontmatter = (ROOT / "skills" / skill / "SKILL.md").read_text().split("---")[1]
        assert re.findall(r'"[^"]+"', frontmatter.split("Triggers:")[1]), skill
        assert not re.search(r"[\uac00-\ud7af]", frontmatter), skill


def test_korean_text_stays_in_korean_documents() -> None:
    allowed = {ROOT / "skills/tow-edit/references/korean-style.md"}
    for document in [ROOT / "docs/methodology.md", *(ROOT / "skills").rglob("*.md")]:
        if document not in allowed:
            assert not re.search(r"[\uac00-\ud7af]", document.read_text()), document


RELEASE_ASSETS = ROOT / ".github/scripts/release_assets.py"
needs_git = pytest.mark.skipif(not (ROOT / ".git").exists(), reason="release archives need a Git checkout")


def release_assets(out: Path, version: str) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(RELEASE_ASSETS), "--version", version, "--out", str(out)]
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)


@needs_git
def test_release_assets_build_the_portable_and_native_antigravity_archives(tmp_path: Path) -> None:
    version = json.loads((ROOT / "plugin.json").read_text())["version"]
    result = release_assets(tmp_path, version)
    assert result.returncode == 0, result.stderr
    names = [f"tow-{version}.zip", f"tow-antigravity-{version}.zip"]
    with zipfile.ZipFile(tmp_path / names[0]) as portable, zipfile.ZipFile(tmp_path / names[1]) as native:
        overlay = "tow/.antigravity-plugin/plugin.json"
        assert set(portable.namelist()) - set(native.namelist()) == {overlay}
        assert native.read("tow/plugin.json") == portable.read(overlay)
        assert native.comment == portable.comment
    sums = "".join(f"{hashlib.sha256((tmp_path / n).read_bytes()).hexdigest()}  {n}\n" for n in names)
    assert (tmp_path / "SHA256SUMS").read_text() == sums


@needs_git
def test_release_assets_refuse_a_version_the_commit_does_not_declare(tmp_path: Path) -> None:
    result = release_assets(tmp_path / "dist", "0.0.0")
    assert result.returncode == 1
    assert "does not declare 0.0.0" in result.stderr
    assert not (tmp_path / "dist").exists()
