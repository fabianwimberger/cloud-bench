#!/usr/bin/env python3
"""Tests for build_history.py."""

import json
import os
import sys
import tempfile
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_history as bh


class TestParseArgs(unittest.TestCase):
    def test_parse_args_required(self):
        """Test that required arguments are parsed."""
        original_argv = sys.argv
        try:
            sys.argv = [
                "build_history.py",
                "--data-dir",
                "/data",
                "--output",
                "/output/history.json",
            ]
            args = bh.parse_args()
            self.assertEqual(args.data_dir, "/data")
            self.assertEqual(args.output, "/output/history.json")
        finally:
            sys.argv = original_argv


class TestLoadDetail(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_valid_detail(self):
        """Test loading a valid detail file."""
        detail_path = os.path.join(self.temp_dir, "detail.json")
        data = {"instances": [{"id": "cx11", "scores": {"overall": 50}}]}
        with open(detail_path, "w") as f:
            json.dump(data, f)

        result = bh.load_detail(detail_path)
        self.assertEqual(result["instances"][0]["id"], "cx11")

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        result = bh.load_detail("/nonexistent/path.json")
        self.assertIsNone(result)

    def test_load_invalid_json(self):
        """Test loading an invalid JSON file."""
        detail_path = os.path.join(self.temp_dir, "invalid.json")
        with open(detail_path, "w") as f:
            f.write("not valid json")

        result = bh.load_detail(detail_path)
        self.assertIsNone(result)


class TestExtractInstanceData(unittest.TestCase):
    def test_extract_single_instance(self):
        """Test extracting data for a single instance."""
        detail = {
            "instances": [
                {
                    "id": "cx11",
                    "scores": {"overall": 50, "cpu": 60},
                    "metrics": {
                        "cpu_single_raw": 1000,
                        "cpu_multi_raw": 2000,
                        "mem_throughput_raw": 8000,
                        "disk_iops_raw": 10000,
                    },
                    "pricing": {"hourly": 0.0048, "monthly": 3.49},
                }
            ]
        }
        run_meta = {"timestamp": "2024-01-01T00:00:00Z", "region": "nbg1"}

        result = bh.extract_instance_data(detail, run_meta, 1.0)

        self.assertIn("cx11", result)
        self.assertEqual(result["cx11"]["timestamp"], "2024-01-01T00:00:00Z")
        self.assertEqual(result["cx11"]["region"], "nbg1")
        self.assertEqual(result["cx11"]["scores"]["overall"], 50)
        self.assertEqual(result["cx11"]["metrics"]["cpu_single_raw"], 1000)

    def test_extract_multiple_instances(self):
        """Test extracting data for multiple instances."""
        detail = {
            "instances": [
                {"id": "cx11", "scores": {"overall": 50}},
                {"id": "cpx11", "scores": {"overall": 75}},
            ]
        }
        run_meta = {"timestamp": "2024-01-01T00:00:00Z", "region": "nbg1"}

        result = bh.extract_instance_data(detail, run_meta, 1.0)

        self.assertEqual(len(result), 2)
        self.assertIn("cx11", result)
        self.assertIn("cpx11", result)

    def test_extract_instance_without_id(self):
        """Test that instances without ID are skipped."""
        detail = {
            "instances": [
                {"id": "cx11", "scores": {"overall": 50}},
                {"scores": {"overall": 75}},  # No id
            ]
        }
        run_meta = {"timestamp": "2024-01-01T00:00:00Z", "region": "nbg1"}

        result = bh.extract_instance_data(detail, run_meta, 1.0)

        self.assertEqual(len(result), 1)
        self.assertIn("cx11", result)

    def test_extract_legacy_metrics(self):
        """Test that legacy metric names are handled."""
        detail = {
            "instances": [
                {
                    "id": "cx11",
                    "scores": {"overall": 50},
                    "metrics": {
                        "cpu_single_events": 1000,  # Legacy name
                        "cpu_multi_events": 2000,  # Legacy name
                        "memory_mib_per_sec": 8000,  # Legacy name
                        "disk_iops": 10000,  # Legacy name
                    },
                }
            ]
        }
        run_meta = {"timestamp": "2024-01-01T00:00:00Z"}

        result = bh.extract_instance_data(detail, run_meta, 1.0)

        # Legacy names should be mapped to new names
        self.assertEqual(result["cx11"]["metrics"]["cpu_single_raw"], 1000)
        self.assertEqual(result["cx11"]["metrics"]["cpu_multi_raw"], 2000)
        self.assertEqual(result["cx11"]["metrics"]["mem_throughput_raw"], 8000)
        self.assertEqual(result["cx11"]["metrics"]["disk_iops_raw"], 10000)

    def test_extract_empty_instances(self):
        """Test extracting from empty instances list."""
        detail = {"instances": []}
        run_meta = {"timestamp": "2024-01-01T00:00:00Z"}

        result = bh.extract_instance_data(detail, run_meta, 1.0)

        self.assertEqual(len(result), 0)

    def test_extract_converts_eur_to_usd(self):
        """Test that EUR pricing is converted to USD."""
        detail = {
            "metadata": {"currency": "EUR"},
            "instances": [
                {
                    "id": "cax11",
                    "scores": {"overall": 50},
                    "pricing": {"hourly": 0.0072, "monthly": 4.49},
                }
            ],
        }
        run_meta = {"timestamp": "2024-01-01T00:00:00Z", "region": "fsn1"}

        result = bh.extract_instance_data(detail, run_meta, 1.15)

        self.assertAlmostEqual(result["cax11"]["pricing"]["monthly"], 5.16, places=2)
        self.assertAlmostEqual(result["cax11"]["pricing"]["hourly"], 0.0083, places=4)

    def test_extract_usd_pricing_unchanged(self):
        """Test that USD pricing is not converted."""
        detail = {
            "metadata": {"currency": "USD"},
            "instances": [
                {
                    "id": "t3.micro",
                    "scores": {"overall": 50},
                    "pricing": {"hourly": 0.0104, "monthly": 7.59},
                }
            ],
        }
        run_meta = {"timestamp": "2024-01-01T00:00:00Z"}

        result = bh.extract_instance_data(detail, run_meta, 1.15)

        self.assertEqual(result["t3.micro"]["pricing"]["monthly"], 7.59)
        self.assertEqual(result["t3.micro"]["pricing"]["hourly"], 0.0104)


class TestBuildHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.runs_dir = os.path.join(self.temp_dir, "runs")
        os.makedirs(self.runs_dir)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_history_no_manifest(self):
        """Test building history without a manifest file."""
        result = bh.build_history(self.temp_dir)

        self.assertEqual(result["schema_version"], "3.0")
        self.assertIn("generated_at", result)
        self.assertEqual(result["instances"], {})

    def test_build_history_single_run(self):
        """Test building history with a single run."""
        # Create manifest
        manifest = {
            "runs": [
                {
                    "id": "run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"detail": "data/runs/run-1/detail.json"},
                }
            ]
        }
        with open(os.path.join(self.temp_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)

        # Create run directory and detail file
        run_dir = os.path.join(self.runs_dir, "run-1")
        os.makedirs(run_dir)
        detail = {
            "instances": [
                {
                    "id": "cx11",
                    "scores": {"overall": 50},
                    "metrics": {"cpu_single_raw": 1000},
                    "specs": {"vcpu": 1, "ram_gb": 2},
                }
            ]
        }
        with open(os.path.join(run_dir, "detail.json"), "w") as f:
            json.dump(detail, f)

        result = bh.build_history(self.temp_dir)

        self.assertEqual(len(result["instances"]), 1)
        self.assertIn("cx11", result["instances"])
        self.assertEqual(result["instances"]["cx11"]["provider"], "hetzner")
        self.assertEqual(len(result["instances"]["cx11"]["runs"]), 1)

    def test_build_history_multiple_runs_same_instance(self):
        """Test building history with multiple runs for the same instance."""
        # Create manifest with two runs
        manifest = {
            "runs": [
                {
                    "id": "run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"detail": "data/runs/run-1/detail.json"},
                },
                {
                    "id": "run-2",
                    "timestamp": "2024-01-02T00:00:00Z",
                    "provider": "hetzner",
                    "region": "fsn1",
                    "files": {"detail": "data/runs/run-2/detail.json"},
                },
            ]
        }
        with open(os.path.join(self.temp_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)

        # Create run 1
        run1_dir = os.path.join(self.runs_dir, "run-1")
        os.makedirs(run1_dir)
        detail1 = {
            "instances": [
                {"id": "cx11", "scores": {"overall": 50}, "specs": {"vcpu": 1}}
            ]
        }
        with open(os.path.join(run1_dir, "detail.json"), "w") as f:
            json.dump(detail1, f)

        # Create run 2
        run2_dir = os.path.join(self.runs_dir, "run-2")
        os.makedirs(run2_dir)
        detail2 = {
            "instances": [
                {"id": "cx11", "scores": {"overall": 55}, "specs": {"vcpu": 1}}
            ]
        }
        with open(os.path.join(run2_dir, "detail.json"), "w") as f:
            json.dump(detail2, f)

        result = bh.build_history(self.temp_dir)

        # Should have one instance with two runs
        self.assertEqual(len(result["instances"]), 1)
        self.assertEqual(len(result["instances"]["cx11"]["runs"]), 2)

        # Runs should be sorted by timestamp
        runs = result["instances"]["cx11"]["runs"]
        self.assertEqual(runs[0]["timestamp"], "2024-01-01T00:00:00Z")
        self.assertEqual(runs[1]["timestamp"], "2024-01-02T00:00:00Z")

    def test_build_history_missing_detail_file(self):
        """Test that missing detail files are handled gracefully."""
        manifest = {
            "runs": [
                {
                    "id": "run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"detail": "data/runs/run-1/detail.json"},
                }
            ]
        }
        with open(os.path.join(self.temp_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)

        # Don't create the detail file

        result = bh.build_history(self.temp_dir)

        # Should still return valid history with no instances
        self.assertEqual(result["instances"], {})

    def test_build_history_without_data_prefix(self):
        """Test that paths without 'data/' prefix work."""
        manifest = {
            "runs": [
                {
                    "id": "run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"detail": "runs/run-1/detail.json"},  # No data/ prefix
                }
            ]
        }
        with open(os.path.join(self.temp_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)

        run_dir = os.path.join(self.runs_dir, "run-1")
        os.makedirs(run_dir)
        detail = {"instances": [{"id": "cx11", "scores": {"overall": 50}}]}
        with open(os.path.join(run_dir, "detail.json"), "w") as f:
            json.dump(detail, f)

        result = bh.build_history(self.temp_dir)

        self.assertIn("cx11", result["instances"])


class TestMain(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "history.json")

        # Create a valid data directory
        self.runs_dir = os.path.join(self.temp_dir, "runs", "run-1")
        os.makedirs(self.runs_dir)

        manifest = {
            "runs": [
                {
                    "id": "run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"detail": "runs/run-1/detail.json"},
                }
            ]
        }
        with open(os.path.join(self.temp_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)

        detail = {"instances": [{"id": "cx11", "scores": {"overall": 50}}]}
        with open(os.path.join(self.runs_dir, "detail.json"), "w") as f:
            json.dump(detail, f)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_main_success(self):
        """Test successful main execution."""
        original_argv = sys.argv
        try:
            sys.argv = [
                "build_history.py",
                "--data-dir",
                self.temp_dir,
                "--output",
                self.output_path,
            ]
            bh.main()

            # Verify output file was created
            self.assertTrue(os.path.exists(self.output_path))

            with open(self.output_path) as f:
                result = json.load(f)

            self.assertEqual(result["schema_version"], "3.0")
            self.assertIn("cx11", result["instances"])
        finally:
            sys.argv = original_argv

    def test_main_invalid_directory(self):
        """Test main with invalid directory."""
        original_argv = sys.argv
        try:
            sys.argv = [
                "build_history.py",
                "--data-dir",
                "/nonexistent/path",
                "--output",
                self.output_path,
            ]

            with self.assertRaises(SystemExit) as cm:
                bh.main()

            self.assertEqual(cm.exception.code, 1)
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
