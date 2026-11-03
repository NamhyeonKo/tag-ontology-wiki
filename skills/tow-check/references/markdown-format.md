# Markdown, math, code and table formatting

Read the [preservation contract](../../../docs/preservation.md) before proposing fixes. The user's adopted template/style governs presentation. Work in small, explicitly selected spans; every word, formula payload, code payload and table value is protected. Formatting does not include correcting facts, rewriting sentences, filling gaps or simplifying expressions.

## Markdown

- Repair selected heading/list/fence markers only when their boundaries are known. Preserve heading text, paragraph/list order, punctuation and links.
- A mismatch between the filename and H1 is a report, not permission to rename either text or file.
- Keep prose as written. Joining sentence fragments, prose-to-list conversion, changing nominal endings and reorganizing paragraphs are post-curation, not lint fixes.
- Preserve original line endings, hard breaks and final newlines outside the selected changes. A missing fence with an ambiguous endpoint is report-only.

## Math

- An approved inline/display delimiter repair can replace `$`/`$$` or move delimiter lines around an identified expression. Preserve its entire inner payload byte for byte, including spacing and text.
- Example: `The window is $$ 2 \times 2 $$ and the stride is 2.` can become `The window is $ 2 \times 2 $ and the stride is 2.` when that exact delimiter change is selected. The payload ` 2 \times 2 ` and surrounding prose are unchanged.
- Treat the payload as opaque bytes from the independent original, including padding. Build new delimiters around those bytes instead of retyping or trimming the expression. For an identified `$$...$$` span becoming `$...$`:

  ```python
  payload = original_span[2:-2]
  replacement = b"$" + payload + b"$"
  # Extract the actual changed span from the candidate, then check it independently.
  assert candidate_span[1:-1] == payload
  ```

  Compare actual original/candidate payloads before replacement and after saving. A reverse replacement of the whole new expression with the old one checks the outer diff, but can conceal changed contents; it is not the required payload check. Do not normalize whitespace or call `strip()` in this comparison.
- Keep numbers, variables, operators, indices, bounds, conditions and `\text{...}` contents. Do not add braces, translate glyphs/macros, simplify, derive, or rewrite an expression under a formatting request.
- Plain text or backticks may be literal code/identifiers. Report uncertain math intent rather than converting it to LaTeX automatically. Matrix re-representation and choosing whether a pipe means absolute value or a condition are content decisions.
- Balance delimiters and compare the payload to the original. Render checks are supplementary, never a replacement for preservation checks.

## Code

- Fence repairs preserve all contained bytes and existing language information; add or replace a language only when explicitly selected and known.
- Leave code and output intact by default. To format the payload itself, require a selected language-aware change and an installed formatter on an isolated copy.
- Independently verify literal/comment contents, ordered tokens and program structure with suitable language tooling. For Python, compare ASTs without source-position attributes and the ordered non-whitespace tokens including comments, strings and numbers; do not run the note's program.
- A formatter's successful exit or parse success alone is not a preservation proof. If the relevant check is unavailable, report the format issue and keep code bytes unchanged. Indentation may change control flow.

## Tables

- Repair selected separator rows to at least three hyphens per column while retaining each existing alignment colon. Example: `| :-- | --: |` → `| :--- | ---: |`.
- Preserve header/cell payloads, numeric spelling (`1.00` stays `1.00`), units, expressions, links and row/column order. Boundary padding/escaping is formatting only when the decoded cell boundaries and content are unambiguous.
- Escaped pipes, inline code, formulas and wikilink aliases can contain `|`. Use a Markdown-aware parser or explicit byte boundaries; never assume every pipe is a column separator.
- Empty cells remain empty. Mismatched columns with uncertain ownership, plain-text grids and table-to-matrix conversions are report-only; do not infer or move values.

## Verification

Record each approved literal before/after span, check it against the current candidate, and compare all protected content with the independent original. Apply only those patches; broad reformatting is outside the plan. For metadata-only changes use `tow verify-body`; it intentionally rejects any changed body and is not a verifier for these format transformations. Keep ambiguous/unverified repairs pending without claiming success.
