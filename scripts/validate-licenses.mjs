#!/usr/bin/env node
// validate-licenses.mjs — Node license-checker output validator.
// Usage: node validate-licenses.mjs <license-checker.json> <config.json>
// Exits 1 if any blocked license found, 2 if review-required without exception.

import { readFileSync } from 'node:fs';

const [, , lcPath, cfgPath] = process.argv;
if (!lcPath || !cfgPath) {
  console.error('Usage: validate-licenses.mjs <license-checker.json> <config.json>');
  process.exit(64);
}

const lc = JSON.parse(readFileSync(lcPath, 'utf8'));
const cfg = JSON.parse(readFileSync(cfgPath, 'utf8'));

const allow = new Set(cfg.allowed || []);
const block = new Set(cfg.blocked || []);
const review = new Set(cfg.review_required || []);
const exceptions = cfg.exceptions || {};

const blocked = [];
const flagged = [];
const unknown = [];

// Split SPDX compound expressions like "(MIT OR WTFPL)" or "Apache-2.0 AND BSD-3-Clause".
// Returns array of individual licenses.
function splitSpdx(expr) {
  return String(expr)
    .replace(/^\(|\)$/g, '')
    .split(/\s+(?:OR|AND)\s+/i)
    .map((s) => s.trim())
    .filter(Boolean);
}

function isAllowed(lic) {
  if (allow.has(lic)) return true;
  // Wildcard support: "MIT*" matches "MIT-0", "MIT License" etc.
  for (const a of allow) {
    if (a.endsWith('*') && lic.startsWith(a.slice(0, -1))) return true;
    if (lic === a) return true;
  }
  return false;
}

for (const [pkgVer, info] of Object.entries(lc)) {
  const licenses = Array.isArray(info.licenses) ? info.licenses : [info.licenses || 'UNKNOWN'];
  const pkgName = pkgVer.replace(/@[^@]+$/, '');

  for (const lic of licenses) {
    const norm = String(lic).trim();

    // Skip the _comment key + per-package exemptions
    if (pkgName === '_comment') continue;
    if (exceptions[pkgName] && pkgName !== '_comment') continue;
    if (exceptions[pkgVer] && pkgVer !== '_comment') continue;

    // Compound expression handling: if expression contains OR, it's allowed if ANY
    // sub-license is allowed. If expression contains only AND, all must be allowed.
    const isCompoundOr = /\bOR\b/i.test(norm);
    const subs = splitSpdx(norm);

    if (isCompoundOr) {
      // OR: pass if ANY sub-license is allowed and none are blocked
      const anyAllowed = subs.some(isAllowed);
      const anyBlocked = subs.some((s) => block.has(s));
      if (anyBlocked && !anyAllowed) {
        blocked.push({ pkg: pkgVer, license: norm, repo: info.repository });
      } else if (!anyAllowed) {
        // None allowed, none blocked → review needed
        if (subs.some((s) => review.has(s))) {
          flagged.push({ pkg: pkgVer, license: norm, repo: info.repository });
        } else {
          unknown.push({ pkg: pkgVer, license: norm, repo: info.repository });
        }
      }
      // else: at least one allowed → OK
      continue;
    }

    // Single license or AND-compound: every sub must be allowed
    if (subs.some((s) => block.has(s))) {
      blocked.push({ pkg: pkgVer, license: norm, repo: info.repository });
      continue;
    }
    if (subs.some((s) => review.has(s))) {
      flagged.push({ pkg: pkgVer, license: norm, repo: info.repository });
      continue;
    }
    if (!subs.every(isAllowed)) {
      unknown.push({ pkg: pkgVer, license: norm, repo: info.repository });
    }
  }
}

let exit = 0;

if (blocked.length) {
  console.error('\x1b[1;31m[license-guard] BLOCKED LICENSES (build will fail):\x1b[0m');
  for (const b of blocked) console.error(`  - ${b.pkg}  [${b.license}]  ${b.repo || ''}`);
  exit = 1;
}

if (flagged.length) {
  console.warn('\x1b[1;33m[license-guard] REVIEW-REQUIRED LICENSES (manual classification needed):\x1b[0m');
  for (const f of flagged) console.warn(`  - ${f.pkg}  [${f.license}]  ${f.repo || ''}`);
  if (exit === 0) exit = 2;
}

if (unknown.length) {
  console.warn('\x1b[1;33m[license-guard] UNKNOWN/UNCLASSIFIED LICENSES:\x1b[0m');
  for (const u of unknown) console.warn(`  - ${u.pkg}  [${u.license}]  ${u.repo || ''}`);
  console.warn('Add to allowed/blocked/review_required in .licensechecker.json before merging.');
  if (exit === 0) exit = 2;
}

if (exit === 0) {
  console.log('\x1b[1;32m[license-guard] All Node deps OK ✓\x1b[0m');
}
process.exit(exit);
