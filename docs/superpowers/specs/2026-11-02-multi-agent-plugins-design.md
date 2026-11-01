# Multi-agent plugin packaging

## Intent and scope

Ship the same TOW workflows as plugins for Claude Code, Codex, and Google Antigravity. The four existing skills, `docs/methodology.md`, and `scripts/tow.py` stay shared. Note preservation, approval rules, CLI behavior, and the `tag-ontology@0.1` dependency remain unchanged.

## Approaches and decision

1. **Shared portable package (chosen implementation):** add root `plugin.json` for Codex and Antigravity, retaining `.claude-plugin/plugin.json` for Claude Code. Add a native Codex marketplace catalog. This uses the supported common layout without copying workflows.
2. Separate Codex and Antigravity compatibility manifests: supported, but duplicates identity and requires newer Antigravity clients that discover the nested manifest.
3. Generate three separate bundles: adds build and synchronization work without a current component difference.

The shared package is an implementation choice under the user's instruction to proceed autonomously. This is repository/plugin support, not submission to public plugin directories or promotion of `dev` to `main`.

## Package and invocation

- Root `plugin.json`: portable identity, version, publisher, and links; the default `skills/` directory is shared.
- `.claude-plugin/`: existing Claude manifest and marketplace remain supported.
- `.agents/plugins/marketplace.json`: Codex catalog entry named `tow`, rooted at `./`, with the same marketplace name as Claude.
- Shared conventions resolve the installed plugin root from the location of `docs/methodology.md`, not a provider-specific environment variable or the vault working directory. The absolute script path remains quoted.
- README installation instructions target the repository's default `main` after release. Development installation evidence is recorded separately in `docs/evaluation.md`.

## Validation

Keep a small package test for identity/catalog consistency, bundled relative references, and execution after relocation to a path with spaces without plugin-root environment variables. Run existing unit/integration tests and static checks. Use the installed `claude`, `codex`, and `agy` clients to validate or install a staged package, inspecting all four skills and the installed helper. Record client versions and distinguish package loading from model-backed execution.

No new runtime dependencies, hooks, MCP servers, installers, or duplicated skill trees are needed. Public-directory review, Obsidian rendering, and unavailable account-backed runs are outside the package checks.

## Sources checked on 2026-11-02

- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins): portable root manifest, default skill layout, and native marketplace catalog.
- [Antigravity plugin authoring](https://antigravity.google/docs/build-plugins): root manifest and shared component directories.
- [Antigravity installation](https://antigravity.google/docs/plugins?tab=cli): local/GitHub installation and installed component inspection.
- Local clients: Claude Code 2.1.310, Codex CLI 0.159.2, Antigravity CLI 1.1.9. Read each client's actual help before documenting its command syntax.
