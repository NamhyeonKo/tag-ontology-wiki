---
name: tow-query
description: >-
  Use when finding vault documents from natural-language conditions, including custom
  properties, tags, topics, folders, dates, ordering, or counts, with or without frontmatter.
  Read-only. Triggers: "what do I have on X?", "find my notes about X", "what's in the
  security domain?", "where is X?", "projects tagged rag", "find notes matching these conditions",
  "I wrote this down somewhere", "where did I save this?", "find this in my vault and project".
---

# tow-query

Translate natural language into reproducible searches: **CLI first → scoped file search when unavailable or insufficient → read and verify**. Read the [conventions](../../docs/methodology.md) and start with `tow config`; no setup, PARA, frontmatter or dictionary is required for host file search.

From a project, search both the connected vault and the current project. Inside the vault, search the vault only; never search project documents from there. Results state their source (`vault` or `project`) and path. This skill is read-only.

## Workflow

1. **Establish scope before reading.** Run `tow config` and use the vault root/source it reports; never infer the vault from Obsidian's active vault. From a project, resolve the project scope and its `.tow/` configuration when present. Follow the conventions' private/ignored rules before content reads. Inside the vault, search only its authorized scope. Never search the project from a vault session.
2. **Interpret the recollection.** Identify the topic, likely terms/aliases, relevant tags and requested conditions. A topic may match concepts, text, title, properties or links; don't assume a TOW schema. Consult `.tow/tag-dictionary.json` when available and relevant for canonical concepts, aliases and narrower concepts. For likely tag candidates, use `tow ontology show <tag> --json` to inspect the broader chain and consider relevant parent concepts too. Ask for the user's memory if the query remains too vague to search usefully.
3. **Search concept matches.** From a project, `tow lookup <concept>` searches the connected vault and current project's `.tow/` tag overlay; in the vault it searches that vault only. Use `tow lookup <concept> --exact` only when the user asks for that exact concept; otherwise include narrower concepts. The helper labels source, path, matched tags and exact-versus-narrower matches. It accepts a tag name or alias; resolve any other recollection to likely tag candidates using the dictionary before calling it. For vague recollections, try likely tag/alias candidates and relevant broader concepts from the ontology chain, using `tow lookup` for each. Keep track of results found only through a broader-concept query: those are inferred candidates, not verified matches to the recollection, even when lookup verifies the note's broader tag. If lookup is unavailable or incomplete, report that limitation and continue with scoped text search; don't treat a failed dictionary/CLI as proof of no match.
4. **Search text in the same scope.** Search eligible vault files and current-project files separately using host file search, then combine and deduplicate results while retaining source labels. `tow project files` lists project Markdown files by tracked/untracked/ignored status, names only; use it for an initialized project and its configured `docs`/`exclude` scope. If the project is not initialized, discover filenames only within the user-authorized project scope. Before reading untracked or ignored project files, list their names and read only files the user selects. Do not use `tow lookup` as a text search: it searches concept tags and narrower concepts.
5. **Optional Obsidian CLI.** It is only a read-only vault search accelerator. Always name the confirmed vault and explicit path, for example `obsidian vault="<vault name or id>" search path="<folder>" query="<terms>"`, `obsidian vault="<vault name or id>" search:context path="<folder>" query="<terms>"`, or `obsidian vault="<vault name or id>" read path="<vault-relative path>"`. Use no other CLI commands: never `eval`, `create`, `delete`, `move`, `rename`, `append` or `prepend`. A folder argument is not an OS permission boundary; obey the host's access rules and use scoped host file tools if the CLI cannot enforce the content exclusions before reading.
6. **Fallback and access errors.** If `tow config` reports no vault, do not guess: fall back to scoped host file search only in a folder the user names. If none is named, ask for one. If the host denies vault access, print the applicable setup hint and stop; do not retry through shell, Obsidian CLI or another tool. Claude Code: `Read(//<vault>/**)` or `permissions.additionalDirectories`; Codex: reads outside the workspace are not blocked by the default sandbox; Antigravity: `read_file(<vault>)` permission rule. Writes are not needed for this skill. This is a skill-level rule, not an OS-level access boundary.
7. **Verify before describing.** Read each candidate being described and check requested predicates on actual content/metadata. Keep helper-verified exact/alias/narrower concept matches separate from broader-concept or text-only inferred candidates; explain each match reason (exact tag, narrower concept, alias, broader concept, title, text, etc.). Missing properties are unknown, not guessed. For vague recollections, present a short ordered list as candidates and ask, “Is this the one?” Say “no matches within the checked scope” only after both applicable concept and text searches were checked. Mark partial scope, errors and unverified notes; query nothing writes files.
8. **Read before summarizing.** Unopened notes may be listed by title/path and verified properties only. Return the output below.

## Output

- Briefly state the interpreted conditions and effective scope; include the executed query/method when useful for reproducing the result.
- List title, path and requested fields. Separate verified exact matches from inferred candidates and explain unknown fields/evidence.
- Give the number actually listed; distinguish total verified matches from a displayed limit. Mark incomplete scans, tool errors, excluded paths and uncertain fields. Say "no matches within the checked scope" only after the fallback/verification supports it.
- Group a domain survey by subtopic when helpful. A category with no retrieved notes is a confirmed gap only after applicable search coverage is verified.
