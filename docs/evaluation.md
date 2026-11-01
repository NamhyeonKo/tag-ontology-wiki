# CLI integration and skill evaluation

The checks below exercise TOW with a real `tag-ontology` CLI. They do not establish release or installation readiness of the plugin.

## Automated integration tests

The default `uv run pytest` runs the unit tests and skips the real CLI tests. To include them, point `TOW_TAG_ONTOLOGY` at a CLI, either the published release or a local build:

```bash
TOW_TAG_ONTOLOGY="npx --yes tag-ontology@0.1" uv run pytest -q
TOW_TAG_ONTOLOGY="node /absolute/path/to/tag-ontology/dist/cli/main.js" uv run pytest -q
```

CI runs them in a separate job against the published 0.1 release on Node.js 22.

[`test_cli_integration.py`](../tests/test_cli_integration.py) copies the [synthetic vault](../tests/fixtures/vault) into a new temporary directory for each test. It checks:

- Custom folder and dictionary settings; exact frontmatter filters, case-insensitive tags, body/alias false positives, and archive inclusion.
- Alias lookup, direct versus descendant note results, and the note scope used by `usage` and `show`.
- Explicit relative/absolute paths outside the default PARA scope; a `show` tag named like a root folder.
- Vault-local changes files, read-only `plan`, dictionary-only `apply`, and stale-base conflicts that write nothing. Changes files outside the vault are rejected.

The fixture deliberately includes an alias tag, a superseded project, an inbox capture with an unregistered category, and an excluded template. It is test data, not a starter vault. `tow lint` checks conventions; dictionary/tag reconciliation is checked separately with `tow ontology usage` and `check`.

## Skill application scenarios

For each scenario, use a separate copy of `tests/fixtures/vault`, the CLI override above, and the current skill with its referenced conventions. Invoke `tow` as `python3 <plugin>/scripts/tow.py --root <copy>`.

| Skill | Request and follow-up | Pass condition |
| --- | --- | --- |
| `tow-query` | Find project notes about RAG, by classification or concept, excluding superseded documents | Exactly `Projects/Category Project.md` and `Projects/Search.md`, deduplicated; open notes before describing them; no writes |
| `tow-check` | First copy the two [check fixtures](../tests/fixtures/check) into `Resources/`. Request a report on those two files, then approve only the two heading promotions and table separator normalization in `Formatting.md` | Report missing frontmatter and the missing link; change only approved notation and `updated`; preserve sentences, cell values, math, code and link targets; leave `No Frontmatter.md` unchanged |
| `tow-tag-suggest` | Recommend tags for `Resources/Chunking.md`, then select only adding `semantic-chunking` and removing `information-retrieval` | Recommend the title concept `chunking` and section concept `semantic-chunking`, exclude the incidental BM25 mention; apply only the user's selection and `updated`; preserve the body and other metadata |
| `tow-tag-sync` | After the preceding selection, request a proposal for Chunking and Pipeline. Approve registering `semantic-chunking` under `chunking` with alias `semantic chunking`, replacing Pipeline's alias tag with `rag`, and removing its broader tag | Wait for approval; use a valid changes file and `plan`/`apply`; add only the approved dictionary entry; change only Pipeline's approved tags/date; end with no scoped unregistered, noncanonical or redundant tags |

For the check scenario, approve `### Formatting` → `# Formatting`, `#### Method` → `## Method`, and `| :--- | ---: |` → `| --- | --- |`. The missing frontmatter and `[[Missing Note]]` remain report-only. Use the processing date for `updated`.

The sync scenario's new entry description is: "Splitting documents at topic changes while keeping related sentences together." It has no children or related concepts. Verify existing dictionary entries and all note bodies independently, rather than relying on an agent's completion report.

## Results (2026-11-01 and 2026-11-02)

- Tests: **45 passed** (41 unit, 4 real CLI integration) on Python 3.10 and 3.13. Without the CLI override: 41 passed, 4 explicitly skipped. Ruff lint/format and Pyright strict passed.
- CLI: Node.js 26.8.2, an isolated copy of an existing pre-release local build (package version `0.0.0`). Its compiled JavaScript tree SHA-256 was `24beba62f9a6ea3b2831e91329ee3a2d513260bf4b1ffec7cfa9064d8f7dad55`.
- Query and check scenarios passed. The main agent verified the query copy was unchanged and that the check copy differed only by the four approved substitutions, including `updated`.
- Tag suggestion passed: only the selected tag, removal and date changed; the unselected title tag was not added.
- The initial tag-sync run failed: an external changes file was rejected, followed by two incorrect JSON envelopes. No dictionary write occurred. The skill now includes the exact `changes`/`kind`/`draft` shape and a vault-local hidden temporary directory. A fresh agent's `plan` and `apply` then succeeded on their first attempts; the main agent independently verified the exact dictionary and note changes. After this run, the skill gained a final step that deletes the batch folder once `apply` has written.
- During that retest, one preliminary command omitted `TOW_TAG_ONTOLOGY` and hit npm E404. Retrying with the selected local build succeeded. There were no subsequent CLI failures. Check evaluation also required correcting two evaluator-only preservation checks; these did not change the skill or note scope.
- Published CLI (2026-11-02): against `tag-ontology` 0.1.1 from npm, the 45 tests passed on Python 3.10 and 3.13. With no override, `tow` used its default `npx --yes tag-ontology@0.1` and ran `lint`, `find`, `ontology usage` and `ontology show` on a fixture copy with the expected results.
- Skill scenarios re-run against the published CLI (2026-11-02): four fresh agents, one per scenario, used `tow` with no override, so it ran `tag-ontology` 0.1.1 from npm. All four passed. Each agent stopped for approval and wrote nothing before it, which file hashes confirmed, and afterwards only the approved lines had changed. `tow-tag-sync` succeeded with `plan` and `apply` on the first attempt, added only the approved dictionary entry, left every existing entry equal, and deleted `.tow-tmp/` afterwards. Final `lint`, `usage` and `check` were clean, apart from the fixture's unused `inbox` entry.
- Friction seen in that re-run: one agent stored the whole `tow` command in a shell variable, which zsh doesn't split, so its first commands exited 127 before it retyped them. Two agents saved a pre-edit copy of a note outside the vault to compare against; both copies were outside the notes and were removed.
- A private copy of an existing vault contained **678 notes**. Against the original `vault_meta.py`, `find ai` returned the same 219 paths, and `find ai --all` the same 221 paths. Both lint commands exited 0. SHA-256 checks confirmed the 681 original input files were unchanged. Only these aggregate results are recorded here; the private notes are not fixtures in this repository.

## Limits

These are individual application scenarios, not a statistical skill benchmark. They explicitly select the skills and therefore do not test automatic skill discovery. Format and tag edits were evaluated on synthetic copies; the private corpus comparison covered lint and category search only.

The first skill scenarios used a frozen pre-release build, to avoid changing a sibling repository under active development; the re-run used the published package. Locally, the integration tests stay opt-in. Live Claude Code plugin installation and Obsidian rendering were not tested.
