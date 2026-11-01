---
name: tow-check
description: >-
  Use when checking notes in a TOW vault for schema and format problems — frontmatter against
  the dictionaries, H1/section structure, table·math·code notation, content-shape issues,
  broken wikilinks or image paths — and when normalizing their format without changing content.
  Triggers: "check my notes", "lint this note", "is the frontmatter right?", "fix the table/math
  formatting", "any broken links?", "노트 검사해줘", "형식 확인", "frontmatter 맞는지 봐줘",
  "표·수식 봐줘", "깨진 링크 있어?".
---

# tow-check

Checks the given notes (files or folders) on five axes and **reports the issues** (report mode, workflow steps 1–3); once the user approves, it fixes **format issues only** (fix mode, steps 4–5). Sentences, cell values, math, code, and link targets stay as they are.

Before starting, read the [TOW conventions](../../docs/methodology.md): they define the `tow` command used below, the frontmatter rules (§4), and the body notation rules (§5).

## Axes

| Axis | Check | Basis or tool | Handling |
| --- | --- | --- | --- |
| ① Frontmatter present | Is there a `---` frontmatter block starting on the first line? | Look directly. `tow lint` and `tow ontology usage` pass over notes without frontmatter, so they look OK there; check this first | Report only. Writing frontmatter needs a classification decision, which is outside this skill |
| ① Meta values | Allowed values, unregistered categories, field scope, unused properties | `tow lint <path>` | Report. A new category goes into the category dictionary after the user approves (conventions §3) |
| ① Meta format | Property order, block lists (including `source`), empty properties (keep `tags: []`), date format, double quotes for YAML special characters, duplicate frontmatter blocks | Conventions §4 | Fixable. Quote-only changes are left out |
| ② Tags | Unregistered tags, aliases used as tags, a broader and a narrower tag on one note, tag count, dictionary integrity | `tow ontology usage <path> --json`; tag count: `tow lint <path>`; dictionary: `tow ontology check --json` | Report. Unregistered tags and dictionary fixes go to `tow-tag-sync`; choosing a note's tags is the user's call |
| ③ Body structure | One H1 = file name, sections from `##` (promote one level at a time when they start at `###`), skipped heading levels (`##` then `####`), pseudo-titles (`> **Title**`, a date line at the top) → H1, list indentation (tabs, per `.obsidian/app.json` and existing notes), paired fences | Conventions §5 | Fixable |
| ③ Inline metadata | Lines such as `Date:` or `Tag:` (or localized ones such as `작성일:`, `태그:`), a `#a, #b` tag line at the top of the body, a lone `---` right after it | Conventions §4 | Report only. These lines can go once their values (date, tags the user picked) are in the frontmatter |
| ③ Body notation | Table separator rows and column counts, inline/block math and code, math in backticks or plain text, sentence flow | [markdown-format.md](references/markdown-format.md) | Fixable |
| ④ Shape | [Shape codes](#shape-codes) | Judgement | Report only |
| ⑤ References | `[[link]]` targets exist (Obsidian resolves links by file name only, so a link that matches only an alias is broken), image and attachment paths exist | Check the files | Report only |

`#`, `|`, and `$` inside code blocks are out of scope.

## Shape codes

Problems with the structure of the content. The user decides whether to fix them, so report each with the action it needs.

| Code | Problem | Action |
| --- | --- | --- |
| `EMPTY` | A title and no real body | Add content |
| `MULTI` | Two or more clearly different topics | Consider splitting the note |
| `NOPOINT` | The point is unclear, so no one-sentence `description` can be drawn | Add a sentence that states the point |
| `EMPTYSEC` | A heading with no content | Fill it or remove the heading |
| `WALL` | A very long block with no headings | Split it into sections |

`OK` when there is no problem; several codes are comma-separated (`NOPOINT, MULTI`).

## Workflow

1. **Scope**: take files or folders. When another skill calls this one, use its scope as given.
2. **Check**: run all five axes. `tow lint`, `tow ontology usage`, and `tow ontology check` run once over the scope; the rest run note by note.
3. **Report**: fill the [report table](#report-table), keeping fixable format issues apart from report-only issues. When a table's column boundaries or a math span can't be determined, report it as "ambiguous".
4. **Fix (on approval)**: fix only the approved format issues and update `updated` (conventions §4). For each note, compare math, table cell values, code, links, and plain sentences before and after, and recount `$`/`$$` pairs, fence pairs, and table columns.
5. **Done** when a re-check finds zero approved format issues and `tow lint` prints `OK`. Hand over the remaining report-only issues as a list.

## Report table

| Note | Format issues (fixable) | Meta and tags | Shape | References |
| --- | --- | --- | --- | --- |
| Transformer.md | Sections start at `###`, separator row `:---` | OK | OK | `[[Self Attention]]` has no target |
| Text Summarization.md | Separator row `:---` | No frontmatter | EMPTYSEC | OK |
