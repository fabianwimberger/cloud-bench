#!/usr/bin/env python3
"""Build consolidated history.json from benchmark-data branch runs."""

import argparse
import json
import os
import sys
from datetime import datetime


SCHEMA_VERSION = "3.0"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build consolidated history.json from benchmark runs"
    )
    parser.add_argument(
        "--data-dir",
        required=True,
        help="Path to the data directory (contains manifest.json and runs/)",
    )
    parser.add_argument("--output", required=True, help="Output path for history.json")
    return parser.parse_args()


def load_detail(detail_path: str) -> dict | None:
    """Load a run's detail.json file."""
    if not os.path.exists(detail_path):
        return None
    try:
        with open(detail_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {detail_path}: {e}", file=sys.stderr)
        return None


def extract_instance_data(detail: dict, run_meta: dict) -> dict[str, dict]:
    """Extract per-instance data from a detail.json file.

    Returns a dict mapping instance_id -> {scores, metrics, pricing, specs}.
    """
    instances_data = {}
    for inst in detail.get("instances", []):
        inst_id = inst.get("id", "")
        if not inst_id:
            continue

        instances_data[inst_id] = {
            "timestamp": run_meta.get("timestamp", ""),
            "region": run_meta.get("region", ""),
            "scores": inst.get("scores", {}),
            "metrics": {
                "cpu_single_raw": inst.get("metrics", {}).get(
                    "cpu_single_raw",
                    inst.get("metrics", {}).get("cpu_single_events", 0),
                ),
                "cpu_multi_raw": inst.get("metrics", {}).get(
                    "cpu_multi_raw", inst.get("metrics", {}).get("cpu_multi_events", 0)
                ),
                "mem_throughput_raw": inst.get("metrics", {}).get(
                    "mem_throughput_raw",
                    inst.get("metrics", {}).get("memory_mib_per_sec", 0),
                ),
                "disk_iops_raw": inst.get("metrics", {}).get(
                    "disk_iops_raw", inst.get("metrics", {}).get("disk_iops", 0)
                ),
            },
            "pricing": inst.get("pricing", {}),
        }

    return instances_data


def build_history(data_dir: str) -> dict:
    """Build the consolidated history from all runs."""
    manifest_path = os.path.join(data_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Warning: No manifest.json found at {manifest_path}", file=sys.stderr)
        return {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "instances": {},
        }

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    # Collect per-instance history across all runs
    history: dict[str, dict] = {}

    for run in manifest.get("runs", []):
        raw_path = run.get("files", {}).get("detail", "")
        # Strip leading "data/" prefix since data_dir already points to data/
        if raw_path.startswith("data/"):
            raw_path = raw_path[5:]
        detail_path = os.path.join(data_dir, raw_path)
        detail = load_detail(detail_path)
        if not detail:
            print(f"  Skipping run {run.get('id', '?')}: no detail data")
            continue

        provider = run.get("provider", "unknown")
        instance_data = extract_instance_data(detail, run)

        for inst_id, run_data in instance_data.items():
            if inst_id not in history:
                # Find specs from the detail instances
                inst_detail: dict = next(
                    (i for i in detail.get("instances", []) if i.get("id") == inst_id),
                    {},
                )
                history[inst_id] = {
                    "provider": provider,
                    "specs": inst_detail.get("specs", {}),
                    "runs": [],
                }

            history[inst_id]["runs"].append(run_data)

    # Sort each instance's runs chronologically
    for inst_id in history:
        history[inst_id]["runs"].sort(key=lambda r: r.get("timestamp", ""))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now().isoformat(),
        "instances": history,
    }


def main():
    args = parse_args()

    if not os.path.isdir(args.data_dir):
        print(f"[ERROR] Data directory not found: {args.data_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Building history from {args.data_dir}...")
    history = build_history(args.data_dir)

    instance_count = len(history.get("instances", {}))
    total_runs = sum(
        len(inst.get("runs", [])) for inst in history.get("instances", {}).values()
    )

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(history, f, indent=2, default=str)

    print(
        f"[OK] History built: {instance_count} instances, {total_runs} total data points"
    )
    print(f"[OK] Written to {args.output}")


if __name__ == "__main__":
    main()
