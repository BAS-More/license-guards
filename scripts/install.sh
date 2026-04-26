#!/usr/bin/env bash
# install.sh — bootstrap license-guards into target repo.
# Run from target repo root:  bash /c/Dev/license-guards/scripts/install.sh

set -euo pipefail

GUARD_DIR="${GUARD_DIR:-/c/Dev/license-guards}"
TARGET="${PWD}"

echo "[license-guards] Installing into: $TARGET"

# 1. Symlink config files (so they update centrally)
mkdir -p "$TARGET/.license-guards"
for cfg in .licensechecker.json pip-licenses.toml deny.toml; do
  if [[ -f "$GUARD_DIR/configs/$cfg" ]]; then
    ln -sf "$GUARD_DIR/configs/$cfg" "$TARGET/.license-guards/$cfg" 2>/dev/null || \
      cp "$GUARD_DIR/configs/$cfg" "$TARGET/.license-guards/$cfg"
    echo "  + .license-guards/$cfg"
  fi
done

# 2. Copy GitHub Actions workflow if .github/workflows exists or repo is git-tracked
if [[ -d .github/workflows ]] || [[ -d .git ]]; then
  mkdir -p .github/workflows
  cp "$GUARD_DIR/workflows/license-guard.yml" .github/workflows/license-guard.yml
  echo "  + .github/workflows/license-guard.yml"
fi

# 3. Add npm scripts if package.json exists
if [[ -f package.json ]]; then
  if command -v jq >/dev/null 2>&1; then
    jq '.scripts["check:licenses"] = "bash /c/Dev/license-guards/scripts/check-licenses.sh"
        | .scripts["check:ee"]       = "bash /c/Dev/license-guards/scripts/check-ee-imports.sh"
        | .scripts["gen:notices"]    = "npx license-checker --json --production | node /c/Dev/license-guards/scripts/gen-notices.mjs > THIRD_PARTY_NOTICES.md"' \
      package.json > package.json.tmp && mv package.json.tmp package.json
    echo "  + npm scripts: check:licenses, check:ee, gen:notices"
  else
    echo "  ! jq not found — add these scripts to package.json manually:"
    echo '    "check:licenses": "bash /c/Dev/license-guards/scripts/check-licenses.sh",'
    echo '    "check:ee": "bash /c/Dev/license-guards/scripts/check-ee-imports.sh",'
    echo '    "gen:notices": "npx license-checker --json --production | node /c/Dev/license-guards/scripts/gen-notices.mjs > THIRD_PARTY_NOTICES.md"'
  fi
fi

# 4. Append .gitignore entries (avoid committing temp lc files)
if [[ -f .gitignore ]]; then
  grep -qxF '/tmp/lc.json' .gitignore || echo '/tmp/lc.json' >> .gitignore
  grep -qxF 'licenses.json' .gitignore || echo 'licenses.json' >> .gitignore
fi

# 5. First-run audit
echo ""
echo "[license-guards] Running first audit..."
bash "$GUARD_DIR/scripts/check-licenses.sh" --audit || true

echo ""
echo "[license-guards] Install complete. Next steps:"
echo "  - npm run check:licenses          # validate deps"
echo "  - npm run check:ee                # validate imports"
echo "  - npm run gen:notices             # produce THIRD_PARTY_NOTICES.md"
echo "  - commit .github/workflows/license-guard.yml + THIRD_PARTY_NOTICES.md"
