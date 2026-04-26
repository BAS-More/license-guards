#!/usr/bin/env python3
"""validate-py-licenses.py — pip-licenses output validator.

Usage: python validate-py-licenses.py <licenses.json> <config.toml>
Exits 1 if any blocked license found, 2 if review-required.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


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

    blocked: list[dict[str, str]] = []
    flagged: list[dict[str, str]] = []
    unknown: list[dict[str, str]] = []

    for pkg in pkgs:
        license_str = (pkg.get("License") or "UNKNOWN").strip()
        # pip-licenses sometimes returns "; " separated
        for lic in [s.strip() for s in license_str.split(";")]:
            if not lic:
                continue
            entry = {"name": pkg.get("Name", "?"), "version": pkg.get("Version", "?"), "license": lic}
            if lic in block:
                blocked.append(entry)
            elif lic in review:
                flagged.append(entry)
            elif lic not in allow:
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

    if exit_code == 0:
        print("\033[1;32m[license-guard] All Python deps OK ✓\033[0m")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
