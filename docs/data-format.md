# Data Format (v2.0)

## Output files

```
frontend/public/data/
├── benchmark-data.json          # Latest summary (used by dashboard)
├── summary-YYYYMMDD-HHMMSS.json # Historical summaries
├── detail-YYYYMMDD-HHMMSS.json  # Full historical data with raw metrics
├── manifest.json                # Index of all runs
├── summary.md                   # Markdown summary
└── benchmark-results.csv        # CSV export
```

## Summary format

~5KB, used by the dashboard landing page.

```json
{
  "schema_version": "2.0",
  "metadata": {
    "generated_at": "2026-02-21T09:15:00Z",
    "run_count": 3,
    "currency": "EUR",
    "provider": "hetzner",
    "region": "fsn1"
  },
  "summary": {
    "labels": ["CPX22 (AMD EPYC)", "CAX11 (ARM64)", "CX23 (Intel)"],
    "instances": [
      {
        "id": "CPX22",
        "name": "CPX22 (AMD EPYC)",
        "scores": { "single_core": 100, "multi_core": 100, "memory": 100, "disk": 100, "overall": 100 },
        "pricing": { "hourly": 0.0100, "monthly": 7.19 },
        "value": 13.91,
        "specs": { "vcpu": 2, "ram_gb": 4, "disk_gb": 80, "arch": "AMD EPYC" }
      }
    ],
    "charts": {
      "single_core": [100, 77.5, 21.2],
      "multi_core": [100, 77.4, 21.0],
      "memory": [100, 51.1, 50.3],
      "disk": [100, 88.1, 77.9],
      "value": [13.91, 19.59, 5.88]
    }
  }
}
```

## Detail format

Full data including raw metrics and system info.

```json
{
  "schema_version": "2.0",
  "metadata": { "..." : "same as summary" },
  "instances": [
    {
      "id": "CPX22",
      "scores": { "..." : "same as summary" },
      "pricing": { "..." : "same as summary" },
      "specs": { "..." : "same as summary" },
      "metrics": {
        "cpu_single_raw": 1643.35,
        "cpu_multi_raw": 3274.31,
        "mem_read_raw": 17291.41,
        "mem_write_raw": 12964.65,
        "mem_throughput_raw": 30256.06,
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

## Manifest

Index for browsing historical runs.

```json
{
  "schema_version": "2.0",
  "runs": [
    {
      "id": "2026-02-21-091512",
      "timestamp": "2026-02-21T09:15:12Z",
      "provider": "hetzner",
      "region": "fsn1",
      "instance_count": 3,
      "files": {
        "summary": "summary-2026-02-21-091512.json",
        "detail": "detail-2026-02-21-091512.json"
      }
    }
  ]
}
```

## `provider_attributes`

Extensible field for provider-specific data. No schema changes needed when adding new providers — just include whatever fields are relevant.
