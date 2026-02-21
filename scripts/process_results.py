#!/usr/bin/env python3
"""Process benchmark results into scored JSON/CSV output."""

import json
import glob
import os
import sys
import argparse
import yaml
from datetime import datetime

import pandas as pd

SCHEMA_VERSION = "2.0"


def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def parse_args():
    parser = argparse.ArgumentParser(description='Process benchmark results')
    parser.add_argument('--input', '-i', required=True, help='Input directory with JSON files')
    parser.add_argument('--output', '-o', required=True, help='Output directory for processed data')
    parser.add_argument('--config', '-c', default='config/instances.yaml', help='Path to instances config YAML')
    parser.add_argument('--region', '-r', required=True, help='Region for this benchmark run')
    parser.add_argument('--provider', '-p', default='hetzner', help='Cloud provider')
    return parser.parse_args()


def load_results(input_dir: str) -> list[dict]:
    results = []
    pattern = os.path.join(input_dir, '*.json')

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    for filepath in glob.glob(pattern):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            required = ['system', 'cpu', 'memory', 'disk']
            missing = [f for f in required if f not in data]
            if missing:
                print(f"Warning: {filepath} missing fields: {missing}", file=sys.stderr)
                continue

            filename = os.path.basename(filepath)
            data['_source_file'] = filename
            # Filename format: <instance_type>-<run_id>.json
            # Instance type is everything before the first run_id segment
            name = filename.replace('.json', '')
            # Also try to get instance_type from the JSON data itself (set by ansible inventory)
            sys_info = data.get('system', {})
            data['_instance_key'] = sys_info.get('instance_type', name.split('-')[0] if name else filename)
            results.append(data)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {filepath}: {e}", file=sys.stderr)
            raise

    return results


def get_instance_type_from_key(key: str, config: dict = None, provider: str = None) -> str:
    key_lower = key.lower()

    # Build instance type list from config instead of hardcoding
    types = []
    if config and provider:
        try:
            instances = config.get('providers', {}).get(provider, {}).get('instances', [])
            types = [inst['id'].lower() for inst in instances if 'id' in inst]
        except (KeyError, TypeError, AttributeError):
            pass

    # Sort by length descending so longer IDs match first (e.g. 'cpx22' before 'cx23')
    types.sort(key=len, reverse=True)

    for t in types:
        if t in key_lower:
            return t
    return key_lower


def get_instance_config(instance_type: str, config: dict, provider: str) -> dict:
    if not config or not instance_type:
        return {}
    
    try:
        provider_config = config.get('providers', {})
        if provider not in provider_config:
            return {}
        
        instances = provider_config[provider].get('instances', [])
        t = instance_type.lower()
        
        for inst in instances:
            if inst.get('id', '').lower() == t:
                return inst
    except (KeyError, TypeError, AttributeError):
        pass
    return {}


def normalize_results(results: list[dict], config: dict, provider: str, region: str) -> pd.DataFrame:
    normalized = []

    for r in results:
        system = r.get('system', {})
        cpu = r.get('cpu', {})
        memory = r.get('memory', {})
        disk = r.get('disk', {})

        key = r.get('_instance_key', 'unknown')
        inst_type = get_instance_type_from_key(key, config, provider)
        inst_config = get_instance_config(inst_type, config, provider)

        pricing = inst_config.get('pricing', {})

        # Provider attributes - extensible dict for provider-specific fields
        attrs = r.get('provider_attributes', {})
        if not attrs:
            attrs = {
                'arch': system.get('arch', inst_config.get('arch', 'Unknown')),
                'os': system.get('os', 'Unknown'),
                'kernel': system.get('kernel'),
                'vcpu': system.get('vcpu', inst_config.get('vcpu', 0)),
                'memory_mb': system.get('memory_mb', inst_config.get('ram_gb', 0) * 1024),
            }

        normalized.append({
            'instance_key': key,
            'instance_type': inst_type.upper(),
            'display_name': f"{inst_type.upper()} ({inst_config.get('arch', 'Unknown')})",
            'vcpu': inst_config.get('vcpu', attrs.get('vcpu', 0)),
            'ram_gb': inst_config.get('ram_gb', 0),
            'disk_gb': inst_config.get('disk_gb', 0),
            'price_hourly': pricing.get('hourly_eur', 0),
            'price_monthly': pricing.get('monthly_eur', 0),
            'metrics': {
                'cpu_single_raw': cpu.get('single_thread_events', 0),
                'cpu_multi_raw': cpu.get('multi_thread_events', 0),
                'mem_read_raw': memory.get('read_mib_per_sec', 0),
                'mem_write_raw': memory.get('write_mib_per_sec', 0),
                'mem_throughput_raw': memory.get('total_throughput_mib', 0),
                'disk_iops_raw': disk.get('read_iops', 0),
            },
            'provider_attributes': attrs,
            'provider': provider,
            'region': region,
            'timestamp': r.get('timestamp', datetime.now().isoformat()),
        })

    return pd.DataFrame(normalized)


