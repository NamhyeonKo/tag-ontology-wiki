---
name: tow-setup
description: >-
  Use when starting TOW in a new or existing Obsidian vault, choosing whether to use PARA,
  mapping existing folders, or configuring optional classification and tag dictionaries.
  Triggers: "set up my vault", "start a new vault with TOW", "use TOW with my existing
  vault", "search my whole vault, not just PARA", "my notes aren't in PARA folders".
---

# tow-setup

Prepare only the structure/features the user wants. Read the [conventions](../../docs/methodology.md) and run `tow config`. This workflow creates approved folders, dictionaries and `tow.json` only; it never moves, renames or edits notes. Search and body work can start without setup.

## Workflow

1. **Inspect names only.** List the root/first-level folders and existing configuration/dictionary filenames. Read relevant configuration and vault instructions, not note bodies. Helper defaults do not establish the user's preferences.
2. **Ask about PARA.** Ask whether the user wants PARA or their own layout, even for an empty vault. An explicit existing choice settles this question. Offer these paths without inferring consent from folder names:

   | Choice | Proposal |
   | --- | --- |
   | PARA | Reuse/map existing PARA folders or propose missing ones with the user's names |
   | Own layout, including an empty vault | Keep every folder; propose `{"scope": "vault"}` for helper searches. No automatic inbox, PARA folders or dictionaries |

   PARA does not imply TOW metadata adoption. Offer classification/tag dictionaries only when the user wants those features. An inbox, daily-note or attachment path is set only when needed and selected; show it in the plan. Dictionary locations may be customized too.
3. **Plan and wait.** Show exact paths to create and the final `tow.json` changes, preserving existing settings. State the search scope and optional features selected. For a full PARA starter bundle, `tow init` previews the missing folders/inbox/dictionaries. For dictionaries in a free-form vault, use `tow init --dictionaries`. Neither preview writes files; omit unselected items from the approved plan.
4. **Apply only the plan.** Write approved configuration and confirm it with `tow config`. Use `tow init --apply` (or `--dictionaries --apply`) only when every previewed item is approved; otherwise create just the approved subset with file tools, preserving existing files. Never create an inbox/dictionary merely to satisfy a helper check.
5. **Verify and report.** Compare created paths and effective settings against the plan and confirm existing notes are untouched. For a free-form configuration-only setup, `tow init` should report `nothing to create`. Run dictionary/lint checks only for adopted, initialized features; distinguish inapplicable checks from passes. Suggest a scoped `tow-query` request as the first usable step, without requiring metadata cleanup.
