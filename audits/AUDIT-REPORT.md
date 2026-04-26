# License Audit Report — BAS-More Portfolio

Date: 2026-04-27
Tool: license-guards v0.1.0 (https://github.com/BAS-More/license-guards)
Scope: 9 active BAS-More product repos

## Executive summary

| Repo | EE-lint | Node deps | Python deps | Status |
|---|---|---|---|---|
| **MAH** | ✅ pass | ✅ pass | n/a | 🟢 CLEAN |
| **OmniDev** | ✅ pass | ✅ pass | n/a | 🟢 CLEAN |
| **Total-Recall** | ✅ pass | ✅ pass | n/a | 🟢 CLEAN |
| **Agent-MVP** | ✅ pass | ✅ pass | n/a | 🟢 CLEAN |
| **ezra-claude-code** | ✅ pass | ✅ pass | n/a | 🟢 CLEAN |
| **Tool Health Agent** | ✅ pass | n/a (no manifest) | n/a | 🟢 CLEAN |
| **TestTeam** | ✅ pass | 🟡 review (axe-core MPL-2.0) | n/a | 🟡 REVIEW |
| **Quiz2Biz** | ✅ pass | ⚠️ npm EOVERRIDE blocks check | n/a | ⚠️ FIX npm |
| **RuView** | ✅ pass | n/a | 🔴 BLOCKED + 🟡 review | 🔴 ACTION REQUIRED |

## Detailed findings

### 🔴 RuView — Python deps with viral-license risk

**Real blockers (replace or document):**

| Package | License | Issue | Action |
|---|---|---|---|
| `tld==0.13.2` | `MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later` | Triple-bad: every alternative is copyleft. Pick MPL-1.1, GPL-2, or LGPL — none safe for closed-source RuView | **Replace.** Try `tldextract` (BSD-3) — same purpose, clean license |
| `asyncssh==2.22.0` | `EPL-2.0 OR GPL-2.0-or-later` | EPL-2.0 weak copyleft + GPL alt. EPL-2.0 OK if not modifying source | **Document as EPL-2.0 use only**, add EPL-2.0 to allowed in this repo OR replace with `paramiko` (LGPL) or `fabric` (BSD) |
| `docutils==0.22.4` | `GNU General Public License (GPL)` (per pip-licenses) | Actually mixed BSD-2 + Python-2.0 + GPL (small file). Pip-licenses oversimplifies | **Whitelist via exception** with note: "actual license = BSD/Python/GPL mixed; we use only BSD-licensed parsers" |

**Review (LGPL — OK to use, attribution required):**

| Package | License | Action |
|---|---|---|
| `paramiko==4.0.0` | LGPL-2.1 | Keep — runtime use OK with notice |
| `semgrep==1.159.0` | LGPL-2.1-or-later | Keep — runtime use OK |
| `pystray==0.19.5` | LGPLv3 | Keep — runtime use OK |

**Unclassified (manual review):**

| Package | Reported as | Action |
|---|---|---|
| `caio==0.9.25` | UNKNOWN | Check upstream metadata |
| `peewee==3.19.0` | UNKNOWN | Actually MIT (verify pyproject) |
| `synthlang==0.1.4` | UNKNOWN | Internal/avi-os pkg — classify as proprietary or MIT |
| `regex==2026.4.4` | `Apache-2.0 AND CNRI-Python` | CNRI-Python is OSI-approved permissive — add to allow |
| `pillow==12.1.1` | `MIT-CMU` | MIT variant — add to allow |
| `email-validator` | `The Unlicense (Unlicense)` | Whitespace mismatch — already allowed, fix verbose name in config |

### 🟡 TestTeam — `axe-core` family MPL-2.0

| Package | License | Action |
|---|---|---|
| `@axe-core/playwright@4.11.1` | MPL-2.0 | Keep — MPL-2.0 added to allowed (file-level copyleft only, doesn't infect TestTeam code) |
| `axe-core@4.11.1` | MPL-2.0 | Same — file-level copyleft is fine for use as a library |

**Recommendation:** Add MPL-2.0 to `allowed` in `.licensechecker.json` permanently (it's added in updated config v0.1.0).

### ⚠️ Quiz2Biz — npm install broken (pre-existing)

```
npm error code EOVERRIDE
npm error Override for protobufjs@^7.5.5 conflicts with direct dependency
```

**Action:** Resolve npm dep conflict in package.json, then re-run `npm run check:licenses`. Not a license issue per se, but blocks scan.

### 🟢 Tool Health Agent — no package manifest

Pure shell + PowerShell scripts (no Node/Python/Rust deps to scan). Add `requirements.txt` or `package.json` if dependencies are introduced.

## Operational state

- ✅ **GitHub repo created:** https://github.com/BAS-More/license-guards (private)
- ✅ **CI workflows installed:** all 9 repos have `.github/workflows/license-guard.yml`
- ✅ **EE-path lint operational:** 0 false positives across 9 repos
- ✅ **License-checker operational:** Node validation passing in 5 repos, 2 needing attention
- ✅ **SPDX compound (`A OR B`, `A AND B`) handled** in both Node and Python validators

## Next-step priorities

1. **RuView** — replace `tld` package with `tldextract` (1-line PR equivalent). Replace `asyncssh` if EPL-2.0 not acceptable. Add `docutils` exception with note.
2. **Quiz2Biz** — fix `protobufjs@^7.5.5` override conflict, re-run audit.
3. **TestTeam** — confirm MPL-2.0 acceptable for org policy (it is, per spec); commit updated config.
4. **All repos** — commit `.github/workflows/license-guard.yml` + initial `THIRD_PARTY_NOTICES.md` so future PRs auto-gate.
5. **Quarterly** — re-run `bash /c/Dev/license-guards/scripts/check-licenses.sh --audit` to catch new EE/enterprise dirs added by upstream deps.
