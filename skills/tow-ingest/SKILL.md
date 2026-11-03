---
name: tow-ingest
description: >-
  Use when filing raw or partially organized captures into a user's chosen vault structure,
  including temporary Date/Tag lines, attachments, or reusable concepts derived from a book,
  report, paper, certification or lecture source. Triggers: "process my inbox", "file these
  captures", "intake", "derive concept notes from this source".
---

# tow-ingest

File captures into the user's chosen structure, normalize approved formatting and use metadata only under their adopted schema. Read the [conventions](../../docs/methodology.md) and `tow config` first. Confirm source/destination roles in a custom vault; default PARA/inbox paths are not requirements. Carry only concept tags the user already selected in the source; this workflow does not invent tags.

For a custom vault, preserve existing fields or absent frontmatter and propose the existing destination (for example `Reading/`). Do not create dictionaries, PARA folders or classification/date fields just to file a note. The metadata draft table and Resource/Area rules below apply only where that recipe is adopted; otherwise use the vault's templates and selected fields. Missing optional metadata is not a blocking issue.

| Need | Read/use |
| --- | --- |
| Format/shape checks and final verification | `tow-check` |
| New categories | `tow-classify` A |
| Source-selected tags absent from dictionary | `tow-tag-sync` |
| Existing overlapping notes | `tow-merge` |
| New note outbound/inbound mentions | `tow-link` intake mode |
| Derive concepts from a source | [Concept ownership](../tow-review/references/concept-ownership.md), before analysis |
| Paper reviews | [Paper review rules](references/paper-review.md) |

## Workflow

**Phases 1–4 read and plan only. All file writes, including backups/scratch, begin after approval in phase 5.**

1. **Scope/index.** Read the category dictionary when adopted/present. An inbox request selects only top-level `*.md` under the user's confirmed inbox; ask for the source if none is established. A named source batch selects that source and its associated raw notes only. Inspect ignore/private policy: ignored captures require explicit path selection; list selected ignored inputs with an ignore-aware listing, since ordinary search may omit them. Disclose any move into tracked/public scope in the plan. Unselected private inputs stay unread/unmoved, including during existing-owner searches.
2. **Analyze every selected note.** Propose destination and only selected/adopted metadata, with classification confidence where applicable. Collect absent dictionary-backed values separately. Use the shared CLI-first search policy by title, aliases and key concepts before creating a file. Report overlap for `tow-merge`; source-derived batches use concept ownership without requiring Resource/Area folders. Obtain applicable `tow-check` report-mode issues and shape codes; inspect referenced images and their other users. Temporary hint/date/tag lines remain until their meaning has a verified approved destination, including in a custom schema.
3. **Show the plan** in the table below. Follow it with format/shape details, ownership/fact destinations, `tow-link`'s link plan, and new category candidates, stating “none” where empty.
4. **Obtain batch approval**, including selected new categories and listed link positions. Ambiguous classification/source choices need selection. This does not replace merge-by-merge strategy choices, discard confirmation, or the separate retroactive-classification decision.
5. **Execute in order.**
   1. Copy selected uncommitted source originals into scratch backup **before any modification**, retaining their original bytes.
   2. Register approved new categories through `tow-classify` only for adopted dictionary-backed classification; do not retroactively edit other notes without its separate decision.
   3. Send overlaps to `tow-merge`, with a strategy selection for each case.
   4. Write the approved final note from its backed-up source, preserve/merge only selected metadata and normalize only approved formatting. Remove temporary date/tag/hint lines only after their values are safely represented. Send unregistered source-selected tags to `tow-tag-sync` only when ontology use is selected, under its approval rules.
   5. Perform approved source cleanup, concept derivation and hub work. Update an existing project's hub status table only where that convention is adopted. Only explicitly requested source derivation/structure work permits body reorganization/file creation/splitting; unrelated ordinary captures keep their prose.
   6. Handle attachments below, then execute the approved `tow-link` intake positions without another blanket approval. Newly found ambiguity remains a user choice.
   7. Verify final notes and every fact's destination in a separate read before removing inbox originals. For splits/rewrites, map every source fact to a surviving note/section; an unmapped fact blocks deletion.
6. **Verify/report.** Compare each final note with its byte backup: line changes must be accounted for by metadata, removed temporary lines, approved formatting/link/path changes, or approved derivation. All other original prose/facts survive. Use `tow-check` for fences, broken links and attachment paths, plus scoped lint/usage as applicable. Report per note: source→destination, type/primary/secondary/status/kind, new categories and uncertain decisions, carried tags/registration, description or `NOPOINT`, shape, inbound/outbound links and their source notes, and attachments. Finish with totals for notes, categories, inbound/outbound links and remaining shape issues.

## Metadata drafts

For adopted TOW metadata, merge into partial frontmatter: preserve existing values and fill only approved missing fields under conventions §4. For custom schemas, use their own drafts; `— (not used)` is valid for TOW-only plan/report columns.

| Field | Intake rule |
| --- | --- |
| `description` | Body-grounded identity/contribution, one sentence (~100 characters); omit and report `NOPOINT` if unsupported |
| `aliases` | Title synonyms/abbreviations/translations; `ABC (Full Name)` contributes both ABC and Full Name |
| `created` | Preserve existing value; otherwise original body date first (`Date: 2022-02-24 (Thu)` → `2022-02-24`, likewise for the same label in the note's language), processing date only if absent |
| `source` | Actual original URL or Area source wikilink; mark an inferred source as a question in the plan for confirmation |
| `tags` | Preserve existing selections; transfer a `Tag:`/`Tags:` line (or the same label in the note's language) or a top `#a, #b` line, removing `#`. Propose typo/case/hyphen corrections for selection. With no selected tags, use `tags: []` |

Classification confidence: **clear** when the dictionary value fits; **ambiguous** with alternatives when several fit; **unknown** when the domain itself needs user direction/new registration. Do not hide uncertainty behind a default.

## Attachments

- Move only images referenced exclusively by the scoped notes by default. Shared or out-of-scope existing images need separate approval to move and repair all references; otherwise leave their bytes/location intact and adjust only the filed note's relative path.
- Use the user's established attachment location/naming policy. The optional TOW recipe is `<attachments>/<note-slug>/<descriptive-name>.png` (or original extension), lowercase English words and hyphens; the note folder identifies the note.
- Use note-relative image paths and numbered, titled captions in the note's language: image label `![Figure 1. Title]` followed by the relative path in parentheses. Copy, verify bytes/references in a separate call, then remove the old unique attachment.

## Plan table

| File/concept | Ownership decision | Type | Destination | Primary + confidence | Secondary | Description draft | Aliases / source / selected tags | Shape | Created | New category? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Capture.md | New reusable Resource | resource | Configured resource domain | registered value — clear | — | Body-grounded sentence | synonyms / actual URL or source? / [] | OK | Original date | No |

Include explicit affected files, fact destinations, visibility changes and attachment/link positions so batch approval has a concrete scope.
