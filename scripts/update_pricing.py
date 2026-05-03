#!/usr/bin/env python3
"""Fetch current pricing from cloud provider APIs and update config/instances.yaml."""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional

import requests
import yaml

HCLOUD_API = "https://api.hetzner.cloud/v1"
MAX_RETRIES = 3
RETRY_DELAY = 2


def fetch_server_types(token: str) -> list[dict]:
    """Fetch all server types from Hetzner API with retry."""
    headers = {"Authorization": f"Bearer {token}"}

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                f"{HCLOUD_API}/server_types", headers=headers, timeout=30
            )
            response.raise_for_status()
            return response.json()["server_types"]
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  [RETRY] Attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise
    raise RuntimeError("Max retries exceeded")


def parse_pricing(server_type: dict) -> Optional[dict]:
    """Extract pricing info from Hetzner server type."""
    prices = server_type.get("prices", [])
    if not prices:
        return None

    location_pricing = prices[0]
    hourly = location_pricing.get("price_hourly", {})
    monthly = location_pricing.get("price_monthly", {})

    # Use net prices (without VAT) for consistency across providers
    hourly_net = hourly.get("net")
    monthly_net = monthly.get("net")

    if not hourly_net or not monthly_net:
        return None

    return {
        "hourly": float(hourly_net),
        "monthly": float(monthly_net),
    }


def get_architecture(server_type: dict) -> str:
    """Determine architecture from server type."""
    name = server_type.get("name", "").lower()
    if "cax" in name:
        return "ARM64"
    return "X86"


def update_hetzner_pricing(
    config: dict, server_types: list[dict], dry_run: bool = False
) -> int:
    """Update Hetzner instances with fetched pricing. Returns count of updated."""
    hetzner = config.get("providers", {}).get("hetzner", {})
    instances = hetzner.get("instances", [])

    type_map = {st["name"]: st for st in server_types}
    updated = 0

    for inst in instances:
        inst_id = inst.get("id", "").lower()
        if inst_id not in type_map:
            print(f"  [WARN] Instance '{inst_id}' not found in API")
            continue

        st = type_map[inst_id]
        pricing = parse_pricing(st)
        if not pricing:
            print(f"  [WARN] No pricing for '{inst_id}'")
            continue

        old_pricing = inst.get("pricing", {})
        if (
            old_pricing.get("hourly") != pricing["hourly"]
            or old_pricing.get("monthly") != pricing["monthly"]
        ):
            inst["pricing"] = pricing
            updated += 1
            print(f"  [UPDATED] {inst_id}: €{pricing['monthly']}/mo")
        else:
            print(f"  [OK] {inst_id}: €{pricing['monthly']}/mo (unchanged)")

    return updated


