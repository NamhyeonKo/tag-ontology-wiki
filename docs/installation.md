# Install and use TOW from GitHub

[Overview](../README.md) · [Contributing](../CONTRIBUTING.md)

TOW adds twelve skills to Claude Code, Codex, and Google Antigravity. Vault-maintenance skills work inside an Obsidian vault; `tow-query`, project tagging, and `tow-send-vault` also support a separate project workspace connected to a personal vault. Installation uses this public repository; no official-directory submission is required.

## Install in your host

Have Git and Python 3.10+ available to the host. Node.js 22.18+ and npm/npx are needed for optional `tag-ontology` parsing/ontology features; file search/body work can run without them. The first CLI run may download `tag-ontology@0.2.0` from npm. TOW uses the host's model, account, file permissions, and privacy settings; it has no separate service or API key.

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

Start a new host session after installation. For vault maintenance, open the Obsidian vault as the workspace. For cross-project use, open the project as the workspace and connect the vault as described below. TOW never stores a personal vault path in project metadata. TOW's guarantees apply to its own workflows and commands, not arbitrary shell commands; shell can bypass file-tool rules. Host sandboxing or OS permissions are the process-level enforcement boundary.

## Confirm the plugin loaded

Run the relevant command in your terminal:

| Host | Inspect the installation | Select a skill in a new session |
| --- | --- | --- |
| Claude Code | `claude plugin details tow@tag-ontology-wiki` | `/tow:tow-query` |
| Codex | `codex plugin list --json` | Use `$` or `/skills` and select `tow-query` |
| Antigravity | `agy plugin list --json` | `/tow-query` |

Confirm `tow`, version `0.5.5`, and its enabled state where shown. In the new session's skill selector, check for `tow-query`, `tow-send-vault`, `tow-check`, `tow-tag-suggest`, and `tow-tag-sync`, plus `tow-classify`, `tow-link`, `tow-edit`, `tow-merge`, `tow-review`, `tow-ingest`, and `tow-setup` (twelve total). Claude's `plugin details` lists its components; `claude plugin list --json` also gives the installed path and enabled state. Codex's install result gives `installedPath`; its plugin list is not a skill inventory. Antigravity's list gives `path` and the discovered skills.

## Configure the vault

