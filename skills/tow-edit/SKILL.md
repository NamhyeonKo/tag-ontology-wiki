---
name: tow-edit
description: >-
  Use when the user explicitly selects template-guided post-curation of named notes,
  such as writing a named empty section or restructuring selected content under their rules.
  Triggers: "edit this note", "fill in this section", "fill the empty sections",
  "restructure this note", "turn this into a list".
---

# tow-edit

This skill works only inside the vault. From another project, stop and use `tow-query` to find vault content or `tow-send-vault` to bring content in.

Before any write, run `tow config` and verify the vault root it prints contains the current working directory and every file being edited; otherwise stop and route the request as above.

Optional, user-guided body aftercare. Read the [conventions](../../docs/methodology.md), [post-curation contract](../../docs/post-curation.md) and [preservation contract](../../docs/preservation.md), then resolve `tow config`. Routine metadata/format requests use their owning skills; they never trigger body generation here.

## Workflow

1. **Establish inputs.** Identify the exact note/section, operation, user rule/template/source and protected content. Read existing authorized instructions/templates before asking. If a required writing/restructuring rule is missing, ask for it and leave the note unchanged; do not substitute the bundled structure/prose recipe.
2. **Read the complete original.** Keep an independent original after the selected operation is approved. Filled sections, custom metadata, code, formulas and tables stay protected unless their exact transformation is separately selected.
3. **Preview the selected transformation.** Show destinations and literal moves/rewrites. A clear request to fill a named empty section may proceed directly only when the rule/source and boundary are already established. A supplied template alone is not permission to rewrite filled content or add unknown facts.
4. **Apply the smallest selected change.** Use the user's template, language and style. Write only into approved new/empty slots from selected evidence. Structural moves copy existing content verbatim unless a precise rewrite scope is explicit. Add no automatic tags, dates, links, new sections or generic template headings.
5. **Verify and report.** Compare all protected regions and metadata with the independent original. Use applicable `tow-check` checks without broadening the scope. Separate actual body additions, verbatim moves, explicit rewrites and unchanged material in the report; report unsupported content rather than filling it by guess.

The [bundled structure example](assets/note-structure-template.md) and [Korean style example](references/korean-style.md) are usable only when the user explicitly chooses them. Plain "clean this up" produces a question/proposal, not a body rewrite.
