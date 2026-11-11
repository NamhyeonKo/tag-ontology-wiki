---
name: tow-ingest
description: >-
  Use when the user wants captures or source notes inside the vault filed to destinations
  they choose. Plans first and moves notes verbatim by default; adding metadata, rewriting
  or deriving concept notes happens only for the steps the user selects. Triggers: "process
  my inbox", "file these captures", "intake", "derive concept notes from this source". For
  bringing project documents into the vault, use tow-send-vault.
---

# tow-ingest

This skill works only inside the vault. From another project, stop and use `tow-query` to find vault content or `tow-send-vault` to bring content in.

Before any write, run `tow config` and verify the vault root it prints contains the current working directory and every file being edited; otherwise stop and route the request as above.

Optional post-curation for a selected capture/source batch, including notes `tow-send-vault` left in the inbox. Read the [conventions](../../docs/methodology.md), [post-curation contract](../../docs/post-curation.md), [preservation contract](../../docs/preservation.md) and `tow config`. Filing can be a verbatim move; it does not imply adding frontmatter, rewriting prose, deriving concepts or adopting PARA.

## Workflow

**Read/plan first. Backups, candidates, configuration and note writes begin only after the relevant approval.**

1. **Select inputs and rules.** Use the named batch; an ordinary inbox request selects only top-level Markdown in the user's confirmed inbox. Resolve the chosen destination and applicable user template/rules. A named destination plus a verbatim move is sufficient. Ask about a missing rule needed for a transformation; never default to bundled Resource/Area/paper prose. Inspect private/ignore policy before content reads; ignored inputs need explicit selection. Disclose moves into tracked/public scope.
2. **Inspect every selected source.** Read its original metadata/body, attachments and actual provenance. Use the shared CLI-first policy over eligible paths to find existing owners by title, aliases and concepts. Read adopted dictionaries only when relevant. Obtain `tow-check` report-mode findings; ambiguous format/source/classification remains a choice, not an inferred value.
3. **Plan exact changes.** List source→destination, rule/template source, selected metadata changes, literal format/link/path patches and preserved body regions. Empty TOW-specific fields remain unused in a custom schema. Overlaps are separate `tow-merge` cases. Concept derivation, source rewriting, new hubs and removal of temporary Date/Tag/hint lines require their own explicit selected scope, not implied intake permission. Explain every source fact's destination before any deletion.
4. **Obtain approval.** The batch covers only its listed changes, categories and link positions. Merge cases still need their own strategy choices, discard confirmation and independent destination verification; retroactive classification remains separate. Prior explicit selections settle only their stated decisions.
5. **Execute selected steps.**
   - Copy originals into an independent vault-local scratch batch before changing them. Prepare candidate notes rather than rewriting the only source copy.
   - Apply only selected metadata under the adopted schema. Register values only for chosen dictionary-backed features (`tow-classify`/`tow-tag-sync`); carry only tags the user selected. Validate metadata-only steps with `tow verify-body` before other body operations.
   - File verbatim by default. Use `tow-check` for individually approved format patches and `tow-link` for listed wrappers/target repairs; neither authorizes sentence/caption rewriting. Content generation or source derivation follows an explicitly selected `tow-edit`/`tow-merge` operation and the user's rules.
   - Transfer a temporary metadata line only when its values and exact removal were selected and verified in their new location; otherwise retain it as source text.
   - Copy/move attachments only under the selected location/naming policy. Shared/out-of-scope images stay put unless separately approved. Preserve attachment bytes and existing caption/alt text; update only the approved path. Verify a copied target/reference in a separate read before removing its old unique source.
   - Verify all final content/fact destinations and links in a separate call while the originals still exist. Missing facts or unverifiable protected payloads block source deletion. Remove originals only when deletion is explicitly selected.
6. **Report and clean up.** Compare candidates/final notes to independent originals under the preservation contract; run only applicable scoped checks. Report moves, chosen fields/rules, exact format/link/path changes, any explicitly authorized generated/rewritten content, unchanged regions and pending decisions. Re-read saved bytes before cleaning only this batch's scratch copies.

## Source-specific references

Use [concept ownership](../tow-review/references/concept-ownership.md) to analyze overlap. The [paper review example](references/paper-review.md) supplies a format only when the user explicitly chooses it. Metadata defaults such as descriptions, aliases, processing dates, `tags: []` or Area/Resource categories are not automatically added; reuse the user's actual template and selected fields.
