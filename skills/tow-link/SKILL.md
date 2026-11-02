---
name: tow-link
description: >-
  Use when connecting vault notes with Obsidian wikilinks at existing mentions
  of note titles or aliases, including inbound links to newly filed notes.
  Triggers: "link my notes", "connect these notes", "add wikilinks", "링크 연결",
  "노트 연결해줘", "[[..]]로 이어줘", "wikilink 걸어줘".
---

# tow-link

Wrap existing mentions of other notes in `[[wikilinks]]` for navigation. Read the [conventions](../../docs/methodology.md) and `tow config` first. Shared concept tags and categories remain the primary connection; body links are optional. Preserve words, sentences, headings and sections. Use existing target files, once per target at its first eligible body mention. Do not write frontmatter `related:`.

## Workflow

1. **Scope.** Use the note, folder/domain or vault the user names; ask if unspecified.
2. **Target index.** Collect actual filenames and frontmatter aliases across the eligible vault. Both targets and edited notes exclude the configured inbox, daily notes, project history, misc and attachments, plus private/ignored inputs under the conventions. Targets may be outside the edit scope.
3. **Scan.** Apply the matching rules below. Inspect existing wikilinks too: an alias-only target is broken and needs a canonical filename with its original display text. Report missing targets for the user's remove/create/keep decision; do not create a note automatically.
4. **Plan and wait for approval.** Show the table below, then separate skipped, ambiguous and missing-target lists.
5. **Apply selected positions only.** Wrap or correct targets, preserve displayed words, and update changed notes' `updated`.
6. **Verify and report.** Check actual targets, first-mention counts, unchanged surrounding text and scoped lint. Report additions/corrections, targets and skip reasons per file.

| File | Existing phrase and context | Target note | Proposed notation | Reason |
| --- | --- | --- | --- | --- |
| Attacks.md | “Stored XSS persists…” | Stored XSS | `[[Stored XSS]]` | Longest first mention |
| Attacks.md | “XSS is…” | Cross Site Scripting | `[[Cross Site Scripting\|XSS]]` | Alias; keep display text |

## Matching rules

- **Existence and meaning:** only actual filenames/aliases qualify; skip self-links. For common titles such as Network, Data or Graph, require clear conceptual context. If the first occurrence means something else, continue to the first eligible mention. Multiple matching notes or uncertain meaning require the user's choice.
- **Longest match:** choose the longest specific title/alias at a position (`Stored XSS` before `XSS`). English matching ignores case.
- **Display preservation:** exact title → `[[Title]]`; aliases or different casing → `[[Title|original words]]`. Escape the separator as `\|` inside table cells. Existing links retain their displayed wording when their target is corrected.
- **Once per target:** later eligible mentions remain plain. An existing valid link counts toward that target's first-mention allowance; report conflicting duplicates rather than adding more.
- **Body only:** sentences, lists and table cells qualify. Skip headings, figure captions, quote lines, frontmatter, fenced/inline code, existing wikilink/Markdown-link interiors, and URLs. A target mentioned only in excluded regions is skipped.
- **Existing mentions only:** adding a hub's `[[Note]]: one-line summary` belongs to `tow-review`/`tow-ingest`. Do not insert sentences or force reciprocal links; backlinks provide reverse navigation.

## Intake mode

When `tow-ingest` files new note X, link **outbound** mentions in X and **inbound** mentions of X's title/aliases across the eligible vault. Include all newly filed notes in a batch's target index so they can link to each other. The approved intake link plan authorizes its listed positions without another approval; ask only about newly discovered ambiguity or changes outside that plan. All matching and exclusion rules still apply.
