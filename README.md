# TOW — Tag Ontology for Wiki

A plugin for Claude Code, Codex, and Google Antigravity to search and maintain a tag-first Obsidian wiki.

[한국어](README.ko.md)

> **Version:** 0.2.1.

## Overview

TOW is a variant of Karpathy's LLM Wiki that organizes notes by tags first. A vault that follows it uses three layers:

- **PARA folders**: Projects, Areas, Resources, Archives.
- **Classification fields** in frontmatter: `category`, `type`, `status`, `kind`.
- **A concept tag ontology**: a tag dictionary with aliases and broader/narrower relations.

The full conventions are in [docs/methodology.md](docs/methodology.md).

TOW installs ten workflows into your local coding agent. You name the vault and notes; the agent reads the relevant files, searches classifications and concept tags, and proposes scoped changes for your approval. The files stay in your Obsidian vault.

The package contains skills, shared conventions, and the Python helper [`scripts/tow.py`](scripts/tow.py). That helper checks classification rules and calls the [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) npm CLI for note parsing, tag queries, and dictionary validation/changes. Your agent host supplies the model and file tools.

```text
tag-ontology@0.1.2        dictionary checks, queries, edits, note parsing
      ▲  npx tag-ontology … --json
tow (this plugin)         vault convention checks, skills
      ▲  Claude Code / Codex / Antigravity
your Obsidian vault
```

## Skills

| Skill | When to use it | Changes |
| --- | --- | --- |
| `tow-query` | Find project notes about RAG, or notes matching a category/concept | Read-only; opens notes before summarizing them |
| `tow-check` | Check frontmatter, headings, tables, math, and references | Reports first; fixes only approved formatting |
| `tow-tag-suggest` | Recommend concept tags for selected notes | Applies only the additions/removals you select |
| `tow-tag-sync` | Register new tags, resolve aliases, or reconcile the dictionary | Proposes first; applies approved dictionary/tag changes |
| `tow-classify` | Register categories, reclassify notes, convert legacy fields | Approve entries and conversions; retroactive changes are a separate choice |
| `tow-link` | Link existing title/alias mentions | Approved first mentions only; preserves displayed words |
| `tow-edit` | Fill empty sections, restructure, or change body style | A clear, scoped request authorizes the edit; asks when ambiguous |
| `tow-merge` | Absorb, split, or reconcile overlapping notes | Select a strategy for each case; confirm discarded facts separately |
| `tow-review` | Review a domain or project's ownership, duplicates, hubs | Reports first; executes selected fixes through the relevant skills |
| `tow-ingest` | File captures and derive reusable notes from sources | Approve the batch before backups, metadata, moves, attachments and links |

All three hosts share these skills, the conventions, and the CLI. In Claude Code, invoke `/tow:tow-query`; in Codex, select `tow-query` with `$` or `/skills`; in Antigravity, invoke `/tow-query`.

## Requirements

- Claude Code, Codex, or Google Antigravity with plugin support
- Git, for installation from GitHub
- Node.js 22.18 or later, with npm/npx on `PATH`, for the `tag-ontology` CLI
- Python 3.10 or later (standard library only)

The skills read the vault files you scope and apply only the changes you approve. Your agent host processes opened note content under its own model and privacy settings. TOW has no hosted backend; npm downloads the pinned CLI, and the host controls file access.

## Install from GitHub

Install directly from this public repository. Official-directory registration is optional. The commands below use `main`; after installation, start a new host session. See the [installation and troubleshooting guide](docs/installation.md) for verification, vault settings, and updates.

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

## First use

Open the vault as your host's workspace, or grant it access to that directory. In a new session, select `tow-query` using the host-specific invocation above, then send:

```text
My vault is /absolute/path/to/vault. Find project notes about RAG by category
or concept, excluding superseded documents. Read matching notes before
summarizing them and return their paths and count. Do not modify files.
```

For an existing vault, check its folder/dictionary paths first. TOW reads `tow.json` at the vault root; omitted settings use the defaults in the [setup guide](docs/installation.md#configure-the-vault). Installation does not create or migrate a vault.

## CLI and setup checks

The helper uses `npx --yes tag-ontology@0.1.2`; npm fetches that exact version when needed. Manual helper commands use the installed `scripts/tow.py` path. The name `tow` in the conventions is shorthand for that path.

Neither TOW 0.2.1 nor `tag-ontology` 0.1.2 has a `doctor` command. Start with:

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.2 --version
```

Then follow the [setup checks](docs/installation.md#check-the-setup) to verify the installed plugin, configuration, dictionaries, and note tags. `lint` covers classification fields and tag counts; the check skill adds the note-by-note formatting/reference review. A clean lint result alone does not cover every skill check.

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
