#!/usr/bin/env python3
"""Tests for validate.py."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import validate  # noqa: E402


class TestRunCommand(unittest.TestCase):
    def test_run_command_returns_stderr_on_exception(self):
        with mock.patch("subprocess.run", side_effect=OSError("boom")):
            success, stdout, stderr = validate.run_command(["tool", "--version"])

        self.assertFalse(success)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "boom")


class TestValidateTerraform(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def make_provider_dir(self, name):
        provider_dir = Path("terraform") / "providers" / name
        provider_dir.mkdir(parents=True)
        for filename in ("main.tf", "variables.tf", "outputs.tf"):
            (provider_dir / filename).write_text("")
        return provider_dir

    def test_missing_terraform_dir_fails(self):
        self.assertFalse(validate.validate_terraform())

    def test_no_provider_root_modules_fails(self):
        (Path("terraform") / "providers").mkdir(parents=True)

        with mock.patch("validate.run_command", return_value=(True, "", "")):
            self.assertFalse(validate.validate_terraform())

    def test_missing_required_file_fails(self):
        provider_dir = self.make_provider_dir("hetzner")
        (provider_dir / "outputs.tf").unlink()

        with mock.patch("validate.run_command", return_value=(True, "", "")):
            self.assertFalse(validate.validate_terraform())

    def test_valid_provider_dirs_pass(self):
        self.make_provider_dir("hetzner")
        self.make_provider_dir("aws")

        with mock.patch("validate.run_command", return_value=(True, "", "")):
            self.assertTrue(validate.validate_terraform())

    def test_init_failure_for_one_provider_fails_overall(self):
        self.make_provider_dir("hetzner")
        self.make_provider_dir("aws")

        def fake_run_command(cmd, cwd=None):
            if cmd[:2] == ["terraform", "init"] and str(cwd).endswith("aws"):
                return False, "", "init failed"
            return True, "", ""

        with mock.patch("validate.run_command", side_effect=fake_run_command):
            self.assertFalse(validate.validate_terraform())


class TestValidateFrontend(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_missing_frontend_fails(self):
        self.assertFalse(validate.validate_frontend())

    def test_invalid_package_json_fails(self):
        frontend = Path("frontend")
        frontend.mkdir()
        (frontend / "package.json").write_text("{invalid")
        (frontend / "vite.config.js").write_text("")
        (frontend / "index.html").write_text("")

        self.assertFalse(validate.validate_frontend())


class TestValidateGithubActions(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.original_cwd)

    def test_missing_workflows_fails(self):
        self.assertFalse(validate.validate_github_actions())

    def test_invalid_workflow_yaml_fails(self):
        workflows = Path(".github/workflows")
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text("name: [")

        self.assertFalse(validate.validate_github_actions())


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
