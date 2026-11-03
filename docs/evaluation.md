# CLI integration and skill evaluation

The checks below exercise TOW with a real `tag-ontology` CLI and installed agent hosts. Publication and directory checks are recorded separately in [release readiness](release-readiness.md).

## Automated integration tests

The default `uv run pytest` runs the unit tests and skips the real CLI tests. To include them, point `TOW_TAG_ONTOLOGY` at a CLI, either the published release or a local build:

```bash
TOW_TAG_ONTOLOGY="npx --yes tag-ontology@0.1.2" uv run pytest -q
TOW_TAG_ONTOLOGY="node /absolute/path/to/tag-ontology/dist/cli/main.js" uv run pytest -q
```

CI runs them in a separate job against published 0.1.2 on Node.js 22.

[`test_cli_integration.py`](../tests/test_cli_integration.py) copies the [synthetic vault](../tests/fixtures/vault) into a new temporary directory for each test. It checks:

- Custom folder and dictionary settings; exact frontmatter filters, case-insensitive tags, body/alias false positives, and archive inclusion.
- Alias lookup, direct versus descendant note results, and the note scope used by `usage` and `show`.
- Explicit relative/absolute paths outside the default PARA scope; a `show` tag named like a root folder.
- Vault-local changes files, read-only `plan`, dictionary-only `apply`, and stale-base conflicts that write nothing. Changes files outside the vault are rejected.

The fixture deliberately includes an alias tag, a superseded project, an inbox capture with an unregistered category, and an excluded template. It is test data, not a starter vault. `tow lint` checks conventions; dictionary/tag reconciliation is checked separately with `tow ontology usage` and `check`.

## Skill application scenarios

For each scenario, use a separate copy of `tests/fixtures/vault`, the CLI override above, and the current skill with its referenced conventions. Invoke `tow` as `<plugin>/scripts/tow.py --root <copy>`.

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

## Live installation check (2026-11-02)

- Post-merge CI passed on `dev` commit `740fa2f`: Python 3.10 and 3.14 checks and the real CLI integration job.
- At this initial check, the repository's default branch, `main`, did not contain the plugin manifests. Installing from `https://github.com/NamhyeonKo/tag-ontology-wiki.git#dev` succeeded in Claude Code 2.1.310 at user scope. `tow@tag-ontology-wiki` 0.1.0 was enabled, its marketplace checkout matched `740fa2f`, and all tracked installed files matched the reviewed head. The executable bit on `scripts/tow.py` was preserved.
- `claude plugin details tow@tag-ontology-wiki` listed all four skills. Running the installed package's tests passed **46 tests** (42 unit, 4 integration) on Python 3.13.5 against published `tag-ontology` 0.1.2.
- A fresh Claude Code session loaded the installed plugin and registered all four `tow:` commands without `--plugin-dir`. The requested `tow:tow-query` run stopped before inference with the account's `429 usage_limit_reached`; it did not verify a model-backed query. SHA-256 comparisons confirmed all 11 synthetic-vault files were unchanged.

## Multi-host package check (2026-11-02)

The root `plugin.json` packages the shared skills, conventions, and helper for Codex and Antigravity; `.claude-plugin/` remains the Claude entry point. The Codex catalog lives in `.agents/plugins/marketplace.json`. The public README commands continue to target the released default branch. Local development checks used:

```bash
codex plugin marketplace add /absolute/path/to/tag-ontology-wiki
codex plugin add tow@tag-ontology-wiki
agy plugin validate /absolute/path/to/staged-package
agy plugin install /absolute/path/to/staged-package
```

