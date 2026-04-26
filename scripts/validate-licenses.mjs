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

for (const [pkgVer, info] of Object.entries(lc)) {
  const licenses = Array.isArray(info.licenses) ? info.licenses : [info.licenses || 'UNKNOWN'];
  const pkgName = pkgVer.replace(/@[^@]+$/, '');

  for (const lic of licenses) {
    const norm = String(lic).trim();

    if (exceptions[pkgName] || exceptions[pkgVer]) continue;

    if (block.has(norm)) {
      blocked.push({ pkg: pkgVer, license: norm, repo: info.repository, path: info.path });
      continue;
    }
    if (review.has(norm)) {
      flagged.push({ pkg: pkgVer, license: norm, repo: info.repository });
      continue;
    }
    if (!allow.has(norm) && ![...allow].some(a => norm.startsWith(a.replace(/\*$/, '')))) {
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
