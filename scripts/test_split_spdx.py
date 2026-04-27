#!/usr/bin/env python3
"""Regression tests for split_spdx in validate-py-licenses.py.

Runs without pytest. Exit 0 = all pass, 1 = any fail.

  python scripts/test_split_spdx.py
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Import split_spdx from the sibling script. We can't `import validate-py-licenses`
# directly because of the dash, so use importlib.
import importlib.util

_HERE = Path(__file__).parent
_SPEC = importlib.util.spec_from_file_location(
    "validate_py_licenses", _HERE / "validate-py-licenses.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)
split_spdx = _MOD.split_spdx


class TestSplitSpdx(unittest.TestCase):
    """Cases the previous implementation got wrong, plus the SPDX-spec ones."""

    # --- bug fixes (regression guards) -------------------------------------

    def test_trailing_paren_in_license_name_is_preserved(self):
        """`str.strip("()")` would chew the trailing `)` off this name."""
        subs, op = split_spdx("GNU General Public License v2 (GPLv2)")
        self.assertEqual(op, "SINGLE")
        self.assertEqual(subs, ["GNU General Public License v2 (GPLv2)"])

    def test_lowercase_or_in_license_name_is_not_a_split_token(self):
        """`re.IGNORECASE` on `\\s+OR\\s+` would split this on " or "."""
        subs, op = split_spdx("GNU Library or Lesser General Public License (LGPL)")
        self.assertEqual(op, "SINGLE")
        self.assertEqual(subs, ["GNU Library or Lesser General Public License (LGPL)"])

    def test_lowercase_and_in_license_name_is_not_a_split_token(self):
        subs, op = split_spdx(
            "Historical Permission Notice and Disclaimer (HPND)"
        )
        self.assertEqual(op, "SINGLE")
        self.assertEqual(
            subs, ["Historical Permission Notice and Disclaimer (HPND)"]
        )

    def test_inner_parens_in_legit_name_are_preserved(self):
        subs, op = split_spdx("Mozilla Public License 2.0 (MPL 2.0)")
        self.assertEqual(op, "SINGLE")
        self.assertEqual(subs, ["Mozilla Public License 2.0 (MPL 2.0)"])

    # --- SPDX spec compliance (still works after fix) ----------------------

    def test_spdx_or_uppercase(self):
        subs, op = split_spdx("MIT OR Apache-2.0")
        self.assertEqual(op, "OR")
        self.assertEqual(subs, ["MIT", "Apache-2.0"])

    def test_spdx_and_uppercase(self):
        subs, op = split_spdx("MIT AND Apache-2.0")
        self.assertEqual(op, "AND")
        self.assertEqual(subs, ["MIT", "Apache-2.0"])

    def test_spdx_or_three_subs(self):
        subs, op = split_spdx("GPL-2.0 OR MIT OR Apache-2.0")
        self.assertEqual(op, "OR")
        self.assertEqual(subs, ["GPL-2.0", "MIT", "Apache-2.0"])

    def test_spdx_outer_parens_stripped(self):
        """SPDX expressions can be wrapped: `(MIT OR Apache-2.0)`."""
        subs, op = split_spdx("(MIT OR Apache-2.0)")
        self.assertEqual(op, "OR")
        self.assertEqual(subs, ["MIT", "Apache-2.0"])

    def test_spdx_outer_parens_with_padding(self):
        subs, op = split_spdx("  ( MIT OR Apache-2.0 )  ")
        self.assertEqual(op, "OR")
        self.assertEqual(subs, ["MIT", "Apache-2.0"])

    # --- single-license edge cases -----------------------------------------

    def test_single_simple(self):
        subs, op = split_spdx("MIT")
        self.assertEqual(op, "SINGLE")
        self.assertEqual(subs, ["MIT"])

    def test_single_with_padding(self):
        subs, op = split_spdx("  MIT License  ")
        self.assertEqual(op, "SINGLE")
        self.assertEqual(subs, ["MIT License"])

    def test_single_unbalanced_open_paren_left_alone(self):
        """Don't strip a single leading `(` if there's no matching `)`."""
        subs, op = split_spdx("(weirdly-named-license")
        self.assertEqual(op, "SINGLE")
        self.assertEqual(subs, ["(weirdly-named-license"])

    def test_single_unbalanced_close_paren_left_alone(self):
        subs, op = split_spdx("weirdly-named-license)")
        self.assertEqual(op, "SINGLE")
        self.assertEqual(subs, ["weirdly-named-license)"])


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
