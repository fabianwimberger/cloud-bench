#!/usr/bin/env python3
"""Tests for process_results.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import process_results as pr


class TestGetInstanceTypeFromKey(unittest.TestCase):
    def setUp(self):
        self.config = {
            "providers": {
                "hetzner": {
                    "instances": [
                        {"id": "cx11"},
                        {"id": "cpx11"},
                        {"id": "cax11"},
                        {"id": "cx21"},
                        {"id": "cpx21"},
                        {"id": "cax21"},
                    ]
                }
            }
        }
        self.provider = "hetzner"

    def test_cax11_extraction(self):
        self.assertEqual(
            pr.get_instance_type_from_key(
                "hetzner-cax11-local", self.config, self.provider
            ),
            "cax11",
        )
        self.assertEqual(
            pr.get_instance_type_from_key("CAX11", self.config, self.provider), "cax11"
        )

    def test_cpx11_extraction(self):
        self.assertEqual(
            pr.get_instance_type_from_key(
                "hetzner-cpx11-local", self.config, self.provider
            ),
            "cpx11",
        )
        self.assertEqual(
            pr.get_instance_type_from_key("CPX11", self.config, self.provider), "cpx11"
        )

    def test_cx11_extraction(self):
        self.assertEqual(
            pr.get_instance_type_from_key(
                "hetzner-cx11-local", self.config, self.provider
            ),
            "cx11",
        )
        self.assertEqual(
            pr.get_instance_type_from_key("CX11", self.config, self.provider), "cx11"
        )

    def test_unknown_key(self):
        self.assertEqual(
            pr.get_instance_type_from_key("unknown", self.config, self.provider),
            "unknown",
        )

    def test_fallback_without_config(self):
        self.assertEqual(pr.get_instance_type_from_key("some-key"), "some-key")


class TestGetInstanceTypeFromKeyAWS(unittest.TestCase):
    """Test instance type extraction for AWS IDs with dots and hyphens."""

    def setUp(self):
        self.config = {
            "providers": {
                "aws": {
                    "instances": [
                        {"id": "t3.medium"},
                        {"id": "t3.large"},
                        {"id": "t3a.medium"},
                        {"id": "t4g.medium"},
                        {"id": "t2.medium"},
                        {"id": "t2.xlarge"},
                    ]
                }
            }
        }
        self.provider = "aws"

    def test_t3_medium_extraction(self):
        self.assertEqual(
            pr.get_instance_type_from_key("t3.medium", self.config, self.provider),
            "t3.medium",
        )

    def test_t3_medium_from_key(self):
        self.assertEqual(
            pr.get_instance_type_from_key(
                "aws-t3.medium-12345", self.config, self.provider
            ),
            "t3.medium",
        )

    def test_t3a_medium_not_confused_with_t3(self):
        """t3a.medium should match t3a.medium, not t3.medium."""
        self.assertEqual(
            pr.get_instance_type_from_key("t3a.medium", self.config, self.provider),
            "t3a.medium",
        )

    def test_t2_medium_extraction(self):
        """Instance IDs with different family prefix (t2)."""
        self.assertEqual(
            pr.get_instance_type_from_key("t2.medium", self.config, self.provider),
            "t2.medium",
        )

    def test_t2_xlarge_from_key(self):
        self.assertEqual(
            pr.get_instance_type_from_key(
                "aws-t2.xlarge-12345", self.config, self.provider
            ),
            "t2.xlarge",
        )

    def test_t4g_medium(self):
        self.assertEqual(
            pr.get_instance_type_from_key("t4g.medium", self.config, self.provider),
            "t4g.medium",
        )


class TestLoadResults(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data = {
            "schema_version": "2.0",
            "system": {"provider": "hetzner", "instance_type": "cx11"},
            "provider_attributes": {
                "arch": "x86_64",
                "os": "Ubuntu 24.04",
                "kernel": "5.15.0",
                "vcpu": 1,
                "memory_mb": 2048,
            },
            "cpu": {"single_thread_events": 1000, "multi_thread_events": 1000},
            "memory": {
                "read_mib_per_sec": 5000,
                "write_mib_per_sec": 3000,
                "total_throughput_mib": 8000,
            },
            "disk": {"read_iops": 10000},
            "timestamp": "2024-01-01T00:00:00Z",
        }

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_valid_result(self):
        result_file = os.path.join(self.temp_dir, "hetzner-cx11-test.json")
        with open(result_file, "w") as f:
            json.dump(self.sample_data, f)

        results = pr.load_results(self.temp_dir)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["system"]["instance_type"], "cx11")

    def test_load_missing_fields(self):
        result_file = os.path.join(self.temp_dir, "incomplete.json")
        with open(result_file, "w") as f:
            json.dump({"system": {}}, f)

        results = pr.load_results(self.temp_dir)
        self.assertEqual(len(results), 0)


class TestNormalizeResults(unittest.TestCase):
    def setUp(self):
        self.sample_results = [
            {
                "_source_file": "hetzner-cx11-test.json",
                "_instance_key": "cx11",
                "system": {"provider": "hetzner", "instance_type": "cx11"},
                "provider_attributes": {
                    "arch": "x86_64",
                    "vcpu": 1,
                    "memory_mb": 2048,
                },
                "cpu": {"single_thread_events": 1000, "multi_thread_events": 1000},
                "memory": {"total_throughput_mib": 8000},
                "disk": {"read_iops": 10000},
                "timestamp": "2024-01-01T00:00:00Z",
            }
        ]
        self.sample_config = {
            "providers": {
                "hetzner": {
                    "instances": [
                        {
                            "id": "cx11",
                            "name": "CX11",
                            "arch": "X86",
                            "vcpu": 1,
                            "ram_gb": 2,
                            "disk_gb": 20,
                            "pricing": {"hourly": 0.0048, "monthly": 3.49},
                        }
                    ]
                }
            }
        }

    def test_normalize_structure(self):
        df = pr.normalize_results(
            self.sample_results, self.sample_config, "hetzner", "nbg1"
        )
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["instance_type"], "CX11")

        # Check metrics structure
        metrics = df.iloc[0]["metrics"]
        self.assertIn("cpu_single_raw", metrics)
        self.assertIn("disk_iops_raw", metrics)

        # Check provider_attributes
        attrs = df.iloc[0]["provider_attributes"]
        self.assertIn("arch", attrs)


class TestCalculateScores(unittest.TestCase):
    def setUp(self):
        import pandas as pd

        self.sample_df = pd.DataFrame(
            [
                {
                    "instance_type": "CX11",
                    "metrics": {
                        "cpu_single_raw": 1000,
                        "cpu_multi_raw": 1000,
                        "mem_throughput_raw": 8000,
                        "disk_iops_raw": 10000,
                    },
                    "price_hourly": 0.0048,
                    "price_monthly": 3.49,
                    "display_name": "CX11 (X86)",
                    "provider_attributes": {"arch": "X86"},
                },
                {
                    "instance_type": "CPX11",
                    "metrics": {
                        "cpu_single_raw": 2000,
                        "cpu_multi_raw": 4000,
                        "mem_throughput_raw": 16000,
                        "disk_iops_raw": 20000,
                    },
                    "price_hourly": 0.0066,
                    "price_monthly": 4.89,
                    "display_name": "CPX11 (X86)",
                    "provider_attributes": {"arch": "X86"},
                },
            ]
        )

    def test_score_normalization(self):
        df = pr.calculate_scores(self.sample_df)
        self.assertGreater(
            df[df["instance_type"] == "CPX11"]["overall_score"].iloc[0],
            df[df["instance_type"] == "CX11"]["overall_score"].iloc[0],
        )

    def test_score_range(self):
        df = pr.calculate_scores(self.sample_df)
        for col in [
            "single_core_score",
            "multi_core_score",
            "memory_score",
            "disk_score",
            "overall_score",
        ]:
            self.assertTrue(all(df[col] >= 0), f"{col} has negative values")
            self.assertTrue(all(df[col] <= 100), f"{col} has values > 100")

    def test_zero_price_handling(self):
        """Test that zero prices don't cause division by zero errors."""
        df_with_zero_price = self.sample_df.copy()
        df_with_zero_price.loc[0, "price_hourly"] = 0
        df_with_zero_price.loc[0, "price_monthly"] = 0

        df = pr.calculate_scores(df_with_zero_price)

        # Should not have inf or nan values
        self.assertFalse(df["value_hourly"].isin([float("inf"), -float("inf")]).any())
        self.assertFalse(df["value_monthly"].isin([float("inf"), -float("inf")]).any())
        self.assertFalse(
            df["cpu_value_monthly"].isin([float("inf"), -float("inf")]).any()
        )

        # Zero price instances should have 0 value scores
        zero_price_row = df.iloc[0]
        self.assertEqual(zero_price_row["value_hourly"], 0.0)
        self.assertEqual(zero_price_row["value_monthly"], 0.0)
        self.assertEqual(zero_price_row["cpu_value_monthly"], 0.0)


