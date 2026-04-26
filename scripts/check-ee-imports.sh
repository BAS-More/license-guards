#!/usr/bin/env bash
# check-ee-imports.sh — fails CI if any source file imports from forbidden EE/enterprise paths.
# Catches accidental use of carve-out modules in scoped-permissive deps (Mastra, Onyx, LiteLLM, Langfuse, OpenHands).
#
# Usage: ./check-ee-imports.sh [src-dir]
#   src-dir defaults to "src" if exists, else "backend"/"packages", else current dir.
# Excludes: node_modules, .git, dist, build, .next, coverage, vendor, third_party.

set -euo pipefail

SEARCH_DIR="${1:-}"
if [[ -z "$SEARCH_DIR" ]]; then
  if [[ -d src ]]; then SEARCH_DIR="src"
  elif [[ -d backend ]]; then SEARCH_DIR="backend"
  elif [[ -d packages ]]; then SEARCH_DIR="packages"
  else SEARCH_DIR="."
  fi
fi

# Forbidden namespace patterns. Each MUST end in a quote/end-of-string boundary
# to avoid matching innocent words like `queue`, `tree`, `core`, `pipe`, `committee`.
#
# Pattern semantics: matches inside an import-like statement only.
# Quote chars are explicitly bracketed [\'\"] so the regex anchors are correct.
#
# Examples that SHOULD match (forbidden):
#   from '@mastra/core/auth/ee/jwt'
#   from 'openhands/enterprise/auth'
#   import * as ee from "@mastra/server-ee"
#   require("langfuse-ee")
#
# Examples that should NOT match:
#   from '../adapters/base'           (no /ee/ namespace)
#   from 'drizzle-orm/sqlite-core'    (ends in -core, not -ee)
#   from './scoring-queue.service'    (ends in -queue.service)
#   from '@scope/some-tree'           (ends in -tree)
FORBIDDEN_REGEXES=(
  # /ee/ namespace inside any import path
  "[\"'][^\"']*/ee/[^\"']+[\"']"
  # /enterprise/ namespace inside any import path
  "[\"'][^\"']*/enterprise/[^\"']+[\"']"
  # path ending in /ee
  "[\"'][^\"']*/ee[\"']"
  # path ending in /enterprise
  "[\"'][^\"']*/enterprise[\"']"
  # package name ending in -ee (preceded by / or @ to anchor at pkg boundary)
  "[\"'](@[^/\"']+/)?[a-zA-Z0-9_]+-ee[\"']"
  # package name ending in -enterprise
  "[\"'](@[^/\"']+/)?[a-zA-Z0-9_]+-enterprise[\"']"
  # @scope/ee or @scope/enterprise as package
  "[\"']@[a-zA-Z0-9_-]+/ee[\"']"
  "[\"']@[a-zA-Z0-9_-]+/enterprise[\"']"
)

EXCLUDE_DIRS=(
  --exclude-dir=node_modules
  --exclude-dir=.git
  --exclude-dir=.next
  --exclude-dir=dist
  --exclude-dir=build
  --exclude-dir=out
  --exclude-dir=coverage
  --exclude-dir=.turbo
  --exclude-dir=.cache
  --exclude-dir=vendor
  --exclude-dir=third_party
  --exclude-dir=__pycache__
  --exclude-dir=.venv
  --exclude-dir=venv
  --exclude-dir=target
  --exclude-dir=.gradle
  --exclude-dir=.idea
  --exclude-dir=.vscode
)

INCLUDES=(
  --include='*.ts' --include='*.tsx' --include='*.mts' --include='*.cts'
  --include='*.js' --include='*.mjs' --include='*.cjs' --include='*.jsx'
  --include='*.py' --include='*.rs' --include='*.go' --include='*.java' --include='*.kt'
)

VIOLATIONS=0
TMP=$(mktemp)

# Pre-filter: only lines that look like an import statement (cuts false positives + speed)
{
  grep -rEn "^[[:space:]]*(import |from |const .*=.*require\(|import\(|use |using )" "$SEARCH_DIR" \
    "${EXCLUDE_DIRS[@]}" "${INCLUDES[@]}" 2>/dev/null \
    || true
} > "$TMP"

for pattern in "${FORBIDDEN_REGEXES[@]}"; do
  if grep -E "$pattern" "$TMP" > /tmp/ee-hits.txt 2>/dev/null; then
    if [[ -s /tmp/ee-hits.txt ]]; then
      printf '\033[1;31m[ee-lint] FORBIDDEN: %s\033[0m\n' "$pattern"
      head -20 /tmp/ee-hits.txt | sed 's/^/  /'
      hit_count=$(wc -l < /tmp/ee-hits.txt | tr -d ' ')
      [[ "$hit_count" -gt 20 ]] && echo "  ... and $((hit_count - 20)) more"
      VIOLATIONS=$((VIOLATIONS + hit_count))
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
