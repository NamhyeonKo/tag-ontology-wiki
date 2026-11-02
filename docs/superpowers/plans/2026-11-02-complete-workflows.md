# Complete Portable TOW Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Port all six remaining workflows, preserving their functionality/approval boundaries, and ship a verified ten-skill GitHub package.

**Architecture:** Shared skills and references use the existing helper and effective `tow.json` settings. Note parsing and ontology operations remain delegated to pinned tag-ontology 0.1.2. Legacy classification conversion is an approved agent workflow, not a new parser.

**Tech Stack:** Markdown skills, Python 3.10+ standard library, pytest, native Claude/Codex/Antigravity clients.

**Spec:** `docs/superpowers/specs/2026-11-02-complete-workflows-design.md`

## Global Constraints

- Preserve all original six workflows and the approval matrix in the spec.
- Keep external CLI `npx --yes tag-ontology@0.1.2`; package/project version 0.2.0.
- No real vault writes, new runtime dependencies, global permission changes, or official-directory submission.
- Native tests use fresh synthetic copies, proposal hashes before approvals, and same-conversation continuations.
- Work in `feat/complete-workflows`; evidence and resumable progress live at `/private/tmp/tow-complete-workflows-20261102`.

## Review Focus

- Host/model fallback must not hide private path dependencies or unsupported legacy commands.
- Parent approval must preserve merge per-case selection and separate retroactive classification choices.
- Link updates must preserve display text and skip code/headings/ambiguity/private candidate paths.
- Intake/merge must preserve facts, shared attachments, source bytes, and inbound links before deletion.
- Custom layouts, ignored inputs and paper-title H1 exceptions must work without the original vault.

## Tasks

### 1. Portable settings and baseline

**Files:** `scripts/tow.py`, `tests/test_tow.py`, fixture `tow.json`, shared conventions.
**Interfaces:** `read_config`/`load_config` retain `dict[str, str]`; add the four string settings from the spec without expanding default note scope.

- [x] Record original skill hashes and meaningful unadapted portability failures.
- [x] Add failing tests for custom input/attachment/daily/misc settings and unsafe new paths; run and inspect failures.
- [x] Add minimal configuration support; update exact fixture/config expectations; run the suite.

### 2–7. Port one skill at a time

**Order:** classify → link → edit → merge → review → ingest.
**Files:** corresponding `skills/tow-*/SKILL.md`; referenced assets under edit/review/ingest; shared conventions/check workflow where paper handling requires it.
**Interfaces:** use `tow config`, configured roots/dictionaries, existing helper `lint`/`ontology` and named peer skills.

For each of the six tasks:

- [x] Read its full original and referenced policies; account for every function and approval boundary.
- [x] Use the recorded baseline and a per-skill synthetic scenario before writing the port.
- [x] Write the portable English workflow and necessary references, keeping original Korean discovery triggers.
- [x] Run a fresh-agent application/contract check and resolve gaps before the next skill.
- [x] Record the exact functional/approval mapping and outcome in the progress ledger.

### 8. Package, documentation and regression gates

**Files:** all three manifests, `pyproject.toml`, `uv.lock`, `tests/test_packaging.py`, English/Korean READMEs and installation guides.
**Interfaces:** exactly ten skill names; all bundled references stay inside the plugin; package version 0.2.0.

- [x] Add failing complete-package checks for all ten skills and private-path/reference portability.
- [x] Bump package/project versions and update all ten-skill/setup/configuration documentation.
- [x] Run full unit/packaging/integration tests, Ruff lint/format, strict Pyright and native package validation.

### 9. Native installed-host validation

**Files:** synthetic scenario fixtures/evaluation record; native artifacts outside repository.
**Interfaces:** native installed 0.2.0 skills/helper, pinned default CLI, custom-layout scenario oracles.

- [x] Install the candidate and verify ten skills and source hashes on all three hosts.
- [x] Exercise classify/link/edit/merge/review/ingest on each, preserving each skill's distinct approval rules.
- [x] Verify pre-approval hashes, exact allowed deltas, unchanged facts/other files, and scratch/attachment outcomes.
- [x] Inspect every failed native tool call and record recovery/limits; rerun failed product cases after fixes.

### 10. Review, CI and promotion

- [x] Obtain fresh independent whole-branch review and resolve concrete findings.
- [ ] Push feature→dev PR; wait for all CI jobs and review completion before merging.
- [ ] Promote dev→main through a reviewed PR and check post-merge CI.
- [ ] Verify new-version installation from public main and publish a source-linked release record/artifacts if the final candidate is ready.
- [ ] Report verified results and any remaining blocker without claiming unexecuted scenarios passed.
