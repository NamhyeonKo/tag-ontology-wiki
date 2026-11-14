<h1 align="center">TOW — Tag Ontology for Wiki</h1>

<p align="center">
  <a href="https://github.com/NamhyeonKo/tag-ontology-wiki/stargazers"><img alt="stars" src="https://img.shields.io/github/stars/NamhyeonKo/tag-ontology-wiki?label=stars"></a>
  <a href="https://github.com/NamhyeonKo/tag-ontology-wiki/releases/latest"><img alt="release" src="https://img.shields.io/github/v/release/NamhyeonKo/tag-ontology-wiki?label=release"></a>
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/github/license/NamhyeonKo/tag-ontology-wiki?label=license"></a>
</p>

<p align="center"><a href="README.md">English</a> · <a href="readme/README.ko.md">한국어</a> · <a href="readme/README.zh-CN.md">简体中文</a> · <a href="readme/README.zh-TW.md">繁體中文</a> · <a href="readme/README.ja.md">日本語</a> · <a href="readme/README.es.md">Español</a> · <a href="readme/README.fr.md">Français</a></p>

An agent skill plugin for working across an Obsidian vault and a coding project: search both by concept, tag project documents in `.tow/` metadata without editing them, and send selected content to the vault as a new note. Vault-maintenance workflows preserve note content. Runs in Claude Code, Codex, and Google Antigravity.

> **Version:** 0.5.10.

## Why TOW?

TOW began as a way to automate Inbox organization in my PARA-based Obsidian vault. I wanted to keep the knowledge I had written and reviewed while using the same documents with AI agents for search and maintenance.

I was concerned that extracting and restructuring source material with an LLM could change the author's intent and context. The goal was to accumulate and use knowledge while preserving the original documents and their existing organization. From Inbox organization, TOW grew to include search, tag management, and integration with external projects.

## Overview

Ordinary maintenance preserves prose, math/code contents and table values; only selected frontmatter and formatting change. Optional post-curation follows your own templates and explicit operation choices. TOW works with existing vault layouts, including notes without frontmatter. Its optional tag-first LLM Wiki recipe has three independently selectable layers:

- **PARA folders**: Projects, Areas, Resources, Archives.
- **Classification fields** in frontmatter: `category`, `type`, `status`, `kind`.
- **A concept tag ontology**: a tag dictionary with aliases and broader/narrower relations.

Choose PARA during setup or keep your own folders. Ordinary search/body work needs neither dictionaries nor metadata cleanup. Queries run one `tow search` that combines concepts from the tag dictionary, titles, headings, text and properties with AND, OR and NOT, then open only the notes they describe in the answer; available properties improve precision. `tow-link`, `tow-merge`, `tow-ingest` and `tow-review` find notes with the same `tow search`. The full conventions are in [docs/methodology.md](docs/methodology.md).

TOW installs twelve workflows into your local agent host. Vault-only workflows manage notes in Obsidian; from a project, `tow-query` searches the connected vault and current project, and `tow-send-vault` creates a new vault note from selected content after approval. Project tags and hashes are stored in project `.tow/` metadata; project documents are not edited.

The package contains skills, shared conventions, and the Python helper [`scripts/tow.py`](scripts/tow.py). That helper checks classification rules and calls the [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) npm CLI for note parsing, tag queries, and dictionary validation/changes. Your agent host supplies the model and file tools.

