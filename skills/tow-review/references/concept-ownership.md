# Concept ownership

Shared by `tow-ingest`, `tow-review` and `tow-merge`. Resolve folder roles from `tow config`; apply the [conventions](../../../docs/methodology.md).

Area source, Resource concept and hub below are semantic roles, not required PARA locations or metadata. In a custom vault, use its source/concept/map equivalents and existing navigation/schema. Preserve provenance in the user's established form; category registration, frontmatter `source` and TOW hub fields apply only where adopted. A stable identity and approved destination can satisfy promotion without a category dictionary.

## 1. Three owners

| Layer | Owns | Does not own |
| --- | --- | --- |
| Area source note | Source outline, study order, exam points, author claims, reading record | Repeated complete explanations of general concepts |
| Resource concept note | Reusable concept independently retrievable beyond one source | Exam question numbers, source-specific fragments or memorization lists |
| Domain hub | Domain definition, learning map, child links and one-line summaries | Copies of child-note bodies |

Source notes link to Resources. A Resource's frontmatter `source` retains the original URL or `[[Area source note]]`; do not add a body Sources section. Resource primary categories identify knowledge domains, while `cert/*` and `paper/*` identify area sources. A main domain note owns its full pipeline; independently reusable concepts may have their own notes.

## 2. Resource promotion

Promote only when most answers are yes:

1. Can one title state its identity?
2. Would someone seek it beyond this source, in another project/book/exam?
3. Is there substantive principle, composition, comparison or example beyond a definition?
4. Is there no existing owner?
5. Can it have a stable identity and destination (domain category/folder when adopted)?

Keep thin term memorization, one-question numbers/formulas/choices, unrelated term lists, page-based groupings and natural subsections of an existing Resource in their source/owner. New Resources use only needed sections of the [structure template](../../tow-edit/assets/note-structure-template.md), rather than copying the source's outline.

## 3. Search before creating

Search the eligible vault by title, aliases, canonical concept tags and body keywords first, respecting private-input policy.

| Finding | Proposal |
| --- | --- |
| Existing canonical owner | Enrich only missing content rather than create a file |
| Multiple owners | Canonical selection and `tow-merge` |
| Natural subsection of an existing note | Absorb into that section |
| Independent concept inside a mixed note | Split if it meets promotion criteria |
| Independent reusable concept with no owner | New Resource |
| Source-specific fragment | Keep in the Area source note |

## 4. Ownership and cohesion

**Canonical priority:** note titled with the concept → note addressing it most directly → domain hub. When two candidates both qualify, the user decides. This governs merges and duplicate cleanup.

| State | Signal | Proposal |
| --- | --- | --- |
| Appropriate Resource | Independent identity and reuse | Keep, index from hub |
| Over-split | One or two sentences that fit a neighboring subsection | Merge into its broader owner |
| Mixed | Distinct questions/domains/tags together | Split only independently substantial concepts |
| Source fragment | Exam choices, terms or report context only | Return to the source Area note |
| Duplicate ownership | Repeated full explanations/lists | Consolidate under canonical priority |

Merge notes answering the same question/learning flow, thin sequential concept-analysis-design notes, or a natural subsection. Split when parts answer different questions with distinct search intent, domains/tags and enough content to deserve independent links. Fragments still failing promotion after a split belong in an Area glossary/exam-points section. Batch-derived notes with no domain connections beyond their source are an isolation signal. Before merging/deleting, map every fact to a surviving owner or Area source.

## 5. Hubs

Check for a hub when a domain has at least three independent notes **or the user wants a map**. Name it after the domain's concept. Body: overview/definition, conceptual subgroups, `[[Note]]: one-line summary`, and recommended learning order. Do not mechanically copy a folder listing or child bodies. Learning order belongs on the domain hub; a subordinate hub explaining its own concept needs only child links. Use the chosen location and adopted schema; TOW type/category/`tags: []` apply only to TOW-schema hubs.

## 6. Duplicate judgment

`[[Note]]: one-line summary` indexing is normal. Repeated complete explanations of the same concept/list are duplicates: keep the canonical owner and propose summaries/links or unique facts elsewhere. Verify every fact exists in the survivor before trimming a section.
