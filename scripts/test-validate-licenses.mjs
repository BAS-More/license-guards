import { test } from 'node:test';
import assert from 'node:assert';
import { execSync } from 'node:child_process';
import { writeFileSync, unlinkSync } from 'node:fs';

test('validate-licenses handles lowercase "or" and trailing parenthesis correctly', (t) => {
  const lcPath = 'dummy-lc-test1.json';
  const cfgPath = 'dummy-cfg-test1.json';

  const lc = {
    "mypkg@1.0.0": {
      "licenses": ["GNU Library or Lesser General Public License (LGPL)"],
      "repository": "https://github.com/foo/bar"
    }
  };

  const cfg = {
    "allowed": [
      "GNU Library or Lesser General Public License (LGPL)"
    ]
  };

  writeFileSync(lcPath, JSON.stringify(lc));
  writeFileSync(cfgPath, JSON.stringify(cfg));

  try {
    const stdout = execSync(`node scripts/validate-licenses.mjs ${lcPath} ${cfgPath}`, { encoding: 'utf8' });
    assert.match(stdout, /All Node deps OK ✓/);
  } finally {
    unlinkSync(lcPath);
    unlinkSync(cfgPath);
  }
});

test('validate-licenses handles compound SPDX licenses correctly', (t) => {
  const lcPath = 'dummy-lc-test2.json';
  const cfgPath = 'dummy-cfg-test2.json';

  const lc = {
    "pkg-a@1.0.0": { "licenses": ["MIT OR Apache-2.0"] },
    "pkg-b@1.0.0": { "licenses": ["Apache-2.0 AND BSD-3-Clause"] },
    "pkg-c@1.0.0": { "licenses": ["(MIT OR GPL-3.0)"] }
  };

  const cfg = {
    "allowed": [
      "MIT",
      "Apache-2.0",
      "BSD-3-Clause"
    ],
    "blocked": [
      "GPL-3.0"
    ]
  };

  writeFileSync(lcPath, JSON.stringify(lc));
  writeFileSync(cfgPath, JSON.stringify(cfg));

  try {
    const stdout = execSync(`node scripts/validate-licenses.mjs ${lcPath} ${cfgPath}`, { encoding: 'utf8' });
    assert.match(stdout, /All Node deps OK ✓/);
  } finally {
    unlinkSync(lcPath);
    unlinkSync(cfgPath);
  }
});
