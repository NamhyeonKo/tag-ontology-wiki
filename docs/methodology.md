# TOW conventions

Shared rules for scope, approval, content preservation and the `tow` helper. Each skill reads this document before it starts work; the step-by-step procedures live in the skills. The optional TOW organization recipe (§1–6: PARA folders, classification, concept tags, frontmatter, note body and the tag dictionary) is in [recipe.md](recipe.md); skills that apply it read that file as well.

## Working scope

TOW works across a vault, a project, and a personal connection between them:

- A **vault** is identified by `tow/config.json` with `"kind": "vault"`; existing `.tow/config.json` vaults and legacy 0.4.x root markers remain readable until migrated. Legacy root markers are `tow.json`, a non-empty root `Tag-Dictionary.json`, or root `Category-Dictionary.md`; an empty `{}` tag dictionary alone is the plugin's starter and is not a legacy marker.
- A **project** is the current Git repository or working directory. Its optional `.tow/config.json` has `"kind": "project"` and may set document scope. Project documents are never edited by TOW's project workflows; tags and hashes live in project `.tow/` metadata.
- A **connection** is personal: `$TOW_VAULT` or `~/.tow/config.json` with `"kind": "user"` identifies the vault from a project session when the current directory is not inside a vault. `tow connect <vault>` previews it; `tow connect <vault> --apply` saves it. No project file stores the personal vault path.

From a project, `tow-query` searches the connected vault and current project. Inside a vault, it searches only that vault. Project tagging writes only `.tow/` metadata. `tow-send-vault` can create a new vault note from selected project content after approval; by default, the selected body is preserved exactly. Vault-maintenance skills remain vault-only. See the [installation guide](installation.md) for host access suggestions and the limits of TOW's safety model.

### Vault and project layouts

The current vault layout stores `config.json`, `tags.md`, `tag-dictionary.json`, `categories.md`, and `category-dictionary.json` in visible `tow/`. Manuals contain rules; dictionaries contain data. Older vaults using `.tow/` or the legacy root layout remain readable until migrated with `tow migrate`. Migration carries root `Tag-Dictionary.md` and Markdown category rule documents into `tow/tags.md` and `tow/categories.md`; after removing old files, update notes that link to those source documents. The project `.tow/` contains `config.json`, `tags.md`, `tag-dictionary.json`, and `documents.json`; shared projects may also use `documents.local.json` for metadata about local files. Project init writes `.tow/.gitignore`: `*` in local mode keeps all of `.tow/` out of Git, and `documents.local.json` in shared mode keeps only the tags of untracked documents out while the rest is committed. To share a local project later, replace `*` with `documents.local.json`; do not delete the file. Projects set up before 0.5.5 keep their `info/exclude` entry, which still works. TOW never edits the project's own `.gitignore` or project document content.

Vault and project configuration paths are relative to their respective roots. Vault dictionary defaults are `tow/tag-dictionary.json` and `tow/category-dictionary.json`, but can be set elsewhere. Visible vault files sync with Obsidian Sync; optionally add `tow/` to Obsidian's “Excluded files” setting to hide it from search and graph. The Tag Ontology Obsidian plugin has its own dictionary path setting, which must match TOW's configured tag dictionary path.

## Vault compatibility

**Use the user's vault as it is.** PARA, TOW frontmatter and the two dictionaries are independent, optional choices. Searching, reading, editing, linking, merging and reviewing notes work without them. Setup is not a prerequisite for those operations.

- Determine applicable conventions from vault instructions, existing templates/notes within the authorized scope, and the user's choices. Field names such as `status` alone do not mean the TOW schema was adopted. The [TOW recipe](recipe.md) (§1–6) describes the PARA layout, schema and style; apply its constraints only where adopted. Preserve custom fields, values, ordering and prose style elsewhere.
- Ask whether the user wants PARA during setup; reuse an explicit prior choice. Folder names or an empty vault do not imply consent. Existing layouts stay in place unless a move is separately selected.
- Missing frontmatter is valid in a vault that does not require it. Do not add classification fields, `tags: []`, `created`, `updated`, or dictionaries as a side effect of body/link/format work. Apply the vault's established date policy when present; otherwise leave metadata unchanged. These rules qualify every skill's date/schema instruction below.
- Read existing dictionaries when relevant, not as a universal startup gate. Tag suggestions can be unverified; classification/ontology adoption proposes only its missing prerequisites and waits for approval before creating them. Generic searches and body work continue without those features.
- `tow lint` checks **TOW conventions**, not arbitrary vault schemas; run it only for notes using that schema and with its category dictionary available. `ontology usage/check` require the tag dictionary and apply only to the selected ontology work. Report unavailable/inapplicable checks separately from passing checks. Use direct Markdown/reference/preservation checks for generic notes; unrelated pre-existing lint findings do not block an approved body edit.
- Resource, Area and hub describe content roles in ownership decisions, not required folders or property values. Use the user's destinations, navigation and metadata. A missing tag/category does not by itself make a note isolated.

