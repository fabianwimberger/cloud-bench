#!/usr/bin/env python3
"""Tests for update_pricing.py."""

import os
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

# Ensure google.cloud.billing_v1 is mockable even when not installed
_google = types.ModuleType("google")
_google_cloud = types.ModuleType("google.cloud")
setattr(_google, "cloud", _google_cloud)  # type: ignore[attr-defined]
sys.modules["google"] = _google
sys.modules["google.cloud"] = _google_cloud
sys.modules.setdefault("google.cloud.billing_v1", MagicMock())

import update_pricing as up  # noqa: E402


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


class TestFetchGCPPricing(unittest.TestCase):
    def setUp(self):
        self.config = {
            "providers": {
                "gcp": {
                    "instances": [
                        {
                            "id": "e2-medium",
                            "name": "E2 Medium",
                            "vcpu": 2,
                            "ram_gb": 4,
                            "pricing": {"hourly": 0.05, "monthly": 36.0},
                        },
                        {
                            "id": "n2-standard-2",
                            "name": "N2 Standard 2",
                            "vcpu": 2,
                            "ram_gb": 8,
                            "pricing": {"hourly": 0.07, "monthly": 50.4},
                        },
                    ]
                }
            }
        }

    def _make_sku(
        self,
        description,
        service_regions,
        resource_family="Compute",
        usage_type="OnDemand",
        unit_price_units=0,
        unit_price_nanos=0,
    ):
        """Helper to create a mock SKU."""
        sku = MagicMock()
        sku.description = description
        sku.service_regions = service_regions

        category = MagicMock()
        category.resource_family = resource_family
        category.usage_type = usage_type
        sku.category = category

        tier = MagicMock()
        rate = MagicMock()
        rate.unit_price.units = unit_price_units
        rate.unit_price.nanos = unit_price_nanos
        tier.pricing_expression.tiered_rates = [rate]
        sku.pricing_info = [tier]

        return sku

    def test_fetch_gcp_pricing_import_error(self):
        """Test that ImportError is handled gracefully."""
        with patch.dict("sys.modules", {"google.cloud.billing_v1": None}):
            result = up.fetch_gcp_pricing(self.config)
            self.assertEqual(result, 0)

    def test_fetch_gcp_pricing_no_instances(self):
        """Test when no GCP instances are configured."""
        config = {"providers": {"gcp": {"instances": []}}}
        result = up.fetch_gcp_pricing(config)
        self.assertEqual(result, 0)

    def test_fetch_gcp_pricing_no_gcp_config(self):
        """Test when no GCP provider is configured."""
        config = {"providers": {}}
        result = up.fetch_gcp_pricing(config)
        self.assertEqual(result, 0)

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_success(self, mock_client_cls):
        """Test successful GCP pricing fetch and update."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Create SKUs that should match our instances
        skus = [
            self._make_sku(
                "E2 Instance Core running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=50000000,  # $0.05
            ),
            self._make_sku(
                "E2 Instance Ram running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=7000000,  # $0.007
            ),
            self._make_sku(
                "N2 Instance Core running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=60000000,  # $0.06
            ),
            self._make_sku(
                "N2 Instance Ram running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=8000000,  # $0.008
            ),
        ]
        mock_client.list_skus.return_value = skus

        result = up.fetch_gcp_pricing(self.config, gcp_region="europe-west3")

        # e2-medium: 2 * 0.05 + 4 * 0.007 = 0.128 -> monthly = 92.16
        # n2-standard-2: 2 * 0.06 + 8 * 0.008 = 0.184 -> monthly = 132.48
        # Both should update since old prices differ
        self.assertEqual(result, 2)
        self.assertEqual(
            self.config["providers"]["gcp"]["instances"][0]["pricing"]["hourly"], 0.128
        )
        self.assertEqual(
            self.config["providers"]["gcp"]["instances"][0]["pricing"]["monthly"], 92.16
        )
        self.assertEqual(
            self.config["providers"]["gcp"]["instances"][1]["pricing"]["hourly"], 0.184
        )
        self.assertEqual(
            self.config["providers"]["gcp"]["instances"][1]["pricing"]["monthly"],
            132.48,
        )

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_unchanged(self, mock_client_cls):
        """Test when prices haven't changed."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Pre-calculate expected rates so prices match exactly
        # hourly = 2 * cpu_rate + 4 * gb_rate = 0.05 -> monthly = 36.0
        # cpu_rate = 0.015, gb_rate = 0.005 => 2*0.015 + 4*0.005 = 0.05
        skus = [
            self._make_sku(
                "E2 Instance Core running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=15000000,  # $0.015
            ),
            self._make_sku(
                "E2 Instance Ram running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=5000000,  # $0.005
            ),
        ]
        mock_client.list_skus.return_value = skus

        config = {
            "providers": {
                "gcp": {
                    "instances": [
                        {
                            "id": "e2-medium",
                            "vcpu": 2,
                            "ram_gb": 4,
                            "pricing": {"hourly": 0.05, "monthly": 36.0},
                        }
                    ]
                }
            }
        }

        result = up.fetch_gcp_pricing(config, gcp_region="europe-west3")
        self.assertEqual(result, 0)

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_excluded_terms(self, mock_client_cls):
        """Test that SKUs with excluded terms are skipped."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        skus = [
            self._make_sku(
                "E2 Instance Core running in Frankfurt (Committed Use)",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=10000000,
            ),
            self._make_sku(
                "E2 Instance Core running in Frankfurt (Reserved)",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=10000000,
            ),
        ]
        mock_client.list_skus.return_value = skus

        result = up.fetch_gcp_pricing(self.config, gcp_region="europe-west3")
        # No matching SKUs, so no updates
        self.assertEqual(result, 0)

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_wrong_region(self, mock_client_cls):
        """Test that SKUs for other regions are skipped."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        skus = [
            self._make_sku(
                "E2 Instance Core running in us-east1",
                ["us-east1"],
                unit_price_units=0,
                unit_price_nanos=50000000,
            ),
        ]
        mock_client.list_skus.return_value = skus

        result = up.fetch_gcp_pricing(self.config, gcp_region="europe-west3")
        self.assertEqual(result, 0)

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_wrong_family(self, mock_client_cls):
        """Test that non-Compute SKUs are skipped."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        skus = [
            self._make_sku(
                "E2 Instance Core running in Frankfurt",
                ["europe-west3"],
                resource_family="Storage",
                unit_price_units=0,
                unit_price_nanos=50000000,
            ),
        ]
        mock_client.list_skus.return_value = skus

        result = up.fetch_gcp_pricing(self.config, gcp_region="europe-west3")
        self.assertEqual(result, 0)

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_api_error(self, mock_client_cls):
        """Test that API errors are handled gracefully."""
        mock_client_cls.side_effect = Exception("API unavailable")

        result = up.fetch_gcp_pricing(self.config)
        self.assertEqual(result, 0)

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_unknown_machine_type(self, mock_client_cls):
        """Test when machine type has no matching series rates."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        skus = [
            self._make_sku(
                "E2 Instance Core running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=50000000,
            ),
        ]
        mock_client.list_skus.return_value = skus

        config = {
            "providers": {
                "gcp": {
                    "instances": [
                        {
                            "id": "xyz-unknown",
                            "vcpu": 2,
                            "ram_gb": 4,
                            "pricing": {"hourly": 0.05, "monthly": 36.0},
                        }
                    ]
                }
            }
        }

        result = up.fetch_gcp_pricing(config, gcp_region="europe-west3")
        self.assertEqual(result, 0)

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_series_regex(self, mock_client_cls):
        """Test that series regex correctly matches various SKU descriptions."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        skus = [
            self._make_sku(
                "N2D AMD Instance Core running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=60000000,
            ),
            self._make_sku(
                "C4A Arm Instance Core running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=80000000,
            ),
            self._make_sku(
                "E2 Custom Instance Ram running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=4000000,
            ),
        ]
        mock_client.list_skus.return_value = skus

        config = {
            "providers": {
                "gcp": {
                    "instances": [
                        {
                            "id": "n2d-standard-2",
                            "vcpu": 2,
                            "ram_gb": 8,
                            "pricing": {"hourly": 0.0, "monthly": 0.0},
                        },
                        {
                            "id": "c4a-standard-2",
                            "vcpu": 2,
                            "ram_gb": 8,
                            "pricing": {"hourly": 0.0, "monthly": 0.0},
                        },
                        {
                            "id": "e2-medium",
                            "vcpu": 2,
                            "ram_gb": 4,
                            "pricing": {"hourly": 0.0, "monthly": 0.0},
                        },
                    ]
                }
            }
        }

        result = up.fetch_gcp_pricing(config, gcp_region="europe-west3")
        # All three should update
        self.assertEqual(result, 3)

        # n2d: 2 * 0.06 + 8 * 0 = 0.12 (no ram rate, so 0)
        # c4a: 2 * 0.08 + 8 * 0 = 0.16
        # e2: 2 * 0 + 4 * 0.004 = 0.016 (no cpu rate, so 0)
        self.assertAlmostEqual(
            config["providers"]["gcp"]["instances"][0]["pricing"]["hourly"],
            0.12,
            places=5,
        )
        self.assertAlmostEqual(
            config["providers"]["gcp"]["instances"][1]["pricing"]["hourly"],
            0.16,
            places=5,
        )
        self.assertAlmostEqual(
            config["providers"]["gcp"]["instances"][2]["pricing"]["hourly"],
            0.016,
            places=5,
        )

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_non_ondemand(self, mock_client_cls):
        """Test that SKUs with usage_type != OnDemand are skipped."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        skus = [
            self._make_sku(
                "E2 Instance Core running in Frankfurt",
                ["europe-west3"],
                usage_type="Preemptible",
                unit_price_units=0,
                unit_price_nanos=50000000,
            ),
        ]
        mock_client.list_skus.return_value = skus

        result = up.fetch_gcp_pricing(self.config, gcp_region="europe-west3")
        # Preemptible SKUs are excluded, so no rates found
        self.assertEqual(result, 0)

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_no_regex_match(self, mock_client_cls):
        """Test that SKUs not matching the series regex are skipped."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Description is Compute / OnDemand / right region but doesn't match regex
        skus = [
            self._make_sku(
                "E2 Micro Instance running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=50000000,
            ),
        ]
        mock_client.list_skus.return_value = skus

        result = up.fetch_gcp_pricing(self.config, gcp_region="europe-west3")
        # No regex match, so no rates found
        self.assertEqual(result, 0)

    @patch("google.cloud.billing_v1.CloudCatalogClient")
    def test_fetch_gcp_pricing_zero_price_empty_rates(self, mock_client_cls):
        """Test that SKUs with zero price lead to empty series_rates."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Matching SKU but with zero price -> no rate added -> empty series_rates
        skus = [
            self._make_sku(
                "E2 Instance Core running in Frankfurt",
                ["europe-west3"],
                unit_price_units=0,
                unit_price_nanos=0,
            ),
        ]
        mock_client.list_skus.return_value = skus

        result = up.fetch_gcp_pricing(self.config, gcp_region="europe-west3")
        # Zero price means no rate stored, empty series_rates -> error path
        self.assertEqual(result, 0)


