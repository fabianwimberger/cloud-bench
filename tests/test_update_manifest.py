#!/usr/bin/env python3
"""Tests for update_manifest.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import update_manifest as um


class TestParseArgs(unittest.TestCase):
    def test_parse_args_required(self):
        """Test that required arguments are parsed."""
        original_argv = sys.argv
        try:
            sys.argv = [
                "update_manifest.py",
                "--manifest",
                "/data/manifest.json",
                "--run-dir",
                "runs/run-1",
                "--provider",
                "hetzner",
                "--region",
                "nbg1",
                "--timestamp",
                "20240101-120000",
            ]
            args = um.parse_args()
            self.assertEqual(args.manifest, "/data/manifest.json")
            self.assertEqual(args.run_dir, "runs/run-1")
            self.assertEqual(args.provider, "hetzner")
            self.assertEqual(args.region, "nbg1")
            self.assertEqual(args.timestamp, "20240101-120000")
        finally:
            sys.argv = original_argv


class TestLoadManifest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_existing_manifest(self):
        """Test loading an existing manifest file."""
        manifest_path = os.path.join(self.temp_dir, "manifest.json")
        data = {
            "schema_version": "2.0",
            "runs": [{"id": "run-1", "timestamp": "2024-01-01"}],
            "instance_index": {"cx11": ["run-1"]},
        }
        with open(manifest_path, "w") as f:
            json.dump(data, f)

        result = um.load_manifest(manifest_path)

        self.assertEqual(len(result["runs"]), 1)
        self.assertEqual(result["runs"][0]["id"], "run-1")
        self.assertEqual(result["instance_index"]["cx11"], ["run-1"])

    def test_load_nonexistent_manifest(self):
        """Test loading a manifest that doesn't exist creates a new one."""
        manifest_path = os.path.join(self.temp_dir, "nonexistent.json")

        result = um.load_manifest(manifest_path)

        self.assertEqual(result["schema_version"], "3.0")
        self.assertEqual(result["runs"], [])
        self.assertEqual(result["instance_index"], {})

    def test_load_manifest_missing_fields(self):
        """Test loading a manifest with missing fields adds them."""
        manifest_path = os.path.join(self.temp_dir, "manifest.json")
        data = {"schema_version": "2.0"}  # Missing runs and instance_index
        with open(manifest_path, "w") as f:
            json.dump(data, f)

        result = um.load_manifest(manifest_path)

        self.assertEqual(result["runs"], [])
        self.assertEqual(result["instance_index"], {})

    def test_load_invalid_json(self):
        """Test loading an invalid JSON creates a new manifest."""
        manifest_path = os.path.join(self.temp_dir, "invalid.json")
        with open(manifest_path, "w") as f:
            f.write("not valid json")

        result = um.load_manifest(manifest_path)

        self.assertEqual(result["schema_version"], "3.0")
        self.assertEqual(result["runs"], [])


