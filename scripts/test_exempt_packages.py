#!/usr/bin/env python3
"""Regression tests for [exempt_packages] support in validate-py-licenses.py.

Runs without pytest. Exit 0 = all pass.

  python scripts/test_exempt_packages.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).parent / "validate-py-licenses.py"


def _run(licenses_json: list, config_toml: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        lic_path = td_p / "lic.json"
        cfg_path = td_p / "cfg.toml"
        lic_path.write_text(json.dumps(licenses_json), encoding="utf-8")
        cfg_path.write_text(config_toml, encoding="utf-8")
        # Force UTF-8 on stdout/stderr so the script's `✓` glyph and ANSI
        # colour codes don't blow up on Windows cp1252 default streams.
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), str(lic_path), str(cfg_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        return result.returncode, result.stdout, result.stderr


_BASE_CFG = textwrap.dedent(
    """
    [allowed]
    licenses = ["MIT License", "BSD-3-Clause"]

    [blocked]
    licenses = ["GNU General Public License v2 (GPLv2)"]

    [review_required]
    licenses = ["LGPL-2.1"]
    """
).strip()


class TestExemptPackages(unittest.TestCase):
    def test_exempt_skips_blocked_license(self):
        cfg = _BASE_CFG + "\n\n[exempt_packages]\nnames = [\"scapy\"]\n"
        pkgs = [{"Name": "scapy", "Version": "2.7.0", "License": "GNU General Public License v2 (GPLv2)"}]
        code, _, err = _run(pkgs, cfg)
        self.assertEqual(code, 0, f"expected exit 0, got {code}; stderr: {err}")
        self.assertIn("EXEMPT PACKAGES", err)
        self.assertIn("scapy==2.7.0", err)
        self.assertNotIn("BLOCKED LICENSES", err)

    def test_non_exempt_still_blocks(self):
        cfg = _BASE_CFG + "\n\n[exempt_packages]\nnames = [\"scapy\"]\n"
        pkgs = [{"Name": "other-gpl-pkg", "Version": "1.0", "License": "GNU General Public License v2 (GPLv2)"}]
        code, _, err = _run(pkgs, cfg)
        self.assertEqual(code, 1, f"expected exit 1, got {code}; stderr: {err}")
        self.assertIn("BLOCKED LICENSES", err)
        self.assertIn("other-gpl-pkg", err)

    def test_exempt_with_reason_is_logged(self):
        cfg = (
            _BASE_CFG
            + '\n\n[exempt_packages]\nnames = ["scapy"]\n[exempt_packages.reasons]\nscapy = "Pure-Python decoder; no static linking."\n'
        )
        pkgs = [{"Name": "scapy", "Version": "2.7.0", "License": "GNU General Public License v2 (GPLv2)"}]
        code, _, err = _run(pkgs, cfg)
        self.assertEqual(code, 0)
        self.assertIn("Pure-Python decoder", err)

    def test_no_exempt_section_works(self):
        """Repos without [exempt_packages] still validate normally."""
        pkgs = [{"Name": "requests", "Version": "2.31.0", "License": "MIT License"}]
        code, _, err = _run(pkgs, _BASE_CFG)
        self.assertEqual(code, 0, f"stderr: {err}")
        self.assertNotIn("EXEMPT PACKAGES", err)

    def test_exempt_does_not_affect_unknown(self):
        cfg = _BASE_CFG + "\n\n[exempt_packages]\nnames = [\"only-scapy\"]\n"
        pkgs = [
            {"Name": "only-scapy", "Version": "1.0", "License": "GNU General Public License v2 (GPLv2)"},
            {"Name": "weirdo-pkg", "Version": "1.0", "License": "Some-Random-License"},
        ]
        code, _, err = _run(pkgs, cfg)
        # only-scapy is exempt -> no contribution. weirdo-pkg is unknown -> exit 2.
        self.assertEqual(code, 2)
        self.assertIn("UNKNOWN", err)
        self.assertIn("weirdo-pkg", err)
        self.assertIn("EXEMPT PACKAGES", err)
        self.assertIn("only-scapy", err)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