TOW 0.5.5 reads `<vault>/tow/config.json` with `"kind": "vault"`. Existing `<vault>/.tow/config.json` and legacy vaults remain readable until migrated. Without a config file, the effective legacy-compatible defaults are:

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
  "misc": "99_Etc",
  "scope": "para"
}
```

A legacy `tow.json` is merged over these same defaults. `tow config` prints effective settings without a `kind` field. A `tow/config.json` vault uses `tow/tag-dictionary.json` and `tow/category-dictionary.json` defaults; older `.tow/config.json` vaults use `.tow/tag-dictionary.json` and `.tow/category-dictionary.json`. Legacy 0.4.x vaults remain readable from root `tow.json` and their root dictionaries until migrated. Only override values that differ in your vault. For example, a vault with `Projects`, `Areas`, `Resources`, `Archives`, project history in `superseded`, and dictionaries in `meta/` can use:

```json
{
  "kind": "vault",
  "projects": "Projects",
  "areas": "Areas",
  "resources": "Resources",
  "archives": "Archives",
  "projectArchive": "superseded",
  "tagDictionary": "meta/Tag-Dictionary.json",
  "categoryDictionary": "meta/category-dictionary.json",
  "inbox": "Capture",
  "attachments": "Support/media",
  "dailyNotes": "Areas/journal",
  "misc": "Support"
}
```

The four PARA folder names identify direct children of the vault root. `projectArchive` names history folders inside projects, such as `Projects/Search/superseded/`; matching folders at any depth in the search scope count. Dictionary paths name files relative to the vault root; a trailing `/` is rejected. Both dictionaries are JSON; the tag dictionary stores concepts and the category dictionary stores registered classifications. Their formats are in the [conventions](methodology.md).

`inbox` and `misc` also name direct-child folders. `attachments` and `dailyNotes` are nonempty paths inside the vault; absolute paths, `..`, and the vault root are rejected. Set them explicitly: changing another key does not rewrite them. They control intake, attachment moves, and link exclusions without widening default PARA searches.

`scope` sets what pathless searches and checks read. `para` (the default) reads only the four PARA folders. `vault` reads every note folder, including inbox/support/history. Use it for your own layout; this does not adopt the TOW schema. Private/ignored scope must still be filtered before scans.

Vault files in visible `tow/` sync with Obsidian Sync and appear in Obsidian's file browser. If you prefer to hide TOW manuals and dictionaries from search and graph, optionally add `tow/` to Obsidian's “Excluded files” setting. Existing `.tow/` and legacy vaults remain usable; update the Tag Ontology plugin to 0.10.1 or later on every device before running `tow migrate` to move them to `tow/`. The plugin has its own “Dictionary path” setting; align it with TOW's configured `tagDictionary`. Plugin 0.10.1 and later automatically detect `tow/tag-dictionary.json` and older defaults, but a custom path must be configured in both places. If you add or rename tags in the plugin's sidebar, turn on its “Kebab-case tag names” setting (0.11.0 or later) so new names follow the `--names kebab` rule TOW checks.

### Start a new or existing vault

Installation creates no vault files. Search/body work can start immediately without frontmatter or dictionaries. Select `tow-setup` when you want configuration; the agent inspects names only and **asks whether you want PARA**, including for an empty vault.

| Your choice | Setup |
| --- | --- |
| PARA | Reuse/map existing folders or propose missing ones; select optional inbox/dictionaries separately |
| Own layout, including an empty vault | Keep folders and notes; propose only `{"scope": "vault"}` for helper searches (`init --scope vault` writes it) |

Nothing is written before approval. PARA, the TOW metadata schema and tag ontology are independent choices. Setup does not move notes or add properties. Filing into a selected destination belongs to `tow-ingest` in either layout.

The helper retains the PARA starter bundle for compatibility: plain `init` in a vault without settings previews the PARA folders. For your own layout, `init --scope vault` records `"scope": "vault"` in the new `tow/config.json` and creates no inbox or PARA folders; `--dictionaries` explicitly adds the two starter dictionaries. `--scope` only applies while the vault has no TOW settings; afterwards, change `scope` in the config file.

```bash
"$TOW" --root "$VAULT" init                                # PARA preview; no writes
"$TOW" --root "$VAULT" init --scope vault                  # own-layout preview; no writes
"$TOW" --root "$VAULT" init --scope vault --dictionaries   # opt-in dictionary preview
"$TOW" --root "$VAULT" init --scope vault --dictionaries --apply
```

Run `--apply` only after approving every previewed item. To create a smaller subset, use the skill's exact approved file plan instead of initializing extra assets.

## Connect a vault to a project

Use a personal connection so project metadata can be shared without exposing your vault path. Outside any vault, a project session can resolve the vault from `TOW_VAULT` and then `~/.tow/config.json` (the environment variable takes precedence). Inside a vault, that nearest ancestor vault takes precedence over either personal connection; use `--root` when you want to choose explicitly. The personal config has the form `{"kind":"user","vault":"<absolute path>"}`. It is outside the project and must not be committed.

From the project, select `tow-setup` and let it inspect names and configuration only. If no vault is connected, first select a vault you identify and set it up there. Then preview the connection and apply it only after approval:

```bash
TOW="/absolute/path/to/installed/tow/scripts/tow.py"
"$TOW" connect /absolute/path/to/vault
"$TOW" connect /absolute/path/to/vault --apply
"$TOW" connect
```

Project metadata is separately registered with the user's choice of local or shared mode. Project init writes `.tow/.gitignore`: `*` in local mode keeps all of `.tow/` out of Git, and `documents.local.json` in shared mode keeps only the tags of untracked documents out. To share a local project later, replace `*` with `documents.local.json`; deleting the file would let those tags be committed. Setup proposes excludes only for dependency/build folders found in the project and never edits the project's own `.gitignore`, project documents, or host settings. From a project, `tow-query` searches both the connected vault and current project, and `tow-send-vault` can create a new vault note from selected content after approval. Inside a vault, queries remain vault-only.

### Host access suggestions

These are permission hints for users to apply; TOW does not edit host configuration. Grant read access only to the intended vault scope, and grant writes only to the configured note folder if sending is wanted. Substitute the actual vault root and note folder:

- **Claude Code:** reads: `Read(//<vault>/**)` or `permissions.additionalDirectories`; sending: `Edit(//<vault>/<note folder>/**)` or per-call approval.
- **Codex:** reads outside the workspace are not blocked by the default sandbox. Writes require the configured vault note folder in `sandbox_workspace_write.writable_roots` or approval. Permission profiles are beta and do not cover MCP.
- **Antigravity:** `read_file(<vault>)`; only if sending is wanted, `write_file(<vault>/<note folder>)` permission rules.

Skills and TOW do not provide an OS-level access boundary. Their guarantees cover TOW's own workflows and commands, not arbitrary shell commands; shell can bypass file-tool rules. Only host sandboxing or OS permissions can constrain processes. Do not bypass an access denial; report the applicable host hint and stop.

## Move vault files to `tow/`

Vaults using `.tow/` or legacy 0.4.x root files remain readable without moving. Before migrating, update the Tag Ontology Obsidian plugin to **0.10.1 or later on every device** so it finds `tow/tag-dictionary.json`. Preview with `tow --root <vault> migrate`; after reviewing the complete plan, apply with `tow --root <vault> migrate --apply`. Migration copies/converts files into visible `tow/`, appends root `Tag-Dictionary.md` and Markdown category rule-document text into `tow/tags.md` and `tow/categories.md`, and keeps the old files. From then on TOW reads and writes only `tow/`: the kept originals (root `Tag-Dictionary.json`, `.tow/`) no longer change, so edit and point the plugin at `tow/tag-dictionary.json`. If the vault has no PARA folders (for example, one used only with the Tag Ontology plugin), the preview warns that the migrated search scope is empty; choose `migrate --scope vault` to record `"scope": "vault"` in the new `tow/config.json`, or create the PARA folders with `init` afterwards. `--scope` applies to a root-file vault whose `tow.json` does not already set it; in a `.tow/` or `tow/` vault, edit `scope` in its config file. After removal, update notes that link to those original Markdown files. Only after the user confirms the plugin is 0.10.1 or later on every device, removal is a separate approved operation: preview `migrate --remove-legacy`, then apply only after verifying the copies. This includes `.tow/` originals and any legacy root files.

## Check the setup

TOW 0.5.5 and `tag-ontology` 0.2.0 have no `doctor` command. Use the applicable read-only checks below. Skip TOW lint on custom schemas; skip dictionary checks when no ontology is selected. Unavailable/inapplicable checks are not passes or installation failures.

**1. Runtime versions — terminal (Node/npm only for ontology/parsing):**

```bash
python3 --version
node --version
npx --yes tag-ontology@0.2.0 --version
```

The last command should print `0.2.0`. It checks that the npm CLI can launch; it does not check your vault.

**2. Installed helper — terminal:**

`--help` and `config` apply to every vault. The `lint`/dictionary commands below apply only to the adopted, initialized TOW features, not arbitrary custom fields.

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
| `--help` | The Python helper starts and lists vault and project commands, including `connect`, `project`, `send`, `lookup`, and `migrate` |
| `config` | Prints merged settings; compare them with actual folders/dictionaries. This command does not validate that those files exist. |
| `lint` | Parses notes through the CLI and checks classification values, field scope, duplicate tags, and tag counts; prints `OK` when clean, or `no notes checked` when the scan read none |
| `ontology check --json` | Checks the tag dictionary; a clean result has `ok: true` and empty `issues` |
| `ontology usage --json` | Reads the configured scope minus exclusions and compares frontmatter/body tags with the dictionary; inspect findings and actual read coverage |

These commands do not edit the vault. npm may write its package cache. Convention/tag findings concern the vault contents and do not by themselves mean plugin installation failed. Notes without frontmatter are skipped by the helper's convention lint; `tow-check` inspects them directly. Formatting, links, and the meaning of a tag hierarchy still need the skill's review.

The pathless checks above scan the configured search scope (PARA folders by default). With `scope: para` and no PARA folders, that scope is empty: `lint`, `find`, `ontology show` and `ontology scan` warn and name the fix for the vault's layout, pathless `ontology usage` stops with exit code 2 instead of listing every tag as unused, and `lookup` lists the vault under `unavailable` instead of returning no results. Naming a folder or note still works. The CLI does not apply `.gitignore` automatically. Use exact approved paths for `lint` and `ontology scan`. `usage <paths>` still reads the whole configured scope minus exclusions for unused-tag detection, and `show` does so even without `--notes`; run them only when that full read scope is authorized or safely excluded beforehand. Otherwise inspect scoped `scan` and relevant dictionary entries, and report aggregate checks unavailable. `find` has no path/exclusion option; use scoped `ontology scan` when the whole search scope is not authorized. See [scope rules](methodology.md#scope-before-reading-note-contents).

You can ask the host to run the same checks:

```text
My vault is /absolute/path/to/vault. Use the installed TOW helper to check
the runtime versions, effective configuration, dictionary integrity, and note
tag usage. Verify the configured paths exist. Report findings without editing files.
```

## Preservation and post-curation

The default maintenance path changes selected frontmatter and formatting only. Markdown, math, code and table **contents** remain unchanged; ambiguous repairs are reported. `tow-check` does not rewrite sentences, simplify formulas, fix algorithms or fill missing cells. User rules/templates govern presentation, including existing table alignment.

For a metadata-only edit, first choose a scratch location preserving the source privacy/ignore boundary. In Git-managed vaults, prospective snapshot paths must pass `git check-ignore` before copying; hidden names alone are insufficient. If protection is missing, propose it before copying or changing ignore rules. After approval, set `BATCH` to that protected vault-relative path, prepare independent snapshots and run:

```bash
"$TOW" --root "$VAULT" verify-body "$BATCH/before.md" "$BATCH/candidate.md"
```

Exit 0 means equal body bytes, 1 means changed body, and 2 means an invalid/unavailable comparison. Both files must be inside the vault and independent (no self/hard-link comparison). This command works without Node, dictionaries or `tow.json`; it does not validate YAML changes or semantic equivalence of format repairs. See the [exact preservation contract](preservation.md) for operation-specific checks.

`tow-edit`, `tow-merge`, `tow-ingest` and `tow-review` retain their names as optional [user-guided post-curation](post-curation.md). Name the operation, targets and your actual template/rules. Verbatim filing needs only the chosen destination; it does not require a writing template. Body generation, filled-section rewriting, merge/split and hub creation are separate explicit choices, never side effects of cleanup/lint/review.

## Use the skills

Explicitly select the skill, then supply the vault root and the files/folders to work on. Claude prefixes every skill with `/tow:`, Antigravity uses `/`, and Codex offers them in `$` or `/skills`.

| Skill | Example request after selection |
| --- | --- |
| `tow-setup` | “Set up /absolute/path/to/vault. Ask whether I want PARA; preserve my layout and create only approved assets.” |
| `tow-query` | “Find project notes about RAG by category or concept. Exclude superseded documents. Read the matches and give paths and count.” |
| `tow-check` | “Check these two notes for frontmatter, headings, tables, math, and broken references. Report first; do not edit.” |
| `tow-tag-suggest` | “Suggest concept tags for this note. Separate additions and removals, explain why, and wait for my choice.” |
| `tow-tag-sync` | “Check this folder's tags against the dictionary. Propose new entries and alias cleanup, review broader + narrower tag pairs against each note's headings, then wait for approval.” |
| `tow-classify` | “Propose a category for these notes. Register it first; ask separately before retroactive changes.” |
| `tow-link` | “Link existing mentions in this folder. Show targets, skipped matches, ambiguity and missing targets before editing.” |
| `tow-edit` | “Use Templates/Concept.md to fill only the empty Examples section from this selected source; preserve all filled content and metadata.” |
| `tow-merge` | “Compare these two notes. Show strategies, retained facts and losses; wait for my case-by-case choice.” |
| `tow-review` | “Review this domain for ownership, duplicates, missing hubs and isolation. Propose fixes before changing files.” |
| `tow-ingest` | “Plan intake of the configured inbox's top-level captures, including metadata, destinations, attachments and links.” |
| `tow-send-vault` | “Send this selected project note to my connected vault as a new note. Preserve the selected body exactly and show the complete proposal before writing.” |

A clear `tow-edit` request authorizes its selected body edit only when the user's rules/template/source and preservation boundary are already established. Missing rules produce a question, never a bundled-template fallback. A review remains read-only until a concrete follow-up operation is selected. Other modifying workflows propose first. Intake/review batch approval still preserves merge-by-merge selection, separate discard confirmation, and the separate retroactive-classification decision. Ignored/private captures need explicit selection, and the plan must disclose any move into tracked/public scope. Shared attachments stay in place unless separately approved.

For example, in Claude Code select `/tow:tow-tag-suggest`, then name the note. After its proposal, select exact changes: “Add only `semantic-chunking` and remove `information-retrieval`; keep the other tags and body.” `tow-tag-sync` uses a dictionary plan before applying approved changes. Approval is part of the skill instructions; actual tool access and permission prompts remain the host's responsibility.

For manual searches:

```bash
"$TOW" --root "$VAULT" find ai/rag --type project
"$TOW" --root "$VAULT" find --type project --status in-progress
"$TOW" --root "$VAULT" ontology show rag --notes --json
```

The first command filters the `category` field; the third follows concept tags and their narrower concepts. The sample values must exist in your own dictionaries. Note scans default to the configured search scope; In PARA scope, `find` and ontology `show` skip project archive folders unless you add `--all`. Free-form scope keeps history-named folders. `find` covers frontmatter tags only; ontology `scan` separates frontmatter/body tags, while `show` and `usage` aggregate both. `show --exact` narrows note paths, not read scope or rollup counts; use the scope rules above before ontology lookups. Natural-language `tow-query` prefers native [Obsidian CLI search](https://obsidian.md/help/cli) for properties/body tags/text and falls back to scoped file search, then verifies exact conditions. It works without dictionaries or setup, preserves custom properties and separates inferred candidates. See [query behavior](../skills/tow-query/SKILL.md).

## Update

Run these commands in your terminal. They update the installed plugin; they do not migrate your vault or run a TOW editing workflow.

### Claude Code

```bash
claude plugin update tow@tag-ontology-wiki
claude plugin details tow@tag-ontology-wiki
```

Third-party marketplaces have automatic updates disabled by default. To enable them, open `/plugin` in a Claude Code session, select the marketplace on the Marketplaces tab, and enable auto-update. A shell `claude plugin marketplace update` refreshes catalog listings alone; use the plugin update command above to update TOW. Claude caches by plugin version, so published package changes require a version bump to reach existing installations through ordinary updates. See [Claude Code's update guidance](https://code.claude.com/docs/en/discover-plugins#keep-plugins-updated).

### Codex

```bash
codex plugin marketplace upgrade tag-ontology-wiki
codex plugin add tow@tag-ontology-wiki
codex plugin list --json
```

Refresh the configured Git marketplace before adding TOW from that snapshot. The marketplace refresh and plugin installation are distinct operations; repeating `add` alone is not an explicit marketplace refresh. Inspect the returned installation information rather than assuming an older loaded session has changed. See the [official OpenAI documentation](https://developers.openai.com/plugins/build/plugins) for marketplace management.

### Antigravity

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
agy plugin list --json
```

The checked Antigravity CLI has no separate plugin update subcommand. Install again from the same GitHub source and inspect the resulting version. See the [Superpowers Antigravity instructions](https://github.com/obra/superpowers#antigravity) for the same host-native reinstall pattern.

After updating, start a new host session and [confirm the plugin loaded](#confirm-the-plugin-loaded). If the old version remains, record the host version, command output, and installed plugin version before reporting it; a successful catalog refresh alone does not prove the installed plugin advanced.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Host has no plugin command | Check the host's help/version and use a client with plugin support |
| Skill does not appear | Confirm TOW is enabled, start a new session, and explicitly select it |
| Missing dictionary / unexpected search results | Check vault targeting and scope; missing optional dictionaries do not block search. Preview selected dictionary setup with `tow init --dictionaries` |
| `search scope is empty` warning or error | The default `para` scope found no PARA folder. Keep your layout with `"scope": "vault"` (`init --scope vault`, `migrate --scope vault`, or the config file), or preview the PARA folders with `tow init` |
| `npx` not found / npm failure | Check Node/npm on the host's `PATH`, registry access, and cache permissions; read the npm error before changing anything |
| `send destination must be … under a configured note folder` | `tow send` writes only under the folders named by `projects`, `areas`, `resources` and `inbox`, also with `"scope": "vault"`. To send into your own folder, set one of those keys to its name in the vault config |
| Host quota or permission denial | Resolve it in the host; keep approval scoped to the intended vault and command |

The examples were checked with Claude Code 2.1.310, Codex CLI 0.159.2, and Antigravity CLI 1.4.12 on macOS. See [evaluation](evaluation.md) for synthetic-vault results and limits. Installation command references: [Claude Code](https://code.claude.com/docs/en/plugins/publish), [Codex](https://developers.openai.com/plugins/build/plugins), [Antigravity](https://antigravity.google/docs/plugins).