def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    df['cpu_single'] = df['metrics'].apply(lambda m: m.get('cpu_single_raw', 0))
    df['cpu_multi'] = df['metrics'].apply(lambda m: m.get('cpu_multi_raw', 0))
    df['mem_throughput'] = df['metrics'].apply(lambda m: m.get('mem_throughput_raw', 0))
    df['disk_iops'] = df['metrics'].apply(lambda m: m.get('disk_iops_raw', 0))

    # Normalize to 0-100
    df['single_core_score'] = (df['cpu_single'] / df['cpu_single'].max() * 100).round(1) if df['cpu_single'].max() > 0 else 0
    df['multi_core_score'] = (df['cpu_multi'] / df['cpu_multi'].max() * 100).round(1) if df['cpu_multi'].max() > 0 else 0
    df['memory_score'] = (df['mem_throughput'] / df['mem_throughput'].max() * 100).round(1) if df['mem_throughput'].max() > 0 else 0
    df['disk_score'] = (df['disk_iops'] / df['disk_iops'].max() * 100).round(1) if df['disk_iops'].max() > 0 else 0

    df['cpu_score'] = ((df['single_core_score'] + df['multi_core_score']) / 2).round(1)
    df['overall_score'] = (df['cpu_score'] * 0.40 + df['memory_score'] * 0.35 + df['disk_score'] * 0.25).round(1)

    # Guard against division by zero for pricing
    zero_price_mask = (df['price_hourly'] == 0) | (df['price_monthly'] == 0)
    if zero_price_mask.any():
        for _, row in df[zero_price_mask].iterrows():
            print(f"Warning: {row['instance_type']} has zero price, value metrics will be 0", file=sys.stderr)

    df['value_hourly'] = 0.0
    df['value_monthly'] = 0.0
    df['cpu_value_monthly'] = 0.0

    valid_price_mask = ~zero_price_mask
    df.loc[valid_price_mask, 'value_hourly'] = (df.loc[valid_price_mask, 'overall_score'] / df.loc[valid_price_mask, 'price_hourly']).round(2)
    df.loc[valid_price_mask, 'value_monthly'] = (df.loc[valid_price_mask, 'overall_score'] / df.loc[valid_price_mask, 'price_monthly']).round(2)
    df.loc[valid_price_mask, 'cpu_value_monthly'] = (df.loc[valid_price_mask, 'cpu_score'] / df.loc[valid_price_mask, 'price_monthly']).round(2)

    return df


def create_instance_summary(row: pd.Series) -> dict:
    provider_attrs = row['provider_attributes'] if isinstance(row['provider_attributes'], dict) else {}
    return {
        'id': row['instance_type'],
        'name': row['display_name'],
        'scores': {
            'single_core': row['single_core_score'],
            'multi_core': row['multi_core_score'],
            'memory': row['memory_score'],
            'disk': row['disk_score'],
            'overall': row['overall_score'],
        },
        'pricing': {
            'hourly': row['price_hourly'],
            'monthly': row['price_monthly'],
        },
        'value': row['cpu_value_monthly'],
        'specs': {
            'vcpu': row['vcpu'],
            'ram_gb': row['ram_gb'],
            'disk_gb': row['disk_gb'],
            'arch': provider_attrs.get('arch', 'Unknown'),
        },
    }


def generate_summary_data(df: pd.DataFrame, provider: str, region: str) -> dict:
    if df.empty:
        return {}

    df_sorted = df.sort_values('overall_score', ascending=False)
    labels = df_sorted['display_name'].tolist()

    return {
        'schema_version': SCHEMA_VERSION,
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'run_count': len(df),
            'currency': 'EUR',
            'provider': provider,
            'region': region,
        },
        'summary': {
            'labels': labels,
            'instances': [create_instance_summary(row) for _, row in df_sorted.iterrows()],
            'charts': {
                'single_core': df_sorted['single_core_score'].tolist(),
                'multi_core': df_sorted['multi_core_score'].tolist(),
                'memory': df_sorted['memory_score'].tolist(),
                'disk': df_sorted['disk_score'].tolist(),
                'value': df_sorted['cpu_value_monthly'].tolist(),
            }
        }
    }


def generate_detail_data(df: pd.DataFrame, provider: str, region: str) -> dict:
    if df.empty:
        return {}

    df_sorted = df.sort_values('overall_score', ascending=False)

    instances = []
    for _, row in df_sorted.iterrows():
        inst = create_instance_summary(row)
        inst['metrics'] = row['metrics']
        inst['provider_attributes'] = row['provider_attributes']
        instances.append(inst)

    return {
        'schema_version': SCHEMA_VERSION,
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'run_count': len(df),
            'currency': 'EUR',
            'provider': provider,
            'region': region,
        },
        'instances': instances,
    }