class TestGenerateSummaryData(unittest.TestCase):
    def setUp(self):
        import pandas as pd

        self.sample_df = pd.DataFrame(
            [
                {
                    "instance_type": "CX11",
                    "display_name": "CX11 (X86)",
                    "vcpu": 1,
                    "ram_gb": 2,
                    "disk_gb": 20,
                    "price_hourly": 0.0048,
                    "price_monthly": 3.49,
                    "single_core_score": 50,
                    "multi_core_score": 50,
                    "memory_score": 50,
                    "disk_score": 50,
                    "overall_score": 50,
                    "value_monthly": 150,
                    "cpu_value_monthly": 150,
                    "metrics": {},
                    "provider_attributes": {"arch": "X86"},
                }
            ]
        )

    def test_schema_version(self):
        data = pr.generate_summary_data(self.sample_df, "hetzner", "nbg1")
        self.assertEqual(data["schema_version"], "2.0")

    def test_summary_structure(self):
        data = pr.generate_summary_data(self.sample_df, "hetzner", "nbg1")
        self.assertIn("metadata", data)
        self.assertIn("summary", data)

        summary = data["summary"]
        self.assertIn("labels", summary)
        self.assertIn("instances", summary)
        self.assertIn("charts", summary)

    def test_instance_format(self):
        data = pr.generate_summary_data(self.sample_df, "hetzner", "nbg1")
        inst = data["summary"]["instances"][0]
        self.assertIn("id", inst)
        self.assertIn("scores", inst)
        self.assertIn("pricing", inst)

    def test_exchange_rates_in_metadata(self):
        """Test that exchange rates are included when config has them."""
        config = {
            "exchange_rates": {
                "usd_to_eur": 0.92,
                "eur_to_usd": 1.087,
                "last_updated": "2026-02-23",
                "source": "Frankfurter API (ECB data)",
            }
        }
        data = pr.generate_summary_data(
            self.sample_df, "hetzner", "nbg1", "EUR", config
        )
        self.assertIn("exchange_rates", data["metadata"])
        self.assertEqual(data["metadata"]["exchange_rates"]["usd_to_eur"], 0.92)

    def test_usd_currency_in_metadata(self):
        """Test that USD currency is properly set for AWS provider."""
        data = pr.generate_summary_data(self.sample_df, "aws", "eu-central-1", "USD")
        self.assertEqual(data["metadata"]["currency"], "USD")