## Preservation and post-curation

Ordinary maintenance changes selected frontmatter and Markdown/math/code/table **formatting**, preserving their content under the [preservation contract](preservation.md). Prefer small literal patches and deterministic checks; model confidence or an unchanged-looking render is not proof. Metadata-only changes use independent snapshots and `tow verify-body` before final replacement.

Body writing, merges, intake transformations and domain aftercare require an explicit selected operation under the user's own rules/templates. Read the [post-curation contract](post-curation.md) when using `tow-edit`, `tow-merge`, `tow-ingest` or `tow-review`. Generic cleanup/lint/review never authorizes body generation, summaries, deletion, split/merge or automatic hub creation. Missing or ambiguous rules produce a question/proposal, with no body changes.

## Search policy

For every skill's note discovery, use **CLI first → scoped file search when unavailable or insufficient → read/verify** as detailed in [tow-query](../skills/tow-query/SKILL.md). Natural language is the user interface; query syntax is internal. Existing properties, body tags, names, links and body content all provide evidence. Missing properties stay unknown; separate exact matches from inferred candidates. Dictionary/CLI failures and partial searches are not proof of absence. All methods obey the scope rules below before reading content.

## The `tow` command

`tow` is the executable Python 3 script `scripts/tow.py` in the installed plugin. Resolve the plugin root from the absolute path of this document: it is the directory above `docs/` (also two directories above the loaded `skills/<name>/SKILL.md`). Use that installed location, independently of the agent host or the vault's working directory. When `tow config` reports that a legacy or `.tow/` vault can be moved, tell the user once and offer the optional `tow-setup` move-to-`tow/` flow; continue the requested work without waiting for migration.

Run the helper from the relevant vault or project. Use `--root <vault>` for a vault-targeted command when needed. Replace `<plugin-root>` below with the installed plugin's absolute path, keep it in a variable, and quote it in zsh or bash:

```bash
TOW="<plugin-root>/scripts/tow.py"
"$TOW" config
```

