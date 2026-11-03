---
name: tow-merge
description: >-
  Use when the user explicitly requests post-curation of overlapping notes under their
  chosen canonical destination and preservation rules. Triggers: "merge this with the
  existing note", "these notes are duplicates", "which note should be canonical?",
  "split this note in two".
---

# tow-merge

Optional case-by-case aftercare, not a lint fix. Read the [conventions](../../docs/methodology.md), [post-curation contract](../../docs/post-curation.md), [preservation contract](../../docs/preservation.md), `tow config` and [concept ownership](../tow-review/references/concept-ownership.md). An overlap finding from intake/review is a proposal, not merge permission.

## Workflow

1. **Establish scope before reading.** Resolve user rules, ignore/private policy and eligible filenames/exclusions. If a required read is blocked, resolve that scoped access or stop. Pass the eligible list/exclusions to every search; filtering a whole-root content search afterward already reads private files. Read the selected notes fully only after scope is known.
2. **Identify the desired result.** Find overlap, source/audience differences and canonical candidates. Require a chosen destination/template or concrete heading/content placement rule; an existing canonical structure selected by the user can supply it. No dictionary, TOW schema or PARA folder is required. Ask about missing/conflicting rules rather than inventing a generic structure.
3. **Select one case at a time.** Show strategies below with actual destination headings, literal transfers, any requested generated summary and exact losses. Wait for the user's strategy before the next case. Accept alternatives; repeat a recommendation at most once. A supplied template is not permission to rewrite filled sections.
4. **Inventory preservation.** Map every source section, sentence/fact, table, code block and formula to `verbatim transfer → destination`, `explicit summary → canonical detail + link`, or `discard → listed user choice`. Preserve complete math/code/table payloads. Summarizing or rewriting existing material needs explicit scope; any listed discard needs its separate confirmation before execution. Unmapped facts block editing/deletion.
5. **Execute the selected strategy.** Back up originals as independent byte copies and prepare candidates. Copy content verbatim into the approved destinations by default. Use the user's template only for the selected structure/new text; no automatic prose restyling. Reconcile metadata under the destination's schema, listing conflicting values for selection and preserving unrelated/absent fields. No inferred dates, categories, aliases or tags. Verify fact destinations in a separate call while all source files still exist, then perform only selected deletions.
6. **Repair selected inbound links.** Search only eligible files with the shared CLI-first policy. Preserve display words in `[[Canonical|original display]]` or `[[Canonical#Section|original display]]`; leave surrounding prose untouched. Follow the adopted date policy. Disclose inaccessible/private scope and newly found ambiguity rather than broadening edits.
7. **Verify/report.** Re-read changed/repair files and compare protected regions, facts and metadata to originals. Run applicable scoped `tow-check`/ontology checks; tags remain the user's selection. Report rule source, chosen strategies, verbatim versus explicitly transformed content, surviving fact locations, deleted files, link repairs and unresolved checks. Keep originals when verification fails.

## Strategies to propose

| Strategy | Result | User choice needed |
| --- | --- | --- |
| Absorb/transfer | Move selected content verbatim into an existing owner | Exact destination sections and whether to delete a source |
| Coexist | Keep notes with selected navigation links | Link positions; no compulsory prose/tag additions |
| Summary + canonical detail | Retain full detail at an owner and a selected summary elsewhere | Explicit summary scope/template; it is content writing |
| Replace | Replace a selected destination with chosen source content | List unique facts at risk and reconfirm any discard |
| Split | Move selected blocks verbatim into chosen destinations | Destination/template and complete fact mapping; no automatic fragmentation |

Merely related notes usually need no merge. A request asking which note is canonical is read-only until a concrete strategy is selected. Dictionary registration and retroactive classification keep their own approval boundaries.
