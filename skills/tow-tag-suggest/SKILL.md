---
name: tow-tag-suggest
description: >-
  Use when the user asks for concept-tag (`tags:`) candidates for specific notes in a TOW
  vault. Recommends only, then attaches the tags the user picks. Triggers: "suggest tags for
  this note", "what tags should this note have?", "extract concept tags".
---

# tow-tag-suggest

**Recommends** concept-tag candidates for the notes the user names. The user decides which tags go on a note; this skill adds only the tags the user picks to its `tags:`.

Before starting, read the [TOW conventions](../../docs/methodology.md): they define the `tow` command used below and the selection rules in §3 "Concept tags" (what to tag, how many, in what priority).

## Workflow

1. **Scope**: only the notes the user names. Recommend for a whole folder only when the user states that scope.
2. **Headings first**: use the H2/H3 structure to find the concepts the note explains directly. Body text adds candidates only for big-picture concepts. The note's title concept is always a candidate.
3. **Pick candidates**: apply conventions §3 plus the [judgement calls](#judgement-calls).
4. **Look up existing vocabulary**: when a tag dictionary is present, look up each candidate in exact match → alias → partial match order and use its canonical spelling; taxonomy paths come from `tow ontology show <tag> --json`. Without a dictionary, inspect tags in authorized notes with the shared CLI-first search policy and mark dictionary status `not checked (no dictionary)`, rather than blocking suggestions or creating a dictionary. Match the vault's adopted tag style; TOW naming/taxonomy rules below are optional.
5. **Recommend** in the [recommendation format](#recommendation-format) and wait for the user's choice. On a note that already has tags, keep the existing tags and split the recommendation into `add` candidates and `remove` candidates (broader + narrower pairs, tags outside the rules).
6. **Apply** only selected additions/removals to `tags:`; if that property/frontmatter is absent, its creation must be explicit in the selection plan. Follow the adopted date policy; preserve other fields and the body. Hand unregistered tags to `tow-tag-sync` only when the user has chosen ontology management; otherwise report them as dictionary-unverified without requiring setup.

## Judgement calls

- **Few**: recommend within the 3–10 range, in priority order. When unsure you match the user's standard, recommend fewer.
- **Judge reuse by the concept's nature**: ask "could another note explain or reference this concept directly?" How many notes use the tag today is not the measure (many notes have no tags yet).
- **The most specific concept**: when a narrower concept goes on the note, the broader one stays off (except the title concept). A language note gets the language tag (`facet`) plus language-neutral concept tags.
- **More narrower concepts than the limit allows**: propose splitting the note before cutting tags. A hub or overview note whose narrower concepts already have their own notes trims down to the broader concepts.
- **Area ↔ resource**: when a tag picked for a resource note is also discussed in its source area note, suggest in one line adding it to that area note too (it goes on when the user picks that note as well).

## Recommendation format

| Note | Candidate tag | Add/remove | Dictionary | Reason |
| --- | --- | --- | --- | --- |
| Chunking.md | `chunking` | add | exists | Title concept |
| Chunking.md | `semantic-chunking` | add | new (broader candidate: `chunking`) | The `## Semantic chunking` section explains it |
| Chunking.md | `rag` | remove | exists | Its narrower concept `chunking` is on the note |

For new candidates, include guessed aliases and broader concepts so `tow-tag-sync` can pick them up.
