# Content-preserving maintenance

The ordinary TOW workflow edits selected frontmatter and formatting, preserving the user's content. This contract covers Markdown, math, code and tables; a formatting request never authorizes rewriting their contents. User rules/templates take precedence over bundled examples.

## Small, verifiable changes

1. Establish the selected paths, adopted rules and exact changes before writing. A lint finding is not approval to apply a fix. Keep ambiguous repairs report-only.
2. Plan the scratch destination and its privacy protection before approval or copying. Use a new vault-local batch that preserves the source's ignore/private boundary, including retained backups after failure/interruption. Hidden does not mean Git-ignored: in a Git-managed vault, require the prospective snapshot/candidate paths to pass `git check-ignore` before any copy. Prefer an existing protected location (for example `private/.tow-tmp/batch/` when `private/` is ignored); if none exists, propose the protection/location and wait rather than exposing the source or silently changing ignore rules. In other vaults honor their established private/sync/access policy. After approval, make independent byte copies, not hard links. Keep a separate candidate; never use the edited file as its own baseline. Preserve line endings and final newlines outside selected spans.
3. Separate metadata-only edits, format edits, link wrapping and post-curation into distinct steps. Use literal before/after replacements for approved format spans; every other byte remains unchanged. Prefer installed, configured linters/formatters in check/diff mode to free-form model rewriting. Do not install a formatter or execute note code to complete routine maintenance.
4. Verify the candidate against its original **before** replacing the note. Apply only after the relevant checks below pass; re-read the saved note to confirm the verified bytes. An unavailable checker is not a pass. Keep backups until final verification, then clean only that batch.

A literal replacement/diff check proves only where a change occurred. Separately compare protected payloads from the actual original and candidate, without substituting the old contents back into the candidate or normalizing them. This matters even for padding inside math delimiters; a model's assertion that a formula is equivalent is insufficient.

## Preservation by operation

| Operation | Allowed formatting | Must remain unchanged | Verification |
| --- | --- | --- | --- |
| Frontmatter | Only approved field/value or YAML-style changes under the adopted schema | Body bytes; unselected keys, values and types | Compare parsed metadata when a YAML-aware tool is available; inspect the exact diff and run `tow verify-body` for body equality |
| Prose/headings/lists | Selected Markdown markers, heading levels or indentation with an unambiguous boundary | Every word, punctuation mark, paragraph/list-item order and content | Exact comparison outside selected markers; do not reflow, summarize, convert prose to lists or rename headings as a lint fix |
| Math | Selected delimiters or layout around an already identified expression | The expression payload, including variables, operators, numbers, indices, conditions, text and meaningful whitespace | Compare the complete inner payload byte for byte; balance delimiters. Mathematical equivalence guessed by a model is not proof |
| Code fences | Selected fence markers or placement around an identified block | Code/output payload bytes, comments, literals, identifiers and ordering | Compare the complete block payload byte for byte; do not guess a missing block boundary or language |
| Code inside a block | An explicitly selected, language-aware formatting change | Literal/comment contents, tokens, control flow and behavior | Use an installed formatter on an isolated copy and a suitable language-aware preservation check. For Python, compare AST structure plus ordered non-whitespace tokens (including comments, strings and numbers). Otherwise leave the payload unchanged and report the limitation |
| Tables | Selected separator syntax, cell-boundary padding or escaping with a proven boundary | All headers/cell payloads, values, units, expressions, links, row/column order and existing alignment unless explicitly selected | Compare ordered cell payloads with a Markdown-aware parser or explicit byte boundaries. Preserve escaped pipes and inline-code/math spans; a simple split on `|` is not proof |
| Wikilinks/attachments | Only explicitly selected wrappers or target/path repair | Displayed words, captions, surrounding prose and attachment bytes | Verify actual target, display and surrounding bytes; link repair is not a format or metadata side effect |

Converting ambiguous plain text/code to LaTeX, changing a matrix into a different representation, simplifying an expression, repairing a code algorithm, filling an empty table cell or adding missing prose is content work. Report it; a separate explicit [post-curation](post-curation.md) request is required. A template alone does not authorize those changes.

## `tow verify-body BEFORE AFTER`

Read-only equality check for **metadata-only** edits. Both paths must be distinct, existing files inside the named vault; symlinks resolving outside it and hard-linked/self baselines are rejected. It needs neither Node/npm, a dictionary nor valid `tow.json`.

```bash
"$TOW" --root "$VAULT" verify-body "$BATCH/before.md" "$BATCH/candidate.md"
```

`BATCH` is the approved, privacy-protected vault-relative scratch path established above; a hidden name alone is insufficient. Exit 0 means exact body-byte equality, exit 1 means different body bytes, and exit 2 means the comparison could not be performed. A leading `---` frontmatter block ends at a standalone closing `---` line (UTF-8 BOM and LF/CRLF supported); an unterminated block fails closed. A note without that leading block is entirely body. The check does not validate YAML values, approval, Markdown rendering, mathematical equivalence, code semantics or format edits. Use the operation-specific checks above for those; never weaken this equality check to accept a changed body.