def fetch_aws_pricing(config: dict, aws_region: str = "eu-central-1") -> int:
    """Fetch AWS pricing using boto3. Returns count of updated instances."""
    try:
        import boto3
    except ImportError:
        print("  [WARN] boto3 not installed, skipping AWS pricing update")
        return 0

    aws_config = config.get("providers", {}).get("aws", {})
    instances = aws_config.get("instances", [])
    if not instances:
        print("  [WARN] No AWS instances in config")
        return 0

    # AWS Pricing API is only available in us-east-1
    pricing_client = boto3.client("pricing", region_name="us-east-1")

    # Map AWS region codes to Pricing API location names
    region_names = {
        "eu-central-1": "EU (Frankfurt)",
        "us-east-1": "US East (N. Virginia)",
        "us-west-2": "US West (Oregon)",
    }
    location = region_names.get(aws_region, "EU (Frankfurt)")

    updated = 0
    for inst in instances:
        inst_id = inst.get("id", "")
        try:
            response = pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {
                        "Type": "TERM_MATCH",
                        "Field": "instanceType",
                        "Value": inst_id,
                    },
                    {
                        "Type": "TERM_MATCH",
                        "Field": "location",
                        "Value": location,
                    },
                    {
                        "Type": "TERM_MATCH",
                        "Field": "operatingSystem",
                        "Value": "Linux",
                    },
                    {
                        "Type": "TERM_MATCH",
                        "Field": "tenancy",
                        "Value": "Shared",
                    },
                    {
                        "Type": "TERM_MATCH",
                        "Field": "preInstalledSw",
                        "Value": "NA",
                    },
                    {
                        "Type": "TERM_MATCH",
                        "Field": "capacitystatus",
                        "Value": "Used",
                    },
                ],
                MaxResults=1,
            )

            price_list = response.get("PriceList", [])
            if not price_list:
                print(f"  [WARN] No pricing found for {inst_id} in {aws_region}")
                continue

            product = json.loads(price_list[0])
            terms = product.get("terms", {}).get("OnDemand", {})
            for term_key in terms:
                price_dimensions = terms[term_key].get("priceDimensions", {})
                for dim_key in price_dimensions:
                    hourly_str = (
                        price_dimensions[dim_key]
                        .get("pricePerUnit", {})
                        .get("USD", "0")
                    )
                    hourly = float(hourly_str)
                    monthly = round(hourly * 720, 2)

                    old_pricing = inst.get("pricing", {})
                    if (
                        old_pricing.get("hourly") != hourly
                        or old_pricing.get("monthly") != monthly
                    ):
                        inst["pricing"] = {"hourly": hourly, "monthly": monthly}
                        updated += 1
                        print(f"  [UPDATED] {inst_id}: ${monthly}/mo")
                    else:
                        print(f"  [OK] {inst_id}: ${monthly}/mo (unchanged)")
                    break
                break

        except Exception as e:
            print(f"  [WARN] Failed to fetch pricing for {inst_id}: {e}")

    return updated


def fetch_ovhcloud_pricing(config: dict) -> int:
    """Fetch OVHcloud pricing using the public catalog API (no auth needed).
    Returns count of updated instances."""
    ovh_config = config.get("providers", {}).get("ovhcloud", {})
    instances = ovh_config.get("instances", [])
    if not instances:
        print("  [WARN] No OVHcloud instances in config")
        return 0

    # OVH public catalog API - no authentication required
    catalog_url = "https://api.ovh.com/v1/order/catalog/public/cloud"
    updated = 0

    try:
        response = requests.get(
            catalog_url,
            params={"ovhSubsidiary": "DE"},
            timeout=30,
        )
        response.raise_for_status()
        catalog = response.json()
    except requests.RequestException as e:
        print(f"  [WARN] Failed to fetch OVH catalog: {e}")
        return 0

    # Build a map of flavor name -> hourly price from the catalog addons.
    # Compute flavor addons use planCode format "{flavor}.consumption"
    # (e.g. "b3-8.consumption"), with region variants like ".LZ.EU".
    # We match the base ".consumption" entry (no region suffix).
    flavor_prices = {}
    for addon in catalog.get("addons", []):
        plan_code = addon.get("planCode", "")
        if not plan_code.endswith(".consumption"):
            continue
        # Skip non-compute addons (databases, storage, etc.)
        if "." in plan_code.replace(".consumption", ""):
            continue

        flavor_name = plan_code.replace(".consumption", "")

        pricings = addon.get("pricings", [])
        for pricing in pricings:
            # OVH catalog returns net price + tax separately
            # Use net price (without VAT) for consistency
            hourly = pricing.get("price", 0) / 100_000_000
            if hourly > 0:
                flavor_prices[flavor_name] = hourly
                break

    for inst in instances:
        inst_id = inst.get("id", "")
        if inst_id not in flavor_prices:
            print(f"  [WARN] No pricing found for {inst_id} in OVH catalog")
            continue

        hourly = round(flavor_prices[inst_id], 4)
        monthly = round(hourly * 720, 2)

        old_pricing = inst.get("pricing", {})
        if old_pricing.get("hourly") != hourly or old_pricing.get("monthly") != monthly:
            inst["pricing"] = {"hourly": hourly, "monthly": monthly}
            updated += 1
            print(f"  [UPDATED] {inst_id}: \u20ac{monthly}/mo")
        else:
            print(f"  [OK] {inst_id}: \u20ac{monthly}/mo (unchanged)")

    return updated


