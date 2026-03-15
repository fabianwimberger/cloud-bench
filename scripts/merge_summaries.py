#!/usr/bin/env python3
"""Merge summaries from multiple benchmark runs into a single combined view."""

import argparse
import json
import os
import sys
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge benchmark summaries from multiple runs"
    )
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument(
        "--data-dir", required=True, help="Path to the data directory containing runs/"
    )
    parser.add_argument(
        "--output", required=True, help="Output path for merged summary"
    )
    return parser.parse_args()


def load_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {path}: {e}", file=sys.stderr)
        return None


def main():
    args = parse_args()

    manifest = load_json(args.manifest)
    if not manifest:
        print("[ERROR] Could not load manifest", file=sys.stderr)
        sys.exit(1)

    runs = manifest.get("runs", [])
    if not runs:
        print("[WARN] No runs in manifest", file=sys.stderr)
        sys.exit(0)

    # Find latest run per provider
    latest_per_provider: dict[str, dict] = {}
    for run in runs:
        provider = run.get("provider", "unknown")
        if provider not in latest_per_provider:
            latest_per_provider[provider] = run

    print(f"Found latest runs for: {', '.join(latest_per_provider.keys())}")

    # Merge summaries
    all_instances = []
    all_labels = []
    exchange_rates = {}
    providers_seen = []

    for provider, run in latest_per_provider.items():
        summary_path = os.path.join(args.data_dir, run["files"]["summary"])
        summary = load_json(summary_path)
        if not summary:
            print(f"  [WARN] No summary for {provider} run {run['id']}")
            continue

        providers_seen.append(provider)
        meta = summary.get("metadata", {})
        if not exchange_rates and meta.get("exchange_rates"):
            exchange_rates = meta["exchange_rates"]

        currency = meta.get("currency", "USD")
        eur_to_usd = meta.get("exchange_rates", {}).get("eur_to_usd", 1.0)

        for inst in summary.get("summary", {}).get("instances", []):
            # Tag each instance with its provider for the frontend
            inst["provider"] = provider
            inst["region"] = run.get("region", "")

            # Normalize all prices to USD
            if currency == "EUR":
                pricing = inst.get("pricing", {})
                pricing["hourly"] = round(pricing.get("hourly", 0) * eur_to_usd, 4)
                pricing["monthly"] = round(pricing.get("monthly", 0) * eur_to_usd, 2)

            all_instances.append(inst)
            all_labels.append(inst["id"])

        print(
            f"  [OK] {provider}: {len(summary.get('summary', {}).get('instances', []))} instances"
        )

    # Re-score across all instances so scores are comparable
    all_instances = rescale_scores(all_instances)

    merged = {
        "schema_version": "2.0",
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "run_count": len(all_instances),
            "currency": "USD",
            "providers": providers_seen,
            "exchange_rates": exchange_rates,
        },
        "summary": {
            "labels": all_labels,
            "instances": all_instances,
        },
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(merged, f, indent=2)

    print(
        f"[OK] Merged {len(all_instances)} instances from {len(providers_seen)} providers"
    )


def rescale_scores(instances: list[dict]) -> list[dict]:
    """Rescale scores across all instances so they are comparable."""
    if not instances:
        return instances

    metrics_keys = [
        "cpu_single_events",
        "cpu_multi_events",
        "memory_mib_per_sec",
        "disk_iops",
    ]
    score_keys = ["single_core", "multi_core", "memory", "disk"]

    # Get raw metric values
    raw_values: dict[str, list[float]] = {k: [] for k in metrics_keys}
    for inst in instances:
        metrics = inst.get("metrics", {})
        for k in metrics_keys:
            val = metrics.get(k, 0)
            if val:
                raw_values[k].append(val)

    # Calculate max for each metric
    max_values = {k: max(vals) if vals else 1 for k, vals in raw_values.items()}

    # Rescale scores as percentage of max
    for inst in instances:
        metrics = inst.get("metrics", {})
        scores = inst.get("scores", {})
        for mk, sk in zip(metrics_keys, score_keys):
            val = metrics.get(mk, 0)
            if max_values[mk] > 0:
                scores[sk] = round(val / max_values[mk] * 100, 1)

        # Recalculate overall as average of component scores
        component_scores = [scores.get(k, 0) for k in score_keys]
        scores["overall"] = (
            round(sum(component_scores) / len(component_scores), 1)
            if component_scores
            else 0
        )

        # Recalculate value score (overall / monthly price)
        monthly = inst.get("pricing", {}).get("monthly", 0)
        if monthly > 0:
            inst["value"] = round(scores["overall"] / monthly, 1)

    return instances


if __name__ == "__main__":
    main()
