# TOW — Tag Ontology for Wiki

An agent skill plugin for managing documents **inside your Obsidian vault**: search notes, manage frontmatter, and fix formatting while preserving content. Runs in Claude Code, Codex, and Google Antigravity with the vault as the workspace.

[English](README.md) · [한국어](readme/README.ko.md) · [简体中文](readme/README.zh-CN.md) · [繁體中文](readme/README.zh-TW.md) · [日本語](readme/README.ja.md) · [Español](readme/README.es.md) · [Français](readme/README.fr.md)

> **Version:** 0.4.1.

## Overview

Ordinary maintenance preserves prose, math/code contents and table values; only selected frontmatter and formatting change. Optional post-curation follows your own templates and explicit operation choices. TOW works with existing vault layouts, including notes without frontmatter. Its optional tag-first LLM Wiki recipe has three independently selectable layers:

- **PARA folders**: Projects, Areas, Resources, Archives.
- **Classification fields** in frontmatter: `category`, `type`, `status`, `kind`.
- **A concept tag ontology**: a tag dictionary with aliases and broader/narrower relations.

Choose PARA during setup or keep your own folders. Ordinary search/body work needs neither dictionaries nor metadata cleanup. Queries use Obsidian CLI first, scoped file search when needed, then content verification; available properties improve precision. The full conventions are in [docs/methodology.md](docs/methodology.md).

TOW installs eleven workflows into your local coding agent. You name the vault and notes; the agent reads the relevant files, searches classifications and concept tags, and proposes scoped changes for your approval. The files stay in your Obsidian vault.

The package contains skills, shared conventions, and the Python helper [`scripts/tow.py`](scripts/tow.py). That helper checks classification rules and calls the [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) npm CLI for note parsing, tag queries, and dictionary validation/changes. Your agent host supplies the model and file tools.

TOW uses the Tag Ontology CLI to query tags and validate/manage dictionaries. Install the [Tag Ontology plugin for Obsidian](https://github.com/NamhyeonKo/obsidian-tag-ontology) ([community plugin page](https://community.obsidian.md/plugins/tag-ontology)) alongside TOW to visually explore the tag hierarchy and relationships you manage in a graph.

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
| `tow-setup` | Choose PARA or an existing layout; optionally enable dictionaries | Lists top-level folders only; creates folders/dictionaries/`tow.json` after approval, never moves notes |
| `tow-query` | Find documents using natural-language conditions, custom properties, tags or text | Read-only; CLI first, scoped file fallback, verified matches and separate inferred candidates |
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

Open the vault as your host's workspace. In a new session, select `tow-query` using the host-specific invocation above, then send:

```text
My vault is /absolute/path/to/vault. Find project notes about RAG by category
or concept, excluding superseded documents. Read matching notes before
summarizing them and return their paths and count. Do not modify files.
```

You can search immediately without setup. For optional organization, select `tow-setup`; it asks whether you want PARA and preserves your existing layout/schema. TOW reads `tow.json` at the vault root; omitted settings use the defaults in the [setup guide](docs/installation.md#configure-the-vault). Installation does not create or migrate a vault.

## CLI and setup checks

The helper uses `npx --yes tag-ontology@0.1.2`; npm fetches that exact version when needed. Manual helper commands use the installed `scripts/tow.py` path. The name `tow` in the conventions is shorthand for that path.

Neither TOW 0.4.1 nor `tag-ontology` 0.1.2 has a `doctor` command. Start with:

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.2 --version
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
