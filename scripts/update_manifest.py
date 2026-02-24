#!/usr/bin/env python3
"""Update manifest.json on the benchmark-data branch with a new run entry."""

import argparse
import json
import os
import sys
from glob import glob


SCHEMA_VERSION = "3.0"


def parse_args():
    parser = argparse.ArgumentParser(description="Update benchmark data manifest")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to the run directory (e.g. data/runs/...)",
    )
    parser.add_argument(
        "--provider", required=True, help="Cloud provider (hetzner/aws)"
    )
    parser.add_argument("--region", required=True, help="Region for this run")
    parser.add_argument("--timestamp", required=True, help="Run timestamp identifier")
    return parser.parse_args()


def load_manifest(path: str) -> dict:
    """Load existing manifest or create a new one."""
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                manifest = json.load(f)
            if "runs" not in manifest:
                manifest["runs"] = []
            if "instance_index" not in manifest:
                manifest["instance_index"] = {}
            return manifest
        except (json.JSONDecodeError, IOError) as e:
            print(
                f"Warning: Could not read manifest, creating new: {e}", file=sys.stderr
            )

    return {"schema_version": SCHEMA_VERSION, "runs": [], "instance_index": {}}


def extract_instances_from_run(run_dir: str) -> list[str]:
    """Scan run directory for summary.json to extract instance list."""
    summary_path = os.path.join(run_dir, "summary.json")
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r") as f:
                summary = json.load(f)
            instances = summary.get("summary", {}).get("instances", [])
            return [inst.get("id", "") for inst in instances if inst.get("id")]
        except (json.JSONDecodeError, IOError):
            pass

    # Fallback: scan raw directory for instance files
    raw_dir = os.path.join(run_dir, "raw")
    if os.path.isdir(raw_dir):
        instances = []
        for filepath in glob(os.path.join(raw_dir, "*.json")):
            name = os.path.basename(filepath).replace(".json", "")
            # Strip run_id suffix: <instance_type>-<run_id>.json
            parts = name.rsplit("-", 1)
            if parts:
                instances.append(parts[0])
        return instances

    return []


def build_instance_index(runs: list[dict]) -> dict[str, list[str]]:
    """Rebuild the instance_index mapping instance types to run IDs."""
    index: dict[str, list[str]] = {}
    for run in runs:
        run_id = run.get("id", "")
        for inst in run.get("instances", []):
            if inst not in index:
                index[inst] = []
            if run_id not in index[inst]:
                index[inst].append(run_id)
    return index


def main():
    args = parse_args()

    manifest = load_manifest(args.manifest)
    manifest["schema_version"] = SCHEMA_VERSION

    # Extract instance list from run data
    instances = extract_instances_from_run(args.run_dir)

    # Build relative file paths
    run_id = f"{args.timestamp}-{args.provider}-{args.region}"
    run_dir_rel = args.run_dir

    run_entry = {
        "id": run_id,
        "timestamp": args.timestamp,
        "provider": args.provider,
        "region": args.region,
        "instance_count": len(instances),
        "instances": instances,
        "files": {
            "summary": os.path.join(run_dir_rel, "summary.json"),
            "detail": os.path.join(run_dir_rel, "detail.json"),
        },
    }

    # Update or append
    existing_idx = next(
        (i for i, r in enumerate(manifest["runs"]) if r["id"] == run_id), None
    )
    if existing_idx is not None:
        manifest["runs"][existing_idx] = run_entry
    else:
        manifest["runs"].append(run_entry)

    # Sort by timestamp descending
    manifest["runs"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    # Rebuild instance index
    manifest["instance_index"] = build_instance_index(manifest["runs"])

    # Write manifest
    os.makedirs(os.path.dirname(args.manifest) or ".", exist_ok=True)
    with open(args.manifest, "w") as f:
        json.dump(manifest, f, indent=2)

    print(
        f"[OK] Manifest updated: {len(manifest['runs'])} runs, {len(instances)} instances in this run"
    )


if __name__ == "__main__":
    main()
