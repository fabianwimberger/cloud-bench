#!/usr/bin/env python3
"""Fetch current pricing from cloud provider APIs and update config/instances.yaml."""

import argparse
import json
import os
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

    hourly_gross = hourly.get("gross")
    monthly_gross = monthly.get("gross")

    if not hourly_gross or not monthly_gross:
        return None

    return {
        "hourly": float(hourly_gross),
        "monthly": float(monthly_gross),
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
            "source": "Hetzner Cloud API / AWS Pricing API",
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
        choices=["hetzner", "aws", "all"],
        help="Provider to update pricing for",
    )
    parser.add_argument(
        "--aws-region",
        default="eu-central-1",
        help="AWS region for pricing (default: eu-central-1)",
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
        )
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML parsing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
