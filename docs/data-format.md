# Data Format

## Overview

Benchmark data is persisted on the `benchmark-data` branch and served to the frontend as static JSON.

```
data/                                    # On benchmark-data branch
├── manifest.json                        # Index of all runs (schema v3.0)
└── runs/
    └── <timestamp>-<provider>-<region>/
        ├── raw/                         # Raw benchmark JSON per instance
        ├── summary.json                 # Scored summary (schema v2.0)
        └── detail.json                  # Full metrics (schema v2.0)

frontend/public/data/                    # Built during deploy
├── benchmark-data.json                  # Merged cross-provider view (schema v2.0)
├── history.json                         # Per-instance history (schema v3.0)
└── manifest.json                        # Copy of manifest
```

## Per-Run Summary (v2.0)

~5KB per run. Provider-specific, used as input for merging.

```json
{
  "schema_version": "2.0",
  "metadata": {
    "generated_at": "2026-03-21T18:37:52Z",
    "run_count": 5,
    "currency": "EUR",
    "provider": "hetzner",
    "region": "fsn1",
    "exchange_rates": { "usd_to_eur": 0.8654, "eur_to_usd": 1.1555 }
  },
  "summary": {
    "labels": ["CX23", "CPX22", "CAX11"],
    "instances": [
      {
        "id": "CX23",
        "name": "CX23",
        "scores": {
          "single_core": 21.2,
          "multi_core": 21.0,
          "memory": 50.3,
          "disk": 77.9,
          "overall": 40.5
        },
        "metrics": {
          "cpu_single_events": 876.43,
          "cpu_multi_events": 1721.55,
          "memory_mib_per_sec": 14892.30,
          "disk_iops": 19306.27
        },
        "pricing": { "hourly": 0.0048, "monthly": 2.99 },
        "value": 13.5,
        "specs": { "vcpu": 2, "ram_gb": 4, "disk_gb": 40, "arch": "X86" }
      }
    ],
    "charts": {
      "single_core": [21.2, 100, 77.5],
      "multi_core": [21.0, 100, 77.4],
      "memory": [50.3, 100, 51.1],
      "disk": [77.9, 100, 88.1],
      "value": [13.5, 13.9, 19.6]
    }
  }
}
```

## Per-Run Detail (v2.0)

Full data including raw metrics and system info.

```json
{
  "schema_version": "2.0",
  "metadata": { "...": "same as summary" },
  "instances": [
    {
      "id": "CX23",
      "scores": { "...": "same as summary" },
      "pricing": { "...": "same as summary" },
      "specs": { "...": "same as summary" },
      "metrics": {
        "cpu_single_raw": 876.43,
        "cpu_multi_raw": 1721.55,
        "mem_read_raw": 8521.41,
        "mem_write_raw": 6370.89,
        "mem_throughput_raw": 14892.30,
        "disk_iops_raw": 19306.27
      },
      "provider_attributes": {
        "arch": "x86_64",
        "os": "Ubuntu 24.04",
        "kernel": "6.8.0-90-generic",
        "vcpu": 2,
        "memory_mb": 3961
      }
    }
  ]
}
```

## Merged Benchmark Data (v2.0)

Cross-provider view built by `merge_summaries.py`. This is what the dashboard loads.

- Raw metrics are **averaged** across all historical runs per instance
- Scores are **rescaled** against the global maximum across all providers
- Pricing is **normalized to USD**

```json
{
  "schema_version": "2.0",
  "metadata": {
    "generated_at": "2026-03-21T19:00:00Z",
    "run_count": 19,
    "currency": "USD",
    "providers": ["hetzner", "aws", "ovhcloud"],
    "exchange_rates": { "usd_to_eur": 0.8654, "eur_to_usd": 1.1555 }
  },
  "summary": {
    "labels": ["CX23", "t3.micro", "D2-4", "..."],
    "instances": [
      {
        "id": "CX23",
        "provider": "hetzner",
        "region": "fsn1",
        "scores": { "single_core": 21.2, "multi_core": 21.0, "memory": 50.3, "disk": 77.9, "overall": 40.5 },
        "metrics": { "cpu_single_events": 876.43, "cpu_multi_events": 1721.55, "memory_mib_per_sec": 14892.30, "disk_iops": 19306.27 },
        "pricing": { "hourly": 0.0055, "monthly": 3.45 },
        "value": 11.7,
        "specs": { "vcpu": 2, "ram_gb": 4, "disk_gb": 40, "arch": "X86" }
      }
    ]
  }
}
```

## Manifest (v3.0)

Index of all historical runs. Persisted on the `benchmark-data` branch.

```json
{
  "schema_version": "3.0",
  "runs": [
    {
      "id": "2026-03-21T18:37:52-hetzner-fsn1",
      "timestamp": "2026-03-21T18:37:52",
      "provider": "hetzner",
      "region": "fsn1",
      "instances": ["CX23", "CX33", "CAX11"],
      "files": {
        "summary": "data/runs/2026-03-21T18:37:52-hetzner-fsn1/summary.json",
        "detail": "data/runs/2026-03-21T18:37:52-hetzner-fsn1/detail.json"
      }
    }
  ],
  "instance_index": {
    "CX23": ["2026-03-21T18:37:52-hetzner-fsn1"],
    "CX33": ["2026-03-21T18:37:52-hetzner-fsn1"]
  }
}
```

## History (v3.0)

Pre-built per-instance history for the dashboard's history view. Built by `build_history.py`.

```json
{
  "schema_version": "3.0",
  "generated_at": "2026-03-21T19:00:00Z",
  "instances": {
    "CX23": {
      "provider": "hetzner",
      "specs": { "vcpu": 2, "ram_gb": 4, "arch": "X86" },
      "runs": [
        {
          "timestamp": "2026-03-21T17:11:43",
          "region": "fsn1",
          "scores": { "single_core": 21.2, "multi_core": 21.0, "memory": 50.3, "disk": 77.9, "overall": 40.5 },
          "metrics": { "cpu_single_raw": 876.43, "cpu_multi_raw": 1721.55, "mem_throughput_raw": 14892.30, "disk_iops_raw": 19306.27 },
          "pricing": { "hourly": 0.0048, "monthly": 2.99 }
        }
      ]
    }
  }
}
```

## `provider_attributes`

Extensible field for provider-specific data. No schema changes needed when adding new providers — include whatever fields are relevant (architecture, OS, kernel, burstable flags, etc.).

## Currency

Prices are stored in the provider's native currency (EUR for Hetzner/OVHcloud, USD for AWS). Exchange rates from ECB are included in metadata. The merged `benchmark-data.json` normalizes everything to USD. The frontend allows toggling between EUR and USD.
