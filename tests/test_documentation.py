import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
LANGUAGES = {"ko", "zh-CN", "zh-TW", "ja", "es", "fr"}
COMMAND_PREFIXES = ("/plugin", "codex ", "agy ", "claude ", "python3 ")


def test_readme_translations_keep_the_same_install_and_update_commands() -> None:
    source = (ROOT / "README.md").read_text()
    translations = list((ROOT / "readme").glob("README.*.md"))
    assert {path.name for path in translations} == {f"README.{language}.md" for language in LANGUAGES}
    commands = re.findall(r"```(?:bash|text)\n(.*?)\n```", source, re.DOTALL)
    commands = [block for block in commands if block.startswith(COMMAND_PREFIXES)]
    skills = re.findall(r"^\| `(tow-[a-z-]+)`", source, re.MULTILINE)
    for path in translations:
        text = path.read_text()
        blocks = re.findall(r"```(?:bash|text)\n(.*?)\n```", text, re.DOTALL)
        assert [block for block in blocks if block.startswith(COMMAND_PREFIXES)] == commands, path
        assert re.findall(r"^\| `(tow-[a-z-]+)`", text, re.MULTILINE) == skills, path


def test_public_documentation_links_resolve_inside_the_repository() -> None:
    documents = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "docs/installation.md",
        *(ROOT / "readme").glob("*.md"),
    ]
    for document in documents:
        for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            if href.startswith(("https://", "http://", "#")):
                continue
            target = (document.parent / href.split("#", 1)[0]).resolve()
            assert target.is_relative_to(ROOT), (document, href)
            assert target.exists(), (document, href)
