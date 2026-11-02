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

1. **Scope.** Use the named domain/category/project folder or explicitly selected notes; ask if unspecified. Exclude configured project history by default and respect private/ignored input policy.
2. **Read every scoped note**, including the whole body and H2/H3 structure. Obtain `tow-check` report-mode findings for each.
3. **Ownership/cohesion.** Classify every note as appropriate, over-split, mixed, source fragment, or duplicate owner using concept ownership §4. Separate ambiguous canonical choices for the user.
4. **Hub.** When at least three independent notes lack a hub, include a hub proposal; also evaluate a map whenever requested. Use domain identity and conceptual subgroups, one-line linked summaries and appropriate learning order, rather than copied child bodies. A new hub gets its appropriate type, registered primary category and `tags: []`.
5. **Duplicates.** Flag repeated complete explanations/lists; a hub's `[[Note]]: one-line summary` is normal. Before trimming, map every fact to its surviving owner.
6. **Connections/classification/tags.** Inspect classification fields and shared concept tags. Distinguish:
   - **Isolation:** no concept tag or secondary category shared with domain peers **and** no inbound link except from its source. Propose tags for the user to select; send existing-mention links to `tow-link`.
   - **Hub omission:** connected by tags but absent from the domain hub's index. Propose a hub addition.
   Group changes by their executor, preserving user ownership of concept tags.
7. **Project direction**, when scope belongs to configured projects: check the hub's current direction and document-status table. Superseded/rejected documents should have a dated replacement/reason banner and move to configured project history, with hub updates; active/on-hold documents and dated logs follow conventions §2. Report this axis as inapplicable for non-project scopes.
8. **Plan → approval → execution.** Present one plan covering ownership, duplicate/hub/link/classification/tag/project changes and their affected paths. Run only selected work. Delegated merges still require sequential case-by-case strategy choices and separate discard confirmation; category retroactive classification is a separate decision. Existing explicit selections settle only their stated choices.
9. **Verify and report.** Re-run `tow-check` over the scope and any new/changed notes. Broken references, H1 and frontmatter issues must be zero **or explicitly listed as pending user decisions**. Report fact ownership, hubs created/enriched, merges/splits/source returns, links, classification and tag changes, with unresolved choices.
