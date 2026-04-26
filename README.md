# License Guards

Cross-repo licensing guard rails for BAS-More products. Drops into any repo (Node/Python/Rust/Go) to enforce zero viral-license exposure.

## What it enforces

1. **No GPL/AGPL/SSPL/NOASSERTION deps** — fails CI on copyleft or ambiguous licenses
2. **No `ee/` or `enterprise/` imports** — fails CI if source files import from carve-out paths in scoped-permissive deps (Mastra, Onyx, LiteLLM, Langfuse, OpenHands)
3. **`THIRD_PARTY_NOTICES.md` always current** — auto-generated on every release; PR fails if stale

## Quick install (per repo)

```bash
# From the target repo root:
curl -fsSL https://raw.githubusercontent.com/BAS-More/license-guards/main/scripts/install.sh | bash
# Or local symlink during dev:
ln -s /c/Dev/license-guards/.licensechecker.json .licensechecker.json
ln -s /c/Dev/license-guards/scripts/check-ee-imports.sh scripts/check-ee-imports.sh
cp /c/Dev/license-guards/workflows/license-guard.yml .github/workflows/license-guard.yml
```

## Files

| Path | Purpose |
|---|---|
| `configs/.licensechecker.json` | Allow-list config for `license-checker` (Node) |
| `configs/pip-licenses.toml` | Allow-list for `pip-licenses` (Python) |
| `configs/deny.toml` | Allow-list for `cargo-deny` (Rust) |
| `scripts/check-licenses.sh` | Multi-stack license check wrapper |
| `scripts/check-ee-imports.sh` | Forbidden-path import lint |
| `scripts/gen-notices.mjs` | Generate `THIRD_PARTY_NOTICES.md` from installed deps |
| `scripts/install.sh` | One-command install into a target repo |
| `workflows/license-guard.yml` | GitHub Actions workflow template |

## Forbidden license SPDX identifiers

These fail builds:
- `GPL-1.0`, `GPL-2.0`, `GPL-3.0` (copyleft)
- `AGPL-1.0`, `AGPL-3.0` (network copyleft)
- `SSPL-1.0` (server-side public, not OSI)
- `LGPL-2.1`, `LGPL-3.0` (linker copyleft — flagged for review, not auto-block)
- `BUSL-1.1` (business-source — review case-by-case)
- `Custom`, `Other`, `NOASSERTION` (must be manually classified before proceeding)

## Forbidden import paths (carve-out lint)

Blocks any source-file `import`/`require`/`from` statement matching:
- `**/ee/**`
- `**/enterprise/**`
- `*-ee` (suffix)
- `*-enterprise` (suffix)

## Maintenance

Quarterly review: `scripts/check-licenses.sh --audit` reports any newly added carve-out paths in current deps.
