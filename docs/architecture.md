# Architecture

```
config/instances.yaml          # Single source of truth for instances & pricing
        │
        ▼
┌── Terraform ──────────────┐
│  modules/hetzner/          │  Provisions servers, SSH keys, firewalls
└────────────┬──────────────┘
             ▼
┌── Ansible ────────────────┐
│  playbooks/benchmark.yml   │  Runs sysbench (CPU, RAM) + fio (Disk)
└────────────┬──────────────┘  5 runs each, takes median
             ▼
┌── Python ─────────────────┐
│  scripts/process_results.py│  Normalizes, scores, outputs JSON/CSV
└────────────┬──────────────┘
             ▼
┌── Frontend ───────────────┐
│  React + Vite              │  Dashboard on GitHub Pages
└───────────────────────────┘
```

## Benchmarks

| Component | Tool | Test |
|-----------|------|------|
| CPU | sysbench | Prime numbers to 20,000 |
| RAM | sysbench | Sequential read/write |
| Disk | fio | Random read IOPS |

## Scoring

All scores are normalized 0-100 relative to the best performer in the run.

```
CPU Score     = (Single Core + Multi Core) / 2
Overall Score = CPU * 0.40 + Memory * 0.35 + Disk * 0.25
Value Score   = CPU Score / Monthly Price (EUR)
```

## Data format

- **Summary** (~5KB): scores, pricing, specs — loads fast for the dashboard
- **Detail**: full raw metrics + `provider_attributes` for extensibility
- **Manifest**: index of all historical runs

See [data-format.md](data-format.md) for the schema.

## Security

- Fresh Ed25519 SSH key generated per run, never reused
- Firewall allows SSH from any IP (key-based auth only)
- `if: always()` cleanup in CI
- Dedicated Hetzner project recommended for isolation
