# Preservation and post-curation evaluation — 0.4.0 candidate

## Scope

User-approved follow-up to PR #15, merged into `dev` at `5caec7f`. The eleven skill names are retained. Ordinary maintenance manages frontmatter and content-preserving formatting; body aftercare requires a selected operation and the user's rules/template. No new formatter, dependency, model service or universal semantic-verification engine is added.

The helper's new `verify-body` compares exact body bytes after metadata-only changes. It is intentionally independent of dictionaries, Node and `tow.json`. It rejects outside-vault paths, self/hard-link comparisons, unavailable snapshots and unterminated leading frontmatter. It does not validate YAML or the meaning of body-format changes. Formatting remains governed by explicit patches, protected-payload checks and host/model compliance with the skill.

## Automated checks

- Thirteen new command-level tests were observed failing before `verify-body` existed, then passing after implementation.
- Coverage includes custom frontmatter with invalid/unneeded `tow.json`, no frontmatter, body thematic breaks, BOM, LF/CRLF and final-newline preservation, prose/math/code/table byte changes, self/hard-link comparisons, traversal, outside symlinks, missing files and unterminated frontmatter.
- Full suite against published `tag-ontology@0.1.2`: **104 passed**, including five real-CLI integration tests. Ruff lint/format and strict Pyright passed. Final PR CI is a separate check.

## Low-cost model consumers

Tool-backed `gpt-6-luna` agents at medium effort were explicitly given the relevant skill and synthetic vault scope. These are skill-consumer runs, not installed-host discovery tests. No actual user vault, native Obsidian session or note program was accessed/executed. Independent main-agent oracles compared actual saved bytes and protected structures; model assertions alone were not accepted.

### Baseline (five cases, pre-change instructions)

Metadata and delimiter edits were attempted, already formatted Python was left intact, and a generic Example sentence was generated without a supplied writing rule/template. The table fix stopped because the previous rule required removing alignment while the user required preserving it. These two instruction conflicts established the need for the post-curation gate and user-alignment precedence. The consumer also reported comparing a file to itself; that was not accepted as preservation evidence.

### First changed-instruction run (nine cases)

| Case | Independent result |
| --- | --- |
| Custom metadata | Only `status: reading` → `done`; other fields/body unchanged; `verify-body` passed |
| Math delimiters | **Failed**: model trimmed original inner spaces while claiming payload preservation |
| Already formatted code | Exact bytes unchanged; formatter check/diff only, no program execution |
| Table separators | `:--`/`--:` → `:---`/`---:`; existing alignment, numeric spelling, escaped wikilink pipe, formula and other cells unchanged |
| Missing writing rule | Asked for source/rule; empty section and filled prose unchanged |
| Ambiguous math/code/table | Literal `R^V`, unknown cell and unknown code indentation left unchanged; uncertainty reported |
| Explicit user template | Added only the supplied sentence to the selected empty section; filled content/metadata unchanged |
| Verbatim filing | Copied to selected `Reading/` destination, independently verified, then removed selected source |
| Review only | Findings only; no hub, metadata, template or note writes |

The first math attempt is retained as a failure. Its reverse-replacement assertion mapped the whole edited expression back to the old expression, concealing padding loss. The notation guide now shows constructing delimiters around original opaque payload bytes and requires independent comparison of actual original/candidate contents without trimming or normalization.

### Targeted follow-up

- Five fresh formula cases included padding, `\text{a  b}`, indices/inequality, `1.00`, fractions and macros. All five saved outputs matched delimiter-only expected bytes. Main-agent checks separately compared original and final inner payloads. The consumer used marker-only replacement/full-file recovery checks rather than independently extracting payloads; this procedural limitation is retained rather than relabeled as model-side payload verification.
- A real Python payload-format case changed only `emit( "a  b" )` → `emit("a  b")` and `finish( )` → `finish()`. Both consumer and main checked AST equality, ordered non-whitespace tokens including strings/numbers/comments, and the unchanged Markdown envelope. No program was executed.
- A chosen transfer/coexist case copied B's paragraph verbatim into A's existing selected section; A's original prefix and all of B were byte-identical. No summary, metadata, link or deletion was added.

## Independent review and privacy regression

A read-only review found one P2: hidden vault-local scratch copies could move explicitly selected ignored/private content into Git-stageable `.tow-tmp/`, especially after failed/interrupted batches. A synthetic Git reproduction confirmed an ignored source produced a stageable hidden backup.

The preservation contract, post-curation contract and both installation guides now require planning/approving protection before copying, prospective `git check-ignore` checks in Git vaults, existing protected locations where possible, and stopping/proposing protection when none exists. This protects retained failed/interrupted batches too; ignore rules are not silently changed. The reviewer confirmed the instruction-level finding was resolved.

A fresh low-cost consumer selected `private/.tow-tmp/...` under an existing ignored `private/` tree, checked both prospective paths before copying, changed only the selected status, ran `verify-body` before/after replacement and cleaned the batch. Main-agent byte/ignore/index checks confirmed no stageable or retained private copies. An expected `diff` exit 1 initially skipped cleanup in the consumer's combined command; follow-up verification/cleanup completed. No real private data was used.

## Reproducing the scenarios

[Fixtures and exact expected outputs](../tests/fixtures/preservation/cases.json) retain seventeen inputs/oracles, including the failed first math output. Copy a case's `before` into `Note.md` (or its `beforeFiles` into the named files) in a new disposable vault; supply `rules` and `request`. The template case also supplies `TEMPLATE.md`; filing uses an existing `Reading/` directory. The private case initializes a disposable Git repo with the supplied `gitIgnore` before copying its synthetic input. Never run a consumer against the committed fixture itself or reveal expected outputs to it. Compare actual note paths/bytes with `expectedPath`/`expectedAfter` or `expectedFiles`, and verify questions/no-writes for `requiresUserInput` cases. Saved expected bytes do not replace semantic checks for code transformations or private-scratch exposure checks.

## Limits

These are individual synthetic executions, not a statistical reliability claim for low-cost models. The initial math false-preservation report demonstrates why independent checks remain necessary. The revised private-scratch policy is instruction-enforced; `verify-body` itself neither creates snapshots nor enforces ignore protection or approvals. It is not a YAML, Markdown, math or code semantic validator. Installed Claude/Codex/Antigravity discovery, GUI rendering, native Obsidian runtime and arbitrary user templates/languages were not validated in this run. No 0.4.0 release or history rewrite was performed.