def _fetch_oci_shape_rates() -> dict[str, dict[str, float]]:
    """Fetch per-unit OCI compute rates from the public Oracle APEX pricing API.
    Returns a dict mapping shape family key (e.g. "E4") to
    {"ocpu_hr": float, "gb_hr": float}."""
    url = "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/"
    try:
        response = requests.get(url, params={"currencyCode": "USD"}, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"  [WARN] Failed to fetch OCI pricing catalog: {e}")
        return {}

    # Items use inconsistent naming across shape generations:
    #   "Compute - Standard - E4 - OCPU"
    #   "Compute - Standard - E4  - Memory"  (double space)
    #   "Compute - Standard - A2 OCPU"       (no dash separator)
    #   "OCI - Compute - Standard - E6 - OCPU"  (OCI prefix)
    # We normalize by stripping the "OCI - " prefix and extracting
    # the family key and rate type via pattern matching.
    import re

    rates: dict[str, dict[str, float]] = {}
    for item in data.get("items", []):
        name = item.get("displayName", "")

        # Strip optional "OCI - " prefix
        name = re.sub(r"^OCI\s*-\s*", "", name)

        if not name.startswith("Compute - Standard - "):
            continue

        # Strip prefix, left with e.g. "E4 - OCPU", "E4  - Memory", "A2 OCPU"
        remainder = name.removeprefix("Compute - Standard - ").strip()

        # Extract family key and rate type
        m = re.match(r"^([A-Z]\d+)\s*[-\s]\s*(OCPU|Memory)", remainder, re.IGNORECASE)
        if not m:
            continue
        family = m.group(1)  # e.g. "E5", "X9", "A1", "A2"
        rate_type = m.group(2).lower()  # "ocpu" or "memory"

        # Extract PAY_AS_YOU_GO price (take the highest non-zero value;
        # A1 returns [0, 0.01] for free-tier + paid)
        price = 0.0
        for loc in item.get("currencyCodeLocalizations", []):
            if loc.get("currencyCode") != "USD":
                continue
            for p in loc.get("prices", []):
                if p.get("model") == "PAY_AS_YOU_GO":
                    price = max(price, p.get("value", 0.0))

        if family not in rates:
            rates[family] = {}
        if rate_type == "ocpu":
            rates[family]["ocpu_hr"] = price
        elif rate_type == "memory":
            rates[family]["gb_hr"] = price

    return rates


# Map OCI shape names to the family key used in the APEX pricing API
_OCI_SHAPE_FAMILY: dict[str, str] = {
    "VM.Standard.E5.Flex": "E5",
    "VM.Standard3.Flex": "X9",
    "VM.Standard.A1.Flex": "A1",
    "VM.Standard.A2.Flex": "A2",
}


def fetch_oci_pricing(config: dict, oci_region: str = "eu-frankfurt-1") -> int:
    """Fetch OCI pricing from the public Oracle APEX pricing API (no auth needed).
    Returns count of updated instances."""
    oci_config = config.get("providers", {}).get("oci", {})
    instances = oci_config.get("instances", [])
    if not instances:
        print("  [WARN] No OCI instances in config")
        return 0

    rates = _fetch_oci_shape_rates()
    if not rates:
        print("  [WARN] Could not fetch OCI pricing rates")
        return 0

    print(
        f"  [OK] Fetched rates for {len(rates)} shape families: "
        f"{', '.join(sorted(rates.keys()))}"
    )

    updated = 0
    for inst in instances:
        inst_id = inst.get("id", "")
        shape_name = inst.get("shape", "")
        ocpus = inst.get("ocpus", 1)
        ram_gb = inst.get("ram_gb", 4)

        family = _OCI_SHAPE_FAMILY.get(shape_name)
        if not family or family not in rates:
            print(f"  [WARN] No pricing for shape '{shape_name}' (instance {inst_id})")
            continue

        family_rates = rates[family]
        ocpu_rate = family_rates.get("ocpu_hr", 0)
        mem_rate = family_rates.get("gb_hr", 0)

        hourly = round(ocpus * ocpu_rate + ram_gb * mem_rate, 4)
        monthly = round(hourly * 720, 2)

        old_pricing = inst.get("pricing", {})
        if old_pricing.get("hourly") != hourly or old_pricing.get("monthly") != monthly:
            inst["pricing"] = {"hourly": hourly, "monthly": monthly}
            updated += 1
            print(
                f"  [UPDATED] {inst_id}: ${monthly}/mo "
                f"(${ocpu_rate}/OCPU-hr + ${mem_rate}/GB-hr)"
            )
        else:
            print(f"  [OK] {inst_id}: ${monthly}/mo (unchanged)")

    return updated


