# Release readiness: TOW 0.5.1

## Release scope (0.5.1)

- Fix vault resolution so the nearest vault wins over personal connections, and treat the plugin's empty root dictionary starter as a non-legacy marker.
- Correct initialization, migration reporting/removal, lookup, atomic-write fallback, and project Git/status edge cases; restore Markdown dictionary synonym guidance.
- Advance the host manifests, Python project, lockfile, and README editions to 0.5.1. Keep the pinned `tag-ontology@0.2.0`; do not tag, publish, or release as part of this change.

## Candidate verification (0.5.1) — 2026-11-06

- Final committed candidate checks: `uv run ruff check` passed; `uv run ruff format --check` reported 62 files already formatted; `uv run pyright` reported 0 errors, warnings, or informations.
- `uv run pytest`: 284 passed, 9 skipped. The exact local-engine integration command passed all 9 tests. `uv lock --check` and committed-diff whitespace checks passed; documentation parity/link checks passed in the full suite.
- Model-backed skill application, installed-host checks, post-merge CI, and publication remain separate gates. The 0.5.1 release archive must be built from its committed candidate; no tag, release, or publication was made here.

---

## Historical release readiness: TOW 0.5.0

## Release order and hand-off

1. Publish `tag-ontology` 0.2.0 to npm before merging or releasing TOW 0.5.0. TOW's pinned integration job depends on that package being available.
2. Promote and release TOW 0.5.0 only after the dependency is published and the candidate checks pass. This documentation task does not run the release workflow, create tags, publish a marketplace package, or push changes.
3. Users migrating a legacy vault must update the Tag Ontology Obsidian plugin to 0.10.0 before running `tow migrate`, so the plugin recognizes `.tow/tag-dictionary.json`.

## Release scope (0.5.0)

- Add cross-project query, project metadata, personal vault connections, and approved send-to-vault workflows; move vault config and dictionaries into `.tow/` while retaining legacy compatibility.
- Keep the exact `tag-ontology@0.2.0` pin and advance all host manifests, the Python project, lockfile and README editions to 0.5.0 so native plugin updates can fetch this package.
- Preserve the existing skill names, paths, approval gates and content-preservation contract. Project tagging writes `.tow/` metadata without editing project documents.

## Candidate verification (0.5.0) — pending

The maintainer runs the release-candidate checks at release time and records their actual results here. **Status: pending; no 0.5.0 release-candidate results are recorded in this historical section.** Record the final local test, lint, format, type-check, lockfile and documentation-link results after running those checks.

Model-backed skill application, installed-host checks, post-merge CI and publication are separate release gates; do not infer those results from local checks.

---

## Historical verification: TOW 0.4.2

Checked on 2026-11-04 before promotion through `dev` to `main`. This patch moved the pinned `tag-ontology` CLI to 0.1.3 and changed how the tag skills treat a broader tag that sits next to its narrower tag. Skill names, paths, approval gates and the preservation contract were unchanged.

### Release scope

