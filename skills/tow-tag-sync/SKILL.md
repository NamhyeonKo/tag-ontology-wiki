---
name: tow-tag-sync
description: >-
  Use when reconciling the concept tags (`tags:`) the user attached to notes in a TOW vault
  with the tag dictionary — registering new concepts with aliases, description, and broader
  placement, merging or renaming variant tags across notes, and reviewing the ontology.
  Triggers: "I added tags", "add these to the tag dictionary", "sync the tag dictionary",
  "find/merge duplicate tags", "where does this tag fit in the ontology?", "태그 달았어",
  "태그 사전에 추가해줘", "Tag-Dictionary 동기화", "중복 태그 확인/병합", "온톨로지 위치 봐줘".
---

# tow-tag-sync

Checks the concept tags on notes against the tag dictionary (the source of truth, one concept per line) and registers or merges them. Choosing a note's `tags:` is the user's call, so this skill changes a note's `tags:` only for an approved merge, rename, alias replacement, format fix, or dropped broader tag. The dictionary file changes only through `tow ontology plan`/`apply`.

Before starting, read the [TOW conventions](../../docs/methodology.md): they define the `tow` command used below, the dictionary model and writing rules (§6), and when a tag belongs on a note (§3).

```json
"hnsw": {"aliases": ["Hierarchical Navigable Small World"], "description": "An ANN index that searches a layered graph from the top layer down", "broader": ["ann-index"]},
```

## Workflow

1. **Compare**: `tow ontology usage [path] --json` (read-only). It returns unregistered tags with the notes using them and similar tags (`unregistered`), tags written as an alias or in different case (`nonCanonical`), unused dictionary entries (`unused`), a broader and a narrower tag on one note (`redundant`), and warnings (`issues`) such as `name-format` and `unplaced` (no `broader`). Tag counts come from `tow lint [path]`.
2. **Judge** each unregistered tag as one of:
   - **New concept**: draft aliases and a description, plus `broader` candidates. Find the closest existing concept with `grep -i` on the tag dictionary and `tow ontology show <tag> --json` (`paths` is its place in the taxonomy); if nothing fits, propose a new grouping node. A new top-level field (`broader: []`) needs its own confirmation.
   - **Variant of an existing tag**: propose a merge, naming which one is canonical and which become aliases.
   - **Same name, different concept**: propose names that tell them apart (`hybrid` mode ≠ `hybrid-search`).
   - **Identifier**: a value that names one specific thing, such as a CVE ID, becomes a lowercase tag (`CVE-2026-41266` → `cve-2026-41266`) registered under its kind (`cve`). An official spelling that differs only in case can't be an alias (dictionary rule), so put it in the `description` together with the item's name.
   Alongside these, propose replacing alias tags with the canonical tag, fixing format violations, and dropping the broader tag of each broader + narrower pair.
3. **Approve**: show the judgement table and get one approval for the batch. Apply requested changes and show it again.
4. **Register**: write the approved items as a changes file (`add`, `edit`, `delete`; start an existing tag's `draft` from the `draft` in `tow ontology show <tag> --json`) in a temporary folder. Check the `diff` and `issues` of `tow ontology plan <changes.json> --json`, then write with `tow ontology apply <changes.json> --base <base from plan> --json`. On exit code 3 (conflict), start again from `plan`. Variants move into the `aliases` of the canonical tag's `draft`. Approved merges, replacements, fixes, and dropped tags change only the `tags:` value of the affected notes (and `updated`, conventions §4).
5. **Done** when `tow ontology usage` shows no `unregistered` or `nonCanonical` entries, `tow ontology check` reports `ok`, and `tow lint` prints `OK`. If notes changed, confirm the body outside the frontmatter is unchanged. Report the number of registered entries, the merged notes, and the remaining warnings.

## Consolidation and ontology review

When the user asks for consolidation, or `usage` keeps reporting the same similar tags, show the candidates as a table and, after approval, handle them with steps 4–5. To review the taxonomy visually, use the Tag Ontology plugin's graph view in Obsidian; to collect the notes under a concept, use `notePaths` from `tow ontology show <tag> --notes --json`.

When `tow lint` reports legacy notes (classification values such as `type/*` or domains still in `tags:`), report them as they are: moving those values into classification fields is outside this skill.
