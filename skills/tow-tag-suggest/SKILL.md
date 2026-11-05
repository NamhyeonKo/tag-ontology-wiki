---
name: tow-tag-suggest
description: >-
  Use when the user asks for concept-tag candidates for vault notes or project documents.
  Recommends only, then attaches the tags the user picks. Triggers: "suggest tags for this
  note", "what tags should this note have?", "extract concept tags", "tag these project docs".
---

# tow-tag-suggest

**Recommends** concept-tag candidates for notes or project documents named by the user. The user decides which tags a document carries; vault tags are written only to selected note frontmatter, while project tags are written only to `.tow/` metadata.

Before starting, read the [TOW conventions](../../docs/methodology.md): they define `tow` and the selection rules in §3 "Concept tags". Project work reads rules from `.tow/tags.md` and follows the project's explicit file scope.

## Workflow

1. **Scope.** For a vault note, work only on the notes the user names, or the folder they explicitly select. For project documents, use `tow project files` to discover the configured document set. List untracked and ignored file names before reading any contents; include those files only when the user selects them. Never edit project document bytes/frontmatter.
2. **Inspect candidates.** Use H2/H3 structure to identify concepts explained directly; the title concept is always a candidate. Body text adds candidates for big-picture concepts. For vault notes, when available, `tow ontology scan <paths…> --json` provides title, description, aliases, existing tags/body tags and headings. For project docs, read `.tow/tags.md` and consult the vault dictionary for shared concepts. Use the configured vault tag dictionary for canonical concepts/aliases and the project `.tow/tag-dictionary.json` for project-only concepts. Look up candidates exact match → alias → partial match; follow the vault's broader/narrower rule when a note explains both concepts directly. Without a dictionary, continue with authorized note vocabulary and mark status `not checked (no dictionary)` rather than blocking suggestions or creating one.
3. **Recommend as one batch.** Present one table for the whole selected set: document, candidate tags, add/remove decision, dictionary status and reason. Keep existing tags; for vault notes, list removals only for tags outside the rules or a broader tag used only as background beside a narrower tag. A broader+narrower pair directly explained by the note is not a removal candidate. Pre-select existing dictionary concepts; list new concepts separately with broader candidates and attach them only if the user picks them. If there is an established convention for number, use it; otherwise recommend few, within 3–10 where applicable. Wait for one approval for the batch.
4. **Apply vault selections.** For vault notes, edit only selected frontmatter `tags:` additions/removals. Follow the [preservation contract](../../docs/preservation.md), preserving body bytes and all other fields. Do not create missing metadata unless selected. Route user-selected unregistered concepts to `tow-tag-sync` only when ontology management is adopted.
5. **Apply project selections.** Prepare one changes JSON with `documents` mapping project-relative paths to the complete selected tag lists and `concepts` containing only user-picked new concepts with `description` and `broader`. Preview with `tow project tag <changes>`; after approval, run `tow project tag <changes> --apply`. This writes only project `.tow/` files; it does not change any project document or vault dictionary. Do not add unselected concepts.

## Judgement calls

- **Few**: recommend within the 3–10 range, in priority order. When unsure you match the user's standard, recommend fewer.
- **Judge reuse by the concept's nature**: ask "could another note explain or reference this concept directly?" How many notes use the tag today is not the measure (many notes have no tags yet).
- **The most specific concept, plus broader ones the note explains**: recommend the narrower concept first. Its broader concept is recommended as well when the note explains it directly too (conventions §3 "Broader and narrower tags together": the title concept, a heading or `description` about it, a definition or comparison), and stays off when the note uses it only as background or in passing. A language note gets the language tag (`facet`) plus language-neutral concept tags.
- **More narrower concepts than the limit allows**: propose splitting the note before cutting tags. A hub or overview note whose narrower concepts already have their own notes trims down to the broader concepts.
- **Area ↔ resource**: when a tag picked for a resource note is also discussed in its source area note, suggest in one line adding it to that area note too (it goes on when the user picks that note as well).

## Recommendation format

| Document | Candidate tags | Decision | Dictionary | Reason |
| --- | --- | --- | --- | --- |
| `Chunking.md` | `chunking`, `semantic-chunking` | add | Existing: `chunking`; new: `semantic-chunking` (broader: `chunking`) | Title and `## Semantic chunking` |

Project documents use the same batch table; clearly separate new project-only concepts and include a description and broader-concept candidates for concepts selected by the user.
