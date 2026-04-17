#!/usr/bin/env python3
"""Tests for validate.py."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import validate  # noqa: E402


class TestValidateDocumentation(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_missing_docs_fails(self):
        """Returns False when required docs are absent."""
        self.assertFalse(validate.validate_documentation())

    def test_readme_sections_detected(self):
        """Scans README for current required sections."""
        Path("README.md").write_text(
            "# Project\n## Quick Start\n## How It Works\n## Features\n"
        )
        Path("docs").mkdir()
        (Path("docs") / "architecture.md").write_text("# arch")
        (Path("docs") / "setup-guide.md").write_text("# setup")

        self.assertTrue(validate.validate_documentation())

    def test_readme_missing_sections_still_passes_docs_check(self):
        """Missing README sections are warnings, not failures."""
        Path("README.md").write_text("# Project\n")
        Path("docs").mkdir()
        (Path("docs") / "architecture.md").write_text("# arch")
        (Path("docs") / "setup-guide.md").write_text("# setup")

        self.assertTrue(validate.validate_documentation())


if __name__ == "__main__":
    unittest.main()
