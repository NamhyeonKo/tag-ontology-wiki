---
name: tow-check
description: >-
  Use when checking frontmatter and Markdown, math, code, table or reference formatting
  while preserving content, including report-only lint and selected safe format fixes.
  Triggers: "check my notes", "lint this note", "is the frontmatter right?",
  "fix the table/math formatting", "any broken links?".
---

# tow-check

This skill works only inside the vault. From another project, stop and use `tow-query` to find vault content or `tow-send-vault` to bring content in.

Before any write, run `tow config` and verify the vault root it prints contains the current working directory and every file being edited; otherwise stop and route the request as above.

Report issues first; apply only approved format changes. Read the [conventions](../../docs/methodology.md), [preservation contract](../../docs/preservation.md) and [notation rules](references/markdown-format.md); for notes using the TOW schema, also read the [TOW recipe](../../docs/recipe.md) (§4 frontmatter, §5 note body). User rules take precedence. This skill never writes missing prose, corrects formulas/code/values, summarizes, merges or splits notes.

`tow` is not a command on your PATH: run the executable `scripts/tow.py` two directories above this file by its absolute path (with `python3` if the host can't execute it), for example `"<plugin-root>/scripts/tow.py" config`.

## Checks

| Axis | Check | Handling |
| --- | --- | --- |
| Frontmatter | Adopted schema, allowed values/types/order, optional presence and selected YAML syntax | Custom fields and absent metadata are valid where permitted. Run scoped `tow lint` only for TOW-schema notes with the category dictionary; classify/tag decisions remain separate |
| Tags | Selected ontology registration, aliases, redundancy, counts and dictionary integrity | Use dictionary-only `check`; run `ontology usage` only when its full read scope satisfies the conventions. Otherwise inspect exact-path `scan` and relevant dictionary entries; report unavailable aggregate checks |
| Markdown | Adopted heading levels, list markers, fences, hard breaks and structure | Repair selected syntax only; preserve heading text/prose/order. Ambiguous block boundaries remain report-only |
| Math/code/tables | Delimiters, fences, selected language-aware formatting, separators, alignment, escaping and columns | Follow the notation rules' exact payload/value checks. No formula rewriting, algorithm repair or invented cells |
| Shape | Empty note/section, mixed topics, unclear point, walls of text | Report codes below; shape findings do not authorize body writing or reorganization |
| References | Actual wikilink/attachment targets | Report missing/ambiguous targets. Selected wrappers/path repair go through `tow-link` or an explicit intake plan; no new note or caption text |

## Workflow

1. **Scope and rules.** Use the selected paths and their actual templates/conventions. Enforce private-input boundaries before reads. A request from another skill supplies only its stated scope.
2. **Inspect and report.** Check each selected note. Label findings as safely fixable, a metadata/user decision, or ambiguous/report-only. Include exact before/after spans for proposed format fixes; missing optional frontmatter/dictionaries are not defects. Do not override user style with bundled defaults.
3. **Apply after approval.** Copy originals and prepare a separate candidate under the preservation contract. Perform only the approved literal patches, keeping metadata edits separate from body-format patches. No blanket whole-note rewrite. A previously explicit choice settles only that exact change.
4. **Verify before replacement.** Compare protected prose, math/code payloads, ordered table values, alignment, links and unselected metadata with the independent original. Use `tow verify-body` for a separate metadata-only step; use operation-specific checks for format changes. Reject self-comparison, token-count-only checks and a formatter exit code as preservation evidence.
5. **Report.** Re-read saved files and verify the selected fixes. List applicable checks, skipped/unavailable checks, remaining findings and preservation results; do not claim ambiguous fixes passed. Follow the adopted date policy only through a selected metadata step.

## Shape codes and report

| Code | Finding | Report-only follow-up |
| --- | --- | --- |
| `EMPTY` | Title without substantive content | Ask whether the user wants explicit template-guided writing |
| `EMPTYSEC` | Empty section | Leave empty; writing/removal is a separate choice |
| `MULTI` | Distinct topics | Offer a review/merge proposal |
| `NOPOINT` | No supported one-sentence identity | Request clarification; do not invent a description/body sentence |
| `WALL` | Long unstructured content | Offer explicit restructuring under the user's rules |

Use `OK` when no finding applies. Report file, exact issue/span, applicable rule, proposed syntax-only change, required preservation check and unresolved choice. Route selected post-curation to its owning skill only after the user chooses that operation.