- Package source: commit `a49c010`, exported without development caches for Antigravity. Native clients were Claude Code 2.1.310, Codex CLI 0.159.2, and Antigravity CLI 1.1.9. Claude and Antigravity validation passed; Claude's existing icon warning remained.
- Tests: **49 passed** (42 existing unit, 3 packaging, 4 integration) on Python 3.13.5 against `tag-ontology` 0.1.2. Ruff lint/format and Pyright strict passed. Packaging tests cover matching identity, the complete catalog source, bundled references, and a relocated executable path containing spaces with host-root variables absent.
- Codex installed and enabled `tow@tag-ontology-wiki` 0.1.0 from the local marketplace. Antigravity installed `tow` with four skills and retained the complete package under its plugin directory. Both installed copies matched every tracked source file; all skill references resolved inside each installed package.
- Both installed helpers passed `lint`, category and tag queries against separate synthetic vault copies using the default npm CLI and no `CLAUDE_PLUGIN_ROOT` or `PLUGIN_ROOT`. Each vault's 11 files retained their SHA-256 hashes.
- A fresh Codex session selected `tow-query`, read the installed conventions, used the installed helper, opened both matching notes, and returned exactly `Projects/Category Project.md` and `Projects/Search.md` (count 2).
- Antigravity's first session started in its scratch directory and could not identify the vault from the launch directory alone. A fresh session with `--add-dir <vault>` and the absolute vault root in the request used the installed helper with `--root`, read both notes, and returned the same two paths and count. Both attempts left the fixture unchanged.
- These initial model-backed checks were read-only query scenarios. The editing workflows and later Claude query are recorded below. The Codex session also emitted an unrelated existing Context7 OAuth startup warning; TOW itself has no MCP servers and completed the query.

