---
name: tow-review
description: >-
  Use when inspecting organized notes against the user's own rules for ownership,
  duplication, missing navigation or project direction and proposing optional aftercare.
  Triggers: "review this domain", "any duplicate content?", "is there a hub note?",
  "this note is too big", "clean up my project notes in the vault".
---

# tow-review

This skill works only inside the vault. From another project, stop and use `tow-query` to find vault content or `tow-send-vault` to bring content in.

Before any write, run `tow config` and verify the vault root it prints contains the current working directory and every file being edited; otherwise stop and route the request as above.

Read-only review and post-curation planning by default. Read the [conventions](../../docs/methodology.md), [post-curation contract](../../docs/post-curation.md), `tow config` and [concept ownership](references/concept-ownership.md). A review/cleanup request never creates a hub, rewrites bodies, splits/merges notes or adds metadata automatically.

## Workflow

1. **Scope and rules.** Use named notes/domain/folder/project; ask if unspecified. Discover user instructions/templates within the authorized scope. Apply confirmed history/private exclusions before reads. Generic vaults need neither PARA nor frontmatter/dictionaries. If no rules exist, report content/navigation observations; request a rule only before a transformation needing it.
2. **Read every scoped note.** Inspect complete bodies, structure and existing metadata/navigation. Use CLI-first discovery and scoped file fallback, plus applicable `tow-check` report-mode findings. Keep read-only review free of backup/scratch/note writes.
3. **Analyze ownership/cohesion.** Identify independent topics, duplicate explanations, mixed notes and source fragments. Base findings on read content and the user's established organization, not a mandatory Resource/Area model. Ambiguous canonical choices remain unresolved.
4. **Inspect navigation.** Consider actual inbound/outbound links, hubs, body/frontmatter tags and meaningful custom properties. Missing TOW fields alone are not isolation. A domain with several independent notes or a requested map can justify a hub proposal, never automatic creation or copied/rewritten bodies. List relevant existing templates and ask for a missing one only when the user chooses that operation.
5. **Check project direction where applicable.** Use the actual project's direction/history rules. No forced banner, status table, move or completion inference. Report unrelated project conventions as inapplicable.
6. **Present findings and choices.** List file/span, evidence, rule source, proposed operation, exact affected paths and preservation boundary. Separate existing defects from optional organization preferences. The user can select individual fixes; a general review approval does not select a content transformation/template.
7. **Route explicit selections.** Format/frontmatter work uses its owning maintenance skill. Body writing/new hubs require a named `tow-edit` scope and chosen template; merges/splits use `tow-merge` case choices; source filing uses `tow-ingest`. Preserve separate discard and retroactive-classification decisions. Do not execute unspecified suggestions or invoke an executor merely because a finding exists.
8. **Verify selected follow-up.** Re-read only authorized changed notes and original/fact destinations. Apply the preservation contract and applicable checks. Report work actually performed, verbatim versus explicit content transformations and unresolved findings; the review itself remains read-only when no operation was selected.
