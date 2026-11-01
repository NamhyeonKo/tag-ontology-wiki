import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_hosts_share_the_same_package_identity() -> None:
    portable = json.loads((ROOT / "plugin.json").read_text())
    claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    for key in ("name", "version", "author", "repository", "license"):
        assert portable[key] == claude[key]
    assert len(list((ROOT / "skills").glob("*/SKILL.md"))) == 4


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
    for name in ("skills", "docs", "scripts"):
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
    assert json.loads(result.stdout) == json.loads((vault / "tow.json").read_text())
