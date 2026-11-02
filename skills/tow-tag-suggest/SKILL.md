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
4. **Look up the dictionary**: for each candidate, `grep -i "<term>"` the tag dictionary (`tagDictionary` in `tow config`) in the order exact match → alias → partial match, and use the canonical tag when one exists. Its place in the taxonomy is `paths` in `tow ontology show <tag> --json`.
5. **Recommend** in the [recommendation format](#recommendation-format) and wait for the user's choice. On a note that already has tags, keep the existing tags and split the recommendation into `add` candidates and `remove` candidates (broader + narrower pairs, tags outside the rules).
6. **Apply** only the additions and removals the user picked to `tags:`, and update `updated`; other frontmatter values and the body stay as they are. Hand unregistered tags to `tow-tag-sync`.

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