| Command | What it does |
| --- | --- |
| `tow connect [<vault>] [--apply]` | Show the personal connection, preview a connection, or save it after approval in `~/.tow/config.json` |
| `tow config` | Print effective vault settings and their source; warn if the Tag Ontology plugin dictionary path differs |
| `tow category add <value> <description> [--apply]` | Preview/register a category dictionary entry; `--apply` writes it after approval |
| `tow init [--scope {para,vault}] [--dictionaries] [--apply]` | Preview/create missing vault files at the configured dictionary paths; in a vault without settings, `--scope vault` records the free-form scope and creates no PARA folders; in a free-form vault, `--dictionaries` opts into starter dictionaries. `--apply` never overwrites |
| `tow migrate [--scope {para,vault}] [--apply] [--remove-legacy]` | Preview/migrate a legacy or `.tow/` vault into `tow/`, carrying Markdown rule documents into the manuals; `--scope` records the search scope in the `tow/config.json` a legacy migration creates; removal of verified originals is separately approved |
| `tow project init --mode {local,shared} [--exclude GLOB] [--apply]` | Preview/register project `.tow/` metadata; writes `.tow/.gitignore` (`*` in local mode, `documents.local.json` in shared mode) |
| `tow project tag <changes> [--apply]` | Preview/apply approved document tags and project-only concepts; writes only project `.tow/` files |
| `tow project status` / `tow project files` | Report stale project metadata or list scoped Markdown paths by Git status (names only) |
| `tow project concepts <project_path>` | From inside a vault, show project-only concept additions for review |
| `tow lookup <tag> [--exact]` | Find notes matching a concept in the vault and current project; `--exact` excludes narrower concepts |
| `tow send <draft> <dest> --source <source> [--transformed] [--apply]` | Preview/create a new note under a configured vault note folder; never overwrite, and check the body against the source unless explicitly transformed |
| `tow verify-body <before> <after>` | Read-only exact body-byte comparison of two vault-local snapshots after metadata-only changes; no CLI/dictionary required |
| `tow lint [path…]` | Check classification fields and tag counts (recipe §3, §4). Prints `OK` when clean, `no notes checked` when the scan read no note |
| `tow find [<prefix>] [--type …] [--status …] [--kind …] [--tag …] [--all]` | Find vault notes matching every condition: category prefix, frontmatter fields and/or tag |
| `tow ontology <command> [arg…]` | Run the [`tag-ontology` CLI](https://github.com/NamhyeonKo/obsidian-tag-ontology) with the vault's settings |

The helper resolves the vault in this order: `--root` → nearest ancestor vault (`tow/config.json`, then `.tow/config.json`, then a 0.4.x marker) → `$TOW_VAULT` → `~/.tow/config.json`. The current vault wins over personal connections; `--root` is explicit. The legacy markers are `tow.json`, a non-empty `Tag-Dictionary.json`, or `Category-Dictionary.md`; an empty `{}` `Tag-Dictionary.json` alone is the plugin's starter, not a legacy marker. If no vault or personal connection is found, it errors with `no vault found; run tow-setup`. Upward searches stop below the home folder. There is no current-folder fallback and no inference from `.obsidian`; it never guesses from Obsidian's active vault. Vault-maintenance write commands remain vault-only; `tow lookup` and project workflows can run from a project. `tow ontology` adds the configured dictionary, `--root`, and `--names kebab`, and limits note scans to the vault search scope. In PARA scope, `show` also skips project archive folders; `--all` keeps them. `scan` requires no dictionary and exposes parsed custom frontmatter, separate frontmatter `tags` and `bodyTags`, and headings. `usage` and `show` count both tag representations; `find` and convention lint use frontmatter tags only. Dictionary `apply` never edits note tags or bodies.

### Scope before reading note contents

The helper/CLI does **not** automatically apply Git ignore or private-input rules. Before content searches or note scans, inspect those rules and determine the eligible paths. Names-only listings may discover candidates; content reads, `Grep`/`rg` and CLI parsing must use the filtered paths, or explicit exclusions. Filtering the results after a broad scan still reads the excluded files.

- For selected notes, pass those exact paths to `tow lint` and `tow ontology scan … --json`, including final verification. Keep dictionary-only `tow ontology check --json` separate.
- For an authorized folder search, pass its approved paths and private-subtree exclusions to the underlying scan/search, such as `tow ontology scan <folder> --exclude <private-subtree> --json`. Enumerate eligible files first when exclusions cannot express the selection.
- `tow find` scans the entire configured search scope; it has no path/exclusion argument. Use it only when that whole scan is authorized and contains no unselected private inputs. Otherwise parse an explicitly scoped `tow ontology scan` result and filter its fields. The same caution applies to pathless `lint`.
- `usage <paths>` still scans the whole configured scope minus explicit exclusions to compute `unused`; the positional paths restrict its per-note findings, not all reads. `show` also scans that scope even without `--notes`. Run either only when its entire effective read scope is authorized or exclusions safely remove every ineligible path before reading. Otherwise use exact-path `scan` and authorized dictionary lookup, and report aggregate checks unavailable. `unused` is not proof that an entry can be deleted; partial reads or parse failures limit that conclusion. `show --exact` restricts returned note paths, not its read scope or rollup counts.
- A body-edit request or a declined retroactive-classification proposal does not authorize a vault-wide verification search. Check only changed/selected paths; report other unresolved work without scanning it.

## Vault settings (`tow/config.json`)

Values that differ between vaults live in `tow/config.json`. A missing file or key uses the defaults below; older `.tow/` vaults and legacy vaults continue to work until migrated. Vault config includes `"kind": "vault"`. The four PARA folders, `inbox`, and `misc` name direct children of the vault root. `projectArchive` names a history folder inside a project; matching folders at any depth in the search scope count. Dictionaries, `attachments`, and `dailyNotes` are paths relative to the vault root. Set each path explicitly when the layout differs; changing `areas` or `misc` does not rewrite another setting.

```json
{
  "kind": "vault",
  "projects": "01_Projects",
  "areas": "02_Areas",
  "resources": "03_Resources",
  "archives": "04_Archives",
  "projectArchive": "archive",
  "tagDictionary": "tow/tag-dictionary.json",
  "categoryDictionary": "tow/category-dictionary.json",
  "inbox": "00_Inbox",
  "attachments": "99_Etc/attachments",
  "dailyNotes": "02_Areas/daily-notes",
  "misc": "99_Etc",
  "scope": "para"
}
```

Resolve configured workflow paths from `tow config` and the supplied vault root; defaults are suggestions until their roles are confirmed in a custom vault. `inbox` is the capture queue, `attachments` stores note-specific media, `dailyNotes` is the daily-note subtree, and `misc` holds support files. Helper searches use `"scope": "para"` by default for compatibility. `"scope": "vault"` includes every note folder (including inbox/support/history), excluding only the category dictionary unless explicitly selected. It does not adopt the TOW schema. Without setup, native CLI/file search still uses the user's authorized scope; do not constrain it to nonexistent default folders.

**An empty scope is not a result.** With `"scope": "para"` and no PARA folder, pathless helper scans read no note. `lint`, `find`, `ontology show` and `ontology scan` then print a `search scope is empty` warning, pathless `ontology usage` exits 2 without reading anything, and `lookup` lists `vault: search scope is empty…` under `unavailable`. Never report "no matches", `OK` or `unused` from such a run. The message names the fix for the vault's layout (`init --scope vault`, `migrate --scope vault`, or `scope` in the config file); which layout to use is the user's choice through `tow-setup`. Until then, pass exact approved paths or use scoped file search.

Before a move, inspect the vault's ignore/private rules. Ignored capture inputs require explicit path selection; include any change in tracked/public visibility in the plan before approval. Apply this rule to intake candidates and existing-note searches. In an adopted PARA layout, link targets and edits normally exclude inbox, daily notes, project history, misc and attachments. In a custom layout, use confirmed role exclusions and the user's scope; default names alone exclude nothing. Explicitly selected ordinary workflow exclusions may be included; private/ignored inputs still require explicit selection. If an attachment store overlaps a note root, exclude only the attachment subtree.

> **When available and relevant**: use the category dictionary as a classification/navigation index. Query the tag dictionary by relevant concepts/aliases rather than reading it whole. Missing dictionaries do not block ordinary work.

## 7. Shared rules

These apply to every TOW skill; skills don't repeat them.

- When `tow config` prints a migrate hint for a legacy or `.tow/` vault, tell the user once and offer the optional `tow-setup` move-to-`tow/` flow. Do not block the requested task while migration is pending.
- **Plan → approve → run**: for work that changes files, show a plan table first and run it after the user approves. Ask for approval once for the whole batch. Merges are approved case by case. A clear body-edit request proceeds directly only when its selected rules/source and preservation boundary are already established under the post-curation contract.
- **Delegation keeps the choices**: an intake/review batch approval covers its listed category registrations and link positions, but merges still need sequential case-by-case strategies, discarded facts need explicit confirmation, and retroactive classification needs its separate decision. A choice already stated explicitly settles that choice.
- **The approval gate stays**: "I'm in a hurry, just do it" or "I trust you" still gets one proposal and one confirmation.
- **Git commits and merges** happen only when the user asks for them in this task.
- **Deleting is separate from writing**: write the new file → verify it in a separate call → only then delete the original. When steps must share one command, chain them with `&&` so a failure stops the rest. Back up uncommitted inbox originals to a scratch directory before changing or deleting them. Before a merge or a delete, check that every fact has a new home.
- **Content preservation**: classification/tag edits preserve body bytes; selected link wrappers preserve displayed prose; format edits preserve prose, math/code payloads and table values under the preservation contract. Body transformations require a separate explicit post-curation scope and the user's rules/template. A formatting or review approval never expands into body rewriting.
- **Dictionary-backed changes go through registration**: when using TOW classification/ontology, register approved new values before use. Ordinary custom properties/tags do not require adopting a dictionary. The user still selects concept tags.
- **Verify before reporting done**: verify the changed paths under their adopted conventions. Run applicable lint/ontology checks as specified in Vault compatibility, and report each unavailable check honestly.
