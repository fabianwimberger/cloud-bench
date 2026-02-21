# Cloud Bench

[![CI](https://github.com/fabianwimberger/cloud-bench/actions/workflows/validate.yml/badge.svg)](https://github.com/fabianwimberger/cloud-bench/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[Live Results →](https://fabianwimberger.github.io/cloud-bench/)**

A cloud instance benchmarking suite comparing CPU, memory, and disk performance across instance types with cost analysis.

Powered by [sysbench](https://github.com/akopytov/sysbench) and [fio](https://github.com/axboe/fio).

## Why This Project?

Cloud instance pricing and performance characteristics vary significantly between providers and instance types. $20/month can get you vastly different compute capabilities depending on your choice. This project provides reproducible, data-driven benchmarks to make informed infrastructure decisions based on actual performance rather than marketing specifications.

**Goals:**
- Compare instance types objectively using standardized benchmarks
- Factor in cost to determine real value (performance per dollar)
- Provide reproducible results that can be independently verified

## Features

- **Multi-provider support** — currently Hetzner Cloud, extensible for AWS, GCP, Azure
- **Standardized benchmarks** — CPU (sysbench), Memory (sysbench), Disk I/O (fio)
- **Cost analysis** — performance per dollar across instance types
- **Interactive dashboard** — React-based visualization of results
- **Automated infrastructure** — Terraform for provisioning, Ansible for execution
- **Security-first** — fresh SSH keys per run, automatic cleanup

## Quick Start

```bash
# Clone and configure
git clone https://github.com/fabianwimberger/cloud-bench.git
cd cloud-bench

# Set your API token
export HCLOUD_TOKEN="your-token"

# Run benchmarks locally
./scripts/run-local.sh

# Or run via GitHub Actions: Actions → Run Benchmarks
```

## How It Works

```
Terraform → Ansible (sysbench/fio) → Python (scoring) → React Dashboard
```

**Methodology:**
- 5 runs per test, median value used for consistency
- Scores normalized 0-100 per category
- Weights: CPU 40%, Memory 35%, Disk 25%
- Cost-efficiency calculated from monthly price and composite score

## Configuration

Edit `config/instances.yaml` to add/remove instances:

```yaml
providers:
  hetzner:
    instances:
      - id: cx23
        name: "CX23"
        arch: "Intel"
        vcpu: 2
        ram_gb: 4
        disk_gb: 40
        pricing:
          hourly_eur: 0.0050
          monthly_eur: 3.59
```

## Project Structure

| Component | Location |
|-----------|----------|
| Instance configs | `config/instances.yaml` |
| Infrastructure | `terraform/` |
| Benchmarks | `ansible/playbooks/benchmark.yml` |
| Result processing | `scripts/process_results.py` |
| Dashboard | `frontend/` |
| Documentation | `docs/` |

## Security

- Fresh Ed25519 SSH key generated per run, never reused
- Auto-cleanup via `if: always()` — infrastructure destroyed even if benchmarks fail
- Cost guard — estimation before each run blocks expensive configurations

## Cost

~10 minutes per run, costs a few cents. Infrastructure is destroyed automatically even if benchmarks fail.

**Protection:**
- Cost estimation before each run (blocks >$5 or >10 instances)
- Orphan cleanup every 6 hours

## License

MIT License — see [LICENSE](LICENSE) file.

### Benchmark Tools

This project uses [sysbench](https://github.com/akopytov/sysbench) and [fio](https://github.com/axboe/fio), both licensed under the GPL.
