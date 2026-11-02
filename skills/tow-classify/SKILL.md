---
name: tow-classify
description: >-
  Use when registering category values or reviewing notes' category, type, status,
  and kind fields, including backfilling, misclassification, category consolidation,
  and legacy classification tags. Triggers: "카테고리 추가/등록", "재분류",
  "분류 보강", "소급 반영", "중복 카테고리 통합".
---

# tow-classify

Manages classification fields and their category dictionary. Read the [conventions](../../docs/methodology.md) and run `tow config` first. Resolve the category dictionary from `categoryDictionary`; read its rules and index. Concept `tags:` belong to `tow-tag-sync`: clarify which axis an ambiguous "tag" request means.

Use only the conventions, category dictionary, and this workflow as classification rules. A category needs no invented minimum number of notes. Allowed `type`, `status`, and `kind` values are fixed by the conventions.

## A. Register a category

1. **Reuse first.** Read the category index and search semantic equivalents, synonyms, abbreviations, and other-language spellings. If the same meaning exists, report reuse of that value and stop registration.
2. **Name and place.** Choose its parent, name, depth, and primary/secondary use. Default depth is two levels; justify a third only when two levels plus a secondary category cannot express it. Resource categories identify knowledge domains; project categories identify projects; area categories identify sources such as books, papers, or certifications.
3. **Propose and obtain approval.** Batch related entries in this table. Include planned dictionary/diagram changes.

   | New value | Parent section | One-line meaning | Primary/secondary | Depth | Why reuse is insufficient |
   | --- | --- | --- | --- | --- | --- |
   | `ai/agent` | `ai` | Goal-directed agent workflows | secondary | 2 | Existing values cover models, not agent workflows |

4. **Register the approved entries.** Update the dictionary section/index, its Mermaid classification graph when present, and `updated`. Include any proposed graph creation in the plan. Put common synonyms/abbreviations at the end of the one-line description so later reuse checks can find them. Preserve unrelated entries and graph nodes.
5. **Ask separately about retroactive classification.** Registration alone does not authorize editing existing notes. If approved, run B for that value across the vault unless the user selects a narrower scope; an already explicit selection or refusal settles this question.
6. **Verify.** Lint affected notes with the installed helper and confirm the new value is recognized. Report the value, parent, diagram/date changes, and retroactive decision.

## B. Review existing notes

1. **Scope.** Use the notes/folder/domain/vault the user names. A's approved follow-up covers that value across the vault unless the user narrows the scope.
2. **Legacy conversion.** Inspect the scoped lint/scan results. For old classification tags, follow [legacy-classification.md](references/legacy-classification.md): show the exact dry-run changes, then apply only approved conversions. This is an agent edit workflow using the installed tools, not an extra helper subcommand.
3. **Read and classify.** Inspect fields and enough body text to justify each proposal. For retroactive additions, find notes where the value is clearly appropriate as a secondary category; skip notes already using it as primary.
4. **Propose, then wait.** List file, current values, proposed values, change type, and evidence. Mark absent dictionary values for A. Present category consolidations as a separate larger change covering both dictionary and affected notes.
5. **Apply only selected classification changes**, preserve bodies/other fields, and update `updated` under the conventions.
6. **Verify** scoped `tow lint` and report each change and any remaining decision.

| Change type | Handling |
| --- | --- |
| Supplement | Add only a clearly supported registered value |
| Uncertain | Explain the evidence and ask; do not infer from loose association |
| Correct | Propose the primary category aligned with the note's identity/folder |
| Remove | Give evidence for each plainly wrong value |
| Consolidate | Plan dictionary and note changes together with A |
| New | Register through A before using the value |

Keep one `type` and an appropriate primary category. Project-only fields stay on project documents; archive location does not imply completion. Classifying broader concepts into narrower categories is a decision for the user. When recurring synonymous categories or domain growth suggest consolidation, offer a review without scheduling or executing it.
