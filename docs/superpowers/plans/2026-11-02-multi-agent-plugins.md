# Multi-agent Plugins Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package TOW for Claude Code, Codex, and Antigravity using the same skills and CLI.

**Architecture:** Keep one skill tree and helper. Add a portable root manifest and Codex catalog; resolve the helper from the installed package location.

**Tech Stack:** JSON manifests, Markdown skills, existing Python 3.10+ standard-library CLI and pytest.

**Spec:** [Design](../specs/2026-11-02-multi-agent-plugins-design.md).

## Global Constraints

- No new runtime dependencies, hooks, MCP servers, installers, or duplicated skill trees are needed.
- README installation instructions target the repository's default `main` after release.
- Note preservation, approval rules, CLI behavior, and the `tag-ontology@0.1` dependency remain unchanged.

## Review Focus

- A relocated install, including spaces, must resolve its helper without provider environment variables.
- Every relative skill reference must remain inside the installed package and exist.
- Claude, Codex, and Antigravity must discover the same four skills.
- A marketplace catalog must point at the complete plugin rather than its manifest directory.
- Document local-client evidence separately from future `main` distribution and model-backed execution.

### Task 1: Shared package contract

**Files:** create `plugin.json`, `.agents/plugins/marketplace.json`, and `tests/test_packaging.py`; modify `docs/methodology.md`.

**Interfaces:** consumes the existing `skills/`, `docs/`, and executable `scripts/tow.py`; produces a single relocatable package with default `skills/` discovery.

- [ ] Add tests for matching package identity, the root Codex catalog entry, all skill-relative references, and relocated direct-path execution with host variables absent.
- [ ] Run `uv run pytest tests/test_packaging.py -q`; confirm missing manifests fail before adding them.
- [ ] Add the portable manifest and Codex catalog, using current name `tow` and version `0.1.0`; replace the Claude-only root lookup in shared conventions.
- [ ] Run the package tests and existing suite, Ruff lint/format, and Pyright; fix only failures introduced by this change.

### Task 2: Native installation and documentation

**Files:** modify `README.md`, `README.ko.md`, and `docs/evaluation.md`; modify `.github/workflows/ci.yml` only if a reproducible client check is needed beyond the package tests.

**Interfaces:** consumes Task 1's shared package; produces verified platform-specific installation examples and an honest support record.

- [ ] Validate Claude and Antigravity with their native commands; install the complete staged package through Codex and Antigravity and inspect four skill paths and the helper executable.
- [ ] Smoke-test installed helper commands on synthetic vaults. Attempt model-backed query execution where account access permits; retain failures as limits.
- [ ] Add concise install/invocation sections for all three hosts without changing release instructions to `dev`.
- [ ] Record versions, results, and limits; mark task results here.
- [ ] Commit the implementation; obtain independent whole-diff review and resolve substantive findings.
- [ ] Open a `dev` PR, verify CI and Codex review, merge only into `dev`, then verify post-merge CI and a clean local branch.
