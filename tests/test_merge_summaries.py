#!/usr/bin/env python3
"""Tests for merge_summaries.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import merge_summaries as ms


class TestParseArgs(unittest.TestCase):
    def test_parse_args_required(self):
        """Test that required arguments are parsed."""
        original_argv = sys.argv
        try:
            sys.argv = [
                "merge_summaries.py",
                "--manifest",
                "/data/manifest.json",
                "--data-dir",
                "/data",
                "--output",
                "/output/merged.json",
            ]
            args = ms.parse_args()
            self.assertEqual(args.manifest, "/data/manifest.json")
            self.assertEqual(args.data_dir, "/data")
            self.assertEqual(args.output, "/output/merged.json")
        finally:
            sys.argv = original_argv


class TestLoadJson(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_valid_json(self):
        """Test loading a valid JSON file."""
        filepath = os.path.join(self.temp_dir, "test.json")
        data = {"key": "value"}
        with open(filepath, "w") as f:
            json.dump(data, f)

        result = ms.load_json(filepath)
        self.assertEqual(result, data)

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        result = ms.load_json("/nonexistent/path.json")
        self.assertIsNone(result)

    def test_load_invalid_json(self):
        """Test loading an invalid JSON file."""
        filepath = os.path.join(self.temp_dir, "invalid.json")
        with open(filepath, "w") as f:
            f.write("not valid json")

        result = ms.load_json(filepath)
        self.assertIsNone(result)


class TestRescaleScores(unittest.TestCase):
    def test_rescale_single_instance(self):
        """Test rescaling with a single instance."""
        instances = [
            {
                "id": "cx11",
                "metrics": {
                    "cpu_single_events": 1000,
                    "cpu_multi_events": 2000,
                    "memory_mib_per_sec": 8000,
                    "disk_iops": 10000,
                },
                "scores": {},
                "pricing": {"monthly": 10},
                "value": 0,
            }
        ]

        result = ms.rescale_scores(instances)

        # Single instance should get 100 in all scores
        self.assertEqual(result[0]["scores"]["single_core"], 100.0)
        self.assertEqual(result[0]["scores"]["multi_core"], 100.0)
        self.assertEqual(result[0]["scores"]["memory"], 100.0)
        self.assertEqual(result[0]["scores"]["disk"], 100.0)
        self.assertEqual(result[0]["scores"]["overall"], 100.0)

    def test_rescale_multiple_instances(self):
        """Test rescaling with multiple instances."""
        instances = [
            {
                "id": "cx11",
                "metrics": {
                    "cpu_single_events": 1000,
                    "cpu_multi_events": 2000,
                    "memory_mib_per_sec": 8000,
                    "disk_iops": 10000,
                },
                "scores": {},
                "pricing": {"monthly": 10},
                "value": 0,
            },
            {
                "id": "cpx11",
                "metrics": {
                    "cpu_single_events": 2000,
                    "cpu_multi_events": 4000,
                    "memory_mib_per_sec": 16000,
                    "disk_iops": 20000,
                },
                "scores": {},
                "pricing": {"monthly": 15},
                "value": 0,
            },
        ]

        result = ms.rescale_scores(instances)

        # cpx11 should be 100% (the max)
        cpx11 = next(i for i in result if i["id"] == "cpx11")
        self.assertEqual(cpx11["scores"]["single_core"], 100.0)
        self.assertEqual(cpx11["scores"]["multi_core"], 100.0)
        self.assertEqual(cpx11["scores"]["memory"], 100.0)
        self.assertEqual(cpx11["scores"]["disk"], 100.0)

        # cx11 should be 50%
        cx11 = next(i for i in result if i["id"] == "cx11")
        self.assertEqual(cx11["scores"]["single_core"], 50.0)
        self.assertEqual(cx11["scores"]["multi_core"], 50.0)
        self.assertEqual(cx11["scores"]["memory"], 50.0)
        self.assertEqual(cx11["scores"]["disk"], 50.0)

    def test_rescale_empty_list(self):
        """Test rescaling an empty list."""
        result = ms.rescale_scores([])
        self.assertEqual(result, [])

    def test_rescale_with_zero_metrics(self):
        """Test rescaling with zero metric values."""
        instances = [
            {
                "id": "cx11",
                "metrics": {
                    "cpu_single_events": 0,
                    "cpu_multi_events": 0,
                    "memory_mib_per_sec": 0,
                    "disk_iops": 0,
                },
                "scores": {},
                "pricing": {"monthly": 10},
                "value": 0,
            }
        ]

        result = ms.rescale_scores(instances)

        # Zero metrics should result in zero scores
        self.assertEqual(result[0]["scores"]["single_core"], 0.0)

    def test_value_score_recalculation(self):
        """Test that value scores are recalculated after rescaling."""
        instances = [
            {
                "id": "cx11",
                "metrics": {
                    "cpu_single_events": 1000,
                    "cpu_multi_events": 2000,
                    "memory_mib_per_sec": 8000,
                    "disk_iops": 10000,
                },
                "scores": {"overall": 50},
                "pricing": {"monthly": 10},
                "value": 0,
            }
        ]

        result = ms.rescale_scores(instances)

        # Value = overall_score / monthly_price
        self.assertEqual(result[0]["value"], 10.0)  # 100 / 10 = 10


class TestMain(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.runs_dir = os.path.join(self.temp_dir, "runs")
        os.makedirs(self.runs_dir)

        self.manifest_path = os.path.join(self.temp_dir, "manifest.json")
        self.output_path = os.path.join(self.temp_dir, "merged.json")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_manifest(self, runs):
        """Helper to create manifest file."""
        manifest = {"runs": runs}
        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f)

    def create_summary(self, run_id, instances):
        """Helper to create summary file."""
        run_dir = os.path.join(self.runs_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)

        summary = {
            "schema_version": "2.0",
            "metadata": {
                "generated_at": "2024-01-01T00:00:00Z",
                "currency": "EUR",
                "exchange_rates": {"eur_to_usd": 1.087},
            },
            "summary": {"instances": instances},
        }

        with open(os.path.join(run_dir, "summary.json"), "w") as f:
            json.dump(summary, f)

    def test_main_no_runs(self):
        """Test main with no runs in manifest."""
        self.create_manifest([])

        original_argv = sys.argv
        try:
            sys.argv = [
                "merge_summaries.py",
                "--manifest",
                self.manifest_path,
                "--data-dir",
                self.temp_dir,
                "--output",
                self.output_path,
            ]

            with self.assertRaises(SystemExit) as cm:
                ms.main()

            self.assertEqual(cm.exception.code, 0)  # Exit 0 for no runs
        finally:
            sys.argv = original_argv

    def test_main_single_run(self):
        """Test main with a single run."""
        self.create_manifest(
            [
                {
                    "id": "run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"summary": "runs/run-1/summary.json"},
                }
            ]
        )

        self.create_summary(
            "run-1",
            [
                {
                    "id": "cx11",
                    "scores": {"overall": 50},
                    "metrics": {"cpu_single_events": 1000},
                    "pricing": {"hourly": 0.0048, "monthly": 3.49},
                }
            ],
        )

        original_argv = sys.argv
        try:
            sys.argv = [
                "merge_summaries.py",
                "--manifest",
                self.manifest_path,
                "--data-dir",
                self.temp_dir,
                "--output",
                self.output_path,
            ]
            ms.main()

            with open(self.output_path) as f:
                result = json.load(f)

            self.assertEqual(result["schema_version"], "2.0")
            self.assertEqual(len(result["summary"]["instances"]), 1)
            self.assertEqual(result["summary"]["instances"][0]["id"], "cx11")
            self.assertEqual(result["summary"]["instances"][0]["provider"], "hetzner")
        finally:
            sys.argv = original_argv

    def test_main_multiple_providers(self):
        """Test main with runs from multiple providers."""
        self.create_manifest(
            [
                {
                    "id": "hetzner-run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"summary": "runs/hetzner-run-1/summary.json"},
                },
                {
                    "id": "aws-run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "aws",
                    "region": "eu-central-1",
                    "files": {"summary": "runs/aws-run-1/summary.json"},
                },
            ]
        )

        self.create_summary(
            "hetzner-run-1",
            [
                {
                    "id": "cx11",
                    "scores": {"overall": 50},
                    "metrics": {"cpu_single_events": 1000},
                    "pricing": {"hourly": 0.0048, "monthly": 3.49},
                }
            ],
        )

        self.create_summary(
            "aws-run-1",
            [
                {
                    "id": "t3.micro",
                    "scores": {"overall": 60},
                    "metrics": {"cpu_single_events": 1200},
                    "pricing": {"hourly": 0.0104, "monthly": 7.5},
                }
            ],
        )

        original_argv = sys.argv
        try:
            sys.argv = [
                "merge_summaries.py",
                "--manifest",
                self.manifest_path,
                "--data-dir",
                self.temp_dir,
                "--output",
                self.output_path,
            ]
            ms.main()

            with open(self.output_path) as f:
                result = json.load(f)

            self.assertEqual(len(result["summary"]["instances"]), 2)
            providers = [i["provider"] for i in result["summary"]["instances"]]
            self.assertIn("hetzner", providers)
            self.assertIn("aws", providers)
        finally:
            sys.argv = original_argv

    def test_main_averaging_metrics(self):
        """Test that metrics are averaged across multiple runs."""
        self.create_manifest(
            [
                {
                    "id": "run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"summary": "runs/run-1/summary.json"},
                },
                {
                    "id": "run-2",
                    "timestamp": "2024-01-02T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"summary": "runs/run-2/summary.json"},
                },
            ]
        )

        self.create_summary(
            "run-1",
            [
                {
                    "id": "cx11",
                    "scores": {"overall": 50},
                    "metrics": {"cpu_single_events": 1000},
                    "pricing": {"hourly": 0.0048, "monthly": 3.49},
                }
            ],
        )

        self.create_summary(
            "run-2",
            [
                {
                    "id": "cx11",
                    "scores": {"overall": 60},
                    "metrics": {"cpu_single_events": 1200},
                    "pricing": {"hourly": 0.0048, "monthly": 3.49},
                }
            ],
        )

        original_argv = sys.argv
        try:
            sys.argv = [
                "merge_summaries.py",
                "--manifest",
                self.manifest_path,
                "--data-dir",
                self.temp_dir,
                "--output",
                self.output_path,
            ]
            ms.main()

            with open(self.output_path) as f:
                result = json.load(f)

            # Should have one instance with averaged metrics
            self.assertEqual(len(result["summary"]["instances"]), 1)
            # Average of 1000 and 1200 = 1100
            self.assertEqual(
                result["summary"]["instances"][0]["metrics"]["cpu_single_events"],
                1100.0,
            )
        finally:
            sys.argv = original_argv

    def test_main_eur_to_usd_conversion(self):
        """Test that EUR prices are converted to USD."""
        self.create_manifest(
            [
                {
                    "id": "run-1",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "provider": "hetzner",
                    "region": "nbg1",
                    "files": {"summary": "runs/run-1/summary.json"},
                }
            ]
        )

        # Create summary with EUR currency
        run_dir = os.path.join(self.runs_dir, "run-1")
        os.makedirs(run_dir, exist_ok=True)
        summary = {
            "schema_version": "2.0",
            "metadata": {
                "generated_at": "2024-01-01T00:00:00Z",
                "currency": "EUR",
                "exchange_rates": {"eur_to_usd": 1.087},
            },
            "summary": {
                "instances": [
                    {
                        "id": "cx11",
                        "scores": {"overall": 50},
                        "metrics": {"cpu_single_events": 1000},
                        "pricing": {"hourly": 0.0048, "monthly": 3.49},  # EUR
                    }
                ]
            },
        }
        with open(os.path.join(run_dir, "summary.json"), "w") as f:
            json.dump(summary, f)

        original_argv = sys.argv
        try:
            sys.argv = [
                "merge_summaries.py",
                "--manifest",
                self.manifest_path,
                "--data-dir",
                self.temp_dir,
                "--output",
                self.output_path,
            ]
            ms.main()

            with open(self.output_path) as f:
                result = json.load(f)

            # Prices should be converted to USD
            pricing = result["summary"]["instances"][0]["pricing"]
            self.assertAlmostEqual(pricing["monthly"], 3.79, places=1)  # 3.49 * 1.087
            self.assertEqual(result["metadata"]["currency"], "USD")
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
