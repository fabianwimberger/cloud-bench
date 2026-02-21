#!/usr/bin/env python3
"""Fetch current pricing from Hetzner Cloud API and update config/instances.yaml."""

import argparse
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
        "hourly_eur": float(hourly_gross),
        "monthly_eur": float(monthly_gross),
    }


def get_architecture(server_type: dict) -> str:
    """Determine architecture from server type."""
    name = server_type.get("name", "").lower()
    if "cax" in name:
        return "ARM64"
    if "cpx" in name:
        return "AMD EPYC"
    return "Intel"


def update_config(
    config_path: str, server_types: list[dict], dry_run: bool = False
) -> dict:
    """Update instances.yaml with fetched pricing."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

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
            old_pricing.get("hourly_eur") != pricing["hourly_eur"]
            or old_pricing.get("monthly_eur") != pricing["monthly_eur"]
        ):
            inst["pricing"] = pricing
            updated += 1
            print(f"  [UPDATED] {inst_id}: €{pricing['monthly_eur']}/mo")
        else:
            print(f"  [OK] {inst_id}: €{pricing['monthly_eur']}/mo (unchanged)")

    print(f"\nSummary: {updated} updated")

    if not dry_run and updated > 0:
        config["_metadata"] = {
            "last_pricing_update": datetime.now().isoformat(),
            "source": "Hetzner Cloud API",
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
        description="Update instance pricing from Hetzner API"
    )
    parser.add_argument(
        "--config", "-c", default="config/instances.yaml", help="Config file path"
    )
    parser.add_argument(
        "--token", "-t", default=os.getenv("HCLOUD_TOKEN"), help="Hetzner API token"
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Show changes without saving"
    )
    args = parser.parse_args()

    if not args.token:
        print("[ERROR] HCLOUD_TOKEN not set. Use --token or set env var.")
        sys.exit(1)

    if not os.path.exists(args.config):
        print(f"[ERROR] Config file not found: {args.config}")
        sys.exit(1)

    print("Fetching pricing from Hetzner API...")
    try:
        server_types = fetch_server_types(args.token)
        print(f"[OK] Fetched {len(server_types)} server types\n")

        update_config(args.config, server_types, dry_run=args.dry_run)
    except requests.RequestException as e:
        print(f"[ERROR] API request failed: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML parsing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
