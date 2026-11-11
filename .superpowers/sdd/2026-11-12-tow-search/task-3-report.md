# Task 3: Evaluator and `tow search`

Date: 2026-11-12  
Status: implemented and verified

## Summary

- Refactored `cmd_lookup` so `lookup_results(...)` returns matching notes and unavailable-source details; retained the existing lookup JSON wrapper and exit behavior.
- Added the `tow search` subcommand and evaluator over vault candidates and the current registered TOW project. The evaluator supports concept, title, heading, body, path, frontmatter, source, AND, OR, NOT, and group clauses; records positive-clause reasons; reports unknown-tag suggestions and unavailable sources; and returns the specified JSON and exit codes.
- Added synthetic tests for Boolean query evaluation and reasons, one-time frontmatter scanning, unknown-tag suggestions, CLI degradation with text fallback, repaired queries, exit codes, and leading NOT syntax. Added an opt-in real-CLI integration test that checks tag/title results and verifies the vault remains unchanged.

## Verification

- `uv run ruff check` — passed.
- `uv run ruff format --check` — passed (67 files formatted).
- `uv run pyright` — passed (0 errors, warnings, or informations).
- `uv run pytest -q` — passed: 392 passed, 10 skipped.
- The opt-in real-CLI integration tests were skipped because `TOW_TAG_ONTOLOGY` was not configured in this environment.
- `git diff --check` — passed.

## Ambiguities resolved

- The brief specifies one positional `query`; argparse accepts it as one string, so queries containing spaces should be quoted (for example, `tow search "title:graph OR title:overview"`). A query beginning with `-NOT` needs `--` to distinguish it from an option (for example, `tow search -- -path:areas`); this case is covered by a test.
- `path:` matches the vault-relative note path for both vault and project results, not an absolute project filesystem path, following the stated field contract.
- The existing integration test module is gated by `TOW_TAG_ONTOLOGY`; its other real-CLI coverage was preserved while adding the new search case.

## Concerns

- Real tag-ontology 0.3.0 integration remains unverified here because no `TOW_TAG_ONTOLOGY` command was set.
- The parser requires `--` to disambiguate a query beginning with a minus from a CLI option; ordinary query strings with spaces continue to be joined and evaluated as one query.
