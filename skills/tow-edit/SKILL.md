---
name: tow-edit
description: >-
  Use when the user explicitly requests body-content changes to named
  vault notes, including filling empty sections, restructuring, notation, list conversion,
  or prose style. Triggers: "edit this note", "fill in this section", "fill the empty
  sections", "restructure this note", "turn this into a list".
---

# tow-edit

This is the scoped body-edit exception to the [conventions](../../docs/methodology.md)' default of preserving prose. A clear request naming the note and change authorizes that edit immediately: apply it without another plan table or approval question. Ask only when the intended scope is ambiguous. Resolve the vault settings with `tow config`.

| Request | Change | Preserve |
| --- | --- | --- |
| Fill only empty sections/items | Empty content | Every filled sentence |
| Change structure | Heading hierarchy and placement using the [structure template](assets/note-structure-template.md) | Sentence content |
| Fix table/math/code notation | [Markdown notation](../tow-check/references/markdown-format.md), including natural sentence flow | Facts, cell values, expressions and code |
| Convert to concise style or lists | Sentence form in the named section | Facts/content and the note's language |
| “Clean this up” or “fix it” without a clear target/change | Ask what to change first | The complete note until clarified |

## Workflow

1. **Determine the scope** and preservation boundary from the request/table.
2. **Read the whole original**, including frontmatter.
3. **Make the smallest scoped edit** in the note's existing style. Preserve its metadata, including absent frontmatter; apply only an established date policy rather than adding `updated` automatically. The structure template is an optional recipe when restructuring is requested.
4. **Connect new prose.** For natural mentions of existing notes, use `tow-link`'s matching rules; existing prose outside the edit scope stays unchanged. Classification/tag changes are separate selected work, with dictionaries required only when those features are adopted.
5. **Verify and report.** Run `tow-check` on the changed note, check its formatting, and compare every out-of-scope sentence, code block, formula and metadata value with the original. Report the changes and preservation result briefly. Unrelated findings remain report-only.