TOW uses the Tag Ontology CLI to query tags and validate/manage dictionaries. Install the [Tag Ontology plugin for Obsidian](https://github.com/NamhyeonKo/obsidian-tag-ontology) ([community plugin page](https://community.obsidian.md/plugins/tag-ontology)) alongside TOW to visually explore the tag hierarchy and relationships you manage in a graph.

```text
tag-ontology@0.3.2        dictionary checks, queries, edits, note parsing
      ▲  npx tag-ontology … --json
tow (this plugin)         vault convention checks, skills
      ▲  Claude Code / Codex / Antigravity
your Obsidian vault
```

## Skills

| Skill | When to use it | Changes |
| --- | --- | --- |
| `tow-setup` | Set up a vault, connect it for project use, or register project metadata | Inspects names first; writes only approved `.tow/` metadata or personal connection settings |
| `tow-send-vault` | Send selected project content to the connected vault | Creates a new note after approval; preserves the selected body unless a transformation is requested |
| `tow-query` | Find documents using natural-language conditions, custom properties, tags or text | Read-only; one `tow search` query (AND, OR, NOT) over concepts, titles, text and fields; lists matches and opens only the notes it describes in the answer |
| `tow-check` | Check frontmatter, Markdown, math, code, tables and references | Reports first; selected syntax fixes preserve prose, payloads and values |
| `tow-tag-suggest` | Recommend concept tags for selected notes | Applies only the additions/removals you select |
| `tow-tag-sync` | Register new tags, resolve aliases, or reconcile the dictionary | Proposes first; applies approved dictionary/tag changes |
| `tow-classify` | Register categories, reclassify notes, convert legacy fields | Approve entries and conversions; retroactive changes are a separate choice |
| `tow-link` | Link existing title/alias mentions | Approved first mentions only; preserves displayed words |
| `tow-edit` | Explicit body aftercare under your template/rules | Selected new/empty content or transformations only; missing rules prompt a question |
| `tow-merge` | Explicit consolidation under chosen destinations/rules | Verbatim transfer by default; per-case choices and separate discard confirmation |
| `tow-review` | Review notes against your rules and propose aftercare | Read-only until a concrete follow-up operation is selected |
| `tow-ingest` | Explicit filing/source aftercare under your chosen rules | Verbatim filing by default; no implied metadata, derivation or rewriting |

All three hosts share these skills, the conventions, and the CLI. In Claude Code, invoke `/tow:tow-query`; in Codex, select `tow-query` with `$` or `/skills`; in Antigravity, invoke `/tow-query`.

## Preservation and optional aftercare

Metadata-only changes use independent snapshots and `tow verify-body` to check exact body bytes. Formatting includes Markdown syntax, math delimiters, code fences/language-aware formatting and tables, but never changes their contents. Ambiguous or unverifiable fixes remain reports. These are skill instructions plus a narrow byte comparison, not a universal semantic verifier or host-enforced security hook.

`tow-edit`, `tow-merge`, `tow-ingest` and `tow-review` keep their names and are optional post-curation workflows. They reuse your supplied/established templates and rules; a general cleanup request or a template alone does not authorize rewriting filled prose, generating a hub or splitting notes. See [preservation](docs/preservation.md) and [post-curation](docs/post-curation.md).

## Requirements

- Claude Code, Codex, or Google Antigravity with plugin support
- Git, for installation from GitHub
- Node.js 22.18 or later, with npm/npx on `PATH`, when using the optional `tag-ontology` parsing/ontology features
- Obsidian CLI is optional; native search requires it enabled and the target vault accessible in the running app. File search remains available without it
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

## Update

Run the commands for your host in your terminal, then start a new session.

**Claude Code:**

```bash
claude plugin update tow@tag-ontology-wiki
```

**Codex:**

```bash
codex plugin marketplace upgrade tag-ontology-wiki
codex plugin add tow@tag-ontology-wiki
```

**Antigravity:** reinstall from the same source.

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

Confirm the installed version with your host's plugin list/details command. See [updates and troubleshooting](docs/installation.md#update) for host-specific behavior and checks.

## First use

For vault-only maintenance, open the vault as your host's workspace. Vault-side TOW files live in visible `tow/`; external project metadata remains in project `.tow/`. For project use, open the project workspace instead and select `tow-setup` to connect the vault and register project metadata. In a new project session, select `tow-query` and send:

```text
My vault is /absolute/path/to/vault. Find project notes about RAG by category
or concept, excluding superseded documents. Search both this project and the
connected vault, read matching notes before summarizing them, and return their
source, paths, match reasons, and count. Do not modify files.
```

Search works without project registration or dictionaries; project tagging requires project `.tow/` metadata. The personal connection lives in `$TOW_VAULT` or `~/.tow/config.json`, never in project files. A vault containing the current directory takes precedence over either personal connection; use `--root` to select explicitly. Inside a vault, queries remain vault-only. For optional vault organization, `tow-setup` asks whether you want PARA and preserves your existing layout/schema. New vault settings live in `tow/config.json`; older `.tow/` and legacy 0.4.x vaults remain readable until migrated to `tow/`; migration carries legacy Markdown rule documents into `tow/tags.md` / `tow/categories.md`, so update links to the old files if they are removed. See the [setup guide](docs/installation.md#configure-the-vault) and [project connection instructions](docs/installation.md#connect-a-vault-to-a-project).

## CLI and setup checks

The helper uses `npx --yes tag-ontology@0.3.2`; npm fetches that exact version when needed. Manual helper commands use the installed `scripts/tow.py` path. The name `tow` in the conventions is shorthand for that path. For project commands, run it from the project; vault-targeted commands may use `--root <vault>`.

Neither TOW 0.5.10 nor `tag-ontology` 0.3.2 has a `doctor` command. Start with:

```bash
python3 --version
node --version
npx --yes tag-ontology@0.3.2 --version
```

Run TOW `lint` only for adopted TOW metadata; dictionary checks apply only to initialized ontology features. Missing optional metadata/dictionaries are not installation failures. Then follow the [setup checks](docs/installation.md#check-the-setup) to verify the installed plugin, configuration, dictionaries, and note tags. `lint` covers classification fields and tag counts; the check skill adds the note-by-note formatting/reference review. A clean lint result alone does not cover every skill check.

## Documentation

- [Installation, vault settings, and troubleshooting](docs/installation.md)
- [Vault conventions and helper commands](docs/methodology.md)
- [Content preservation](docs/preservation.md) and [optional post-curation](docs/post-curation.md)
- [Evaluation and verification limits](docs/evaluation.md)

Detailed guides are maintained in English and shared by every README edition.

## Contributing

Bug reports, focused fixes, documentation improvements, and translation corrections are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, checks, and the distinction between skill references and reader translations. Use the [issue forms](https://github.com/NamhyeonKo/tag-ontology-wiki/issues/new/choose) to report a bug or suggest a feature.

## Support

TOW is free and open source. If it saves you time, you can [buy me a coffee](https://buymeacoffee.com/namhyunko).

## License

[MIT](LICENSE)