def fetch_gcp_pricing(config: dict, gcp_region: str = "europe-west3") -> int:
    """Fetch GCP pricing using the Cloud Billing Catalog API.
    Returns count of updated instances."""
    try:
        from google.cloud import billing_v1
    except ImportError:
        print(
            "  [WARN] google-cloud-billing not installed, skipping GCP pricing update"
        )
        return 0

    gcp_config = config.get("providers", {}).get("gcp", {})
    instances = gcp_config.get("instances", [])
    if not instances:
        print("  [WARN] No GCP instances in config")
        return 0

    # Compute Engine service ID
    service_name = "services/6F81-5844-456A"

    # Series identifiers as they appear at the start of SKU descriptions.
    # Listed longest-first so the regex prefers more specific matches (n2d before n2).
    known_series = [
        "n2d",
        "n4a",
        "c2d",
        "c3d",
        "c4a",
        "c4d",
        "n1",
        "n2",
        "n4",
        "e2",
        "t2a",
        "t2d",
        "c2",
        "c3",
        "c4",
    ]
    # Qualifiers between series and "Instance" (e.g. "C4A Arm Instance Core ...",
    # "N2D AMD Instance Core ...", "E2 Custom Instance Core ...").
    series_re = re.compile(
        r"^("
        + "|".join(known_series)
        + r")\s+(?:AMD|Arm|Custom)?\s*Instance\s+(Core|Ram)\s+running\s+in\s+",
        re.IGNORECASE,
    )
    # Variants we must skip — none of these are vanilla on-demand pricing.
    excluded_terms = (
        "sole tenancy",
        "committed use",
        "reserved",
        "premium",
        "overcommit",
        "dws",
        "extended",
        "memory-optimized",
    )

    try:
        client = billing_v1.CloudCatalogClient()
        request = billing_v1.ListSkusRequest(parent=service_name)

        # Per-series per-vCPU and per-GB hourly rates
        series_rates: dict[str, dict[str, float]] = {}

        for sku in client.list_skus(request=request):
            if gcp_region not in sku.service_regions:
                continue
            category = sku.category
            if category.resource_family != "Compute":
                continue
            if category.usage_type != "OnDemand":
                continue

            desc = sku.description
            desc_lower = desc.lower()
            if any(term in desc_lower for term in excluded_terms):
                continue

            m = series_re.match(desc)
            if not m:
                continue

            series_key = m.group(1).lower()
            rate_type = "cpu_hr" if m.group(2).lower() == "core" else "gb_hr"

            # Take first non-zero tiered rate
            for tier in sku.pricing_info:
                for rate in tier.pricing_expression.tiered_rates:
                    price = rate.unit_price.units + rate.unit_price.nanos / 1e9
                    if price > 0:
                        series_rates.setdefault(series_key, {})[rate_type] = price
                        break
                break

        if not series_rates:
            print(f"  [ERROR] No GCP pricing rates found for region {gcp_region}")
            return 0

        print(
            f"  [OK] Fetched rates for {len(series_rates)} machine series: "
            f"{', '.join(sorted(series_rates.keys()))}"
        )

    except Exception as e:
        print(f"  [ERROR] Failed to fetch GCP pricing from Cloud Billing API: {e}")
        return 0

    # Map machine type to series key (e.g. "n2d-standard-2" -> "n2d")
    def _get_series(machine_type: str) -> str | None:
        series = machine_type.split("-")[0]  # e2, n2, n2d, t2d, t2a
        if series in series_rates:
            return series
        return None

    updated = 0
    for inst in instances:
        inst_id = inst.get("id", "")
        vcpu = inst.get("vcpu", 0)
        ram_gb = inst.get("ram_gb", 0)

        series = _get_series(inst_id)
        if not series or series not in series_rates:
            print(f"  [WARN] No pricing rates for machine type '{inst_id}'")
            continue

        rates = series_rates[series]
        cpu_rate = rates.get("cpu_hr", 0)
        gb_rate = rates.get("gb_hr", 0)

        hourly = round(vcpu * cpu_rate + ram_gb * gb_rate, 5)
        monthly = round(hourly * 720, 2)

        old_pricing = inst.get("pricing", {})
        if old_pricing.get("hourly") != hourly or old_pricing.get("monthly") != monthly:
            inst["pricing"] = {"hourly": hourly, "monthly": monthly}
            updated += 1
            print(
                f"  [UPDATED] {inst_id}: ${monthly}/mo "
                f"(${cpu_rate}/vCPU-hr + ${gb_rate}/GB-hr)"
            )
        else:
            print(f"  [OK] {inst_id}: ${monthly}/mo (unchanged)")

    return updated


