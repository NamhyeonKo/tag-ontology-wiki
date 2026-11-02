# Note structure template

For Resource restructuring through `tow-edit` and new Resource notes through `tow-ingest`/`tow-review`. Use only sections the concept needs, in the note's language; do not copy every optional section.

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

Use `-` lists and concise clauses or nominal endings in the note's language rather than full narrative sentences. For Korean notes, read [korean-style.md](../references/korean-style.md). Split long sentences into bullets/subitems, one clause per bullet, preserving every fact. Rewrite tables/code only when restructuring them is in the approved scope.

Links follow `tow-link` (actual targets, first eligible mention, code excluded). Register new categories through `tow-classify`; concept tags are selected by the user, with `tow-tag-suggest` only when requested.
