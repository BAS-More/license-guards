#!/usr/bin/env node
// gen-notices.mjs — generate THIRD_PARTY_NOTICES.md from license-checker output.
// Usage: node gen-notices.mjs > THIRD_PARTY_NOTICES.md
// Run via npm script: "notices": "npx license-checker --json --production | node scripts/gen-notices.mjs > THIRD_PARTY_NOTICES.md"

import { readFileSync } from 'node:fs';

let raw = '';
if (process.stdin.isTTY) {
  // Stdin not piped — try ./licenses.json
  try {
    raw = readFileSync('./licenses.json', 'utf8');
  } catch {
    console.error('Pipe license-checker JSON to stdin or place licenses.json in cwd.');
    process.exit(64);
  }
} else {
  raw = await new Promise((resolve) => {
    const chunks = [];
    process.stdin.on('data', (c) => chunks.push(c));
    process.stdin.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
  });
}

const lc = JSON.parse(raw);

const lines = [];
lines.push('# Third-Party Notices');
lines.push('');
lines.push(`Generated: ${new Date().toISOString()}`);
lines.push('');
lines.push('This product uses open-source software listed below. Each entry retains its original copyright and license terms.');
lines.push('');

// Group by license
const byLicense = new Map();
for (const [pkgVer, info] of Object.entries(lc)) {
  const licenses = Array.isArray(info.licenses) ? info.licenses.join(', ') : (info.licenses || 'UNKNOWN');
  if (!byLicense.has(licenses)) byLicense.set(licenses, []);
  byLicense.get(licenses).push({
    pkg: pkgVer,
    publisher: info.publisher || '',
    repository: info.repository || '',
    url: info.url || '',
    licenseFile: info.licenseFile || '',
  });
}

const sortedLicenses = [...byLicense.keys()].sort();
for (const license of sortedLicenses) {
  lines.push(`## ${license}`);
  lines.push('');
  const pkgs = byLicense.get(license).sort((a, b) => a.pkg.localeCompare(b.pkg));
  for (const p of pkgs) {
    const link = p.repository || p.url;
    lines.push(`- **${p.pkg}**${p.publisher ? ` — ${p.publisher}` : ''}${link ? ` ([${link}](${link}))` : ''}`);
  }
  lines.push('');
}

lines.push('---');
lines.push('');
lines.push('Full license texts are reproduced in the `LICENSES/` directory of this repository (or available at the repository links above).');
lines.push('');

process.stdout.write(lines.join('\n'));
