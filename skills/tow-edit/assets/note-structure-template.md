# Note structure template

A bundled example, usable only when the user explicitly selects this template. It does not substitute for the user's own structure, instructions or writing rules. Selecting a template alone does not authorize filling or rewriting existing notes.

This is an optional TOW prose recipe. Preserve the vault's existing structure/style unless its replacement is requested; using this template does not require PARA folders, TOW frontmatter or dictionary creation.

```markdown
# <Note title>

## Overview

- <Definition, use and key summary>
- <Natural link to another note, first mention only>

## Principles

### <How or why it works>

- <One clause per bullet>

## Types

### <Type or component>

- <Explanation>

## Comparison and relations

## Examples and applications
```

| Content | Structure |
| --- | --- |
| One concept with no useful subdivision | Overview only |
| How/why it works is central | Principles, then H3 subtopics |
| Actual distinct types/components | Types, then H3 per type |
| Components within one type | H4 below its H3 |
| Confusable neighboring concepts | Comparison and relations |
| Examples needed for understanding/reuse | Examples and applications |

Only when this prose style is explicitly selected, use `-` lists and concise clauses or nominal endings in the note's language rather than full narrative sentences. For Korean notes, read [korean-style.md](../references/korean-style.md). Within a separately selected prose-transformation scope, split long sentences into bullets/subitems, preserving every fact; otherwise keep filled sentences verbatim. Rewrite tables/code only when restructuring them is in the approved scope.

Links follow `tow-link` (actual targets, first eligible mention, code excluded). Register new categories through `tow-classify`; concept tags are selected by the user, with `tow-tag-suggest` only when requested.
