# TOW recipe

The optional TOW organization recipe: PARA folders, classification fields, concept tags, frontmatter, note body and the tag dictionary. Read the [TOW conventions](methodology.md) first: they define `tow`, scope, approval and preservation, and [Vault compatibility](methodology.md#vault-compatibility) decides where these sections apply. Sections keep their numbers; §7 "Shared rules" is in the conventions.

## 1. Overview

- Optional recipe: **PARA (folders, structure) + LLM Wiki (metadata)**. Each can be adopted independently.
- Philosophy: build the knowledge graph from **tags rather than links**, and let the LLM go from the category dictionary index straight to the files, **without RAG**. Classification goes in **fields** such as `type` and `category`; the concept entities a note covers go in **`tags:`**.
- PARA folders (the number prefixes in the defaults sort the Obsidian sidebar):

| Folder | `tow/config.json` key | Default | Holds |
| --- | --- | --- | --- |
| projects | `projects` | `01_Projects` | **Projects** with a goal and a deadline |
| areas | `areas` | `02_Areas` | Ongoing areas of **life** |
| resources | `resources` | `03_Resources` | **Study material** (the body of knowledge) |
| archives | `archives` | `04_Archives` | **Finished projects** |
| project archive | `projectArchive` | `archive` | Superseded or rejected documents of an active project (§2). Any folder with this name, at any depth, counts |

Captures waiting to be classified stay in an inbox, as written. In the default layout, inbox, templates and attachments sit outside PARA, so default helper scans leave them out. Custom paths do not change the helper's search scope; the workflows apply their own configured intake and link exclusions.

## 2. Folders and depth

- **A folder is a coarse location** (for example `<domain>/` under resources). Fine-grained and cross-cutting classification goes in **tags**.
- **At most 3 levels** below the PARA folder (`<resources>/ai/llm/note.md`).
- The archives folder holds **your own finished projects** only. External originals such as paper PDFs belong elsewhere: they would pollute the knowledge base and the graph.
- **Project archive folder**: superseded or rejected documents of an active project go into an archive folder inside that project (not the archives folder). Put a banner at the top (`> Status: superseded (date) → [[Replacement]]. Reason: …`) and update the project hub's "current direction" and document table. Active and on-hold documents stay in `idea/`, told apart in the hub table; dated logs stay where they are. Exploration and search skip archive folders by default.

## 3. Classification and tags

Note metadata has two axes. **Classification (what kind of note)** goes in the `type`, `category`, `status`, and `kind` fields; **concepts (what it covers)** go in `tags:`. Keep them apart.

### Classification fields

- **`type`**: `resource | project | area | daily-note`, one scalar per note. Daily notes live in the areas folder with `type: daily-note`. A hub takes `project`, `area`, or `resource`, by where it belongs. The two dictionaries are management files and have no `type`.
- **`category`**: a **list** of knowledge domains, content identifiers, or project names. Lowercase letters and hyphens, hierarchy with slashes (`ai/rag`); only proper nouns may use capitals. **The first item is the primary category** (aligned with the folder); the rest are secondary, for cross-classification. The primary category's axis depends on the PARA folder:
  1. projects: `{project-name}` alone (knowledge domains go secondary)
  2. areas: a content identifier such as `book/{title}`, `paper/{alias}`, `cert/{name}` (knowledge domains go secondary)
  3. resources: a knowledge domain (for example `security/cryptography`)
- **`status`**: `draft | in-progress | complete`, optional: the **completeness of a project document**, as opposed to the progress of the project as a whole. The archives folder tells whether something is archived; leave `status` out when completeness is unknown.
- **`kind`**: `idea | research | proposal | specification | design | plan | retro | log`, optional: the **nature of a project document**, not a stage in time. Hubs leave it out when none fits.
- `status` and `kind` appear only on `type: project` notes.
- `category` values must be registered in the category dictionary. A new category needs the **user's approval first**, then goes into the category dictionary.
- Obsidian's tag pane doesn't roll `ai/rag` up into `ai`, so search by prefix: `tow find ai`.

### Category dictionary format

The category dictionary is JSON at `tow/category-dictionary.json` by default. It is an object keyed by category value; each value has a `description` string, keys are sorted, and each entry occupies one line. Configure a different root-relative path with `categoryDictionary` in `tow/config.json`.

### Concept tags (`tags:`)

Concept tags are the **concept entities a note covers directly** (for example a `Transformer` note → `self-attention`, `positional-encoding`). A narrower tag alone doesn't decide its broader concept (`deep-learning`): the broader tag stays when the note explains that concept directly too, and stays off when it is only background (see "Broader and narrower tags together" below). A tag is a concept that could be **a node of the domain's taxonomy when you study it**: anything from a top-level field to a leaf concept (`data-structure` → `tree`), but not language syntax or implementation details. Tags are the candidate pool for chunks and graph nodes, so each one must be **an entity many notes can reuse**. The dictionary is an **ontology (a SKOS-style thesaurus)** with broader/narrower and related links between concepts, not a flat list. The tag dictionary is the source of truth (`aliases`, `description`, `broader`, `related` per tag); its model and writing rules are in §6.

| | Rule |
| --- | --- |
| Tag | The **most specific concept** the note explains in a heading (section) or a definition, and the note's **own title concept**. A broader concept when the note explains it directly too, or when no narrower one is on the note (for example the field of a hub note). Named standalone concepts (techniques, algorithms, attacks, systems, standards) and **tool, product, and vendor names** (`aws`, `arduino`) count. An **identifier** such as a single vulnerability becomes a lowercase tag placed under its kind in the dictionary (`cve-2026-41266` → broader `cve`) |
| Don't tag | **Properties, qualities, and metrics** (interoperability, latency, traceability), section names, **specific API, function, or parameter identifiers** (`printf`, `println`, `chunk_size`; **language-neutral programming concepts** such as `output`, `pointer`, `loop`, `operator` are taxonomy nodes and do get tagged — a language note carries the language tag plus the concept tag, for example `java` + `output`), parameters, passing mentions that are only links, terms specific to one paper, and words too general to mean anything (`data`). General tags read in combination with others, such as `platform`, `lifecycle`, `device`, `ai`, are allowed |

- Format: lowercase letters and hyphens. Names in other languages, abbreviations, and synonyms go in the dictionary's **aliases**. Keep different concepts with the same name apart (`thread-protocol`). Keep a compound that means one thing whole (`model-compression`); split one that reads as general words combined (`on-device` + `ai`).
- **Count**: 3–10 recommended, **15 at most** (20 for an overview note that bundles several topics; a note with three or more numbered sections `## N.k.` counts as one). `tow lint` warns above the limit. When a note overflows, keep tags by the priority below, but **when narrower concepts pile up, consider splitting the note by topic before cutting tags**. A hub or overview note whose narrower concepts already have their own notes stays whole (splitting would only rename) and trims its tags to the broader concepts.
  - Priority: ① the title concept ② concepts the note explains directly, narrower ones first ③ tags shared with other notes ④ tool and vendor names that appear only as examples.
- **Area ↔ resource alignment**: when a tag found in a resource note is also discussed in its source (an area lecture note), tag the area note too. A broader tag that merely overlaps in a heading stays off the area note.
- **Ontology rules**: a note's `tags:` is a flat list (no `/` hierarchy); the hierarchy lives in the dictionary's `broader` (the direct broader concepts, several allowed, `[]` = top-level field). Tag the most specific concept (a language note also carries its language tag, which is a `facet`); whether its broader tag stays follows the next rule. Every new concept gets a place through `broader` when it is registered (otherwise an `unplaced` warning). Look a tag up with `tow ontology show <tag> --json` (broader paths, narrower count, note count; with `--notes`, the notes with the tag or any narrower one). See the whole taxonomy in the Tag Ontology plugin's graph view in Obsidian.
- **Broader and narrower tags together**: a narrower tag on a note is not by itself a reason to drop its broader tag. **Keep both when the note explains each concept directly; leave the broader one off when the note uses it only as background**, as the field its topic belongs to, or in a passing mention. Evidence that the note explains the broader concept directly, cheapest to check first:
  1. it is the note's title concept: its name or an alias matches the file name, a part of it split at ` - `, `(`, `)` or `:`, or a single word of it (letters and digits only, ignoring case; `pki` in `Digital Signatures and PKI.md`);
  2. a heading or the frontmatter `description` whose subject is that concept, or a note `aliases` value that names it (by its name or one of its dictionary aliases);
  3. a passage that defines it, or explains or compares it alongside the narrower concept.

  The broader concept's word inside a narrower concept's name is not evidence (`## Retrieval-augmented generation` is about `rag`, not `information-retrieval`). `tow ontology usage` lists each note carrying a tag together with one of its narrower tags under `redundant` (`tag` is the broader tag, `narrower` the narrower ones on that note). It is a **structural review candidate, not an error**: the CLI doesn't read the body, and it already leaves out `facet` tags and a broader tag that is the note's title concept (evidence 1), and `usage --strict` doesn't fail on it. `tow ontology scan <paths…> --json` returns each note's `path`, `frontmatter` (with `description` and `aliases`), `tags`, `bodyTags` and full `headings` for this review.
- Before creating a tag, `grep -i` the dictionary (exact match → alias → partial match) and **reuse** what is there.
- **The user picks concept tags and puts them on notes.** The agent proposes candidates only when asked. New tags the user added are checked against the dictionary with `tow ontology usage` (duplicates, aliases, similar tags) and then registered. **`tow-tag-suggest`** owns proposing candidates; **`tow-tag-sync`** owns checking, registering, and merging.
- Checks: `tow ontology usage [path] --json` (tags on notes against the dictionary), `tow ontology check --json` (dictionary integrity), `tow lint [path]` (allowed values, unregistered categories, field scope, tag counts).

### Linking notes

- In the TOW recipe, shared concept tags and `category` values provide connections. In other vaults, existing wikilinks, hubs, body tags and custom properties also establish navigation; new metadata is not required to link notes.
- Body `[[wikilinks]]` are **optional prose decoration**: add one where a natural mention exists. A note without them is still linked.
- The TOW recipe does not use frontmatter `related:`. Preserve that property in schemas that do use it.
- Existing notes keep the concept tags they have; the user manages them note by note. When a new category is registered, offer to apply it to existing notes.

## 4. Frontmatter schema (LLM Wiki style)

Notes adopting the TOW schema follow the frontmatter below. Other notes retain their existing schema or lack of frontmatter. Real TOW notes omit empty properties but keep `tags: []` for the user to fill. Templates include optional properties as empty slots.

```yaml
---
description: "One sentence that says what the note is."
type: resource
category:
  - "ai/llm"
  - "ai/rag"
tags: []
source:
  - "https://example.com"
aliases:
  - "Another name for the title"
created: 2026-10-19
updated: 2026-10-19
---
```

Project notes add `status` and `kind` after `type` when needed.

- **Property order**: `description` → `type` → `status` → `kind` → `category` → `tags` → `source` → `aliases` → `created` → `updated`. Skip properties that don't apply. Extra properties go before the dates; the dictionaries may keep their own metadata.
- **YAML style**: lists are block lists indented two spaces; an empty list is `[]`. **Double quotes are optional** on description, category, tag, source, and alias values. Obsidian's property editor sometimes strips them when it saves, so keep the quoting each note already has and leave quote-only changes out of any normalization. When the agent writes a new value, it follows the note's existing style, or uses double quotes if there is none. Values with YAML special characters (`: `, ` #`, or a leading `- ? [ ] { } & * ! | > ' % @`) always get double quotes. `type`, `status`, and `kind` are unquoted scalars; real dates are `YYYY-MM-DD`.
- `tags` belong to the user. Preserve existing values and empty properties, and leave existing notes without the property as they are. New notes and templates get `tags: []`.
- `aliases` are **synonyms, abbreviations, and translations of the note title**. Narrower concepts and search keywords belong in `tags`, which the user manages. Moving existing aliases into tags needs separate approval.
- `source`: **study notes keep their sources, even when they combine many.** Always a YAML list, even with one value. Omit it for your own writing with no source.
- `description`: **a one-sentence summary (~100 characters)** in the note's language, based only on the body. If the body is too thin to support one, omit the property and report the shape issue `NOPOINT` (`tow-check`). Daily notes without a summary omit it.
- `created`, `updated`: keep an existing `created`; a new note with no date in the body gets the processing date. New templates use `"{{date:YYYY-MM-DD}}"`. `updated` isn't maintained automatically, so **set it to the processing date whenever you change the note file** (content, classification, tags, links, or format).
- `confidence`, `stage`, and `related` are unused properties.
- **No `title` field**: the file name is the title (the LLM Wiki concept ID), and title variants (another language, for example) go in `aliases`.

### Source policy (`source:`)

1. **Common sources** (well-known books, sites, open papers): the original URL only.
2. **Hard-to-find files**: upload to a web archive and use **the archive URL**.
3. Full original texts stay out of the vault, the archives folder especially.

## 5. Note body

- **Title**: exactly **one** `# <title>` (H1) at the top of the body, matching the **file name** (no `title` frontmatter field).
- **Paper-review exception**: an area note whose primary category is `paper/<alias>` keeps the full paper title as its H1 and as an alias. Its filename uses the main title before the subtitle to avoid forbidden filename characters such as `:`. Do not shorten that H1 to the filename; this exception does not apply to other notes.
- **Sections** start at `##` (H2), then `###`, `####`. (Obsidian shows the file name as the title, so the body's standard starts at H2.)
- **A `#` inside a code block** (a comment, for example) is not a heading; leave it as is.
- **Tables**: repair selected separator/padding syntax while preserving alignment, cell values, escaping and row/column order. Missing or ambiguous cells are report-only; do not invent them.
- **Math and code**: selected delimiter/fence/layout repairs preserve the complete expression/code payload. Plain text and code are not automatically converted to LaTeX. Do not change sentence flow, expressions or algorithms to satisfy a formatting preference; ambiguous spans remain report-only.
- Details and examples: [markdown-format.md](../skills/tow-check/references/markdown-format.md)

## 6. Tag dictionary

The tag dictionary is the **ontology (taxonomy)** of the concept tags used in `tags:`. The concept list (tags, aliases, definitions, broader and related concepts) lives only in the dictionary JSON. Classification values (domains, identifiers) belong to the category dictionary.

### Model: a graph of concepts

A thesaurus that lightly follows the core of W3C **SKOS** (Simple Knowledge Organization System). One tag is one concept (`skos:Concept`), and the relations between concepts form the taxonomy. A note's `tags:` stays a flat list; the hierarchy exists only in the dictionary.

| Dictionary field | SKOS | Meaning |
| --- | --- | --- |
| Key (tag) | `prefLabel` | The concept's preferred name: lowercase letters and hyphens, the name the field commonly uses |
| `aliases` | `altLabel` | Other names for the same concept (other languages, abbreviations, full names). Tags and aliases are unique across the dictionary |
| `description` | `definition` | A one-sentence definition that tells the concept apart from others with the same name |
| `broader` | `broader` | The **direct broader concepts**; several are allowed. `[]` marks a top-level field; no key means unplaced |
| `related` | `related` | Associated but not hierarchical (symmetric). Never overlaps the hierarchy |

- **What `broader` means**: "A is a kind of B, or a subtopic that makes up field B" (for example `reflected-xss` → `xss`, `xss` → `web-security`). It is not strict is-a but **the taxonomy you study by (BT/NT)**. Write only the direct link; tools compute the full ancestry (SKOS `broaderTransitive`).
- **Several broader concepts**: a concept that spans two fields gets both (`llm` → `generative-ai`, `nlp`).
- **Direct links only**: an ancestor already reached through another broader concept stays out of `broader` (`redundant-broader` warning).
- **No cycles**: a concept never lists itself or one of its narrower concepts as broader (`self-reference` and `broader-cycle` errors).
- **Top-level fields (roots)** have `broader: []` (for example `ai`, `network`, `security`, `algorithm`, `data-structure`). Distinct fields such as algorithms, data structures, and programming languages are separate roots.
- **Concept vs. language-specific concept**: ask "is it the same concept in another language?" A shared concept (`array`, `loop`, `output`, `list`) sits under its own field (`data-structure`, `programming-language`), not under a language. A concept whose meaning the language defines (C's `pointer`, Python's `slicing`) also gets the language as a broader concept (`pointer` → `data-type`, `c-language`). A note ties a shared concept to a language by carrying **the language tag plus the concept tag**.
- **`facet` (context tag)**: language nodes (`c-language`, `java`, `python`) are marked `"facet": "language"`. A facet tag gives context, so it can sit on a note next to its narrower concepts (`pointer`) without counting as redundant.
- **Grouping nodes**: an intermediate concept that groups narrower ones (`network-attack`, `model-evaluation`) needs no notes of its own. `usage` doesn't list a concept that has narrower concepts as `unused`.

### Reading

- Query the dictionary JSON with `grep -i` instead of reading it whole (one line per concept, so the name, aliases, definition, and broader concepts come together).
- Structure: `tow ontology show <tag> --json` gives the broader paths (`paths`), the narrower count, and the note count including narrower concepts. The whole taxonomy is in the Tag Ontology plugin's graph view.
- The notes for a concept and everything below it: `tow ontology show <tag> --notes --json` (`--exact` for the tag alone). For example `network-attack` also returns notes tagged `dos`, `ddos`, or `sniffing`.
- Lookup order: exact tag → alias → partial match (similar candidates) → new.

### Writing

- **The user tags notes**; the agent checks the tags with `tow ontology usage` and registers them through `tow ontology plan`/`apply`, which keeps one concept per line, sorted. Agents change the dictionary file only this way; the Tag Ontology plugin's sidebar editor writes the same layout. A changes file cannot set `facet`: set that field in the dictionary file itself, keeping the entry on its one line.
- **Every new concept gets a place.** Find the broader concept to attach it to first (`show`, `grep`); if none fits, create a nearby grouping node. Registering without `broader` raises an `unplaced` warning.
- Tag notes with the **most specific (leaf) concept** they explain. The dictionary already knows its broader concepts, so a broader tag goes on as well only when the note explains that concept directly too (§3 "Broader and narrower tags together").
- What to tag, how many, and in what priority is defined in §3 "Concept tags". In short: tag only concepts that could be a node of the domain's taxonomy.
- Keep concepts with the same name but different meanings apart (`mcp-sampling` ≠ `sampling`, `thread-protocol`). Fold other spellings of the same concept into aliases.
- When the abbreviation is the field's usual name, the abbreviation is the tag; when the full name is, the full name is. The other one becomes an alias. Hierarchy goes in `broader`, never in `/` (tags are flat and hyphenated).
