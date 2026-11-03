---
name: tow-review
description: >-
  Use when checking an organized vault domain, category, or project for concept ownership,
  duplicate explanations, over-splitting, mixed topics, missing hubs, isolation, or project
  direction. Triggers: "review this domain", "any duplicate content?", "is there a hub
  note?", "this note is too big", "clean up the project docs".
---

# tow-review

Review a group of notes, propose a health plan, then route selected fixes to their owning skills. Read the [conventions](../../docs/methodology.md), `tow config`, and [concept ownership](references/concept-ownership.md), which owns the judgment criteria. Independent search intent and ownership matter more than file count.

| Finding | Executor |
| --- | --- |
| Format, shape, broken references | `tow-check` |
| Merge, split, return fragments to source | `tow-merge` |
| Existing-mention links for isolated/hub notes | `tow-link` |
| Classification supplements/corrections | `tow-classify` |
| Concept-tag dictionary consistency | `tow-tag-sync` |
| Create/enrich a hub | This skill, using concept ownership §5 |

## Workflow

1. **Scope.** Use the named domain/category/project folder or explicitly selected notes; ask if unspecified. Use the shared CLI-first policy for discovery. Exclude history only where that role/exclusion is adopted or requested; respect private/ignored input policy. Review works without folders matching PARA, frontmatter or dictionaries.
2. **Read every scoped note**, including the whole body and H2/H3 structure. Obtain `tow-check` report-mode findings for each.
3. **Ownership/cohesion.** Classify every note as appropriate, over-split, mixed, source fragment, or duplicate owner using concept ownership §4. Separate ambiguous canonical choices for the user.
4. **Hub.** When at least three independent notes lack a hub, include a hub proposal; also evaluate a map whenever requested. Use domain identity and conceptual subgroups, one-line linked summaries and appropriate learning order, rather than copied child bodies. A new hub follows the user's selected location/schema, including no frontmatter. Add TOW type/category/tags only where adopted and approved.
5. **Duplicates.** Flag repeated complete explanations/lists; a hub's `[[Note]]: one-line summary` is normal. Before trimming, map every fact to its surviving owner.
6. **Connections/classification/tags.** Inspect classification fields and shared concept tags. Distinguish:
   - **Isolation:** inspect the vault's actual navigation: inbound/outbound wikilinks, hubs, body/frontmatter tags and meaningful shared properties. Missing TOW fields alone are not isolation. Propose supported connections; offer tags only as an optional user choice and send existing-mention links to `tow-link`.
   - **Hub omission:** connected by tags but absent from the domain hub's index. Propose a hub addition.
   Group changes by their executor, preserving user ownership of concept tags.
7. **Project direction**, when the scope is an actual project: check its established direction/history convention, if any. The TOW hub/status-table/banner/history recipe applies only where adopted; propose any move explicitly. Report this axis as inapplicable when there is no relevant project convention.
8. **Plan → approval → execution.** Present one plan covering ownership, duplicate/hub/link/classification/tag/project changes and their affected paths. Run only selected work. Delegated merges still require sequential case-by-case strategy choices and separate discard confirmation; category retroactive classification is a separate decision. Existing explicit selections settle only their stated choices.
9. **Verify and report.** Re-run applicable `tow-check` checks over the authorized scope and new/changed notes. Unresolved findings under adopted rules remain explicit pending decisions; optional missing frontmatter/dictionaries are not defects. Report fact ownership, hubs created/enriched, merges/splits/source returns, links, selected classification/tag changes and unavailable checks.
