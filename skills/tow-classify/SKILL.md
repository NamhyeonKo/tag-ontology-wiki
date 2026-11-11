---
name: tow-classify
description: >-
  Use when registering category values or reviewing notes' category, type, status, and kind
  fields, including backfilling, misclassification, category consolidation, and legacy
  classification tags. Triggers: "add/register a category", "reclassify these notes",
  "backfill the new category", "merge duplicate categories".
---

# tow-classify

This skill works only inside the vault. From another project, stop and use `tow-query` to find vault content or `tow-send-vault` to bring content in.

Before any write, run `tow config` and verify the vault root it prints contains the current working directory and every file being edited; otherwise stop and route the request as above.

Manages classification fields and, when adopted, their category dictionary. Read the [conventions](../../docs/methodology.md) and the [TOW recipe](../../docs/recipe.md) (§3 classification, §4 frontmatter), and run `tow config` first. Inspect the user's actual schema before proposing fields/values. For TOW categories, use `tow/category-dictionary.json` by default (or the configured `categoryDictionary` path) and read `tow/categories.md` for its rules when present. Concept-tag selection belongs to `tow-tag-suggest`, dictionary consistency to `tow-tag-sync`; clarify an ambiguous "tag" request.

Use the adopted vault rules, category dictionary and this workflow as classification rules. A category needs no invented minimum number of notes. The recipe's fixed `type`, `status` and `kind` values apply only to TOW-schema notes. For a custom schema, preserve its field names/values, show evidence for changes and use the plan/apply/preservation steps below without TOW-specific dictionary or legacy conversion requirements. No PARA move is implied. If the user selects TOW classification and its dictionary is missing, propose that prerequisite's path/content for approval before registering values; a dictionary does not imply adopting PARA or a tag ontology.

For every selected note-metadata edit, follow the [preservation contract](../../docs/preservation.md): keep independent before/candidate copies, verify only selected metadata values, and require `tow verify-body <before> <candidate>` to pass before replacing the note. This operation does not authorize fixing body format, rewriting prose or invoking post-curation. Dictionary files are verified separately by their own rules.

`tow` is not a command on your PATH: run the executable `scripts/tow.py` two directories above this file by its absolute path (with `python3` if the host can't execute it), for example `"<plugin-root>/scripts/tow.py" config`.

## A. Register a category

1. **Reuse first.** Read the configured category dictionary and `tow/categories.md` rules; search semantic equivalents, synonyms, abbreviations, and other-language spellings. If the same meaning exists, report reuse of that value and stop registration.
2. **Name and place.** Choose its parent, name, depth, and primary/secondary use. Default depth is two levels; justify a third only when two levels plus a secondary category cannot express it. Resource categories identify knowledge domains; project categories identify projects; area categories identify sources such as books, papers, or certifications.
3. **Propose and obtain approval.** Batch related entries in this table. Include planned dictionary/diagram changes.

   | New value | Parent section | One-line meaning | Primary/secondary | Depth | Why reuse is insufficient |
   | --- | --- | --- | --- | --- | --- |
   | `ai/agent` | `ai` | Goal-directed agent workflows | secondary | 2 | Existing values cover models, not agent workflows |

4. **Register the approved entries.** If the configured `categoryDictionary` ends in `.md`, keep the 0.4.2 Markdown flow: update the selected category's dictionary entry and index/graph/date under the approved plan, preserving unrelated content. Put common synonyms and abbreviations at the end of the one-line description so later reuse checks can find them. Offer `tow migrate` as an optional way to convert the legacy vault; migration is not a prerequisite to category registration. Otherwise, run `tow category add <value> <description>` to preview each JSON entry; after approval, run `tow category add <value> <description> --apply`. Follow `tow/categories.md` and do not edit the JSON dictionary by hand.
5. **Ask separately about retroactive classification.** Registration alone does not authorize editing existing notes. If approved, run B for that value across the vault unless the user selects a narrower scope; an already explicit selection or refusal settles this question.
6. **Verify.** For TOW classification, lint affected TOW notes when applicable and confirm the new value is recognized in the configured category dictionary (JSON or Markdown). For custom fields, compare parsed values with adopted rules. Report the value, parent, approved diagram/date changes, and retroactive decision; dictionary-only registration does not authorize reading other notes.

## B. Review existing notes

1. **Scope.** Use the notes/folder/domain/vault the user names. A's approved follow-up covers that value across the vault unless the user narrows the scope.
2. **Legacy conversion.** Inspect the scoped lint/scan results. For old classification tags, follow [legacy-classification.md](references/legacy-classification.md): show the exact dry-run changes, then apply only approved conversions. This is an agent edit workflow using the installed tools, not an extra helper subcommand.
3. **Read and classify.** Inspect fields and enough body text to justify each proposal. For retroactive additions, find notes where the value is clearly appropriate as a secondary category; skip notes already using it as primary.
4. **Propose, then wait.** List file, current values, proposed values, change type, and evidence. Mark absent dictionary values for A. Present category consolidations as a separate larger change covering both dictionary and affected notes.
5. **Apply only selected classification changes**, preserve bodies/other fields, and follow the adopted date policy.
6. **Verify** selected fields against the applicable schema, using scoped `tow lint` only for TOW notes, and report each change and remaining decision.

| Change type | Handling |
| --- | --- |
| Supplement | Add only a clearly supported registered value |
| Uncertain | Explain the evidence and ask; do not infer from loose association |
| Correct | Propose the primary category aligned with the note's identity/folder |
| Remove | Give evidence for each plainly wrong value |
| Consolidate | Plan dictionary and note changes together with A |
| New | Register through A before using the value |

For TOW notes, keep one `type` and an appropriate primary category; project-only fields stay on project documents. Archive location never implies completion. Classifying broader concepts into narrower categories is a decision for the user. When recurring synonymous categories or domain growth suggest consolidation, offer a review without scheduling or executing it.
