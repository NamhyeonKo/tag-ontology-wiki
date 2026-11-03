# Vault compatibility review — 2026-11-03

This is the 0.3.0 instruction snapshot committed in `d0cdc5d`. For the subsequent preservation/post-curation boundaries, see the [0.4.0 evaluation](preservation-evaluation.md). Coverage correction for the published 0.1.2 CLI: usage/show include frontmatter and body tags and scan the configured scope minus exclusions even with selected usage paths or without show note output. The current [scope rules](methodology.md#scope-before-reading-note-contents) supersede the earlier frontmatter-only/scoped-read assumptions below.

## Scope and outcome

Reviewed all eleven skill entry points, shared conventions and their Markdown, ownership, paper and structure references. The previous candidate inherited dictionary-first navigation, required TOW metadata and automatic date changes even in custom vaults. Those assumptions are now conditional on the user's adopted conventions. PARA, metadata and ontology are independent choices.

| Skill | Conflict found | Resulting behavior |
| --- | --- | --- |
| `tow-setup` | Empty vault implied PARA; free-form setup still created inbox/dictionaries | Ask about PARA explicitly; own layout can use configuration only; optional assets require selection |
| `tow-query` | Fixed metadata filters/dictionaries; no explicit native CLI fallback | Natural language → CLI query → eligible file search → predicate/content verification; custom and absent properties supported |
| `tow-check` | Missing frontmatter/custom values counted as TOW defects; mandatory lint | Use adopted schema/style; generic checks work without metadata; distinguish skipped validation |
| `tow-classify` | Fixed fields/values/dictionary assumed | Classify under the existing schema; explicit TOW categories retain registration/retroactive approval gates |
| `tow-edit` | Body edit added `updated` and imposed a template | Preserve custom metadata/absence and style; only established date policy applies |
| `tow-ingest` | Filing implied PARA, TOW metadata and dictionary reads | Use selected source/destination and existing schema; no automatic metadata/dictionary adoption |
| `tow-link` | Fixed role exclusions and automatic dates | Index actual filenames/aliases, honor confirmed scope and preserve custom properties |
| `tow-merge` | Metadata union imposed TOW schema/order | Preserve destination schema, resolve custom conflicts in the strategy, retain fact/deletion gates |
| `tow-review` | Hub creation required TOW metadata; isolation depended on tags/categories | Use actual links/hubs/tags/properties; content ownership works without classification |
| `tow-tag-suggest` | Dictionary lookup and ontology handoff unconditional | Suggest without a dictionary, mark vocabulary unverified; apply only selected tags/representation |
| `tow-tag-sync` | Missing dictionary blocked flow; unrelated lint required | Propose only its tag dictionary if selected; preserve plan/apply/conflict controls and disclose frontmatter-only coverage |

Authoritative rules are in [Vault compatibility](methodology.md#vault-compatibility), [search policy](methodology.md#search-policy), and each [skill](../skills/). `tow lint` remains a TOW-schema checker; it is not a validator for arbitrary custom schemas.

## Verification

- Before edits, an independent instruction-path evaluation of all eleven skills and pure-function probes reproduced the dictionary/schema/date conflicts. This was not a live run of eleven workflows.
- Four new setup/scope behavior tests failed against the previous helper before implementation. Seven dictionary-path cases also failed before adding relative-path and preflight symlink-boundary checks.
- Full suite with published `tag-ontology@0.1.2`: **91 passed**, including five real-CLI integration tests. Ruff lint/format and strict Pyright passed.
- Final independent review identified explicit nested-dictionary exclusion and initialization collisions/wrong object types/OS errors. Regression tests reproduced both; the fixes preserve selected nested paths and validate initialization targets before writes.
- The new real-CLI fixture confirms scans without dictionaries include no-frontmatter notes and notes in inbox/support/archive-named folders. Structured `find` keeps custom status values and archive-named matches; it still does not implement body-tag search.
- A fresh skill consumer executed two read-only queries in a synthetic free-form vault. The broad RAG query returned five eligible notes, including a body-only tag and support/archive folders. The exact `status: reading AND rating >= 4` request returned only `notes/RAG.md` (numeric rating 4), excluding a body YAML example and a lower rating.
- The same consumer filled only an explicitly selected empty section. Independent byte comparison confirmed that only `notes/RAG.md` changed, every original byte survived, custom frontmatter was identical and no dictionaries were created.

## Limits

Native Obsidian CLI commands/syntax were checked against [official CLI documentation](https://obsidian.md/help/cli) and [search documentation](https://obsidian.md/help/plugins/search). The synthetic vault was deliberately unregistered; queries used the real tag-ontology scan plus file-search fallback, without touching the user's active Obsidian vault. Native Obsidian index correctness, GUI rendering and installed-host discovery were not exercised. The remaining workflows received instruction-level review; this run does not claim fresh end-to-end executions of every editing workflow or statistical model reliability. Existing host evaluation records describe older candidates separately. No commit, release or host update was performed.
