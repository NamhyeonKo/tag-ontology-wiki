---
name: tow-tag-sync
description: >-
  Use when reconciling the concept tags (`tags:`) the user attached to notes in a TOW vault
  with the tag dictionary — registering new concepts with aliases, description, and broader
  placement, merging or renaming variant tags across notes, and reviewing the ontology.
  Triggers: "I added tags", "add these to the tag dictionary", "sync the tag dictionary",
  "find/merge duplicate tags", "where does this tag fit in the ontology?".
---

# tow-tag-sync

Checks the concept tags on notes against the tag dictionary (the source of truth, one concept per line) and registers or merges them. Choosing a note's `tags:` is the user's call, so this skill changes a note's `tags:` only for an approved merge, rename, alias replacement, format fix, or dropped broader tag. The dictionary file changes only through `tow ontology plan`/`apply`.

Before starting, read the [TOW conventions](../../docs/methodology.md): they define the `tow` command used below, the dictionary model and writing rules (§6), and when a tag belongs on a note (§3).

This is the optional TOW ontology workflow, independent of PARA and the rest of the metadata schema. Resolve the selected tag dictionary first. If absent, explain the prerequisite and propose its exact location and empty JSON object for approval; create only that selected file before registration. No category dictionary, inbox or PARA folders are required. If ontology adoption is declined, keep notes unchanged and offer `tow-tag-suggest` or ordinary tag search. Body-only tags may be discovered by `tow-query`, but the current ontology CLI manages frontmatter tags; disclose that coverage and obtain a separate explicit plan before transferring body tags or changing their representation.

Changes files contain an ordered `changes` array. For example, registering a concept:

```json
{
  "schemaVersion": 1,
  "changes": [{
    "kind": "add",
    "draft": {
      "name": "hnsw",
      "description": "An ANN index that searches a layered graph from the top layer down",
      "aliases": ["Hierarchical Navigable Small World"],
      "parents": ["ann-index"],
      "children": [],
      "related": []
    }
  }]
}
```

All six `draft` fields are required. An `edit` item also needs `tag` (the existing name); a `delete` item has only `kind` and `tag`. `parents` becomes `broader` in the dictionary. For edits, preserve the complete draft from `show` rather than starting from this add example.

For every selected note-metadata edit, follow the [preservation contract](../../docs/preservation.md): keep independent before/candidate copies, verify only selected metadata values, and require `tow verify-body <before> <candidate>` to pass before replacing the note. This operation does not authorize fixing body format, rewriting prose or invoking post-curation. Dictionary files are verified separately by their own rules.

## Workflow

1. **Compare**: `tow ontology usage [path] --json` (read-only). It returns unregistered tags with the notes using them and similar tags (`unregistered`), tags written as an alias or in different case (`nonCanonical`), unused dictionary entries (`unused`), a broader and a narrower tag on one note (`redundant`), and warnings (`issues`) such as `name-format` and `unplaced` (no `broader`). Tag counts come from `tow lint [path]`.
2. **Judge** each unregistered tag as one of:
   - **New concept**: draft aliases and a description, plus `broader` candidates. Find the closest existing concept with `grep -i` on the tag dictionary and `tow ontology show <tag> --json` (`paths` is its place in the taxonomy); if nothing fits, propose a new grouping node. A new top-level field (`broader: []`) needs its own confirmation.
   - **Variant of an existing tag**: propose a merge, naming which one is canonical and which become aliases.
   - **Same name, different concept**: propose names that tell them apart (`hybrid` mode ≠ `hybrid-search`).
   - **Identifier**: a value that names one specific thing, such as a CVE ID, becomes a lowercase tag (`CVE-2026-41266` → `cve-2026-41266`) registered under its kind (`cve`). An official spelling that differs only in case can't be an alias (dictionary rule), so put it in the `description` together with the item's name.
   Alongside these, propose replacing alias tags with the canonical tag, fixing format violations, and dropping the broader tag of each broader + narrower pair.
3. **Approve**: show the judgement table and get one approval for the batch. Apply requested changes and show it again.
4. **Register**: write the approved items as a changes file (`add`, `edit`, `delete`; start an existing tag's `draft` from the `draft` in `tow ontology show <tag> --json`) in a new hidden temporary folder **inside the vault root**, for example `.tow-tmp/<batch>/changes.json`. The CLI rejects changes files outside `--root`; hidden folders stay out of note scans. Check the `diff` and `issues` of `tow ontology plan <changes.json> --json`, then write with `tow ontology apply <changes.json> --base <base from plan> --json`. On exit code 3 (conflict), start again from `plan`. Once `apply` has written, or the batch is dropped, delete the batch folder (and `.tow-tmp/` when it is empty) so no scratch files stay in the vault. Variants move into the `aliases` of the canonical tag's `draft`. Approved merges, replacements, fixes, and dropped tags change only affected `tags:` values plus dates under the adopted policy; custom metadata stays unchanged.
5. **Done** when scoped `tow ontology usage` has no unresolved selected `unregistered` or `nonCanonical` entries, `tow ontology check` reports `ok`, and the batch folder is gone. Run `tow lint` only when the note schema and category dictionary make it applicable; unrelated schema findings do not block ontology work. If notes changed, confirm the body outside frontmatter is unchanged. Report registered entries, merged notes, remaining warnings, unavailable checks and body-tag coverage limits.

## Consolidation and ontology review

When the user asks for consolidation, or `usage` keeps reporting the same similar tags, show the candidates as a table and, after approval, handle them with steps 4–5. To review the taxonomy visually, use the Tag Ontology plugin's graph view in Obsidian; to collect the notes under a concept, use `notePaths` from `tow ontology show <tag> --notes --json`.

When `tow lint` reports legacy notes (classification values such as `type/*` or domains still in `tags:`), report them as they are: moving those values into classification fields is outside this skill.
