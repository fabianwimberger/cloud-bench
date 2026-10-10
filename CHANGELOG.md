# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixes

- Hetzner and UpCloud servers accept SSH only from the runner addresses instead of from any address; the benchmark job adds its own address before connecting.
- The benchmark workflows wait until every instance answers over SSH. The check used to pass while hosts were still unreachable.
- `run-local.sh` runs Terraform in the selected provider's directory and passes only the variables it declares.

### Dependencies

- Terraform 1.10.5 → 1.16.5 in the workflows.

## [v2.4.0] - 2026-10-10

Adds UpCloud as a seventh provider, with four Starter and Premium plans in Frankfurt.

### Features

- Add UpCloud as a provider: `STARTER-2xCPU-4GB`, `STARTER-4xCPU-8GB`, `PREMIUM-2xCPU-4GB`, and `PREMIUM-4xCPU-8GB` in `de-fra1`, priced in EUR. Each server runs on the storage its plan includes, Standard for Starter and MaxIOPS for Premium.
- UpCloud is selectable in the benchmark workflows and in `run-local.sh`, with `UPCLOUD_USERNAME` and `UPCLOUD_PASSWORD` as credentials.
- The pricing update reads UpCloud's price list. It needs the same credentials and an account billed in EUR, and skips UpCloud without them.
- The cost estimate charges a full hour per UpCloud server, because plans are billed per started hour.
- Add a manual cleanup workflow that deletes leftover UpCloud benchmark servers together with their storage.

### Fixes

- Update the EUR/USD exchange rate used for cost comparison.

### Testing

- All four UpCloud plans were provisioned, benchmarked, and removed through the benchmark workflow, and the pricing update was run against UpCloud's live price list.

### Dependencies

- Ruff 0.16.9 → 0.16.10.
- source-map-js 1.2.1 → 1.2.2 in the dashboard.

### Documentation & Links

