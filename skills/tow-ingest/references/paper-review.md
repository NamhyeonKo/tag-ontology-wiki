# Paper review notes

Apply these rules to paper-review intake; the remaining `tow-ingest` process and approval gates still apply.

- **Filename:** main title before its subtitle, avoiding forbidden filename characters such as `:` (for example `Self-RAG.md`).
- **H1:** exact full paper title, including its colon/subtitle. This is the conventions' narrow paper-review exception to filename-matching H1.
- **Folder:** source Area under configured `areas`, normally its `papers/` subfolder. Discover the existing paper source folder or include its creation in the destination plan; do not use a personal absolute/default area path.
- **Classification:** `type: area`; primary category `paper/<paper-alias>`, registered through `tow-classify` before use; technical domains are secondary categories.
- **Source:** the original paper URL (publisher, arXiv, etc.).
- **Description:** one sentence (~100 characters) stating its contribution, rather than repeating the title.
- **Aliases:** the exact full paper title is required; also include established short names and translations. Double-quote YAML values containing special characters such as `: `.
