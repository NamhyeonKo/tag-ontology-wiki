# Install and use TOW from GitHub

[한국어](installation.ko.md) · [Overview](../README.md)

TOW adds ten skills to a local agent host. The agent uses the bundled Python helper and the npm `tag-ontology` CLI to work on your Obsidian vault. Installation uses this public repository; no official-directory submission is required.

## Install in your host

Have Git, Python 3.10+, Node.js 22.18+, and npm/npx available to the host. The first CLI run may download `tag-ontology@0.1.2` from npm. TOW uses the host's model, account, file permissions, and privacy settings; it has no separate service or API key.

**Claude Code — run inside a Claude Code session:**

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

For Claude Code before 2.1.275, use these two commands instead:

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

**Codex — run in your terminal:**

```bash
codex plugin marketplace add NamhyeonKo/tag-ontology-wiki --ref main
codex plugin add tow@tag-ontology-wiki --json
```

**Antigravity — run in your terminal:**

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

Start a new host session after installation. Open your vault as the workspace, or grant the host access to it and include its absolute path in the request.

## Confirm the plugin loaded

Run the relevant command in your terminal:

| Host | Inspect the installation | Select a skill in a new session |
| --- | --- | --- |
| Claude Code | `claude plugin details tow@tag-ontology-wiki` | `/tow:tow-query` |
| Codex | `codex plugin list --json` | Use `$` or `/skills` and select `tow-query` |
| Antigravity | `agy plugin list --json` | `/tow-query` |

Confirm `tow`, version `0.2.0`, and its enabled state where shown. In the new session's skill selector, check for `tow-query`, `tow-check`, `tow-tag-suggest`, and `tow-tag-sync`, plus `tow-classify`, `tow-link`, `tow-edit`, `tow-merge`, `tow-review`, and `tow-ingest` (ten total). Claude's `plugin details` lists its components; `claude plugin list --json` also gives the installed path and enabled state. Codex's install result gives `installedPath`; its plugin list is not a skill inventory. Antigravity's list gives `path` and the discovered skills.

## Configure the vault

TOW reads `<vault>/tow.json`. Without it, the effective defaults are:

```json
{
  "projects": "01_Projects",
  "areas": "02_Areas",
  "resources": "03_Resources",
  "archives": "04_Archives",
  "projectArchive": "archive",
  "tagDictionary": "Tag-Dictionary.json",
  "categoryDictionary": "Category-Dictionary.md",
  "inbox": "00_Inbox",
  "attachments": "99_Etc/attachments",
  "dailyNotes": "02_Areas/daily-notes",
  "misc": "99_Etc"
}
```

Only override values that differ in your vault. For example, a vault with `Projects`, `Areas`, `Resources`, `Archives`, project history in `superseded`, and dictionaries in `meta/` can use:

```json
{
  "projects": "Projects",
  "areas": "Areas",
  "resources": "Resources",
  "archives": "Archives",
  "projectArchive": "superseded",
  "tagDictionary": "meta/Tag-Dictionary.json",
  "categoryDictionary": "meta/Category-Dictionary.md",
  "inbox": "Capture",
  "attachments": "Support/media",
  "dailyNotes": "Areas/journal",
  "misc": "Support"
}
```

The four PARA folder names identify direct children of the vault root. `projectArchive` names history folders inside projects, such as `Projects/Search/superseded/`; matching folders at any depth in the search scope count. Dictionary paths are relative to the vault root. The tag dictionary is a JSON object of concept entries; the category dictionary is a Markdown index of registered classifications. Their formats are in the [conventions](methodology.md).

`inbox` and `misc` also name direct-child folders. `attachments` and `dailyNotes` are nonempty paths inside the vault; absolute paths, `..`, and the vault root are rejected. Set them explicitly: changing another key does not rewrite them. They control intake, attachment moves, and link exclusions without widening default PARA searches.

Installation does not create dictionaries, folders, or frontmatter. For a vault that has not adopted these conventions, ask the agent to inspect the current layout and propose the required setup first. Approve any file creation or migration separately.

## Check the setup

TOW 0.2.0 and `tag-ontology` 0.1.2 have no `doctor` command. Use these read-only vault checks in order.