- [README](https://github.com/fabianwimberger/cloud-bench#readme)
- [Setup guide](https://github.com/fabianwimberger/cloud-bench/blob/main/docs/setup-guide.md)
- [Full changelog](https://github.com/fabianwimberger/cloud-bench/compare/v2.3.3...v2.4.0)

## [v2.3.3] - 2026-10-03

Updates the Python linter while preserving the existing lint rules.

### Fixes

- Declare the existing lint rule selection explicitly so dependency updates preserve the same checks.

### Dependencies

- Update Ruff from 0.15.22 to 0.16.9.

### Documentation & Links

- [README](https://github.com/fabianwimberger/cloud-bench#readme)
- [Full changelog](https://github.com/fabianwimberger/cloud-bench/compare/v2.3.2...v2.3.3)

## [v2.3.2] - 2026-10-03

Centralizes Python dependency declarations for local runs and workflows.

### Fixes

- Install local result-processing dependencies in a project virtual environment before provisioning starts.
- Run validation tests with the active Python interpreter.

### Dependencies

- Declare runtime and development dependencies in `pyproject.toml` for installation and dependency updates.

### Testing

- Run full checks for pull requests to develop.
- Use the project virtual environment for local lint and test commands.

### Documentation & Links

- [README](https://github.com/fabianwimberger/cloud-bench#readme)
- [Full changelog](https://github.com/fabianwimberger/cloud-bench/compare/v2.3.1...v2.3.2)

## [v2.3.1] - 2026-10-03

Updates cloud SDKs, dashboard build dependencies and Python test dependencies.

### Dependencies

- Bump boto3 from 1.43.92 to 1.43.108
- Bump google-cloud-billing from 1.20.0 to 1.21.0
- Bump pandas from 3.0.5 to 3.0.6
- Bump vite from 8.3.0 to 8.3.2
- Bump pytest from 9.0.3 to 9.1.1
- Bump pytest-cov from 6.0.0 to 7.1.0

### Documentation & Links

- [README](https://github.com/fabianwimberger/cloud-bench#readme)
- [Full changelog](https://github.com/fabianwimberger/cloud-bench/compare/v2.3.0...v2.3.1)

## [v2.3.0] - 2026-09-19

Adds a Hetzner orphan cleanup workflow and corrects the benchmark summary and documentation.

### Features

- Add a Hetzner orphan cleanup workflow that removes leftover benchmark servers and floating IPs

### Fixes

- Remove a dead PR-only step from the benchmark summary that ran outside pull requests
- Correct the documented instance count and orphan-cleanup behaviour

### Dependencies

- Bump boto3 from 1.43.77 to 1.43.92
- Bump numpy from 2.5.1 to 2.5.3
- Bump vite from 8.2.1 to 8.3.0
- Bump react and react-dom from 19.2.8 to 19.3.0

### Documentation & Links

- [README](https://github.com/fabianwimberger/cloud-bench#readme)

## [v2.2.1] - 2026-08-15

Cloud-Bench fixes a currency display bug, isolates cloud provider credentials so one broken secret can't block every other provider, and corrects Hetzner's cost estimate for its full-hour billing.

### Fixes

- Store benchmark pricing in its native currency throughout the pipeline and convert only at display time, fixing prices that fluctuated between runs due to exchange-rate drift
- Give each cloud provider its own isolated Terraform configuration, so one provider's broken credentials no longer block benchmark runs for every other provider
- Bill Hetzner runs a full hour in cost estimates, matching its actual hourly-rounded billing
- Bump nanoid to fix a high-severity npm audit finding

### Documentation & Links

- [README](https://github.com/fabianwimberger/cloud-bench#readme)

## [v2.2.0] - 2026-05-10

Cloud-Bench now includes a broader Azure benchmark set and a more reliable benchmark runner path for quota-limited Azure runs.

### Features

- Add seven Azure benchmark candidates covering burstable, general-purpose, memory-oriented, and ARM64 VM families
- Include current OVHcloud, GCP, and Azure benchmark results in the published data set

### Fixes

- Pass benchmark instance selections through Terraform variable files to preserve exact instance IDs
- Guard Azure benchmark runs against regional core quota limits before provisioning
- Retry Azure cleanup after resource-release delays so teardown completes reliably

### Documentation & Links

- [README](https://github.com/fabianwimberger/cloud-bench#readme)

## [v2.1.1] - 2026-05-09

Cloud-Bench now restores the Azure benchmark path and dashboard runtime after the previous release.

### Fixes

- Run piped benchmark shell commands with Bash so `pipefail` works on benchmark hosts
- Fix the dashboard initialization order that caused the production bundle to fail at runtime
- Keep merged dashboard scoring aligned with provider scoring weights
- Pass benchmark summaries to GitHub Script through the environment instead of interpolating them into JavaScript
- Reuse the validated runner IP when updating OCI security lists
- Stop suppressing `benchmark-all` Terraform destroy failures

### Documentation & Links

- [README](https://github.com/fabianwimberger/cloud-bench#readme)

## [v2.1.0] - 2026-05-09

Value calculation improvements and benchmark robustness fixes.

### Features
- Disk toggle for value calculation — include/exclude disk costs in provider comparison
- Multi-select architecture and provider filtering in the UI
- Fix footer padding

### Fixes
- Add pipefail to benchmark shell tasks for early error detection
- Harden exchange-rate error handling
- Fix ruff formatting

### Documentation & Links
- https://github.com/fabianwimberger/cloud-bench

## [v2.0.0] - 2026-05-03

Adds Microsoft Azure and Google Cloud Platform as fifth and sixth providers, completing big-three hyperscaler coverage alongside Hetzner, OVHcloud, and Oracle Cloud.

### Providers & Instances

Now benchmarking **29 instance types** across **6 cloud providers**.

| Provider | Instances |
|----------|-----------|
| Hetzner Cloud | CX23, CX33, CAX11, CAX21, CPX22, CPX32, CCX13, CCX23 |
| AWS EC2 | t3.micro, t3.small, t4g.micro, t4g.small, c7i-flex.large, m7i-flex.large |
| OVHcloud | D2-4, B3-8, C3-4, C3-8, R3-16 |
| Oracle Cloud (OCI) | E5.Flex 1/4, Standard3.Flex 1/4, A2.Flex 2/4 |
| **Google Cloud (new)** | **e2/n2/n2d/t2d/c4a-standard-2** |
| **Microsoft Azure (new)** | **Standard_D2as_v7, Standard_D2ps_v6** |

### New Features

- **Microsoft Azure** — Terraform module, Retail Prices API pricing, cleanup workflow, dashboard badge
- **Google Cloud Platform** — Terraform module, Cloud Billing API pricing, hyperdisk auto-selection, cleanup workflow, dashboard badge
- Dynamic cost guard derived from `instances.yaml`
- Frontend: per-instance storage-included indicator and redesigned providers stat card

### Dependencies

- Bump `vite` from 8.0.9 to 8.0.10
- Bump `boto3` from 1.42.91 to 1.42.96
- Bump `aquasecurity/trivy-action` from 0.35.0 to 0.36.0

### Documentation & Links

- [Docs](https://github.com/fabianwimberger/cloud-bench/tree/main/docs)
- [Dashboard](https://fabianwimberger.github.io/cloud-bench/)
- [Setup Guide](https://github.com/fabianwimberger/cloud-bench/blob/main/docs/setup-guide.md)

## [v1.1.2] - 2026-04-25

Test coverage additions, README restructuring, and routine dependency updates.

### Fixes

- Removed misleading 'Encrypted' label and updated README section checks

### Tests

- Added coverage for `validate.validate_documentation`

### Documentation

- Added pipeline diagram
- Replaced why-this-project with a Background section
- Reordered README so Features sit above Quick Start
- Consolidated Quick Start into Local and Cloud subsections
- Dropped redundant live-results header badge (dashboard has its own section)
- Fixed cleanup-schedule description (manual trigger)

### Dependencies

- Bump boto3 from 1.42.83 to 1.42.91
- Bump vite from 8.0.4 to 8.0.9
- Bump react and react-dom from 19.2.4 to 19.2.5
- Bump pytest from 8.3.5 to 9.0.3 in /tests
- Bump actions/upload-pages-artifact from 4 to 5
- Bump actions/github-script from 8 to 9

### Chores

- Added community health files

### Documentation & Links

- [Docs](https://github.com/fabianwimberger/cloud-bench/tree/main/docs)
- [Dashboard](https://fabianwimberger.github.io/cloud-bench/)

## [v1.1.1] - 2026-04-06

Pricing fixes, test coverage reporting, and updated instance pricing across all providers.

### Fixes

- Fixed main page showing stale pricing (used oldest run instead of newest)
- Fixed history view displaying EUR prices as USD without conversion
- Updated instance pricing from all cloud provider APIs (Hetzner April 2026 price changes)

### Testing

- Added codecov coverage reporting to CI
- Added tests for Python scripts (`process_results`, `estimate_cost`, `update_pricing`, `build_history`, `update_manifest`)

### Dependencies

- Bump boto3 from 1.42.73 to 1.42.83
- Bump numpy from 2.4.3 to 2.4.4
- Bump pandas from 3.0.1 to 3.0.2
- Bump requests from 2.33.0 to 2.33.1
- Bump vite from 8.0.1 to 8.0.4
- Bump actions/deploy-pages from 4 to 5

### Documentation & Links

- [Docs](https://github.com/fabianwimberger/cloud-bench/tree/main/docs)
- [Dashboard](https://fabianwimberger.github.io/cloud-bench/)

## [v1.1.0] - 2026-03-28

Add Oracle Cloud Infrastructure (OCI) as fourth provider, parallel benchmark workflow, and security improvements.

### Providers & Instances

Now benchmarking **22 instance types** across **4 cloud providers**.

| Provider | Instances |
|----------|-----------|
| Hetzner Cloud | CX23, CX33, CAX11, CAX21, CPX22, CPX32, CCX13, CCX23 |
| AWS EC2 | t3.micro, t3.small, t4g.micro, t4g.small, c7i-flex.large, m7i-flex.large |
| OVHcloud | D2-4, B3-8, C3-4, C3-8, R3-16 |
| **OCI (new)** | **E5.Flex 1/4, Standard3.Flex 1/4, A2.Flex 2/4** |

### New Features

- **Oracle Cloud Infrastructure** — Terraform module, pricing via APEX API, cleanup workflow, and least-privilege IAM guide
- **Parallel benchmark workflow** — run all providers simultaneously via `benchmark-all`
- **OCI provider badge and filter** in dashboard with hover tooltips

### Security

- Provider secrets passed via `TF_VAR` env vars instead of CLI args
- Replaced deprecated safety CLI with `pip-audit` for dependency scanning
- Bumped `requests` to 2.33.0 (CVE-2026-25645)

### Fixes

- Wait for cloud-init on OVHcloud to prevent apt lock hangs
- Upgraded Ansible from 11.4.0 to 13.5.0
- Silenced `INJECT_FACTS_AS_VARS` deprecation warning
- Specific error messages for data loading failures in frontend
- Resolved picomatch high severity vulnerability

### Dependencies

- Bump vite from 8.0.0 to 8.0.1
- Bump requests from 2.32.5 to 2.33.0

### Documentation & Links

- [Docs](https://github.com/fabianwimberger/cloud-bench/tree/main/docs)
- [Dashboard](https://fabianwimberger.github.io/cloud-bench/)
- [OCI Setup Guide](https://github.com/fabianwimberger/cloud-bench/blob/main/docs/setup-guide.md)

## [v1.0.0] - 2026-03-22

## Cloud Bench v1.0.0

**The first official release of an open-source cloud instance benchmarking suite.**

Compare CPU, memory, and disk performance across **19 instance types** from **Hetzner Cloud**, **AWS EC2**, and **OVHcloud** — including cost analysis and an interactive dashboard.

### Providers & Instances

| Provider        | Instances |
|-----------------|----------|
| **Hetzner Cloud** | CX23, CX33, CAX11, CAX21, CPX22, CPX32, CCX13, CCX23 |
| **AWS EC2**       | t3.micro, t3.small, t4g.micro, t4g.small, c7i-flex.large, m7i-flex.large |
| **OVHcloud**      | D2-4, B3-8, C3-4, C3-8, R3-16 |

### Benchmarks

| Test                | Tool     | Parameters |
|---------------------|----------|------------|
| CPU (single-thread) | sysbench | `--cpu-max-prime=20000 --threads=1` |
| CPU (multi-thread)  | sysbench | `--cpu-max-prime=20000 --threads=<nproc>` |
| Memory (read/write) | sysbench | `--memory-total-size=1G` |
| Disk IOPS           | fio      | `randread bs=4k iodepth=32 runtime=20s` |

### Dashboard

**[View live dashboard](https://fabianwimberger.github.io/cloud-bench/)**
- Interactive filtering, sorting, and side-by-side comparison
- Per-instance history with performance charts & raw metrics
- EUR/USD toggle with live ECB exchange rates

### Infrastructure

- **Fully automated** — Terraform + Ansible + Python scoring
- **Cost guards** — blocks runs over **$5** or **15 instances**
- **Security** — ephemeral SSH keys, firewall whitelisting, auto cleanup
- **Pricing** — auto-updated via Hetzner, AWS, and OVH APIs

### Run Benchmarks Locally

Compare your own machine against official results — no cloud credentials required:

```bash
git clone https://github.com/fabianwimberger/cloud-bench.git
cd cloud-bench
sudo bash scripts/run-local-bench.sh
```

### Documentation & Links

- Docs: https://github.com/fabianwimberger/cloud-bench/tree/main/docs
- Dashboard: https://fabianwimberger.github.io/cloud-bench/
- Local Bench Guide: https://github.com/fabianwimberger/cloud-bench/blob/main/docs/local-benchmark.md
