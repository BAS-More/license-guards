#!/usr/bin/env python3
"""validate-py-licenses.py — pip-licenses output validator with SPDX compound support.

Usage: python validate-py-licenses.py <licenses.json> <config.toml>
Exits 1 if any blocked license found, 2 if review-required or unknown.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


# Per the SPDX spec, OR/AND are uppercase keywords. The previous
# `re.IGNORECASE` flag false-matched the literal word " or " inside legitimate
# license names like "GNU Library or Lesser General Public License (LGPL)",
# splitting them into nonsense fragments.
SPDX_OR = re.compile(r"\s+OR\s+")
SPDX_AND = re.compile(r"\s+AND\s+")


def split_spdx(expr: str) -> tuple[list[str], str]:
    """Split a compound SPDX expression. Returns (subs, op) where op in {'OR','AND','SINGLE'}."""
    expr = expr.strip()
    # Strip outer parens ONLY if they wrap the whole expression — don't use
    # str.strip("()") because it chews trailing `)` off names like
    # "GNU General Public License v2 (GPLv2)" and breaks exact-string lookup.
    if expr.startswith("(") and expr.endswith(")"):
        expr = expr[1:-1].strip()
    if SPDX_OR.search(expr):
        return [s.strip() for s in SPDX_OR.split(expr) if s.strip()], "OR"
    if SPDX_AND.search(expr):
        return [s.strip() for s in SPDX_AND.split(expr) if s.strip()], "AND"
    return [expr], "SINGLE"


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: validate-py-licenses.py <licenses.json> <config.toml>", file=sys.stderr)
        return 64

    lic_path = Path(sys.argv[1])
    cfg_path = Path(sys.argv[2])

    pkgs = json.loads(lic_path.read_text(encoding="utf-8"))
    cfg = tomllib.loads(cfg_path.read_text(encoding="utf-8"))

    allow = set(cfg.get("allowed", {}).get("licenses", []))
    block = set(cfg.get("blocked", {}).get("licenses", []))
    review = set(cfg.get("review_required", {}).get("licenses", []))

    # Per-package exemptions — let a project explicitly accept a normally-
    # blocked license for a specific dependency without weakening the
    # license-string buckets for everything else. Each entry is the exact
    # `Name` field from pip-licenses output. Optional `reason` map lives
    # alongside for documentation; the script only needs the names.
    #
    # Schema (in pip-licenses.toml):
    #   [exempt_packages]
    #   names = ["scapy", "some-other-pkg"]
    #   [exempt_packages.reasons]
    #   scapy = "GPLv2 accepted: pure-Python protocol-decoder; no static linking; not redistributed."
    exempt_pkgs = set(cfg.get("exempt_packages", {}).get("names", []))

    def is_allowed(lic: str) -> bool:
        return lic in allow

    def is_blocked(lic: str) -> bool:
        return lic in block

    def is_review(lic: str) -> bool:
        return lic in review

    blocked: list[dict[str, str]] = []
    flagged: list[dict[str, str]] = []
    unknown: list[dict[str, str]] = []
    exempt_hits: list[dict[str, str]] = []

    for pkg in pkgs:
        pkg_name = pkg.get("Name", "?")
        license_str = (pkg.get("License") or "UNKNOWN").strip()

        # Per-package exemption: skip license-bucket checks entirely. The
        # package is recorded so reviewers see what was waved through.
        if pkg_name in exempt_pkgs:
            exempt_hits.append({"name": pkg_name, "version": pkg.get("Version", "?"), "license": license_str})
            continue

        if license_str in {"UNKNOWN", ""}:
            unknown.append({"name": pkg_name, "version": pkg.get("Version", "?"), "license": "UNKNOWN"})
            continue

        # pip-licenses sometimes returns "; " separated for multi-license meta — treat each independently
        for license_chunk in [s.strip() for s in license_str.split(";") if s.strip()]:
            subs, op = split_spdx(license_chunk)
            entry = {"name": pkg_name, "version": pkg.get("Version", "?"), "license": license_chunk}

            if op == "OR":
                # OR: pass if ANY sub is allowed
                if any(is_blocked(s) for s in subs) and not any(is_allowed(s) for s in subs):
                    blocked.append(entry)
                elif any(is_allowed(s) for s in subs):
                    pass  # OK
                elif any(is_review(s) for s in subs):
                    flagged.append(entry)
                else:
                    unknown.append(entry)
            elif op == "AND":
                # AND: must satisfy all subs
                if any(is_blocked(s) for s in subs):
                    blocked.append(entry)
                elif any(is_review(s) for s in subs):
                    flagged.append(entry)
                elif not all(is_allowed(s) for s in subs):
                    unknown.append(entry)
            else:
                # SINGLE
                lic = subs[0]
                if is_blocked(lic):
                    blocked.append(entry)
                elif is_review(lic):
                    flagged.append(entry)
                elif not is_allowed(lic):
                    unknown.append(entry)

    exit_code = 0

    if blocked:
        print("\033[1;31m[license-guard] BLOCKED LICENSES (build will fail):\033[0m", file=sys.stderr)
        for b in blocked:
            print(f"  - {b['name']}=={b['version']}  [{b['license']}]", file=sys.stderr)
        exit_code = 1

    if flagged:
        print("\033[1;33m[license-guard] REVIEW-REQUIRED LICENSES:\033[0m", file=sys.stderr)
        for f in flagged:
            print(f"  - {f['name']}=={f['version']}  [{f['license']}]", file=sys.stderr)
        if exit_code == 0:
            exit_code = 2

    if unknown:
        print("\033[1;33m[license-guard] UNKNOWN LICENSES (need classification):\033[0m", file=sys.stderr)
        for u in unknown:
            print(f"  - {u['name']}=={u['version']}  [{u['license']}]", file=sys.stderr)
        print("Add to allowed/blocked/review_required in pip-licenses.toml.", file=sys.stderr)
        if exit_code == 0:
            exit_code = 2

    # Surface exemptions in stderr so reviewers see them every run.
    # Always informational — never affects exit_code.
    if exempt_hits:
        reasons = cfg.get("exempt_packages", {}).get("reasons", {})
        print("\033[1;36m[license-guard] EXEMPT PACKAGES (per-project waiver):\033[0m", file=sys.stderr)
        for e in exempt_hits:
            why = reasons.get(e["name"], "no reason recorded")
            print(f"  - {e['name']}=={e['version']}  [{e['license']}]  - {why}", file=sys.stderr)

    if exit_code == 0:
        print("\033[1;32m[license-guard] All Python deps OK ✓\033[0m")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