Package/marketplace formats follow the [OpenAI packaging guide](https://developers.openai.com/plugins/build/plugins) and [Antigravity authoring guide](https://antigravity.google/docs/build-plugins). The local command spellings were checked against each installed client rather than inferred from another host.

## Editing and release verification (2026-11-02)

The two installed new hosts each ran the three editing scenarios above in fresh synthetic copies, first as a proposal and then as an explicitly approved batch in the same conversation. Each proposal's complete file hashes were checked before its approval was sent.

| Host | `tow-check` | `tow-tag-suggest` | `tow-tag-sync` |
| --- | --- | --- | --- |
| Codex CLI 0.159.2 | PASS: only the approved headings, separator and date | PASS: only selected tags and date | PASS: exact new entry and Pipeline tag/date changes; first-attempt plan/apply; scratch removed |
| Antigravity CLI 1.4.12 | PASS: exact approved substitutions and date | PASS: only selected tags and date | PASS after scoped host permission retries; exact dictionary/Pipeline changes; scratch removed |

The main agent reran both independent verifiers and inspected their exact-delta assertions and native traces. For every scenario, the proposal changed no files (13 check-fixture files or 11 ordinary fixture files). Approved edits preserved all other bytes, every existing dictionary entry, the unselected title tag, and the note bodies. Sync's final scoped `usage`, `check`, and `lint` passed; the fixture's unused `inbox` entry remained.

Antigravity recovered nine failed tool calls, including guessed default dictionary paths, one invalid `find` invocation, and sandbox failures during atomic dictionary write and batch cleanup. Its normal host flow authorized scoped retries for the approved fixture paths. No blanket bypass flag, persistent permission change, or evaluator-side cleanup was used. Its native initialization reported the account's existing `always-proceed` permission profile; these results establish the instruction-level approval boundary and content preservation, not interactive permission prompting under every profile.

These editing runs used installed TOW 0.1.0 from runtime source `33f09ab` and resolved `tag-ontology` 0.1.2. Candidate 0.1.1 pins that same CLI version and adds distribution metadata; it does not change skill procedures. Codex's existing Context7 OAuth warning and one shell snapshot warning did not prevent its runs.

Claude Code 2.1.310 was initially retried after a native reinstall made its installed conventions match `dev`. All four commands loaded, but the model call again stopped before inference with `429 usage_limit_reached`, zero input/output tokens, and the CLI's reset notice of 04:20 Asia/Seoul. All 11 fixture files remained unchanged; this attempt was blocked, not a passing scenario.

After the reset, the ordinary native marketplace/plugin update advanced Claude's installed copy from 0.1.0 to 0.1.1 at merged `dev` commit `5db6477`. A fresh `/tow:tow-query` session read the installed conventions and category dictionary, ran the installed helper's `config`, category query, ontology query, and project listing, and opened both matching notes before answering. It returned exactly `Projects/Category Project.md` and `Projects/Search.md`, count 2, with no permission denials or failed tool calls. All 11 fixture file hashes remained unchanged.

The first post-reset attempt returned the correct answer through read-only fallback because the evaluator allowed direct helper execution but not the model's `python3 <installed-helper>` form. It is not counted as the helper-backed pass. The passing retry allowed that exact installed script path with Python and used separate direct commands; no blanket permission bypass or global permission change was used. These checks do not cover every permission profile or unprompted skill discovery.

The [release readiness record](release-readiness.md) separates local package checks from `main` promotion and public-directory portal checks. Native CLI validation is not a directory approval.

## Complete portable workflows 0.2.0 (2026-11-02)

The six additional workflows were ported from their original functional/approval contracts and checked one at a time with fresh agents on disposable, renamed-layout vaults. The package has ten skills; existing names, including `tow-tag-sync`, are unchanged. No user vault was edited.

All **67 tests** passed against published `tag-ontology` 0.1.2 (63 unit/package, four integration), with Ruff lint/format and strict Pyright. Claude and Antigravity package validation passed. Native installs matched all 55 portable files (Claude/Codex) or 54 normalized Antigravity files, including the executable helper. Independent whole-branch review through `4af3ad0` found no substantive blocker; CI passed Python 3.10, Python 3.14 and published-CLI integration.

| Native host | classify | link | edit | merge | review | ingest |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code 2.1.310 | PASS | PASS | PASS | PASS | PASS | PASS |
| Codex 0.159.2 | PASS | PASS | PASS | PASS | PASS | PASS |
| Antigravity 1.4.12 | PASS | PASS | PASS | PASS | PASS | PASS |

Each proposal's complete file hashes were checked before its exact synthetic approval resumed the same native conversation. State oracles and command/read traces verified selected metadata/body deltas, declined retroactive classification, first-mention links, direct authorization of a clear body edit, hub-only approval, sequential merge choices, fact destinations before deletion, paper full-title H1/alias, byte-preserving unique-media moves and unchanged shared/private inputs. Private-canary absence was supplemental: actual content searches and CLI parsing had to exclude private inputs before reading them. The parent independently reran state assertions and post-deletion scoped installed-helper checks.

**Source provenance:** initial cases used `15fd94f`. Explicit scan-scope guidance at `f613a76` was reread for Codex's approved turns; affected Claude classification/review/intake and Antigravity edit/review were rerun in fresh copies. Claude's remaining merge scope failure led to `4af3ad0`'s mandatory scope gate. Fresh merge pairs then passed on all three hosts, including configuration/ignore/eligible-path setup before body searches and a separate destination verification while the source still existed. Unchanged, already scoped link/edit and other unaffected cases retain their original source labels. These are controlled mixed-candidate results, not eighteen new executions of one identical revision. The helper is identical across these candidates; `4af3ad0` changes only the merge skill relative to `f613a76`.

Claude edit/review helper gaps were closed by read-only validation continuations in their original sessions, with unchanged hashes. Claude intake recovered in normal task-scoped `acceptEdits` mode using plain copy and byte comparison after `dontAsk` denied flagged copy commands. Antigravity used its existing `always-proceed` profile and scoped per-command sandbox retries. No blanket bypass flag, persistent permission change, account/model switch or quota workaround was used. Interactive permission prompting is not established by these runs.

Retained failures include client-session metadata denials, zero-token missing-session resumes, the earlier Codex usage limit, incorrect/denied tool commands, timeouts, and real overly broad scans in earlier candidates. The old quota notice's reset had already passed when work resumed; normal same-thread retries succeeded. No failed attempt was relabeled as a pass. Three overstrict oracle assumptions were separately adjudicated: a roots-only index need not duplicate a child value; approved byte-identical hidden backups are valid; and display-preserving links to an existing absorbed section are valid. All other fact, field, file and byte assertions remained. Invalid early fixture PNGs were replaced with validated images before native runs.

These are individual explicitly selected synthetic scenarios, with no statistical or automatic-discovery claim. H1/link targets and preservation were checked independently; `tow lint` alone does not verify them. External paper retrieval, user-vault migration, GUI rendering and interactive approval UX were not tested. Post-promotion CI and public-main installation are separate release checks, recorded in the GitHub release; official-directory registration remains deferred.

## Initial 0.3.0 setup candidate (2026-11-03; superseded below)

First-time-user feedback asked for an initial PARA setup or a search scope beyond PARA. On an empty vault the 0.2.1 helper stopped at missing dictionaries, and on a vault with notes outside PARA folders `find` returned nothing without a warning. 0.3.0 adds `tow init [--apply]`, the `"scope": "vault"` setting, warnings for an empty PARA scope and missing dictionaries, and the `tow-setup` skill.

All **75 tests** passed against published `tag-ontology` 0.1.2, with Ruff lint/format and strict Pyright; Claude and Antigravity package validation passed (eleven skills).

Codex CLI 0.159.2 with model `gpt-6-luna` ran the uncommitted candidate's skills from the repository path (not a native install) in three synthetic vaults, proposal first and then an explicit approval resumed in the same session:

| Vault | Proposal | After approval |
| --- | --- | --- |
| Empty | Default PARA folders, inbox, starter dictionaries; no `tow.json` | Exactly those created; `init` reports nothing to create; check and lint pass |
| Free-form (`notes/`, `journal/`) | `{"scope": "vault"}` plus inbox and dictionaries | Exactly those created; the 5 existing files' hashes unchanged |
| PARA-like names (`Projects/`, `Inbox/`, …) | Folder-name mapping in `tow.json` plus dictionaries | Exactly those created; the 5 existing files' hashes unchanged |

Every proposal left all files unchanged, and command traces show only name listings, `config` and dry-run `init` before approval; no note contents were read. A fresh `tow-query` session in the free-form vault returned exactly `notes/Chunking.md` and `notes/RAG.md` (count 2) through the whole-vault scope. Codex's workspace sandbox denied the default npm cache, so the first CLI call in some sessions failed and the model retried with a temporary npm cache; this is a host sandbox limit, not a TOW behavior. Native installation, Claude Code and Antigravity runs of `tow-setup` were not repeated for this candidate.

## Limits

These are individual application scenarios, not a statistical skill benchmark. They explicitly select the skills and therefore do not test automatic skill discovery. Format and tag edits were evaluated on synthetic copies; the private corpus comparison covered lint and category search only.

The first skill scenarios used a frozen pre-release build, to avoid changing a sibling repository under active development; the re-run used the published package. Locally, the integration tests stay opt-in. All three hosts have installed query checks; Codex and Antigravity also have the editing checks above. Public-directory portal checks/submission and Obsidian rendering were not tested. At this pre-promotion cutoff, default-branch installation was still a release gate; post-promotion results belong to the GitHub release verification record.

## Optional PARA and custom-vault compatibility (2026-11-03)

The setup candidate above was revised after the user clarified that PARA must be a choice, not inferred from an empty vault. A free-form setup now creates no inbox or dictionaries by default; `init --dictionaries` is explicit. Whole-vault scope keeps ordinary notes in inbox/support/archive-named folders. All eleven skills were reviewed for schema, dictionary, date and layout assumptions, with shared compatibility rules and scoped CLI-first/file-fallback query behavior.

The full suite passed **91 tests**, including five real `tag-ontology@0.1.2` integration tests, plus Ruff lint/format and strict Pyright. Independent skill-consumer execution covered two queries and a scoped body edit in a synthetic free-form vault; byte verification confirmed metadata/source preservation. Native Obsidian CLI was not used on an unregistered fixture, and the user's active vault was not accessed. See the [per-skill review, exact checks and limits](vault-compatibility-review.md). These results supersede the earlier candidate's automatic free-form inbox/dictionary behavior; they do not revalidate all hosts or all editing workflows.

## Content preservation and user-guided post-curation — 0.4.0 candidate (2026-11-03)

Following merged PR #15 (`5caec7f`), ordinary maintenance now preserves prose, formula/code contents and table values; optional aftercare uses explicitly selected operations and user rules/templates. `tow verify-body` adds a narrow dictionary/Node-independent exact-body check for metadata-only edits.

Full suite: **104 passed**, including five published-CLI integrations; Ruff lint/format and strict Pyright passed. Low-cost `gpt-6-luna` consumers exercised baseline, formatting, template, filing, transfer and private-scratch scenarios. One initial formula-padding failure and inadequate comparison claim are retained, followed by targeted payload and privacy checks; this is not a universal model-reliability claim. See [preservation evaluation, reusable fixtures, independent review and limits](preservation-evaluation.md). Historical host results above concern older revisions.
