# Legacy classification conversion

Use this when classification values still live in a note's `tags:` list. Read the note and parsed frontmatter with the installed tools; use the configured category dictionary. Preview exact frontmatter changes before requesting approval. The body stays byte-for-byte unchanged.

## Eligibility

- A note needs a frontmatter block and a tags list.
- Skip this conversion if either `type` or `category` is already present, even empty. Such notes can still receive a separately approved classification review.
- Skip notes without a convertible tags list. Do not invent frontmatter or classification values from a filename.

## Conversion rules

Process existing tag values in order, distinguishing exact registered category strings from concept tags.

| Old tag | Proposed field/value |
| --- | --- |
| `type/<value>` | `type: <value>` |
| `status/<value>` | `status: <value>` |
| `kind/<value>` or `stage/<value>` | `kind: <value>` |
| `status/archived` | Remove this legacy marker; archive location expresses storage, not known completeness |
| Exact registered category value | Move it into the ordered `category` list |
| Other value | Keep it as a concept tag, with its original value |

Preserve remaining fields, dates, sources, and concept tags. Keep `tags: []` when no concepts remain. Never fill in `complete` from `archived`. Surface conflicting scalar values, unsupported values, ambiguous domains, and unknown categories for a decision rather than silently discarding or guessing.

## Dry-run, approval, apply

1. Read every candidate and show a field-level diff/table, including any removed legacy marker. Record the original body and an input snapshot for comparison.
2. Obtain selection of the exact conversions. The proposal phase writes no notes or scratch files. An existing explicit approval can cover the listed conversions; unlisted fixes need a new decision.
3. Edit only those notes' approved frontmatter fields and the required `updated` date. Re-read the current file before editing so intervening user changes are not overwritten.
4. Compare every body and unselected field with its original snapshot. Run scoped `tow lint`; report unresolved legacy cases and unregistered concept tags for `tow-tag-sync`. Already converted notes remain unchanged on a repeated conversion request.