class TestExtractInstancesFromRun(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_from_summary(self):
        """Test extracting instances from summary.json."""
        summary_path = os.path.join(self.temp_dir, "summary.json")
        summary = {
            "summary": {
                "instances": [
                    {"id": "cx11"},
                    {"id": "cpx11"},
                    {"id": "cax11"},
                ]
            }
        }
        with open(summary_path, "w") as f:
            json.dump(summary, f)

        result = um.extract_instances_from_run(self.temp_dir)

        self.assertEqual(len(result), 3)
        self.assertIn("cx11", result)
        self.assertIn("cpx11", result)
        self.assertIn("cax11", result)

    def test_extract_from_raw_directory(self):
        """Test extracting instances from raw directory fallback."""
        raw_dir = os.path.join(self.temp_dir, "raw")
        os.makedirs(raw_dir)

        # Create instance result files
        for instance_file in ["cx11-abc123.json", "cpx11-def456.json"]:
            with open(os.path.join(raw_dir, instance_file), "w") as f:
                json.dump({"data": "test"}, f)

        result = um.extract_instances_from_run(self.temp_dir)

        self.assertEqual(len(result), 2)
        self.assertIn("cx11", result)
        self.assertIn("cpx11", result)

    def test_extract_empty_run(self):
        """Test extracting from a run with no data."""
        result = um.extract_instances_from_run(self.temp_dir)

        self.assertEqual(result, [])

    def test_extract_invalid_summary_json(self):
        """Test handling invalid summary.json."""
        summary_path = os.path.join(self.temp_dir, "summary.json")
        with open(summary_path, "w") as f:
            f.write("invalid json")

        result = um.extract_instances_from_run(self.temp_dir)

        self.assertEqual(result, [])


class TestBuildInstanceIndex(unittest.TestCase):
    def test_build_index_single_run(self):
        """Test building index with a single run."""
        runs = [
            {
                "id": "run-1",
                "instances": ["cx11", "cpx11"],
            }
        ]

        result = um.build_instance_index(runs)

        self.assertEqual(result["cx11"], ["run-1"])
        self.assertEqual(result["cpx11"], ["run-1"])

    def test_build_index_multiple_runs(self):
        """Test building index with multiple runs."""
        runs = [
            {"id": "run-1", "instances": ["cx11", "cpx11"]},
            {"id": "run-2", "instances": ["cx11", "cax11"]},
        ]

        result = um.build_instance_index(runs)

        # cx11 appears in both runs
        self.assertEqual(sorted(result["cx11"]), ["run-1", "run-2"])
        # cpx11 and cax11 each appear in one run
        self.assertEqual(result["cpx11"], ["run-1"])
        self.assertEqual(result["cax11"], ["run-2"])

    def test_build_index_no_duplicates(self):
        """Test that duplicate run IDs are not added."""
        runs = [
            {"id": "run-1", "instances": ["cx11"]},
            {"id": "run-1", "instances": ["cx11"]},  # Duplicate
        ]

        result = um.build_instance_index(runs)

        # Should only have one entry
        self.assertEqual(result["cx11"], ["run-1"])

    def test_build_index_empty_runs(self):
        """Test building index with empty runs list."""
        result = um.build_instance_index([])

        self.assertEqual(result, {})


class TestMain(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manifest_path = os.path.join(self.temp_dir, "manifest.json")
        self.run_dir = os.path.join(self.temp_dir, "runs", "run-1")
        os.makedirs(self.run_dir)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_summary(self, instances):
        """Helper to create summary.json."""
        summary = {"summary": {"instances": [{"id": i} for i in instances]}}
        with open(os.path.join(self.run_dir, "summary.json"), "w") as f:
            json.dump(summary, f)

    def test_main_new_manifest(self):
        """Test creating a new manifest."""
        self.create_summary(["cx11", "cpx11"])

        original_argv = sys.argv
        try:
            sys.argv = [
                "update_manifest.py",
                "--manifest",
                self.manifest_path,
                "--run-dir",
                self.run_dir,
                "--provider",
                "hetzner",
                "--region",
                "nbg1",
                "--timestamp",
                "20240101-120000",
            ]
            um.main()

            with open(self.manifest_path) as f:
                manifest = json.load(f)

            self.assertEqual(manifest["schema_version"], "3.0")
            self.assertEqual(len(manifest["runs"]), 1)
            self.assertEqual(manifest["runs"][0]["id"], "20240101-120000-hetzner-nbg1")
            self.assertEqual(manifest["runs"][0]["instance_count"], 2)
            self.assertEqual(manifest["instance_index"]["cx11"], ["20240101-120000-hetzner-nbg1"])
        finally:
            sys.argv = original_argv

    def test_main_update_existing(self):
        """Test updating an existing manifest entry."""
        # Create initial manifest
        initial_manifest = {
            "schema_version": "3.0",
            "runs": [
                {
                    "id": "20240101-120000-hetzner-nbg1",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "instance_count": 1,
                    "instances": ["cx11"],
                    "files": {"summary": "runs/run-1/summary.json"},
                }
            ],
            "instance_index": {"cx11": ["20240101-120000-hetzner-nbg1"]},
        }
        with open(self.manifest_path, "w") as f:
            json.dump(initial_manifest, f)

        # Update with new instances
        self.create_summary(["cx11", "cpx11"])

        original_argv = sys.argv
        try:
            sys.argv = [
                "update_manifest.py",
                "--manifest",
                self.manifest_path,
                "--run-dir",
                self.run_dir,
                "--provider",
                "hetzner",
                "--region",
                "nbg1",
                "--timestamp",
                "20240101-120000",
            ]
            um.main()

            with open(self.manifest_path) as f:
                manifest = json.load(f)

            # Should still have only one run (updated)
            self.assertEqual(len(manifest["runs"]), 1)
            self.assertEqual(manifest["runs"][0]["instance_count"], 2)
            self.assertEqual(sorted(manifest["runs"][0]["instances"]), sorted(["cx11", "cpx11"]))
        finally:
            sys.argv = original_argv

    def test_main_sorts_by_timestamp(self):
        """Test that runs are sorted by timestamp descending."""
        # Create initial manifest with older run
        initial_manifest = {
            "schema_version": "3.0",
            "runs": [
                {
                    "id": "20240101-100000-hetzner-nbg1",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "instance_count": 1,
                    "instances": ["cx11"],
                    "files": {},
                }
            ],
            "instance_index": {},
        }
        with open(self.manifest_path, "w") as f:
            json.dump(initial_manifest, f)

        self.create_summary(["cpx11"])

        original_argv = sys.argv
        try:
            sys.argv = [
                "update_manifest.py",
                "--manifest",
                self.manifest_path,
                "--run-dir",
                self.run_dir,
                "--provider",
                "hetzner",
                "--region",
                "nbg1",
                "--timestamp",
                "20240101-120000",  # Newer
            ]
            um.main()

            with open(self.manifest_path) as f:
                manifest = json.load(f)

            # Runs should be sorted by timestamp descending
            self.assertEqual(len(manifest["runs"]), 2)
            self.assertEqual(
                manifest["runs"][0]["id"], "20240101-120000-hetzner-nbg1"
            )  # Newer first
            self.assertEqual(manifest["runs"][1]["id"], "20240101-100000-hetzner-nbg1")
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
