# Markdown notation details (tables, math, code)

Read this when checking or normalizing the tables, math, and code in a note's body. The principles are in the [TOW conventions](../../../docs/methodology.md) §5; this file has the detailed rules and examples. Every conversion **preserves content**: cell values, math, code, and plain sentences stay the same.

## 1. Tables

- Headers are written `| Header 1 | Header 2 |`.
- Separator rows **always use `| --- |` for every cell** (exactly three hyphens, one space on each side), for example `| --- | --- |`. Existing separator rows are normalized to this form too: long dashes and alignment colons (`:---`, `---:`, `:---:`) become `---`.
- Every row gets the same number of columns and uniform spacing at cell boundaries; cell content, column order, and empty cells are preserved.
- Space- or dash-aligned tables with clear column boundaries become pipe tables. A pipe character alone doesn't make a plain sentence or an absolute-value formula a table.
- Tables are for data with meaningful column headers. A grid of numbers (a matrix) is a `bmatrix` (§2), not a table with an empty header row (`|  |  |`).

## 2. Math

**The test is whether it reads naturally as part of a sentence**, not whether text comes before it.

- **Inline `$…$`**: short expressions, symbols, and values read as part of a sentence (mid-sentence or at the end, list items, table cells, variable descriptions).
  - `If the window is $2 \times 2$ and the stride is 2`
  - `a filter of size $h$`
  - `If the convolution result before activation is $[26,41,35]$ and the bias is $b=2$, then $c = [28,43,37]$.`
- **Block `$$`**: large expressions that read as a unit on their own (multi-line aligned equations, `bmatrix`, `aligned`, `cases`, definitions or results with large fractions or sums). The opening and closing `$$` each sit on a line of their own.
- A `$$` block always sits between sentences, never inside one:

  ```text
  [before] If the window is / $$ 2 \times 2 $$ / and the stride is 2   ← one sentence cut into three pieces
  [after]  If the window is $2 \times 2$ and the stride is 2
  ```

- **Math written as plain text or code becomes LaTeX**: math symbols and expressions in backticks (`` `W` ``, `` `h_{t-1}` ``) or in a ` ```text ` block, and plain-text math without `$` (`Σ`, `xᵀW`, `R^V`, `a_i`). LaTeX commands in backticks (`` `\sigma` ``) don't render, so they always move into `$…$`. Words inside math are wrapped in `\text{…}` (`\text{softmax}`).
- **Math in tables**: a `|` (absolute value, conditional) inside `$…$` in a cell reads as a column boundary, so write `\vert` or `\mid`.
- **Matrices**: `\begin{bmatrix} 12 & 20 \\ 8 & 12 \end{bmatrix}`.

## 3. Code

The same test as math: **does it read naturally as part of a sentence?**

- A short one-line piece of code, token, or example phrase read as part of a sentence is inline code within the sentence. When a code block cuts a sentence, join the two sides into one sentence.

  ~~~text
  [before] A combination used widely in practice:

  ```text
  Skip-gram + Negative Sampling
  ```
  ~~~

  → [after] ``A combination used widely in practice: `Skip-gram + Negative Sampling` ``

- Code that reads as a unit on its own (a one-line example standing alone, multi-line code, output, diagrams) keeps its fenced code block, for example a ` ```text k-fold Cross Validation ``` ` standing alone after a list.
- Code content stays unchanged. A `#` (comment) inside a code block is not a heading.

## 4. Check order

1. `$`/`$$` pairs, fence pairs, table column counts and separator rows.
2. **Sentence flow**: are the lines around a `$$` sentence fragments; does a one-line code block cut a sentence?
3. Is any math left in backticks or plain text (§2)?
4. Compare math, table cell values, code, and links before and after the conversion. When a span can't be determined, report it rather than filling it in by guess.