class TestMarkdownSummaryCurrency(unittest.TestCase):
    def setUp(self):
        import pandas as pd

        self.sample_df = pd.DataFrame(
            [
                {
                    "instance_type": "T3.MEDIUM",
                    "display_name": "T3.MEDIUM (X86)",
                    "vcpu": 2,
                    "ram_gb": 4,
                    "disk_gb": 20,
                    "price_hourly": 0.0416,
                    "price_monthly": 29.95,
                    "single_core_score": 60,
                    "multi_core_score": 55,
                    "memory_score": 65,
                    "disk_score": 70,
                    "overall_score": 62,
                    "value_monthly": 2.07,
                    "cpu_value_monthly": 1.92,
                    "metrics": {},
                    "provider_attributes": {"arch": "X86"},
                }
            ]
        )

    def test_usd_currency_in_markdown(self):
        """Test that USD is used in markdown when specified."""
        md = pr.generate_markdown_summary(self.sample_df, "USD")
        self.assertIn("USD/Month", md)
        self.assertIn("USD29.95", md)
        self.assertIn("CPU points/USD", md)

    def test_eur_currency_in_markdown(self):
        """Test that EUR is used by default."""
        md = pr.generate_markdown_summary(self.sample_df)
        self.assertIn("EUR/Month", md)


class TestExtensibility(unittest.TestCase):
    """Test that provider_attributes allows adding new providers without code changes."""

    def setUp(self):
        self.aws_result = [
            {
                "_source_file": "aws-t3.medium-test.json",
                "_instance_key": "t3.medium",
                "system": {"provider": "aws", "instance_type": "t3.medium"},
                "provider_attributes": {
                    "arch": "x86_64",
                    "vcpu": 2,
                    "memory_mb": 4096,
                    "ebs_optimized": True,
                    "burstable": True,
                    "baseline_cpu": 20,
                },
                "cpu": {"single_thread_events": 1500, "multi_thread_events": 3000},
                "memory": {"total_throughput_mib": 12000},
                "disk": {"read_iops": 20000},
                "timestamp": "2024-01-01T00:00:00Z",
            }
        ]
        self.config = {
            "providers": {
                "aws": {
                    "instances": [
                        {
                            "id": "t3.medium",
                            "name": "t3.medium",
                            "arch": "X86",
                            "vcpu": 2,
                            "ram_gb": 4,
                            "disk_gb": 20,
                            "pricing": {"hourly": 0.0416, "monthly": 29.95},
                        }
                    ]
                }
            }
        }

    def test_aws_attributes_preserved(self):
        df = pr.normalize_results(self.aws_result, self.config, "aws", "eu-central-1")
        attrs = df.iloc[0]["provider_attributes"]

        # Standard fields
        self.assertEqual(attrs["arch"], "x86_64")

        # AWS-specific fields
        self.assertEqual(attrs["ebs_optimized"], True)
        self.assertEqual(attrs["burstable"], True)
        self.assertEqual(attrs["baseline_cpu"], 20)

    def test_aws_instance_type_uppercased(self):
        df = pr.normalize_results(self.aws_result, self.config, "aws", "eu-central-1")
        self.assertEqual(df.iloc[0]["instance_type"], "T3.MEDIUM")


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_manifest_created(self):
        metadata = {
            "run_id": "test-run",
            "generated_at": "2024-01-01T00:00:00Z",
            "provider": "hetzner",
            "region": "nbg1",
            "run_count": 3,
        }
        pr.update_manifest(self.temp_dir, "summary-1.json", "detail-1.json", metadata)

        manifest_path = os.path.join(self.temp_dir, "manifest.json")
        self.assertTrue(os.path.exists(manifest_path))

        with open(manifest_path) as f:
            manifest = json.load(f)

        self.assertEqual(manifest["schema_version"], "2.0")
        self.assertEqual(len(manifest["runs"]), 1)


if __name__ == "__main__":
    unittest.main()