class TestUpdateConfigGCP(unittest.TestCase):
    @patch("update_pricing.fetch_gcp_pricing", return_value=1)
    @patch("update_pricing.fetch_exchange_rates", return_value={})
    def test_update_config_gcp_provider(self, mock_fetch_rates, mock_fetch_gcp):
        """Test update_config calls fetch_gcp_pricing when provider is gcp."""
        config = {
            "providers": {
                "gcp": {
                    "instances": [
                        {
                            "id": "e2-medium",
                            "vcpu": 2,
                            "ram_gb": 4,
                            "pricing": {"hourly": 0.05, "monthly": 36.0},
                        }
                    ]
                }
            }
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config, f)
            temp_path = f.name

        try:
            result = up.update_config(
                temp_path, [], dry_run=False, provider="gcp"
            )
            mock_fetch_gcp.assert_called_once()
            # fetch_gcp_pricing returned 1, so metadata should be written
            self.assertIn("_metadata", result)
            self.assertIn(
                "GCP Cloud Billing API", result["_metadata"]["source"]
            )
        finally:
            os.unlink(temp_path)


class TestMainGCP(unittest.TestCase):
    @patch("update_pricing.fetch_gcp_pricing", return_value=0)
    @patch("update_pricing.fetch_server_types", return_value=[])
    @patch("update_pricing.fetch_exchange_rates", return_value={})
    def test_main_gcp_provider(self, mock_rates, mock_server, mock_gcp):
        """Test main() accepts --provider gcp and invokes fetch_gcp_pricing."""
        config = {"providers": {"gcp": {"instances": []}}}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config, f)
            temp_path = f.name

        try:
            with patch(
                "sys.argv",
                ["update_pricing", "--provider", "gcp", "--config", temp_path],
            ):
                up.main()
            mock_gcp.assert_called_once()
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
