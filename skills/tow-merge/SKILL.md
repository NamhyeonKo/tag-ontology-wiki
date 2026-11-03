---
name: tow-merge
description: >-
  Use when overlapping vault notes need a canonical owner, absorption, replacement,
  coexistence, or splitting. Triggers: "merge this with the existing note", "these notes are
  duplicates", "which note should be canonical?", "split this note in two".
---

# tow-merge

Reconcile notes covering the same concept using [concept ownership](../tow-review/references/concept-ownership.md). Read the [conventions](../../docs/methodology.md) and `tow config`. Merely related notes can share tags/categories and optional `tow-link` links instead of merging. Each merge case needs the user's strategy selection, including when called from an approved intake/review batch.

Ownership is based on content, not required PARA folders/frontmatter. Keep the selected destination's schema or lack of metadata. The merge table below is the TOW recipe, not permission to invent fields or reinterpret custom ones; reconcile conflicting custom properties in the strategy plan, preserving unrelated values and following the adopted date policy.

## Workflow

1. **Establish scope before reading/searching.** Read the conventions' [scope rules](../../docs/methodology.md#scope-before-reading-note-contents), `tow config`, and this vault's ignore/private rules. Use names-only listings to establish an eligible-file list and explicit exclusions; this step is complete only when those boundaries are known. If a required read is blocked, resolve that scoped permission or stop. Then read each selected pair/group's identity, source, level and audience (exam summary, canonical concept, lecture notes).
2. **Classify overlap** with the table below and choose the canonical owner using the ownership rules. Ask when ambiguous.
3. **Select one case at a time.** Present 2–4 strategies for the current case, each with a resulting heading/file preview and exact losses. Ask about the next case only after this case is selected. Accept the user's alternative; repeat a recommendation at most once.
4. **Inventory preservation before editing.** For every disappearing H2/H3 section, table, code block and footnote-like fact, record `transfer → destination section`, `summary → canonical detail + link`, or `discard → explicit user choice`. Any discard needs an additional confirmation of the listed facts before execution. Stop and revisit the strategy if anything has no destination.
5. **Execute the selected strategy.** Back up uncommitted originals under the conventions. Edit body content with [Markdown notation](../tow-check/references/markdown-format.md), preserving transferred tables/math/code; merge frontmatter below; leave a summary/link when selected. Verify the actual fact destinations in a separate call **before deleting** an absorbed/replaced original.
6. **Repair inbound links within step 1's eligible files.** Use the shared CLI-first policy with that file list or its exclusions; a whole-root Grep followed by filtering already reads private inputs. Rewrite deleted/renamed targets as `[[Canonical|original display]]`, or `[[Canonical#Section|original display]]` for section absorption. Preserve surrounding sentences and follow the adopted date policy. Report inaccessible/private scope rather than claiming it was checked. Retain selected categories/tags where used; register missing values only for adopted dictionary-backed features.
7. **Verify and report.** Run applicable `tow-check` checks on changed/repair notes and verify zero broken links in that scope. If ontology-backed tags were combined and the dictionary is available, run scoped `tow ontology usage` and propose removing redundant broader tags rather than silently deleting them. Report skipped checks, each selected strategy, transferred facts, deleted files, inbound repair count and pending case/decision.

## Overlap and strategies

| Type | Situation | Candidate strategies |
| --- | --- | --- |
| `FULL` | Both cover the whole concept | Absorb / replace |
| `SECTION` | A's section is B's full subject | Transfer canonical ownership + summary/link |
| `LEVEL` | Same concept at different depths | Transfer + summary/link / coexist + links |
| `HUB` | One map, one content note | Absorb into hub section / coexist + links |
| `PARTIAL` | Overlap plus independent material | Transfer only the overlap + summary/link |

| Strategy | Result | Loss to disclose |
| --- | --- | --- |
| Absorb | Move content into canonical sections; delete other note after verification (normally keep the existing note for new-vs-existing) | None when every fact transfers |
| Transfer + summary/link | Canonical detail in one owner, concise linked summary in the other | Detail removed from the summary side; retained at the owner |
| Coexist + links | Keep both, mutual links and shared selected tags/categories | None; duplication remains |
| Replace | Overwrite one with the other | Unique context/facts; explicitly list and reconfirm |
| Split | Give mixed content separate owners | None; file count increases |

Prefer absorption or transfer with preserved facts. A preview must identify actual destination headings and show the resulting summary/link, not just name a strategy.

## Frontmatter merge

| Field | Handling |
| --- | --- |
| `description` | Rewrite one sentence for the combined identity, rather than concatenate descriptions |
| `category` | Union; one primary matching the final identity, other values secondary |
| `tags` | Union; deduplicate canonical values and resolve aliases |
| `source` | Union list |
| `aliases` | Union of true synonyms of the final title; absorbed titles qualify only when synonymous, not automatically |
| `created` | Earliest existing date |
| `updated` | Processing date |

Retain the adopted schema/order and unrelated fields. Missing metadata stays absent unless its addition is selected in the merge plan. Link repair, rather than invented aliases, preserves navigation from removed titles.
