# Cloud-Bench

[![Benchmarks](https://github.com/fabianwimberger/cloud-bench/actions/workflows/benchmark.yml/badge.svg)](https://github.com/fabianwimberger/cloud-bench/actions/workflows/benchmark.yml)
[![Validate](https://github.com/fabianwimberger/cloud-bench/actions/workflows/validate.yml/badge.svg)](https://github.com/fabianwimberger/cloud-bench/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Cloud instance benchmarking suite comparing CPU, memory, and disk performance across instance types with cost analysis.

Powered by [sysbench](https://github.com/akopytov/sysbench) and [fio](https://github.com/axboe/fio).

## Quick Start

```bash
export HCLOUD_TOKEN="your-token"
./scripts/run-local.sh
```

Or run via GitHub Actions: **Actions → Run Benchmarks**

## How It Works

```
Terraform → Ansible (sysbench/fio) → Python (scoring) → React Dashboard
```

**Methodology:** 5 runs per test, median value used. Scores normalized 0-100. Weights: CPU 40%, Memory 35%, Disk 25%.

## Requirements

- Terraform 1.10+
- Ansible 11.4+
- Python 3.13+
- Node.js 22+
- Hetzner Cloud API token

## Configuration

Edit `config/instances.yaml` to add/remove instances — no code changes needed.

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

## Cost

~10 minutes per run, costs a few cents. Infrastructure is destroyed automatically even if benchmarks fail.

**Protection:** Cost estimation before each run (blocks >$5 or >10 instances), orphan cleanup every 6 hours.

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
- Auto-cleanup via `if: always()`

See [docs/setup-guide.md](docs/setup-guide.md) for full setup instructions.

## License

MIT — see [LICENSE](LICENSE) file. Benchmarking tools: sysbench & fio (GPL).
