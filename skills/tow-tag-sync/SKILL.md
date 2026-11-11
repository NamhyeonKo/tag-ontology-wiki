---
name: tow-tag-sync
description: >-
  Use when reconciling vault concept tags with the tag dictionary or importing project-only
  concepts from a named project. Triggers: "I added tags", "add these to the tag dictionary",
  "sync the tag dictionary", "import project concepts", "find/merge duplicate tags",
  "where does this tag fit in the ontology?".
---

# tow-tag-sync

This skill works only inside the vault. From another project, stop and use `tow-query` to find vault content or `tow-send-vault` to bring content in.

Before any write, run `tow config` and verify the vault root it prints contains the current working directory and every file being edited; otherwise stop and route the request as above.

Checks the concept tags on notes against the dictionary and registers or merges approved concepts. Choosing a note's `tags:` is the user's call; note metadata changes only for an approved merge, rename, alias replacement, format fix, or dropped broader tag the note doesn't explain directly. The vault tag dictionary lives at `tow/tag-dictionary.json` by default (or the configured `tagDictionary` path); vault rules are in `tow/tags.md`. Project dictionaries and manuals remain in project `.tow/`.

Before starting, read the [TOW conventions](../../docs/methodology.md), the vault's `tow/tags.md` manual when present, and the dictionary model/rules in the [TOW recipe](../../docs/recipe.md) §6. If the tag dictionary is absent, propose the prerequisite and exact path for approval; don't initialize it without approval. No category dictionary, inbox or PARA folders are required. If ontology adoption is declined, keep notes unchanged and offer `tow-tag-suggest` or ordinary tag search. The CLI's `usage` and `show` include frontmatter and body tags; scoped `scan` separates their origins. Dictionary `apply` changes neither representation on notes. Keep note edits in frontmatter; body-tag changes need a separate explicit body-edit plan.

For this workflow, read the configured tag dictionary JSON and the vault's `tow/tags.md` manual before planning ontology changes.

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

