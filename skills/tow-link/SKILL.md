---
name: tow-link
description: >-
  Use when connecting vault notes with Obsidian wikilinks at existing mentions of note
  titles or aliases, including inbound links to newly filed notes. Triggers: "link my
  notes", "connect these notes", "add wikilinks".
---

# tow-link

This skill works only inside the vault. From another project, stop and use `tow-query` to find vault content or `tow-send-vault` to bring content in.

Before any write, run `tow config` and verify the vault root it prints contains the current working directory and every file being edited; otherwise stop and route the request as above.

Wrap existing mentions of other notes in `[[wikilinks]]` for navigation. Read the [conventions](../../docs/methodology.md) and `tow config` first. Tags/categories/dictionaries are not prerequisites for navigation. Preserve words, sentences, headings, sections and existing metadata (including custom `related:`). Use existing target files, once per target at its first eligible body mention.

`tow` is not a command on your PATH: run the executable `scripts/tow.py` two directories above this file by its absolute path (with `python3` if the host can't execute it), for example `"<plugin-root>/scripts/tow.py" config`.

## Workflow

1. **Scope.** Use the note, folder/domain or vault the user names; ask if unspecified.
2. **Target index.** Discover actual filenames and any existing aliases across the eligible vault using the shared search policy: one `tow search` query such as `tow search '"<title>" OR "<alias>"'`, which applies the scope and ignore rules and lists notes mentioning the target in titles, headings or text; host file search only for what it lists under `unavailable`. No frontmatter is required. Apply adopted workflow exclusions and private/ignored rules under the conventions; default PARA/support folder names do not exclude custom-vault notes. Targets may be outside the edit scope, but stay inside the authorized read scope.
3. **Scan.** Apply the matching rules below. Inspect existing wikilinks too: an alias-only target is broken and needs a canonical filename with its original display text. Report missing targets for the user's remove/create/keep decision; do not create a note automatically.
4. **Plan and wait for approval.** Show the table below, then separate skipped, ambiguous and missing-target lists.
5. **Apply selected positions only.** Wrap or correct targets, preserve displayed words/metadata, and follow the adopted date policy without adding new metadata fields.
6. **Verify and report.** Check actual targets, first-mention counts, unchanged surrounding text/metadata and applicable scoped validation. Report additions/corrections, targets, skipped checks and skip reasons per file.

| File | Existing phrase and context | Target note | Proposed notation | Reason |
| --- | --- | --- | --- | --- |
| Attacks.md | “Stored XSS persists…” | Stored XSS | `[[Stored XSS]]` | Longest first mention |
| Attacks.md | “XSS is…” | Cross Site Scripting | `[[Cross Site Scripting\|XSS]]` | Alias; keep display text |

## Matching rules

- **Existence and meaning:** only actual filenames/aliases qualify; skip self-links. For common titles such as Network, Data or Graph, require clear conceptual context. If the first occurrence means something else, continue to the first eligible mention. Multiple matching notes or uncertain meaning require the user's choice.
- **Longest match:** choose the longest specific title/alias at a position (`Stored XSS` before `XSS`). English matching ignores case.
- **Display preservation:** exact title → `[[Title]]`; aliases or different casing → `[[Title|original words]]`. Escape the separator as `\|` inside table cells. Existing links retain their displayed wording when their target is corrected.
- **Once per target:** later eligible mentions remain plain. An existing valid link counts toward that target's first-mention allowance; report conflicting duplicates rather than adding more.
- **Body only:** sentences, lists and table cells qualify. Skip headings, figure captions, quote lines, frontmatter, fenced/inline code, existing wikilink/Markdown-link interiors, and URLs. A target mentioned only in excluded regions is skipped.
- **Existing mentions only:** writing a hub summary requires a separately selected, user-guided `tow-edit` operation after a `tow-review`/`tow-ingest` proposal. Do not insert sentences or force reciprocal links; backlinks provide reverse navigation.

## Intake mode

When `tow-ingest` files new note X, link **outbound** mentions in X and **inbound** mentions of X's title/aliases across the eligible vault. Include all newly filed notes in a batch's target index so they can link to each other. The approved intake link plan authorizes its listed positions without another approval; ask only about newly discovered ambiguity or changes outside that plan. All matching and exclusion rules still apply.
