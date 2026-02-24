#!/usr/bin/env python3
"""Estimate benchmark run cost from instances.yaml."""

import argparse
import json

import yaml


def estimate_cost(
    provider: str, instances_input: str, config_path: str = "config/instances.yaml"
) -> dict:
    """Calculate estimated cost for a benchmark run."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    provider_config = config.get("providers", {}).get(provider, {})
    all_instances = provider_config.get("instances", [])
    currency = provider_config.get("currency", "EUR")

    if instances_input == "all":
        to_benchmark = all_instances
    else:
        instance_ids = [i.strip().lower() for i in instances_input.split(",")]
        to_benchmark = [i for i in all_instances if i["id"].lower() in instance_ids]

    # 20 minutes runtime (conservative)
    RUNTIME_HOURS = 0.33

    # Get exchange rates from config
    exchange = config.get("exchange_rates", {})
    eur_to_usd = exchange.get("eur_to_usd", 1.087)
    usd_to_eur = exchange.get("usd_to_eur", 0.92)

    total_cost_native = sum(
        i.get("pricing", {}).get("hourly", 0) * RUNTIME_HOURS for i in to_benchmark
    )

    # Convert to both EUR and USD
    if currency == "USD":
        total_cost_usd = total_cost_native
        total_cost_eur = total_cost_native * usd_to_eur
    else:
        total_cost_eur = total_cost_native
        total_cost_usd = total_cost_native * eur_to_usd

    return {
        "cost_eur": round(total_cost_eur, 4),
        "cost_usd": round(total_cost_usd, 4),
        "count": len(to_benchmark),
        "instances": [i["id"] for i in to_benchmark],
    }


def main():
    parser = argparse.ArgumentParser(description="Estimate benchmark cost")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--instances", required=True)
    parser.add_argument("--config", default="config/instances.yaml")
    args = parser.parse_args()

    result = estimate_cost(args.provider, args.instances, args.config)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
