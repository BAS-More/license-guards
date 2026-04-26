#!/usr/bin/env bash
# check-licenses.sh — multi-stack license check wrapper.
# Detects project type (Node/Python/Rust) and runs appropriate validator against
# /c/Dev/license-guards/configs/*. Exits non-zero on blocked or unclassified licenses.
#
# Usage: ./check-licenses.sh [--audit]
#   --audit   Print full report instead of failing on first issue.

set -euo pipefail

GUARD_DIR="${GUARD_DIR:-/c/Dev/license-guards}"
AUDIT_MODE=0
[[ "${1:-}" == "--audit" ]] && AUDIT_MODE=1

EXIT=0
log()  { printf '\033[1;34m[license-guard]\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m[license-guard FAIL]\033[0m %s\n' "$*"; EXIT=1; }
ok()   { printf '\033[1;32m[license-guard OK]\033[0m %s\n' "$*"; }

# ---------------- Node ----------------
if [[ -f package.json ]]; then
  log "Node project detected"
  if ! command -v npx >/dev/null 2>&1; then
    fail "npx not found — install Node.js"
  else
    npx --yes license-checker --production --json --excludePrivatePackages > /tmp/lc.json 2>/dev/null || true
    node "$GUARD_DIR/scripts/validate-licenses.mjs" /tmp/lc.json "$GUARD_DIR/configs/.licensechecker.json" \
      || { fail "Node license check failed"; [[ $AUDIT_MODE -eq 0 ]] && exit 1; }
    ok "Node licenses validated"
  fi
fi

# ---------------- Python ----------------
if [[ -f pyproject.toml || -f requirements.txt || -f setup.py ]]; then
  log "Python project detected"
  if ! command -v pip-licenses >/dev/null 2>&1; then
    log "Installing pip-licenses..."
    pip install --quiet pip-licenses || pip install --quiet --user pip-licenses
  fi
  pip-licenses --format=json --with-license-file > /tmp/py-lc.json
  python "$GUARD_DIR/scripts/validate-py-licenses.py" /tmp/py-lc.json "$GUARD_DIR/configs/pip-licenses.toml" \
    || { fail "Python license check failed"; [[ $AUDIT_MODE -eq 0 ]] && exit 1; }
  ok "Python licenses validated"
fi

# ---------------- Rust ----------------
if [[ -f Cargo.toml ]]; then
  log "Rust project detected"
  if ! command -v cargo-deny >/dev/null 2>&1; then
    log "Installing cargo-deny..."
    cargo install --quiet cargo-deny --locked
  fi
  cp "$GUARD_DIR/configs/deny.toml" deny.toml.tmp
  cargo deny --config deny.toml.tmp check licenses \
    || { fail "Rust license check failed"; [[ $AUDIT_MODE -eq 0 ]] && exit 1; }
  rm -f deny.toml.tmp
  ok "Rust licenses validated"
fi

# ---------------- EE-path lint ----------------
log "Running EE/enterprise import lint..."
bash "$GUARD_DIR/scripts/check-ee-imports.sh" \
  || { fail "EE-path import lint failed"; [[ $AUDIT_MODE -eq 0 ]] && exit 1; }
ok "EE-path lint passed"

if [[ $EXIT -eq 0 ]]; then
  log "All license guards passed ✓"
else
  log "License guards FAILED — see messages above"
fi
exit $EXIT
