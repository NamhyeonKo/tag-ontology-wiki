# Complete portable TOW workflows

## Intent and authorization

The user requested all six remaining vault skills, preservation of their functionality and approval rules, removal of personal-vault dependencies, validation on Claude Code/Codex/Antigravity, documentation updates, independent review, CI, and sequential merging. The original skill directory is reference material; no real vault files are edited by this task.

## Approach

Keep one shared portable package and the existing Python helper/`tag-ontology@0.1.2` boundary. Copying the originals unchanged leaves private paths and missing scripts; separate host implementations duplicate the workflows. Adapt the six workflows and their references once, using the common conventions and effective vault settings. Native host permissions remain authoritative.

## Scope and interfaces

- Add `tow-classify`, `tow-link`, `tow-edit`, `tow-merge`, `tow-review`, and `tow-ingest`, with the original concept-ownership, note-structure, and paper-review references.
- Retain the existing four workflows and all their preservation/selection rules.
- Extend `tow.json` with string settings `inbox`, `attachments`, `dailyNotes`, and `misc`. Defaults: `00_Inbox`, `99_Etc/attachments`, `02_Areas/daily-notes`, and `99_Etc`. These are configurable layout defaults, not fixed paths in skill operations.
- `inbox` and `misc` are direct-child folder names. `attachments` and `dailyNotes` are nonempty vault-relative paths; reject absolute paths, `..`, and the root itself. Existing PARA scan scope stays unchanged; explicitly scoped intake paths remain supported.
- Replace private `AGENTS.md` references with packaged conventions and user/vault policy. Replace `vault_meta.py lint/sync` with helper lint/ontology usage. Legacy migration is a documented dry-run proposal followed by approved agent edits, using the original conversion rules; no second Markdown parser or unsupported CLI command is introduced.
- Legacy migration maps `type/*`, `status/*`, `kind/*`, and `stage/*` to fields; `stage` becomes `kind`; `status/archived` is omitted; exact registered categories become category values; concept tags and empty tags survive. Already-classified notes are skipped by the legacy conversion. Show conflicts/invalid values before approval and preserve bodies.
- Paper reviews retain a filename-safe short title, full paper-title H1 and alias, `type: area`, `paper/<alias>` primary category, source URL, and contribution description. Document this H1 exception for the check workflow.
- Bump the package and project to 0.2.0 so native versioned caches receive the new skills. The external CLI remains pinned at 0.1.2.

## Approval and preservation matrix

| Workflow | Boundary to preserve |
| --- | --- |
| classify | Approve new category plans; ask separately about retroactive scope; legacy conversion previews before approved writes; preserve bodies and unselected fields |
| link | Scope, candidate/ambiguity plan, then approved wrapping/corrections only; first body mention, longest match, display text preserved; parent intake approval covers its listed links |
| edit | An explicit, clearly scoped body-edit request authorizes that edit immediately; ambiguity needs clarification; no extra blanket approval gate; preserve every unrequested part |
| merge | Present strategies and obtain a selection for each case sequentially; extra explicit selection for discarded facts; verify every fact's destination before deletion; repair inbound links |
| review | Read all scoped notes, report ownership/duplicates/hubs/isolation/classification/project direction, then an approved plan; delegated merges retain per-case choices |
| ingest | Phases 1–4 read/plan only; approved batch before backups/moves/frontmatter; preserve selected source tags/dates; merges retain per-case selection; copy/verify before source deletion; shared attachments stay unless separately approved |

Ignored/private capture inputs require explicit selection. Intake plans disclose any move into tracked/public scope before approval. Link candidates/edit scope exclude configured inbox, daily notes, project history, miscellaneous support files and attachment storage. No host-wide permission weakening or automatic publication.

## Validation

1. Record baseline portability failures from unadapted originals in a relocated synthetic package before authoring adaptations.
2. Test configuration contracts first; port and check each skill before proceeding to the next. Validate all links, references, cross-skill names and absence of private dependencies.
3. Use renamed synthetic folders/dictionaries and retained baseline hashes. Cover new category/legacy conversion, first-mention links, explicit body edits, per-case merges, hub-only review approval, and intake with paper H1, unique/shared attachments and private-input boundaries.
4. Install the candidate through native clients and exercise all six workflows on each host. Check proposals before sending simulated-user approvals; resume the same native conversations and verify exact allowed deltas/content preservation. Record failed tool calls, recoveries, quota blocks, and permission-profile limits honestly.
5. Run the full unit/packaging/integration suite, Ruff, strict Pyright, native package validation, independent review, PR CI, and post-merge CI. Promote through reviewed feature→dev→main PRs. Recheck public-main installation of the new version after promotion.

## Boundaries

No actual user vault migration, official-directory submission, new backend, new dependencies, global `tow` installer, or speculative doctor command. Test artifacts/native transcripts stay outside the shipped package. Single synthetic scenarios demonstrate observed behavior, not universal reliability.