def fetch_azure_pricing(config: dict, azure_region: str = "northeurope") -> int:
    """Fetch Azure VM pricing using the Retail Prices API (public, no auth).
    Returns count of updated instances."""
    azure_config = config.get("providers", {}).get("azure", {})
    instances = azure_config.get("instances", [])
    if not instances:
        print("  [WARN] No Azure instances in config")
        return 0

    # Azure Retail Prices API — no authentication required
    api_url = "https://prices.azure.com/api/retail/prices"
    updated = 0

    for inst in instances:
        inst_id = inst.get("id", "")
        try:
            response = requests.get(
                api_url,
                params={
                    "$filter": (
                        f"armSkuName eq '{inst_id}' "
                        f"and armRegionName eq '{azure_region}' "
                        f"and serviceName eq 'Virtual Machines' "
                        f"and priceType eq 'Consumption'"
                    )
                },
                timeout=30,
            )
            response.raise_for_status()
            items = response.json().get("Items", [])
        except requests.RequestException as e:
            print(f"  [WARN] Failed to fetch pricing for {inst_id}: {e}")
            continue

        linux_items = [
            item
            for item in items
            if "Windows" not in item.get("productName", "")
            and "Cloud Services" not in item.get("productName", "")
            and "Spot" not in item.get("skuName", "")
            and "Low Priority" not in item.get("skuName", "")
            and item.get("type") == "Consumption"
        ]

        if not linux_items:
            print(f"  [WARN] No Linux pricing found for {inst_id} in {azure_region}")
            continue

        # Take the lowest on-demand hourly rate
        hourly = round(min(item.get("retailPrice", 0) for item in linux_items), 5)
        if hourly <= 0:
            print(f"  [WARN] Zero pricing returned for {inst_id}")
            continue

        monthly = round(hourly * 720, 2)

        old_pricing = inst.get("pricing", {})
        if old_pricing.get("hourly") != hourly or old_pricing.get("monthly") != monthly:
            inst["pricing"] = {"hourly": hourly, "monthly": monthly}
            updated += 1
            print(f"  [UPDATED] {inst_id}: ${monthly}/mo")
        else:
            print(f"  [OK] {inst_id}: ${monthly}/mo (unchanged)")

    return updated