`tow` is not a command on your PATH: run the executable `scripts/tow.py` two directories above this file by its absolute path (with `python3` if the host can't execute it), for example `"<plugin-root>/scripts/tow.py" config`.

## Workflow

1. **Compare**: follow the conventions' scope rule before `tow ontology usage [path] --json` or any `show`: both read the whole configured scope minus exclusions, even with positional usage paths or without `--notes`. If those reads are not authorized, use exact-path `scan` plus relevant dictionary entries and report aggregate checks unavailable. If `usage` stops because the search scope is empty, no note was read: resolve the scope through `tow-setup`, or pass the user's exact folders, before judging any tag. `usage` returns unregistered tags with their notes and similar tags (`unregistered`), alias/case variants (`nonCanonical`), unused entries (`unused`), broader + narrower pairs on one note to review (`redundant`), and dictionary warnings (`issues`). Identify each finding's frontmatter/body origin before proposing note edits. Helper lint counts frontmatter tags only. Never remove an entry solely from a partial-scope `unused` result.
2. **Judge** each unregistered tag as one of:
   - **New concept**: draft aliases and a description, plus `broader` candidates. Find the closest existing concept with `grep -i` on the tag dictionary and `tow ontology show <tag> --json` (`paths` is its place in the taxonomy); if nothing fits, propose a new grouping node. A new top-level field (`broader: []`) needs its own confirmation.
   - **Variant of an existing tag**: propose a merge, naming which one is canonical and which become aliases.
   - **Same name, different concept**: propose names that tell them apart (`hybrid` mode ≠ `hybrid-search`).
   - **Identifier**: a value that names one specific thing, such as a CVE ID, becomes a lowercase tag (`CVE-2026-41266` → `cve-2026-41266`) registered under its kind (`cve`). An official spelling that differs only in case can't be an alias (dictionary rule), so put it in the `description` together with the item's name.
   Alongside these, propose replacing alias tags with the canonical tag and fixing format violations. Never propose dropping a broader tag just because `usage` lists it as `redundant`; review it in step 3.
3. **Review broader + narrower pairs**: take each `redundant` row (`tag` is the broader tag, `narrower` the narrower tags on the same note) and each pair a proposed alias replacement would create (`usage` doesn't match aliases, so it can't see that pair yet).
   - Run `tow ontology scan <paths…> --json` on exactly those notes. Read each note's title (`path`), `frontmatter.description`, `frontmatter.aliases`, `tags`/`bodyTags` and `headings`, and `grep -i` the dictionary line of the broader tag for its aliases.
   - **Keep** the broader tag when this shows the note explains that concept directly, by the evidence in recipe §3 "Broader and narrower tags together". When the title, description and headings don't settle it, read only the passages that mention the broader concept or its aliases.
   - Propose a **drop candidate** only when the note uses the broader concept as background, as the field its topic belongs to, or in a passing mention. If the evidence stays unclear, keep the tag and say so.
   - A broader tag that is only a body tag (`bodyTags`) stays report-only here; dropping it needs a separate body-edit plan.
4. **Approve**: show the judgement table, listing each reviewed pair as `keep` or `drop candidate` with its evidence (the heading, description or passage), and get one approval for the batch. Apply requested changes and show it again.
5. **Register**: write the approved items as a changes file (`add`, `edit`, `delete`; start an existing tag's `draft` from the `draft` in an authorized `tow ontology show <tag> --json`) in a new privacy-protected temporary folder **inside the vault root**, for example `.tow-tmp/<batch>/changes.json` only when that location is already protected. The CLI rejects changes files outside `--root`; hidden folders stay out of note scans but are not automatically Git-ignored. Check the complete `diff` and `issues` of `tow ontology plan <changes.json> --json`, record the reviewed changes-file bytes/hash, then write with `tow ontology apply <changes.json> --base <base from plan> --json` only while those changes bytes remain identical. The base protects dictionary bytes, not the changes file or note contents. On any drift or exit code 3 (conflict), start again from `plan`. Once `apply` has written, or the batch is dropped, delete only this batch folder (and `.tow-tmp/` when it is empty). Variants move into the canonical tag's aliases. Approved note changes affect only selected `tags:` values plus dates under the adopted policy; custom metadata stays unchanged.
6. **Done** when scoped `tow ontology usage` has no unresolved selected `unregistered` or `nonCanonical` entries, `tow ontology check` reports `ok`, and the batch folder is gone. Kept `redundant` pairs remain in `usage` output and don't block completion. Run `tow lint` only when the note schema and category dictionary make it applicable; unrelated schema findings do not block ontology work. If notes changed, confirm the body outside frontmatter is unchanged. Report registered entries, merged notes, kept pairs with their evidence, remaining warnings, unavailable checks and body-tag coverage limits.

## Import project-only concepts

When the user names a project path while working inside the vault, first run `tow project concepts <project_path>` as a read-only preview and show its output. Only additions absent from the vault dictionary are included; never apply project copies of concepts that already exist in the vault. After approval, save the complete output from `tow project concepts` directly as the changes file (it is already a complete changes document; do not extract the array) in a protected temporary folder inside the vault, run `tow ontology plan <changes-file> --json`, and show the complete diff/issues before applying. This is an additions-only import and does not edit project metadata or notes.

## Consolidation and ontology review

When the user asks for consolidation, or `usage` keeps reporting the same similar tags, show the candidates as a table and, after approval, handle them with steps 5–6. To review the taxonomy visually, use the Tag Ontology plugin's graph view in Obsidian; to collect the notes under a concept, use `notePaths` from `tow ontology show <tag> --notes --json`.

When `tow lint` reports legacy notes (classification values such as `type/*` or domains still in `tags:`), report them as they are: moving those values into classification fields is outside this skill.
