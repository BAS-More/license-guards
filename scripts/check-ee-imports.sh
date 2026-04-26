#!/usr/bin/env bash
# check-ee-imports.sh — fails CI if any source file imports from forbidden EE/enterprise paths.
# Catches accidental use of carve-out modules in scoped-permissive deps (Mastra, Onyx, LiteLLM, Langfuse, OpenHands).
#
# Usage: ./check-ee-imports.sh [src-dir]
#   src-dir defaults to "src" if exists, else current dir.

set -euo pipefail

SEARCH_DIR="${1:-}"
if [[ -z "$SEARCH_DIR" ]]; then
  if [[ -d src ]]; then SEARCH_DIR="src"
  elif [[ -d backend ]]; then SEARCH_DIR="backend"
  elif [[ -d packages ]]; then SEARCH_DIR="packages"
  else SEARCH_DIR="."
  fi
fi

# Forbidden import path patterns (regex, case-sensitive).
# Format: substring that should never appear in an import string.
FORBIDDEN=(
  '/ee/'
  '\\ee\\'
  '/enterprise/'
  '\\enterprise\\'
  '-ee['"'"'"]'   # @scope/pkg-ee" or '...-ee'
  '-enterprise['"'"'"]'
  '/ee['"'"'"]'   # ends in /ee" or /ee'
  '/enterprise['"'"'"]'
)

# File patterns to scan
EXTENSIONS='\.(ts|tsx|mts|cts|js|mjs|cjs|jsx|py|rs|go|java|kt)$'

VIOLATIONS=0
TMP=$(mktemp)

# Find candidate import lines once
{
  grep -rEn "^[[:space:]]*(import|from|require|use|using)[[:space:]].*" "$SEARCH_DIR" 2>/dev/null \
    --include='*.ts' --include='*.tsx' --include='*.mts' --include='*.cts' \
    --include='*.js' --include='*.mjs' --include='*.cjs' --include='*.jsx' \
    --include='*.py' --include='*.rs' --include='*.go' --include='*.java' --include='*.kt' \
    || true
} > "$TMP"

for pattern in "${FORBIDDEN[@]}"; do
  if grep -E "$pattern" "$TMP" > /tmp/ee-hits.txt 2>/dev/null; then
    if [[ -s /tmp/ee-hits.txt ]]; then
      printf '\033[1;31m[ee-lint] FORBIDDEN PATTERN: %s\033[0m\n' "$pattern"
      cat /tmp/ee-hits.txt | sed 's/^/  /'
      VIOLATIONS=$((VIOLATIONS + $(wc -l < /tmp/ee-hits.txt)))
    fi
  fi
done

rm -f "$TMP" /tmp/ee-hits.txt

if [[ $VIOLATIONS -gt 0 ]]; then
  printf '\033[1;31m[ee-lint] %d violation(s) found. Imports from EE/enterprise paths are forbidden.\033[0m\n' "$VIOLATIONS"
  echo "Fix: replace with non-EE module path, or extract pattern via clean-room reimplementation."
  exit 1
fi

printf '\033[1;32m[ee-lint] No EE/enterprise imports detected. ✓\033[0m\n'
exit 0