def fetch_exchange_rates() -> dict:
    """Fetch EUR/USD rate from Frankfurter API (ECB data, free, no key)."""
    try:
        response = requests.get(
            "https://api.frankfurter.dev/v1/latest",
            params={"base": "EUR", "symbols": "USD"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        eur_to_usd = data["rates"]["USD"]
        return {
            "eur_to_usd": round(eur_to_usd, 4),
            "usd_to_eur": round(1.0 / eur_to_usd, 4),
            "last_updated": data["date"],
            "source": "Frankfurter API (ECB data)",
        }
    except requests.RequestException as e:
        print(f"  [WARN] Failed to fetch exchange rates: {e}")
        return {}


def update_config(
    config_path: str,
    server_types: list[dict],
    dry_run: bool = False,
    provider: str = "all",
    aws_region: str = "eu-central-1",
    azure_region: str = "northeurope",
) -> dict:
    """Update instances.yaml with fetched pricing."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    total_updated = 0

    # Update Hetzner pricing
    if provider in ("all", "hetzner") and server_types:
        print("\nUpdating Hetzner pricing...")
        total_updated += update_hetzner_pricing(config, server_types, dry_run)

    # Update AWS pricing
    if provider in ("all", "aws"):
        print("\nUpdating AWS pricing...")
        total_updated += fetch_aws_pricing(config, aws_region)

    # Update OVHcloud pricing
    if provider in ("all", "ovhcloud"):
        print("\nUpdating OVHcloud pricing...")
        total_updated += fetch_ovhcloud_pricing(config)

    # Update OCI pricing
    if provider in ("all", "oci"):
        print("\nUpdating OCI pricing...")
        total_updated += fetch_oci_pricing(config)

    # Update GCP pricing
    if provider in ("all", "gcp"):
        print("\nUpdating GCP pricing...")
        total_updated += fetch_gcp_pricing(config)

    # Update Azure pricing
    if provider in ("all", "azure"):
        print("\nUpdating Azure pricing...")
        total_updated += fetch_azure_pricing(config, azure_region)

    # Update exchange rates
    print("\nFetching exchange rates...")
    exchange_rates = fetch_exchange_rates()
    if exchange_rates:
        old_rates = config.get("exchange_rates", {})
        if old_rates.get("eur_to_usd") != exchange_rates.get("eur_to_usd"):
            config["exchange_rates"] = exchange_rates
            total_updated += 1
            print(f"  [UPDATED] EUR/USD: {exchange_rates['eur_to_usd']}")
        else:
            print(f"  [OK] EUR/USD: {exchange_rates['eur_to_usd']} (unchanged)")

    print(f"\nSummary: {total_updated} updated")

    if not dry_run and total_updated > 0:
        config["_metadata"] = {
            "last_pricing_update": datetime.now().isoformat(),
            "source": "Hetzner Cloud API / AWS Pricing API / OVH Catalog API / OCI APEX Pricing API / GCP Cloud Billing API / Azure Retail Prices API",
        }
        with open(config_path, "w") as f:
            yaml.dump(
                config, f, default_flow_style=False, sort_keys=False, allow_unicode=True
            )
        print(f"[OK] Saved to {config_path}")
    elif dry_run:
        print("[DRY RUN] No changes saved")

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Update instance pricing from cloud provider APIs"
    )
    parser.add_argument(
        "--config", "-c", default="config/instances.yaml", help="Config file path"
    )
    parser.add_argument(
        "--token", "-t", default=os.getenv("HCLOUD_TOKEN"), help="Hetzner API token"
    )
    parser.add_argument(
        "--provider",
        "-p",
        default="all",
        choices=["hetzner", "aws", "ovhcloud", "oci", "gcp", "azure", "all"],
        help="Provider to update pricing for",
    )
    parser.add_argument(
        "--aws-region",
        default="eu-central-1",
        help="AWS region for pricing (default: eu-central-1)",
    )
    parser.add_argument(
        "--azure-region",
        default="northeurope",
        help="Azure region for pricing (default: northeurope)",
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Show changes without saving"
    )
    args = parser.parse_args()

    if args.provider in ("all", "hetzner") and not args.token:
        print("[ERROR] HCLOUD_TOKEN not set. Use --token or set env var.")
        sys.exit(1)

    if not os.path.exists(args.config):
        print(f"[ERROR] Config file not found: {args.config}")
        sys.exit(1)

    server_types = []
    if args.provider in ("all", "hetzner"):
        print("Fetching pricing from Hetzner API...")
        try:
            server_types = fetch_server_types(args.token)
            print(f"[OK] Fetched {len(server_types)} server types")
        except requests.RequestException as e:
            print(f"[ERROR] Hetzner API request failed: {e}")
            if args.provider == "hetzner":
                sys.exit(1)

    try:
        update_config(
            args.config,
            server_types,
            dry_run=args.dry_run,
            provider=args.provider,
            aws_region=args.aws_region,
            azure_region=args.azure_region,
        )
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML parsing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
