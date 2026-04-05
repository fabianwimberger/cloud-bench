#!/usr/bin/env python3
"""Tests for estimate_cost.py."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import estimate_cost as ec


class TestEstimateCost(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "instances.yaml")
        self.config = {
            "providers": {
                "hetzner": {
                    "currency": "EUR",
                    "instances": [
                        {
                            "id": "cx11",
                            "name": "CX11",
                            "pricing": {"hourly": 0.0048, "monthly": 3.49},
                        },
                        {
                            "id": "cpx11",
                            "name": "CPX11",
                            "pricing": {"hourly": 0.0066, "monthly": 4.89},
                        },
                        {
                            "id": "cax11",
                            "name": "CAX11",
                            "pricing": {"hourly": 0.0048, "monthly": 3.49},
                        },
                    ],
                },
                "aws": {
                    "currency": "USD",
                    "instances": [
                        {
                            "id": "t3.micro",
                            "name": "T3 Micro",
                            "pricing": {"hourly": 0.0104, "monthly": 7.5},
                        },
                        {
                            "id": "t3.small",
                            "name": "T3 Small",
                            "pricing": {"hourly": 0.0208, "monthly": 15.0},
                        },
                    ],
                },
            },
            "exchange_rates": {
                "eur_to_usd": 1.087,
                "usd_to_eur": 0.92,
            },
        }
        import yaml

        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_estimate_all_instances(self):
        """Test estimating cost for all instances."""
        result = ec.estimate_cost("hetzner", "all", self.config_path)

        self.assertEqual(result["count"], 3)
        self.assertIn("cx11", result["instances"])
        self.assertIn("cpx11", result["instances"])
        self.assertIn("cax11", result["instances"])

        # Cost calculation: 0.33 hours * sum of hourly rates
        # (0.0048 + 0.0066 + 0.0048) * 0.33 = 0.0056436 EUR
        self.assertGreater(result["cost_eur"], 0)
        self.assertEqual(result["cost_usd"], round(result["cost_eur"] * 1.087, 4))

    def test_estimate_specific_instances(self):
        """Test estimating cost for specific instances."""
        result = ec.estimate_cost("hetzner", "cx11,cpx11", self.config_path)

        self.assertEqual(result["count"], 2)
        self.assertIn("cx11", result["instances"])
        self.assertIn("cpx11", result["instances"])
        self.assertNotIn("cax11", result["instances"])

    def test_estimate_single_instance(self):
        """Test estimating cost for a single instance."""
        result = ec.estimate_cost("hetzner", "cx11", self.config_path)

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["instances"], ["cx11"])

    def test_estimate_with_spaces(self):
        """Test that spaces in instance list are handled."""
        result = ec.estimate_cost("hetzner", "cx11, cpx11", self.config_path)

        self.assertEqual(result["count"], 2)

    def test_estimate_case_insensitive(self):
        """Test that instance IDs are case insensitive."""
        result = ec.estimate_cost("hetzner", "CX11,CPX11", self.config_path)

        self.assertEqual(result["count"], 2)

    def test_estimate_aws_usd(self):
        """Test that AWS costs are in USD."""
        result = ec.estimate_cost("aws", "all", self.config_path)

        self.assertEqual(result["count"], 2)
        # AWS is USD, so USD cost should be the native cost
        expected_hourly = 0.0104 + 0.0208
        expected_cost_native = expected_hourly * 0.33
        self.assertAlmostEqual(result["cost_usd"], round(expected_cost_native, 4), places=3)
        # EUR cost should be converted
        self.assertAlmostEqual(result["cost_eur"], round(expected_cost_native * 0.92, 4), places=3)

    def test_estimate_unknown_provider(self):
        """Test estimating cost for unknown provider returns empty."""
        result = ec.estimate_cost("unknown", "all", self.config_path)

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["instances"], [])
        self.assertEqual(result["cost_eur"], 0)
        self.assertEqual(result["cost_usd"], 0)

    def test_estimate_no_exchange_rates(self):
        """Test estimation when exchange rates are missing."""
        config_no_rates = {
            "providers": {
                "hetzner": {
                    "currency": "EUR",
                    "instances": [
                        {
                            "id": "cx11",
                            "pricing": {"hourly": 0.0048, "monthly": 3.49},
                        }
                    ],
                }
            }
        }
        config_path = os.path.join(self.temp_dir, "no_rates.yaml")
        import yaml

        with open(config_path, "w") as f:
            yaml.dump(config_no_rates, f)

        result = ec.estimate_cost("hetzner", "all", config_path)

        # Should use default exchange rate of 1.0
        self.assertGreater(result["cost_eur"], 0)
        self.assertGreater(result["cost_usd"], 0)


class TestMain(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "instances.yaml")
        self.config = {
            "providers": {
                "hetzner": {
                    "currency": "EUR",
                    "instances": [
                        {
                            "id": "cx11",
                            "pricing": {"hourly": 0.0048, "monthly": 3.49},
                        }
                    ],
                }
            }
        }
        import yaml

        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_main_output(self):
        """Test main function prints valid JSON."""
        import io
        from contextlib import redirect_stdout

        # Mock sys.argv
        original_argv = sys.argv
        try:
            sys.argv = [
                "estimate_cost.py",
                "--provider",
                "hetzner",
                "--instances",
                "all",
                "--config",
                self.config_path,
            ]

            f = io.StringIO()
            with redirect_stdout(f):
                ec.main()

            output = f.getvalue()
            result = json.loads(output)

            self.assertEqual(result["count"], 1)
            self.assertIn("cx11", result["instances"])
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main()
