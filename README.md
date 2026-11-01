# TOW — Tag Ontology for Wiki

A Claude Code plugin for running a tag-first LLM wiki in Obsidian.

[한국어](README.ko.md)

> **Status:** in development. The skills need the `tag-ontology` CLI, which is not published yet.

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
      ▲  /plugin install
your Obsidian vault
```

## Skills

| Skill | Purpose |
| --- | --- |
| `tow:tow-check` | Check notes against the vault conventions and the tag dictionary |
| `tow:tow-tag-sync` | Reconcile the tags used in notes with the tag dictionary |
| `tow:tow-tag-suggest` | Suggest concept tags for a note; attach only the ones you pick |
| `tow:tow-query` | Find notes by category, concept tag, or both (read-only) |

## Requirements

- Claude Code
- Node.js 22.18 or later, for the `tag-ontology` CLI
- Python 3.10 or later (standard library only)

## Install

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

On Claude Code older than 2.1.275:

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

## Development

```bash
uv sync
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
```

The skills call [`scripts/tow.py`](scripts/tow.py), which reads notes through `npx --yes tag-ontology@0.1`. To use another build of the CLI, set `TOW_TAG_ONTOLOGY` to its command, for example `TOW_TAG_ONTOLOGY="node /path/to/cli.js"`.

The real CLI integration tests are optional. Select an existing CLI build to run them alongside the unit tests:

```bash
TOW_TAG_ONTOLOGY="node /absolute/path/to/tag-ontology/dist/cli/main.js" uv run pytest
```

Without this variable, the integration tests are skipped. They copy the [synthetic vault](tests/fixtures/vault) into temporary directories and never use your own vault. See [evaluation](docs/evaluation.md) for the skill scenarios and verification limits.

## License

[MIT](LICENSE)
