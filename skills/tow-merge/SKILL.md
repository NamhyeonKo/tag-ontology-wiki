---
name: tow-merge
description: >-
  Use when overlapping vault notes need a canonical owner, absorption, replacement,
  coexistence, or splitting. Triggers: "기존 문서랑 합쳐줘", "중복인데 정리해줘",
  "이미 있는 노트에 합쳐", "정본 어디로 할지 정해줘", "이 노트 둘로 나눠줘".
---

# tow-merge

Reconcile notes covering the same concept using [concept ownership](../tow-review/references/concept-ownership.md). Read the [conventions](../../docs/methodology.md) and `tow config`. Merely related notes can share tags/categories and optional `tow-link` links instead of merging. Each merge case needs the user's strategy selection, including when called from an approved intake/review batch.

## Workflow

1. **Establish candidates.** Read each pair/group's identity, source, level and audience (exam summary, canonical concept, lecture notes).
2. **Classify overlap** with the table below and choose the canonical owner using the ownership rules. Ask when ambiguous.
3. **Select one case at a time.** Present 2–4 strategies for the current case, each with a resulting heading/file preview and exact losses. Ask about the next case only after this case is selected. Accept the user's alternative; repeat a recommendation at most once.
4. **Inventory preservation before editing.** For every disappearing H2/H3 section, table, code block and footnote-like fact, record `transfer → destination section`, `summary → canonical detail + link`, or `discard → explicit user choice`. Any discard needs an additional confirmation of the listed facts before execution. Stop and revisit the strategy if anything has no destination.
5. **Execute the selected strategy.** Back up uncommitted originals under the conventions. Edit body content with [Markdown notation](../tow-check/references/markdown-format.md), preserving transferred tables/math/code; merge frontmatter below; leave a summary/link when selected. Verify the actual fact destinations in a separate call **before deleting** an absorbed/replaced original.
6. **Repair inbound links across the authorized vault.** Rewrite deleted/renamed targets as `[[Canonical|original display]]`, or `[[Canonical#Section|original display]]` for section absorption. Preserve surrounding sentences and update changed files' dates. Report inaccessible/private scope rather than claiming it was checked. Combined notes retain their selected secondary categories/tags; register missing values through `tow-classify`/`tow-tag-sync` before use.
7. **Verify and report.** Run `tow-check` on changed/repair notes and verify zero broken links in that scope. If tags were combined, run `tow ontology usage` and propose removing redundant broader tags rather than silently deleting them. Report each selected strategy, transferred facts, deleted files, inbound repair count and pending case/decision.

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

Retain the conventions' schema/order and unrelated valid fields. Link repair, rather than invented aliases, preserves navigation from removed titles.
