---
name: tow-query
description: >-
  Use when finding vault documents from natural-language conditions, including custom
  properties, tags, topics, folders, dates, ordering, or counts, with or without frontmatter.
  Read-only. Triggers: "what do I have on X?", "find my notes about X", "what's in the
  security domain?", "where is X?", "projects tagged rag", "find notes matching these conditions".
---

# tow-query

Translate natural language into reproducible searches: **CLI first → scoped file search when unavailable or insufficient → read and verify**. Read the [conventions](../../docs/methodology.md) and resolve the actual vault with `tow config`; no setup, PARA, frontmatter or dictionary is required. This is a skill using existing tools, not a SQL/MCP server.

Work within the vault opened as the host's workspace. Results describe documents in that vault; use the other vault-management skills only for explicitly selected follow-up work there.

## Workflow

1. **Establish scope before reading.** Resolve the requested vault, approved paths, private/ignored rules and exclusions. Follow the conventions' scope rules with every tool. Never search the active/default Obsidian vault by accident. In a custom vault, default PARA/inbox/archive names impose no scope. History exclusions apply only when adopted or requested.
2. **Interpret conditions.** Identify AND/OR/NOT groups, property comparisons, topic/tag matches, requested output fields, ordering and limit. Learn actual field names/types/values from authorized instructions, templates or candidate notes; reuse the user's vocabulary. A topic can match category, tags, aliases, title or body; union these signals and deduplicate. Do not assume `status`, `type` or their allowed values exist. Consult dictionaries for canonical values/aliases/narrower concepts only when available and relevant.
3. **Search through an available CLI.** Prefer native Obsidian CLI search for properties, body tags and text. Use the confirmed target vault and an approved folder or equivalent search restriction; inspect `obsidian help search` when needed. The [official CLI reference](https://obsidian.md/help/cli) and [search syntax](https://obsidian.md/help/plugins/search) document supported commands/operators. Example for an authorized `notes/` folder in a confirmed vault:

   ```bash
   obsidian vault="Research" search path="notes" query='[status:reading] (tag:#rag OR "retrieval augmented generation")' format=json
   ```

   Use `search:context` or exact-path `properties`/`read` for selected candidates. CLI availability includes correct vault registration and supported commands; its presence on PATH alone is insufficient. If a CLI cannot enforce private-file exclusions before reading content, use scoped file tools instead.

   The existing helper is useful for parsed properties and optional ontology expansion:

   ```bash
   tow ontology scan notes --json                 # no dictionary needed; custom frontmatter included
   tow find ai/rag --type project                 # TOW category prefix AND type
   tow ontology show rag --notes --json           # optional dictionary; includes narrower concepts
   ```

   `tow find` accepts only category/type/status/kind/tag filters, scans its whole configured scope and skips notes without frontmatter. Use it only when those semantics and scope fit; its result is not a complete body-tag/text search. `scan` exposes body tags separately. `show` reads the configured scope even without `--notes`; use it only under the conventions' full-read/exclusion rule. `show --exact` omits descendant note paths but retains rollup counts; `--all` includes PARA project history. A saved, relevant Base can be queried with `base:query`; inspect its filters first because its `path` selects the Base definition, not a result-folder boundary. Do not create one just to search.
4. **Fall back when needed.** If CLI access fails, returns no/insufficient candidates, omits relevant note forms or uses a stale/limited index, discover approved files by filename/path, then search aliases, body tags and text with host file tools or `rg` over the eligible paths. Preserve the same logical conditions and exclusions. List names first when needed; filter private inputs before content reads. Read candidates and parse frontmatter with an available YAML-aware tool for property comparisons; a body/code example of `status: reading` is not a property match. Do not install tools or write an index/config/dictionary for a query. Report parse/tool failures rather than treating them as empty values.
5. **Verify the result.** Check all required predicates on parsed values; distinguish scalar equality, list membership, numeric/date comparisons, missing, null and empty values. Native search is candidate retrieval when its matching semantics differ from the requested predicate. Missing status is unknown, not in-progress or complete. Body evidence may justify a separately labeled inferred candidate, never an exact property match. For relational/link questions, verify actual links/targets. Sort by the requested field (state property dates versus filesystem times), put unknown keys separately, then apply the limit to verified results. Do not take a CLI-limited subset as a global top-N; retrieve the complete eligible candidate set before global sorting/counting, or report the result as partial.
6. **Read before describing.** Open each note whose content you summarize. Unopened notes can be listed by title/path and verified properties only. Return the output below without editing files.

## Output

- Briefly state the interpreted conditions and effective scope; include the executed query/method when useful for reproducing the result.
- List title, path and requested fields. Separate verified exact matches from inferred candidates and explain unknown fields/evidence.
- Give the number actually listed; distinguish total verified matches from a displayed limit. Mark incomplete scans, tool errors, excluded paths and uncertain fields. Say "no matches within the checked scope" only after the fallback/verification supports it.
- Group a domain survey by subtopic when helpful. A category with no retrieved notes is a confirmed gap only after applicable search coverage is verified.
