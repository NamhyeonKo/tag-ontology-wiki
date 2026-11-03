# Contributing to TOW

Focused bug fixes, documentation improvements, tests, and translation corrections are welcome. For a new workflow or a change to preservation, search scope, or approval behavior, open an issue describing the problem and intended behavior before building it.

## Report a bug or suggest a feature

Use the [issue forms](https://github.com/NamhyeonKo/tag-ontology-wiki/issues/new/choose). For a bug, include the TOW version, agent host/version, operating system, smallest reproduction, expected and actual behavior, and relevant output. For installation/update problems, include both the command and the installed version afterward.

Use synthetic notes or redact examples before sharing them. Do not attach private vaults, credentials, access tokens, or unredacted agent logs. An issue about missing search results should describe the selected scope without publishing private note contents.

## Development setup

You need Git, Python 3.10+, and [uv](https://docs.astral.sh/uv/getting-started/installation/). Node.js 22.18+ and npm/npx are needed for real Tag Ontology CLI integration tests.

Fork and clone the repository, then create a branch for your change. From the checkout root:

```bash
uv sync --locked
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
```

These are the checks used by [CI](.github/workflows/ci.yml). The runtime helper uses only the Python standard library; keep runtime dependencies out of documentation-only changes.

### Real CLI integration

The helper calls `npx --yes tag-ontology@0.1.2`. The exact version makes the downloaded executable reproducible. Set `TOW_TAG_ONTOLOGY` to run integration tests:

```bash
TOW_TAG_ONTOLOGY="npx --yes tag-ontology@0.1.2" uv run pytest
```

You can also point it at a local build, for example `TOW_TAG_ONTOLOGY="node /absolute/path/to/cli.js"`. Without this variable, real CLI integration tests are skipped. Tests copy the [synthetic fixture vault](tests/fixtures/vault) into temporary directories; do not use a personal vault as a test fixture. npm may download the pinned package and write its cache.

Python checks do not establish that an agent follows a skill correctly. For changes to skill instructions, describe the synthetic scenario, selected files, approval, observed changes, and preservation checks. Mark unavailable host/runtime coverage explicitly. See [evaluation](docs/evaluation.md) and [preservation evaluation](docs/preservation-evaluation.md) for existing scenarios and their limits.

## Repository map

| Path | Purpose |
| --- | --- |
| `skills/` | Shared agent instructions and their references/assets |
| `docs/methodology.md` | Canonical conventions, scope rules, and installed helper resolution |
| `docs/preservation.md` | Canonical content-preservation contract |
| `docs/post-curation.md` | Canonical optional aftercare contract |
| `docs/installation.md` | Human-facing installation, settings, and troubleshooting guide |
| `scripts/` | Python helper and its modules |
| `tests/` | Unit, packaging, documentation, and opt-in CLI integration checks |
| `readme/` | Human-facing README translations |
| `plugin.json`, `.claude-plugin/`, `.antigravity-plugin/`, `.agents/plugins/` | Host manifests and marketplaces |

### Skill references and translations

Skills explicitly read `docs/methodology.md`, `docs/preservation.md`, and `docs/post-curation.md`. These English documents are runtime inputs, not just website copy. `methodology.md` also resolves the installed plugin root from its location directly under `docs/`.

Keep their paths and relative links stable. Moving them, adding a language directory to their paths, or redirecting a skill to a translation requires checking every referring skill and the relocated-package test. Do not add a directory-wide read of `docs/` or `readme/` to load translations.

`README.md` is the source for reader translations in `readme/README.<language>.md`. The maintained editions are Korean (`ko`), Simplified Chinese (`zh-CN`), Traditional Chinese (`zh-TW`), Japanese (`ja`), Spanish (`es`), and French (`fr`). Every edition links to the same English detailed guides. Separate language copies of `docs/` and the retired Korean installation guide are not maintained.

Translate the complete README and keep code commands, CLI flags, skill names, version requirements, and preservation/approval limits aligned with English. Translate example requests, but keep executable commands unchanged. Fix relative links for the `readme/` location and retain the language navigation. When changing shared README instructions, update every affected edition and run `uv run pytest tests/test_documentation.py`.

Local planning/research under `docs/superpowers/` is ignored. Do not add it or private workspace material to a contribution.

## Pull requests

- Describe the concrete problem and resulting behavior, linking the issue when applicable.
- Keep the change focused; update affected callers, tests, fixtures, and docs together.
- For fixes, add a regression check when the behavior needs one. For documentation, verify commands and links against their source.
- List the checks actually run and any skipped or unavailable coverage. AI-assisted contributions carry the same responsibility for correctness and verification.
- Preserve existing vault content, custom schemas, scoped reads, and explicit approval boundaries. A cleanup request must not silently authorize rewriting note bodies.

For release changes, keep versions consistent across the Python project and host manifests, and document the required host update steps. A documentation PR does not authorize a release, marketplace submission, or publication.

## License

Contributions are made under the repository's [MIT license](LICENSE).
