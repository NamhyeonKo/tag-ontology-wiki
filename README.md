# TOW — Tag Ontology for Wiki

Plugins for Claude Code, Codex, and Google Antigravity to run a tag-first LLM wiki in Obsidian.

[한국어](README.ko.md)

> **Version:** 0.1.1.

## Overview

TOW is a variant of Karpathy's LLM Wiki that organizes notes by tags first. A vault that follows it uses three layers:

- **PARA folders**: Projects, Areas, Resources, Archives.
- **Classification fields** in frontmatter: `category`, `type`, `status`, `kind`.
- **A concept tag ontology**: a tag dictionary with aliases and broader/narrower relations.

The full conventions are in [docs/methodology.md](docs/methodology.md).

The plugin gives the agent skills that follow these conventions, plus a Python checker for the vault conventions.
Dictionary validation, queries, edits, and note parsing come from the [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) CLI. TOW calls the CLI and does not parse notes itself.

```text
tag-ontology (npm CLI)    dictionary checks, queries, edits, note parsing
      ▲  npx tag-ontology … --json
tow (this plugin)         vault convention checks, skills
      ▲  Claude Code / Codex / Antigravity
your Obsidian vault
```

## Skills

| Skill | Purpose |
| --- | --- |
| `tow-check` | Check notes against the vault conventions and the tag dictionary |
| `tow-tag-sync` | Reconcile the tags used in notes with the tag dictionary |
| `tow-tag-suggest` | Suggest concept tags for a note; attach only the ones you pick |
| `tow-query` | Find notes by category, concept tag, or both (read-only) |

All three hosts share these skills, the conventions, and the CLI. In Claude Code, invoke `/tow:tow-query`; in Codex, select `tow-query` with `$` or `/skills`; in Antigravity, invoke `/tow-query`.

## Requirements

- Claude Code, Codex, or Google Antigravity with plugin support
- Node.js 22.18 or later, for the `tag-ontology` CLI
- Python 3.10 or later (standard library only)

The skills read the vault files you scope and apply only the changes you approve. Your agent host processes opened note content under its own model and privacy settings. TOW has no hosted backend; npm downloads the pinned CLI, and the host controls file access.

## Install

### Claude Code

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

On Claude Code older than 2.1.275:

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

### Codex

Run in your shell:

```bash
codex plugin marketplace add NamhyeonKo/tag-ontology-wiki --ref main
codex plugin add tow@tag-ontology-wiki
```

### Antigravity

Run in your shell, then start a new Antigravity session:

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

## Development

```bash
uv sync
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
```

The skills call [`scripts/tow.py`](scripts/tow.py), which reads notes through `npx --yes tag-ontology@0.1.2`. The exact version makes the downloaded executable reproducible for plugin distribution. To use another build of the CLI, set `TOW_TAG_ONTOLOGY` to its command, for example `TOW_TAG_ONTOLOGY="node /path/to/cli.js"`.

The real CLI integration tests are optional locally. Point `TOW_TAG_ONTOLOGY` at a CLI to run them alongside the unit tests:

```bash
TOW_TAG_ONTOLOGY="npx --yes tag-ontology@0.1.2" uv run pytest
```

Without this variable, the integration tests are skipped. They copy the [synthetic vault](tests/fixtures/vault) into temporary directories and never use your own vault. See [evaluation](docs/evaluation.md) for the skill scenarios and verification limits.

## License

[MIT](LICENSE)