- Pin the default executable, CI and current install/contributing/README instructions to `npx --yes tag-ontology@0.1.3`, the published npm `latest` (engines `node >=22.18`, matching TOW's Node.js requirement). In 0.1.3, `usage` reports `redundant` as a structural review candidate that `--strict` does not fail on, and it also treats a single word of the file name as the title concept. Its `scan` text output also lists `description`, `aliases` and all headings. TOW doesn't publish the npm package.
- `docs/methodology.md` §3/§6: a narrower tag alone no longer removes its broader tag; both stay when the note explains each directly (rule "Broader and narrower tags together").
- `tow-tag-sync` reviews each `redundant` pair with exact-path `scan --json` and proposes a drop candidate only for background use. `tow-tag-suggest` recommends a broader concept next to its narrower one when the note explains it directly ([#20](https://github.com/NamhyeonKo/tag-ontology-wiki/pull/20)).

### Candidate verification

- Fresh full suite: **112 passed**, including all six integration tests against published `tag-ontology@0.1.3`; synthetic vaults only. The new integration test fails against 0.1.2 (`--strict` exits 1), so it checks the pinned behavior.
- Ruff lint/format, strict Pyright and `uv sync --locked` passed. `npx --yes tag-ontology@0.1.3 --version` printed `0.1.3`.
- Not run: a fresh agent applying the updated tag skills to the evaluation scenarios, and installed-host checks. Dev/main CI and the GitHub release are recorded as they complete.
- The draft release was created by the Release workflow from reviewed main commit `8d32996`. Locally, its script reproduced byte-identical archives to a manual build of that commit, and `claude plugin validate --strict` (Claude Code 2.1.318) passed on the portable archive.

---

## Historical verification: TOW 0.4.1

Checked on 2026-11-03 before promotion through `dev` to `main`. This patch prepares the public documentation and contribution workflow without changing skills or their canonical runtime guidance.

### Release scope

- Keep English `README.md` at the root and publish six reader translations under `readme/`: Korean, Simplified/Traditional Chinese, Japanese, Spanish, and French.
- Document native install/update commands, installed-version checks, and troubleshooting for Claude Code, Codex, and Antigravity.
- Add `CONTRIBUTING.md` and focused GitHub issue/PR templates. Retire the separate Korean installation guide; every README uses the same detailed English guides.
- Keep `docs/methodology.md`, `docs/preservation.md`, `docs/post-curation.md`, all skill files, and the Python helper unchanged. Do not create translated `docs/` trees or widen skill discovery.
- Advance all host manifests, the Python project, and lockfile to 0.4.1 so native plugin updates can fetch this package. The separate `tag-ontology` npm package remains at the pinned 0.1.2; it is not published by this release.

### Candidate verification

- Fresh full suite: **110 passed**, including all five integration tests against published `tag-ontology@0.1.2`; synthetic vaults only.
- Ruff lint/format and strict Pyright passed. Documentation tests check translation command/skill-list parity and repository-local links.
- Final-commit archive validation, dev/main CI, release assets, and post-publication installed-host checks are recorded in the GitHub release as they complete. Candidate checks alone do not establish those results.

---

## Historical verification: TOW 0.4.0

Checked on 2026-11-03 before promotion through `dev` to `main`. This release manages documents inside the Obsidian vault opened as the agent host's workspace. It retains all eleven skill names and targets Claude Code, Codex and Google Antigravity.

### Release scope

- Search existing vault notes with CLI-first retrieval and scoped file fallback; custom layouts and notes without frontmatter remain supported.
- Keep PARA, TOW classification and tag ontology independently optional. Setup uses the user's choice and never migrates notes automatically.
- Preserve prose, math/code payloads and table values/order during selected metadata/format maintenance. Metadata-only changes use independent originals and `tow verify-body`.
- Keep body aftercare under explicit selected operations and the user's templates/rules. A review or formatting request does not generate or rewrite filled prose.
- Correct existing CLI coverage guidance: ontology usage/show read the configured scope minus exclusions and include both frontmatter/body tags; selected usage paths and show output flags do not narrow every read. Dictionary apply does not edit notes.
- Reject dictionary paths ending in `/` before initialization writes; a malformed file path must not create a dictionary directory. The four regression cases failed before the fix and passed afterward.
- Keep `docs/superpowers/` local-only and excluded from tracked release contents. This release does not add persistent personal-vault connections, external-project authoring or a new retrieval/formatting backend. No Git history rewrite is included.

### Candidate verification

- Fresh full suite: **108 passed**, including five published `tag-ontology@0.1.2` integration tests and four dictionary-path regression cases, in 11.51 seconds. Synthetic copies only; no user vault was used.
- Ruff lint passed; Ruff format check reported 44 files already formatted; strict Pyright reported zero errors/warnings.
- All three host manifests, Python project and lockfile agree on **0.4.0**. Relative package links and tracked-file exclusion of local planning passed.
- Review, final-commit archive validation, post-merge CI and publication are recorded in the GitHub release. The candidate test result alone is not a native Obsidian/GUI or new installed-host functional result.

See [preservation evaluation](preservation-evaluation.md) and [vault compatibility review](vault-compatibility-review.md) for the synthetic skill observations, retained failures and limits. Release archives follow the portable/native manifest projection below, using the 0.4.0 final commit and filenames. Official-directory submissions and the separate tag-ontology npm package are outside this release.

---

## Historical verification: TOW 0.1.1 candidate

Checked on 2026-11-02 before main promotion. This is a verification record, not a directory-approval claim. The GitHub release records the final publication and post-promotion installation checks.

### Functional checks

| Gate | Result |
| --- | --- |
| Codex query and all three editing workflows | Passed on installed 0.1.0 runtime `33f09ab`; exact deltas and approval-phase hashes independently checked |
| Antigravity query and all three editing workflows | Passed; sync needed normal scoped host permission retries |
| Claude installed query | Passed on native-updated 0.1.1 after the account reset; installed helper used, both exact notes read, count 2, all 11 fixture files unchanged |
| User vaults | Not used; each scenario had an independent synthetic copy |

See [evaluation](evaluation.md) for scenarios, preserved boundaries, versions, and runtime failures. Model-backed tests are individual observations, not a statistical reliability benchmark.

### Candidate changes

- Raise all manifests and Python project metadata from 0.1.0 to 0.1.1. An observed `claude plugin update` kept the older installed copy when both versions were 0.1.0. Native reinstall confirmed the new conventions loaded. Versioned releases must advance so an ordinary update can fetch them. [Claude release guidance](https://code.claude.com/docs/en/plugins/publish).
- Pin the default executable to `npx --yes tag-ontology@0.1.2`, which is the package used in the successful integration and editing checks. This supersedes the earlier 0.1 minor-range choice for public distribution. Exact registry versions are required by the [Anthropic pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist). The explicit `TOW_TAG_ONTOLOGY` override remains available.
- Declare OpenAI's `requires_local_executor: true`, include listing text and a shared 512-pixel PNG, and keep TOW skills-only. A local vault and Python/npm execution are required. [Desktop-only skills submission](https://developers.openai.com/plugins/deploy/desktop-only), [listing metadata](https://developers.openai.com/plugins/deploy/submission).
- Add an Antigravity-specific manifest for its display name, logo, and starter prompts while sharing every skill and helper. [Antigravity authoring requirements](https://antigravity.google/docs/build-plugins).

### Distribution artifacts

The [Release workflow](../.github/workflows/release.yml) automates this procedure. Run it manually with the version, the reviewed commit, a title and the notes. [`release_assets.py`](../.github/scripts/release_assets.py) refuses a commit whose manifests and Python project declare another version. It builds both archives below and checks their integrity, helper mode, symlinks and native root manifest, then writes `SHA256SUMS`. The workflow attaches all three to a **draft** release targeting that commit; publishing the draft creates its `v<version>` tag. It refuses an existing release or tag. Host validators (`claude plugin validate --strict`, `agy plugin validate --strict`) still run outside it.

Keep archives outside the repository; a bundled ZIP would itself be an extra binary for directory review. Export committed files with executable modes preserved:

```bash
git archive --format=zip --prefix=tow/ HEAD > /absolute/output/tow-0.1.1.zip
```

The portable/Claude archive includes root `plugin.json` and the host overlays. For the Antigravity archive, replace `tow/plugin.json` with the contents of `tow/.antigravity-plugin/plugin.json`, omit the nested overlay copy, and preserve every other ZIP entry and its metadata. The native manifest then sits at the canonical root location without duplicating any skill source. Validate the extracted archive with `agy plugin validate --strict <extracted/tow>`.

Antigravity CLI 1.4.12 warns when a root manifest is shadowed by its native overlay; `--strict` rejects that warning. This is why its public artifact contains one native root manifest. Direct GitHub installation still selects the native overlay, but is not the strict public-artifact check. No warning is suppressed and no validator flag is bypassed.

### Candidate checks completed

- Full suite: 51 passed against `tag-ontology` 0.1.2; Ruff lint/format and Pyright strict passed.
- Claude Code 2.1.310 validated the portable archive in strict mode with no icon warning.
- Antigravity CLI 1.4.12 validated the normalized native archive in strict JSON mode: four skills, no findings.
- Codex CLI 0.159.2 installed and enabled candidate 0.1.1; Antigravity installed candidate 0.1.1 with the four expected skills.
- Claude's ordinary native update advanced 0.1.0 to 0.1.1 after `dev` merge `5db6477`; the fresh installed query passed with no permission denials. Earlier quota-blocked and evaluator-denied attempts remain documented in the evaluation record.
- ZIP integrity, complete skill/reference assets, file-count/size bounds, absence of development caches/symlinks, and executable mode on `scripts/tow.py` were checked. Archives stay outside the repository.
- These are local candidate/artifact checks. Authenticated portal scans and post-promotion `main` installs are separate gates below.

### Main release gate

At this pre-promotion snapshot, `main` was the initial repository commit `b9fe178`; tested implementation work was on `dev`. The README install commands intentionally keep the default/main source. The Claude functional gate is now clear. Promote through a reviewed `dev` to `main` PR, then test those exact default-branch install commands. Do not repair release documentation directly on `main`.

A release should identify the final reviewed commit, attach the checked archives, and record post-merge CI and default-branch installation results. Local archive checks alone do not prove installation from a branch that has not been promoted.

### Public-directory gate

| Destination | Concrete next check |
| --- | --- |
| Own public GitHub marketplace | Main promotion and default-branch installation; no central listing form is required for the repository catalog |
| OpenAI directory | Upload the skills-only desktop archive, choose the submitting verified developer identity, and inspect portal metadata/skill scans before submission |
| Anthropic directory | Validate the repository in `claude.ai/directory/manage`, confirm the connected account's repository write access, and inspect directory findings |
| Antigravity Marketplace | Validate the native archive strictly, then provide it with the public repository through the official partner intake process |

These are different distribution paths. The [Claude directory process](https://code.claude.com/docs/en/plugins/publish) does not grant a listing in `claude-plugins-official`; official-marketplace placement uses Anthropic partner contact. The [OpenAI submission process](https://developers.openai.com/plugins/deploy/submission) requires publishing identity/access and portal checks. Antigravity links its [partner intake form](https://forms.gle/2EX5RFYPoJe1UgxR9) from the authoring guide.

This session could not access authenticated portals: computer-use inventory returned no browsers, with `The browser access host is unavailable` and native pipe startup failure. Portal access, name availability, verified publishing identity, linked GitHub access, automated directory scans, and review decisions therefore remain unverified. Do not infer account permissions from local CLI authentication, and do not claim a registration from a locally valid package.

### Ready-to-review listing data

- Product: **TOW**; identifier `tow`; candidate 0.1.1; category Productivity; publisher field `NamhyeonKo` (the existing public repository author, subject to the portal's verified identity).
- Subtitle: **Tag-first wiki for your notes**.
- Purpose: search/check local Obsidian notes, suggest concept tags, and reconcile the dictionary after the user's selection/approval.
- Requirements: local vault access, Python 3.10+, Node.js 22.18+, and the pinned npm CLI.
- Data behavior: the agent host processes the notes it opens; TOW has no hosted backend. npm fetches the CLI. File access and any elevated command approval remain controlled by the host.
- Source/website: `https://github.com/NamhyeonKo/tag-ontology-wiki`; support: the repository's Issues page; license MIT.
- Artwork: `assets/icon.png` (512x512 PNG) and editable `assets/icon.svg`.
- No MCP server, hooks, embedded credentials, demo account, or invented business/contact identity is included. Skills-only submission does not require the MCP-specific review cases or demo recording; portal requirements must still be checked.
