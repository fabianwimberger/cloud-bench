# Architecture

## Pipeline

```
config/instances.yaml            # Single source of truth for instances & pricing
        │
        ▼
┌── Terraform ──────────────┐
│  modules/hetzner/          │   Provisions servers, SSH keys, firewalls
│  modules/aws/              │   EC2 instances, security groups, key pairs
│  modules/ovhcloud/         │   OpenStack instances, key pairs (no security groups)
└────────────┬──────────────┘
             ▼
┌── Ansible ────────────────┐
│  playbooks/benchmark.yml   │   Runs sysbench (CPU, RAM) + fio (Disk)
└────────────┬──────────────┘   5 runs each, takes median
             ▼
┌── Python ─────────────────┐
│  process_results.py        │   Normalizes, scores, outputs JSON/CSV/Markdown
│  update_manifest.py        │   Indexes run into manifest.json
│  build_history.py          │   Builds per-instance history from all runs
│  merge_summaries.py        │   Merges providers, averages metrics across runs
└────────────┬──────────────┘
             ▼
┌── Frontend ───────────────┐
│  React + Vite + Chart.js   │   Dashboard on GitHub Pages
└───────────────────────────┘
```

## Data Persistence

All benchmark data lives on the `benchmark-data` branch:

```
data/
├── manifest.json                              # Index of all runs (schema v3.0)
└── runs/
    └── <timestamp>-<provider>-<region>/
        ├── raw/                               # Raw benchmark JSON per instance
        ├── summary.json                       # Scored summary for this run
        └── detail.json                        # Full metrics + provider attributes
```

The deploy step merges all runs into `benchmark-data.json` and `history.json` for the frontend.

## Benchmarks

| Component | Tool | Command |
|-----------|------|---------|
| CPU (single) | sysbench | `sysbench cpu --cpu-max-prime=20000 --threads=1` |
| CPU (multi) | sysbench | `sysbench cpu --cpu-max-prime=20000 --threads=<nproc>` |
| Memory read | sysbench | `sysbench memory --memory-oper=read --memory-total-size=1G` |
| Memory write | sysbench | `sysbench memory --memory-oper=write --memory-total-size=1G` |
| Disk IOPS | fio | `fio --rw=randread --bs=4k --iodepth=32 --direct=1 --runtime=20` |

All benchmarks run on Ubuntu 24.04. Each test runs 5 times, median is used.

## Scoring

Scores are normalized 0-100 relative to the best performer across all instances.

```
CPU Score     = (Single Core + Multi Core) / 2
Overall Score = CPU * 0.40 + Memory * 0.35 + Disk * 0.25
Value Score   = Overall Score / Monthly Price
```

### Metric Averaging

When multiple benchmark runs exist for an instance, raw metrics (CPU events, memory throughput, disk IOPS) are averaged across all runs before scoring. This reduces noise from single-run variance. Scores are then recalculated from the averaged metrics.

### Cross-Provider Rescaling

When merging results from multiple providers, all scores are rescaled against the global maximum so instances from different providers are directly comparable. Pricing is normalized to USD using ECB exchange rates.

## Data Formats

- **Summary** (~5KB): scores, pricing, specs — loads fast for the dashboard
- **Detail**: full raw metrics + `provider_attributes` for extensibility
- **Manifest** (v3.0): index of all historical runs with `instance_index` for lookups
- **History** (v3.0): pre-built per-instance time series for the history view

See [data-format.md](data-format.md) for full schemas.

## Security

- Fresh Ed25519 SSH key generated per run, never reused
- Firewall/security group allows SSH from runner IP only (Hetzner + AWS)
- OVHcloud does not support security groups — SSH key auth only
- `if: always()` cleanup in CI ensures infrastructure destruction
- Orphan cleanup workflows: every 6 hours (Hetzner, AWS), manual trigger (OVHcloud)
- Dedicated project/IAM user/OpenStack user recommended for isolation

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `benchmark.yml` | Manual | Full benchmark pipeline: provision → benchmark → process → deploy |
| `validate.yml` | Push/PR | CI: terraform, ansible, python (ruff/mypy/pytest), frontend, trivy |
| `pr-check.yml` | PR | Terraform format, init, validate, plan |
| `cost-guard.yml` | Called | Reusable cost estimation (blocks >$5 or >15 instances) |
| `deploy-ui.yml` | Manual | Rebuild and deploy frontend to GitHub Pages |
| `update-pricing.yml` | Manual | Fetch live pricing from provider APIs + ECB exchange rates |
| `cleanup-aws.yml` | Manual | Terminate orphaned AWS instances older than 2 hours |
| `cleanup-ovhcloud.yml` | Manual | Terminate orphaned OVHcloud instances older than 2 hours |