def generate_markdown_summary(df: pd.DataFrame) -> str:
    if df.empty:
        return "No benchmark results available."

    df_sorted = df.sort_values('overall_score', ascending=False)

    lines = [
        "## Performance & Value Rankings",
        "",
        "| Rank | Instance | Single | Multi | Memory | Disk | Overall | EUR/Month | Value |",
        "|------|----------|--------|-------|--------|------|---------|-----------|-------|",
    ]

    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        lines.append(
            f"| {i} | {row['display_name']} | {row['single_core_score']:.0f} | "
            f"{row['multi_core_score']:.0f} | {row['memory_score']:.0f} | {row['disk_score']:.0f} | "
            f"**{row['overall_score']:.0f}** | EUR{row['price_monthly']:.2f} | {row['value_monthly']:.1f} |"
        )

    lines.extend(["", "### Best Value (Performance per Euro)", ""])

    df_value = df.sort_values('cpu_value_monthly', ascending=False)
    for i, (_, row) in enumerate(df_value.head(3).iterrows(), 1):
        lines.append(f"{i}. **{row['display_name']}** - {row['cpu_value_monthly']:.1f} CPU points/EUR")

    return '\n'.join(lines)


def update_manifest(output_dir: str, summary_file: str, detail_file: str, metadata: dict) -> None:
    manifest_path = os.path.join(output_dir, 'manifest.json')
    MAX_MANIFEST_RUNS = 50  # Prevent manifest from growing too large

    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, IOError):
            manifest = {'schema_version': SCHEMA_VERSION, 'runs': []}
    else:
        manifest = {'schema_version': SCHEMA_VERSION, 'runs': []}

    run = {
        'id': metadata.get('run_id', datetime.now().strftime('%Y%m%d-%H%M%S')),
        'timestamp': metadata.get('generated_at', datetime.now().isoformat()),
        'provider': metadata.get('provider', 'unknown'),
        'region': metadata.get('region', 'unknown'),
        'instance_count': metadata.get('run_count', 0),
        'files': {'summary': summary_file, 'detail': detail_file}
    }

    # Update or append
    existing = [i for i, r in enumerate(manifest['runs']) if r['id'] == run['id']]
    if existing:
        manifest['runs'][existing[0]] = run
    else:
        manifest['runs'].append(run)

    manifest['runs'].sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit manifest size to prevent frontend performance issues
    if len(manifest['runs']) > MAX_MANIFEST_RUNS:
        removed = manifest['runs'][MAX_MANIFEST_RUNS:]
        manifest['runs'] = manifest['runs'][:MAX_MANIFEST_RUNS]
        print(f"Note: Trimmed {len(removed)} old runs from manifest to keep size manageable")

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def main():
    try:
        args = parse_args()

        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Input directory does not exist: {args.input}")

        os.makedirs(args.output, exist_ok=True)

        config = load_config(args.config)
        results = load_results(args.input)

        if not results:
            print("No results found!", file=sys.stderr)
            sys.exit(1)

        print(f"Loaded {len(results)} benchmark results")

        df = normalize_results(results, config, args.provider, args.region)

        if df.empty:
            print("Error: No valid data after normalization", file=sys.stderr)
            sys.exit(1)

        df = calculate_scores(df)

        timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
        summary_file = f'summary-{timestamp}.json'
        detail_file = f'detail-{timestamp}.json'

        summary_data = generate_summary_data(df, args.provider, args.region)
        detail_data = generate_detail_data(df, args.provider, args.region)
        summary_md = generate_markdown_summary(df)

        metadata = {
            'run_id': timestamp,
            'generated_at': summary_data['metadata']['generated_at'],
            'provider': args.provider,
            'region': args.region,
            'run_count': len(df),
        }

        with open(os.path.join(args.output, summary_file), 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        print(f"  [OK] {summary_file}")

        with open(os.path.join(args.output, 'benchmark-data.json'), 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        print("  [OK] benchmark-data.json")

        with open(os.path.join(args.output, detail_file), 'w') as f:
            json.dump(detail_data, f, indent=2, default=str)
        print(f"  [OK] {detail_file}")

        with open(os.path.join(args.output, 'summary.md'), 'w') as f:
            f.write(summary_md)
        print("  [OK] summary.md")

        csv_cols = ['instance_type', 'vcpu', 'ram_gb', 'disk_gb',
                   'price_monthly', 'single_core_score', 'multi_core_score',
                   'memory_score', 'disk_score', 'overall_score', 'cpu_value_monthly']
        df.to_csv(os.path.join(args.output, 'benchmark-results.csv'), columns=csv_cols, index=False)
        print("  [OK] benchmark-results.csv")

        update_manifest(args.output, summary_file, detail_file, metadata)
        print("  [OK] manifest.json")

        print("\nTop performers:")
        for i, row in df.sort_values('overall_score', ascending=False).head(3).iterrows():
            print(f"  {row['display_name']}: {row['overall_score']:.0f} (EUR{row['price_monthly']}/mo)")

        print("\nBest value:")
        for i, row in df.sort_values('cpu_value_monthly', ascending=False).head(3).iterrows():
            print(f"  {row['display_name']}: {row['cpu_value_monthly']:.1f} CPU pts/EUR")

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
