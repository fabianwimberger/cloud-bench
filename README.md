# Cloud Bench

[![CI](https://github.com/fabianwimberger/cloud-bench/actions/workflows/validate.yml/badge.svg)](https://github.com/fabianwimberger/cloud-bench/actions)
[![codecov](https://codecov.io/gh/fabianwimberger/cloud-bench/branch/main/graph/badge.svg)](https://codecov.io/gh/fabianwimberger/cloud-bench)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Live Results](https://img.shields.io/badge/Live%20Results-View%20Dashboard-blue)](https://fabianwimberger.github.io/cloud-bench/)

A cloud instance benchmarking suite comparing CPU, memory, and disk performance across providers with cost analysis. 23 instance types across Hetzner Cloud, AWS EC2, OVHcloud, and Oracle Cloud (OCI).

## Why This Project?

Cloud instance pricing and performance vary significantly between providers and instance types. $20/month can get you vastly different compute capabilities depending on your choice. This project provides reproducible, data-driven benchmarks to make informed infrastructure decisions based on actual performance rather than marketing specs.

**Goals:**
- Compare instance types objectively using standardized benchmarks
- Factor in cost to determine real value (performance per dollar)
- Provide reproducible results that can be independently verified

## Live Dashboard

View the latest results at **[fabianwimberger.github.io/cloud-bench](https://fabianwimberger.github.io/cloud-bench/)**

Scores shown are averaged across all benchmark runs for each instance type, not just the latest run.

## Run Benchmarks Locally

Compare your own machine against the official results — no cloud credentials needed:

```bash
git clone https://github.com/fabianwimberger/cloud-bench.git
cd cloud-bench
sudo bash scripts/run-local-bench.sh
```

Runs the exact same sysbench/fio benchmarks and outputs a JSON file + terminal summary. See [docs/local-benchmark.md](docs/local-benchmark.md) for details.

## Quick Start (Cloud Benchmarks)

```bash
# Clone and configure
git clone https://github.com/fabianwimberger/cloud-bench.git
cd cloud-bench

# Hetzner Cloud
export HCLOUD_TOKEN="your-token"
./scripts/run-local.sh

# AWS
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
PROVIDER=aws ./scripts/run-local.sh

# OVHcloud
export OVH_OPENSTACK_USERNAME="user-xxxxx"
export OVH_OPENSTACK_PASSWORD="your-password"
export OVH_CLOUD_PROJECT_ID="your-project-id"
PROVIDER=ovhcloud ./scripts/run-local.sh

# Or run via GitHub Actions: Actions > Run Benchmarks
```

## How It Works

```
config/instances.yaml → Terraform → Ansible (sysbench/fio) → Python (scoring) → React Dashboard
```

**Methodology:**
- 5 runs per test, median value used for consistency
- Scores normalized 0-100 per category
- Weights: CPU 40%, Memory 35%, Disk 25%
- Raw metrics averaged across all historical runs per instance
- Cost-efficiency calculated from monthly price and composite score
- All benchmarks run on Ubuntu 24.04 in EU (Frankfurt) regions

## Configuration

Edit `config/instances.yaml` to add/remove instances:

```yaml
providers:
  hetzner:
    currency: EUR
    default_region: fsn1
    instances:
      - id: cx23
        name: CX23
        arch: X86
        vcpu: 2
        ram_gb: 4
        disk_gb: 40
        pricing:
          hourly: 0.0048
          monthly: 2.99
```

No code changes needed — Terraform, Ansible, and the frontend all pick up config changes automatically. See [docs/configuration.md](docs/configuration.md) for details.

## Features

- **Multi-provider** — Hetzner Cloud, AWS EC2, OVHcloud, OCI (23 instance types)
- **Standardized benchmarks** — CPU (sysbench), Memory (sysbench), Disk I/O (fio)
- **Metric averaging** — scores based on all historical runs, not just the latest
- **Cost analysis** — performance per dollar with EUR/USD toggle
- **Interactive dashboard** — filtering, comparison, per-instance history charts
- **Automated pricing** — live pricing from provider APIs + ECB exchange rates
- **Security-first** — fresh SSH keys per run, firewall whitelisting, automatic cleanup
- **Cost guards** — pre-run estimation blocks expensive configurations ($5 / 15 instance limit)
- **Local benchmarking** — standalone script for users to compare their own hardware

## Security

- Fresh Ed25519 SSH key generated per run, never reused
- Firewall/security group allows SSH from runner IP only
- Auto-cleanup via `if: always()` — infrastructure destroyed even if benchmarks fail
- Orphan cleanup workflows as safety net (manual trigger for all providers)

## Documentation

- [Setup Guide](docs/setup-guide.md) — credentials and first run
- [Configuration](docs/configuration.md) — instances, regions, providers
- [Architecture](docs/architecture.md) — system design and scoring
- [Data Format](docs/data-format.md) — JSON schemas
- [Cost Analysis](docs/cost-analysis.md) — per-run costs and safety nets
- [Runbook](docs/runbook.md) — troubleshooting
- [Local Benchmark](docs/local-benchmark.md) — run benchmarks on your own machine

## License

MIT License — see [LICENSE](LICENSE) file.

### Third-Party Licenses

| Component | License | Source |
|-----------|---------|--------|
| sysbench | [GPL v2+](https://github.com/akopytov/sysbench/blob/master/COPYING) | https://github.com/akopytov/sysbench |
| fio | [GPL v2](https://github.com/axboe/fio/blob/master/COPYING) | https://github.com/axboe/fio |
