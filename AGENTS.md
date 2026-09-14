<!-- bas-more-project-memory:v1:start -->
## Project memory
After the repository's mandatory entry and handover reads, read
.project-memory/config.json and .project-memory/POLICY.md from the repository root.
Setup is enabled by the owner. Continue incomplete setup within this repository
without asking again; preserve any working graph engine and its recorded pins.
Before coding, use the documented session/freshness, context and upstream-impact
workflow. After edits, refresh relevant graphs and record actual validation.
Graph readiness requires the policy's acceptance evidence; installed rules alone
do not establish that graphs, semantic retrieval, hooks or integrations work.
<!-- bas-more-project-memory:v1:end -->

# AGENTS.md — operating contract for AI coding agents (Jules, etc.)

Agents read this file automatically. Your job is to FIX the issue, not introduce new ones — smallest change wins.

## Build / test / verify
- Lint: none configured.
- Test (Python): `python tests/test_split_spdx.py` and `python tests/test_exempt_packages.py` (standalone unittest).
- Node validators: verify via CLI, e.g. `node scripts/validate-licenses.mjs <licenses.json> <config.json>` (exit 0 = OK).

A change is not done until the build passes and the full existing test suite passes.

## Operating constraints
1. Smallest change; no unrelated refactors, reformatting, or renames.
2. Stay in scope; <= ~150 changed lines / <= 5 files. Larger -> stop and report for re-scoping.
3. Prove it: add a test that fails before / passes after; run the full suite; if anything fails, open NO pull request — report instead.
4. Preserve existing public APIs and behaviour unless the task explicitly changes them.
5. In the PR description, list every file changed and why, and the tests you added.

## Forbidden zones — STOP and report; never touch unless that IS the explicit task
Auth / authorization, payments / billing, secrets / credentials, database schema or migrations, CI / deploy / infrastructure config, adding new dependencies, any change to a public API or on-wire behaviour, and any branch that auto-deploys to production.

## If you cannot comply
If you cannot satisfy these constraints — or after genuine investigation you find no real issue — open NO pull request and report what you checked and what is blocking. Do not invent or manufacture work.