**1. Runtime versions — terminal:**

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.2 --version
```

The last command should print `0.1.2`. It checks that the npm CLI can launch; it does not check your vault.

**2. Installed helper — terminal:**

Use your host's installation information above to locate `scripts/tow.py`. Replace the two absolute paths below. Keep just the script path in `TOW`, and quote it when running it; this works in bash and zsh, including paths with spaces.

```bash
TOW="/absolute/path/to/installed/tow/scripts/tow.py"
VAULT="/absolute/path/to/vault"
"$TOW" --help
"$TOW" --root "$VAULT" config
"$TOW" --root "$VAULT" lint
"$TOW" --root "$VAULT" ontology check --json
"$TOW" --root "$VAULT" ontology usage --json
```

| Check | Meaning |
| --- | --- |
| `--help` | The Python helper starts and lists `config`, `lint`, `find`, and `ontology` |
| `config` | Prints merged settings; compare them with actual folders/dictionaries. This command does not validate that those files exist. |
| `lint` | Parses notes through the CLI and checks classification values, field scope, duplicate tags, and tag counts; prints `OK` when clean |
| `ontology check --json` | Checks the tag dictionary; a clean result has `ok: true` and empty `issues` |
| `ontology usage --json` | Compares scoped note tags with the dictionary; inspect unregistered, alias, and redundant broader-tag findings |

These commands do not edit the vault. npm may write its package cache. Convention/tag findings concern the vault contents and do not by themselves mean plugin installation failed. Notes without frontmatter are skipped by the helper's convention lint; `tow-check` inspects them directly. Formatting, links, and the meaning of a tag hierarchy still need the skill's review.

You can ask the host to run the same checks:

```text
My vault is /absolute/path/to/vault. Use the installed TOW helper to check
the runtime versions, effective configuration, dictionary integrity, and note
tag usage. Verify the configured paths exist. Report findings without editing files.
```

## Use the ten skills

Explicitly select the skill, then supply the vault root and the files/folders to work on. Claude prefixes every skill with `/tow:`, Antigravity uses `/`, and Codex offers them in `$` or `/skills`.

| Skill | Example request after selection |
| --- | --- |
| `tow-query` | “Find project notes about RAG by category or concept. Exclude superseded documents. Read the matches and give paths and count.” |
| `tow-check` | “Check these two notes for frontmatter, headings, tables, math, and broken references. Report first; do not edit.” |
| `tow-tag-suggest` | “Suggest concept tags for this note. Separate additions and removals, explain why, and wait for my choice.” |
| `tow-tag-sync` | “Check this folder's tags against the dictionary. Propose new entries and alias/broader-tag cleanup, then wait for approval.” |
| `tow-classify` | “Propose a category for these notes. Register it first; ask separately before retroactive changes.” |
| `tow-link` | “Link existing mentions in this folder. Show targets, skipped matches, ambiguity and missing targets before editing.” |
| `tow-edit` | “Fill only the empty Examples section in this named note; preserve its filled text, code and metadata.” |
| `tow-merge` | “Compare these two notes. Show strategies, retained facts and losses; wait for my case-by-case choice.” |
| `tow-review` | “Review this domain for ownership, duplicates, missing hubs and isolation. Propose fixes before changing files.” |
| `tow-ingest` | “Plan intake of the configured inbox's top-level captures, including metadata, destinations, attachments and links.” |

A clear `tow-edit` request authorizes its stated body edits immediately. Other modifying workflows propose first. Intake/review batch approval still preserves merge-by-merge selection, separate discard confirmation, and the separate retroactive-classification decision. Ignored/private captures need explicit selection, and the plan must disclose any move into tracked/public scope. Shared attachments stay in place unless separately approved.

For example, in Claude Code select `/tow:tow-tag-suggest`, then name the note. After its proposal, select exact changes: “Add only `semantic-chunking` and remove `information-retrieval`; keep the other tags and body.” The sync skill uses a dictionary plan before applying approved changes. Approval is part of the skill instructions; actual tool access and permission prompts remain the host's responsibility.

For manual searches:

```bash
"$TOW" --root "$VAULT" find ai/rag --type project
"$TOW" --root "$VAULT" find --type project --status in-progress
"$TOW" --root "$VAULT" ontology show rag --notes --json
```

The first command filters the `category` field; the third follows concept tags and their narrower concepts. The sample values must exist in your own dictionaries. Note scans default to the configured PARA scope; `find` and ontology `show` skip project archive folders unless you add `--all`. See [query behavior](../skills/tow-query/SKILL.md) for unions and intersections.

## Update and troubleshoot

For Claude Code, run `claude plugin update tow@tag-ontology-wiki`. For Codex, refresh `codex plugin marketplace upgrade tag-ontology-wiki`, then run `codex plugin add tow@tag-ontology-wiki`. Antigravity's current CLI has no separate update subcommand; use its GitHub install command to install the package again. Inspect the resulting version and start a new session. Claude caches by plugin version, so ordinary updates require a version bump to pick up a changed package.

| Symptom | Check |
| --- | --- |
| Host has no plugin command | Check the host's help/version and use a client with plugin support |
| Skill does not appear | Confirm TOW is enabled, start a new session, and explicitly select it |
| Missing dictionary / unexpected search results | Check the absolute vault root, `tow config`, existing dictionary paths, PARA scope, and project archive settings |
| `npx` not found / npm failure | Check Node/npm on the host's `PATH`, registry access, and cache permissions; read the npm error before changing anything |
| Host quota or permission denial | Resolve it in the host; keep approval scoped to the intended vault and command |

The examples were checked with Claude Code 2.1.310, Codex CLI 0.159.2, and Antigravity CLI 1.4.12 on macOS. See [evaluation](evaluation.md) for synthetic-vault results and limits. Installation command references: [Claude Code](https://code.claude.com/docs/en/plugins/publish), [Codex](https://developers.openai.com/plugins/build/plugins), [Antigravity](https://antigravity.google/docs/plugins).
