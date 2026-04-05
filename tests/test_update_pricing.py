#!/usr/bin/env python3
"""Tests for update_pricing.py."""

import os
import sys

import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import update_pricing as up


class TestParsePricing(unittest.TestCase):
    def test_parse_pricing_valid(self):
        """Test parsing valid pricing data."""
        server_type = {
            "prices": [
                {
                    "price_hourly": {"net": "0.0048"},
                    "price_monthly": {"net": "3.49"},
                }
            ]
        }

        result = up.parse_pricing(server_type)

        self.assertEqual(result["hourly"], 0.0048)
        self.assertEqual(result["monthly"], 3.49)

    def test_parse_pricing_no_prices(self):
        """Test parsing with no prices."""
        server_type = {"prices": []}

        result = up.parse_pricing(server_type)

        self.assertIsNone(result)

    def test_parse_pricing_missing_net(self):
        """Test parsing with missing net prices."""
        server_type = {
            "prices": [
                {
                    "price_hourly": {},
                    "price_monthly": {},
                }
            ]
        }

        result = up.parse_pricing(server_type)

        self.assertIsNone(result)

    def test_parse_pricing_no_prices_key(self):
        """Test parsing with no prices key."""
        server_type = {}

        result = up.parse_pricing(server_type)

        self.assertIsNone(result)


class TestGetArchitecture(unittest.TestCase):
    def test_get_architecture_arm(self):
        """Test detecting ARM architecture."""
        server_type = {"name": "cax11"}
        result = up.get_architecture(server_type)
        self.assertEqual(result, "ARM64")

    def test_get_architecture_x86(self):
        """Test detecting X86 architecture."""
        server_type = {"name": "cx11"}
        result = up.get_architecture(server_type)
        self.assertEqual(result, "X86")

    def test_get_architecture_cpx(self):
        """Test CPX (x86) instance."""
        server_type = {"name": "cpx21"}
        result = up.get_architecture(server_type)
        self.assertEqual(result, "X86")


class TestUpdateHetznerPricing(unittest.TestCase):
    def setUp(self):
        self.config = {
            "providers": {
                "hetzner": {
                    "instances": [
                        {
                            "id": "cx11",
                            "name": "CX11",
                            "pricing": {"hourly": 0.0048, "monthly": 3.49},
                        },
                        {
                            "id": "cax11",
                            "name": "CAX11",
                            "pricing": {"hourly": 0.0048, "monthly": 3.49},
                        },
                    ]
                }
            }
        }

    def test_update_with_no_changes(self):
        """Test updating when prices haven't changed."""
        server_types = [
            {
                "name": "cx11",
                "prices": [
                    {
                        "price_hourly": {"net": "0.0048"},
                        "price_monthly": {"net": "3.49"},
                    }
                ],
            },
            {
                "name": "cax11",
                "prices": [
                    {
                        "price_hourly": {"net": "0.0048"},
                        "price_monthly": {"net": "3.49"},
                    }
                ],
            },
        ]

        updated = up.update_hetzner_pricing(self.config, server_types, dry_run=True)

        # No changes since prices match
        self.assertEqual(updated, 0)

    def test_update_with_price_change(self):
        """Test updating when prices have changed."""
        server_types = [
            {
                "name": "cx11",
                "prices": [
                    {
                        "price_hourly": {"net": "0.0050"},  # Changed
                        "price_monthly": {"net": "3.60"},  # Changed
                    }
                ],
            },
            {
                "name": "cax11",
                "prices": [
                    {
                        "price_hourly": {"net": "0.0048"},
                        "price_monthly": {"net": "3.49"},
                    }
                ],
            },
        ]

        updated = up.update_hetzner_pricing(self.config, server_types, dry_run=True)

        # One instance updated
        self.assertEqual(updated, 1)

    def test_update_instance_not_found(self):
        """Test when instance is not in API response."""
        server_types = [
            {
                "name": "cx22",  # Different instance
                "prices": [
                    {
                        "price_hourly": {"net": "0.0080"},
                        "price_monthly": "6.00",
                    }
                ],
            }
        ]

        updated = up.update_hetzner_pricing(self.config, server_types, dry_run=True)

        # No updates since cx11 not found
        self.assertEqual(updated, 0)


class TestFetchExchangeRates(unittest.TestCase):
    @patch("update_pricing.requests.get")
    def test_fetch_exchange_rates_success(self, mock_get):
        """Test successful exchange rate fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rates": {"USD": 1.087},
            "date": "2024-01-01",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = up.fetch_exchange_rates()

        self.assertEqual(result["eur_to_usd"], 1.087)
        self.assertEqual(result["usd_to_eur"], round(1 / 1.087, 4))
        self.assertEqual(result["last_updated"], "2024-01-01")

    @patch("update_pricing.requests.get")
    def test_fetch_exchange_rates_failure(self, mock_get):
        """Test failed exchange rate fetch."""
        import requests

        mock_get.side_effect = requests.RequestException("API error")

        result = up.fetch_exchange_rates()

        self.assertEqual(result, {})


class TestOCIHelpers(unittest.TestCase):
    def test_oci_shape_family_map(self):
        """Test OCI shape family mappings exist."""
        # Verify expected mappings exist
        self.assertEqual(up._OCI_SHAPE_FAMILY["VM.Standard.E5.Flex"], "E5")
        self.assertEqual(up._OCI_SHAPE_FAMILY["VM.Standard3.Flex"], "X9")
        self.assertEqual(up._OCI_SHAPE_FAMILY["VM.Standard.A1.Flex"], "A1")
        self.assertEqual(up._OCI_SHAPE_FAMILY["VM.Standard.A2.Flex"], "A2")


if __name__ == "__main__":
    unittest.main()
