---
name: tow-query
description: >-
  Use when the user asks what knowledge exists in a TOW vault and where — by domain, topic,
  category, or concept tag, including multi-condition searches. Read-only.
  Triggers: "what do I have on X?", "find my notes about X", "what's in the security domain?",
  "where is X?", "projects tagged rag", "뭐 있어?", "X 관련 정리한 거 찾아줘",
  "security 도메인에 뭐 있어?", "내 vault에 ~ 뭐 정리했지?", "어디 있어?", "rag이면서 project인 거".
---

# tow-query

**Answers "what knowledge is where". Read-only.** Other skills also use it to check what already exists.

Before starting, read the [TOW conventions](../../docs/methodology.md): they define the `tow` command used below. `tow config` gives the actual PARA folders, the project archive folder name, and the paths of the two dictionaries.

Three principles:

1. **Index first**: read the category dictionary (`categoryDictionary`) first, as the map of classifications. The tag dictionary (`tagDictionary`) is large; `grep -i` it only for the concepts you are looking for (tags and aliases).
2. **Cross folders, categories, and concept tags**: classification values and concept tags cut across folders. Search the whole vault for the value to find notes in other domain folders too (for example, the `db/sql` category can be on notes in both `db/` and `security/`).
3. **Read before you describe**: open every note whose content you describe. List unopened notes by title and path only.

Project archive folders (superseded and rejected documents) are skipped by default; read the hub's "current direction" first. Include them only when the user asks about history.

## Survey (union: "what's there")

1. **Interpret the query**: a domain (security), a topic or keyword (SQL), a category (`db/sql`), or a concept entity (`hnsw`).
2. **Index**: find related categories and their parents in the category dictionary, and canonical tags and aliases with `grep -i "<term>"` on the tag dictionary.
3. **Collect candidates** as a union, without duplicates:
   - Folders: the related domain folders under resources, and so on
   - Category: `tow find <category prefix>` (`find ai` = everything under `ai/`; `--all` includes project archives)
   - Concept tag: `notePaths` from `tow ontology show <tag> --notes --json` (rolls up narrower concepts; `--exact` for the tag alone; `--all` includes project archives)
   - Keywords and aliases: title and body keywords, as a supplement when needed
4. **Open the notes you will summarize.**
5. **Answer** in the [output format](#output-format).

## Facet (intersection: "notes matching all of these")

Finds notes that meet several conditions at once, such as "projects about rag", "ai projects in progress", or "notes covering bm25".

1. **Pin down the canonical values**: classifications from the category dictionary (rag → `ai/rag`), concepts from the tag dictionary (self attention → `self-attention`). `type`, `status`, and `kind` are scalar fields; `status` and `kind` are optional properties of project documents; daily notes are `type: daily-note`.
2. **Match exactly, then intersect.** Always search in this form (`<archive>` and `<PARA folders…>` come from `tow config`):

   ```bash
   rg -l --no-ignore-vcs -g '!**/<archive>/**' '<pattern>' <PARA folders…>
   ```

   `--no-ignore-vcs` keeps notes listed in `.gitignore` in the search, and project archive folders stay excluded by default. Limiting the search to the PARA folders keeps non-note files such as templates out.
   - Scalar field: `'^type: project$'`
   - List value (category, tags): `'^\s*-\s*"?ai/rag"?\s*$'` (values may be quoted)
   - Intersection: `comm -12 <(rg … '<pattern A>' … | sort) <(rg … '<pattern B>' … | sort)`
   - A question that mixes classification and concept, such as "about rag", searches the category (`ai/rag`) and the concept tag (`rag`) separately and takes the union. The strings differ, so one search never finds the other.
3. Skim the titles in the results and open only the notes you need for the answer.

Match the frontmatter list format (`^\s*-\s*<value>\s*$`) for precision. A loose `rg rag` gives false positives from body text and similar words (`db/nosql` matches a search for `sql`).

## Output format

- Group by subtopic (folder, category, broader concept).
- For each note, **title + path**; a one-line summary only for notes you read.
- The total count equals the number of notes listed.
- Mark categories defined in the category dictionary but with no notes as gaps.
