# Release readiness: TOW 0.1.1 candidate

Checked on 2026-11-02. This is a candidate and a verification record, not a publication or directory-approval claim.

## Functional checks

| Gate | Result |
| --- | --- |
| Codex query and all three editing workflows | Passed on installed 0.1.0 runtime `33f09ab`; exact deltas and approval-phase hashes independently checked |
| Antigravity query and all three editing workflows | Passed; sync needed normal scoped host permission retries |
| Claude installed query | Blocked before inference by account `429 usage_limit_reached`; CLI reset notice 04:20 Asia/Seoul |
| User vaults | Not used; each scenario had an independent synthetic copy |

See [evaluation](evaluation.md) for scenarios, preserved boundaries, versions, and runtime failures. Model-backed tests are individual observations, not a statistical reliability benchmark.

## Candidate changes

- Raise all manifests and Python project metadata from 0.1.0 to 0.1.1. An observed `claude plugin update` kept the older installed copy when both versions were 0.1.0. Native reinstall confirmed the new conventions loaded. Versioned releases must advance so an ordinary update can fetch them. [Claude release guidance](https://code.claude.com/docs/en/plugins/publish).
- Pin the default executable to `npx --yes tag-ontology@0.1.2`, which is the package used in the successful integration and editing checks. This supersedes the earlier 0.1 minor-range choice for public distribution. Exact registry versions are required by the [Anthropic pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist). The explicit `TOW_TAG_ONTOLOGY` override remains available.
- Declare OpenAI's `requires_local_executor: true`, include listing text and a shared 512-pixel PNG, and keep TOW skills-only. A local vault and Python/npm execution are required. [Desktop-only skills submission](https://developers.openai.com/plugins/deploy/desktop-only), [listing metadata](https://developers.openai.com/plugins/deploy/submission).
- Add an Antigravity-specific manifest for its display name, logo, and starter prompts while sharing every skill and helper. [Antigravity authoring requirements](https://antigravity.google/docs/build-plugins).

## Distribution artifacts

Keep archives outside the repository; a bundled ZIP would itself be an extra binary for directory review. Export committed files with executable modes preserved:

```bash
git archive --format=zip --prefix=tow/ HEAD > /absolute/output/tow-0.1.1.zip
```

The portable/Claude archive includes root `plugin.json` and the host overlays. For the Antigravity archive, replace `tow/plugin.json` with the contents of `tow/.antigravity-plugin/plugin.json`, omit the nested overlay copy, and preserve every other ZIP entry and its metadata. The native manifest then sits at the canonical root location without duplicating any skill source. Validate the extracted archive with `agy plugin validate --strict <extracted/tow>`.

Antigravity CLI 1.4.12 warns when a root manifest is shadowed by its native overlay; `--strict` rejects that warning. This is why its public artifact contains one native root manifest. Direct GitHub installation still selects the native overlay, but is not the strict public-artifact check. No warning is suppressed and no validator flag is bypassed.

## Candidate checks completed

- Full suite: 51 passed against `tag-ontology` 0.1.2; Ruff lint/format and Pyright strict passed.
- Claude Code 2.1.310 validated the portable archive in strict mode with no icon warning.
- Antigravity CLI 1.4.12 validated the normalized native archive in strict JSON mode: four skills, no findings.
- Codex CLI 0.159.2 installed and enabled candidate 0.1.1; Antigravity installed candidate 0.1.1 with the four expected skills.
- ZIP integrity, complete skill/reference assets, file-count/size bounds, absence of development caches/symlinks, and executable mode on `scripts/tow.py` were checked. Archives stay outside the repository.
- These are local candidate/artifact checks. Authenticated portal scans and post-promotion `main` installs are separate gates below.

## Main release gate

`main` is still the initial repository commit `b9fe178`; tested implementation work is on `dev`. The README install commands intentionally keep the default/main source. Prepare and review a `dev` to `main` PR, clear the blocked Claude check, then promote and test those exact default-branch install commands. Do not repair release documentation directly on `main`.

No release tag or published GitHub release is created by this verification. A release should identify the final reviewed commit and attach the checked archives; local archive checks do not prove installation from a branch that has not been promoted.

## Public-directory gate

| Destination | Concrete next check |
| --- | --- |
| Own public GitHub marketplace | Main promotion and default-branch installation; no central listing form is required for the repository catalog |
| OpenAI directory | Upload the skills-only desktop archive, choose the submitting verified developer identity, and inspect portal metadata/skill scans before submission |
| Anthropic directory | Validate the repository in `claude.ai/directory/manage`, confirm the connected account's repository write access, and inspect directory findings |
| Antigravity Marketplace | Validate the native archive strictly, then provide it with the public repository through the official partner intake process |

These are different distribution paths. The [Claude directory process](https://code.claude.com/docs/en/plugins/publish) does not grant a listing in `claude-plugins-official`; official-marketplace placement uses Anthropic partner contact. The [OpenAI submission process](https://developers.openai.com/plugins/deploy/submission) requires publishing identity/access and portal checks. Antigravity links its [partner intake form](https://forms.gle/2EX5RFYPoJe1UgxR9) from the authoring guide.

This session could not access authenticated portals: computer-use inventory returned no browsers, with `The browser access host is unavailable` and native pipe startup failure. Portal access, name availability, verified publishing identity, linked GitHub access, automated directory scans, and review decisions therefore remain unverified. Do not infer account permissions from local CLI authentication, and do not claim a registration from a locally valid package.

## Ready-to-review listing data

- Product: **TOW**; identifier `tow`; candidate 0.1.1; category Productivity; publisher field `NamhyeonKo` (the existing public repository author, subject to the portal's verified identity).
- Subtitle: **Tag-first wiki for your notes**.
- Purpose: search/check local Obsidian notes, suggest concept tags, and reconcile the dictionary after the user's selection/approval.
- Requirements: local vault access, Python 3.10+, Node.js 22.18+, and the pinned npm CLI.
- Data behavior: the agent host processes the notes it opens; TOW has no hosted backend. npm fetches the CLI. File access and any elevated command approval remain controlled by the host.
- Source/website: `https://github.com/NamhyeonKo/tag-ontology-wiki`; support: the repository's Issues page; license MIT.
- Artwork: `assets/icon.png` (512x512 PNG) and editable `assets/icon.svg`.
- No MCP server, hooks, embedded credentials, demo account, or invented business/contact identity is included. Skills-only submission does not require the MCP-specific review cases or demo recording; portal requirements must still be checked.
