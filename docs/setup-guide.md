# Setup Guide

## Prerequisites

- GitHub account
- Hetzner Cloud account

## Steps

### 1. Clone the repository

```bash
git clone https://github.com/fabianwimberger/cloud-bench.git
cd cloud-bench
```

### 2. Create a dedicated Hetzner project

In [Hetzner Console](https://console.hetzner.cloud/), create a new project (e.g. "cloud-bench"). This isolates costs and makes cleanup easy.

### 3. Generate an API token

In your project: **Security > API Tokens > Generate API Token** (Read & Write).

### 4. Add the secret to GitHub

**Repository Settings > Secrets and variables > Actions** — add `HCLOUD_TOKEN`.

### 5. Set a billing alert

In Hetzner Console, set an alert at e.g. €10 as a safety net.

### 6. Run

Go to **Actions > Run Benchmarks > Run workflow**.

## Local run

```bash
export HCLOUD_TOKEN="your-token"
./scripts/run-local.sh
```

The script auto-detects your IP for the firewall. It provisions, benchmarks, processes results, and prompts to destroy.

## Verifying

```bash
cd terraform
terraform init
terraform plan -var="run_id=test" -var="hcloud_token=$HCLOUD_TOKEN" -var='allowed_ssh_ips=["YOUR_IP/32"]'
```

## Troubleshooting

**SSH failures**: The workflow auto-whitelists the runner IP. For local runs, check that `ALLOWED_SSH_IPS` is set correctly.

**Terraform errors**: Run `terraform init` and `terraform validate`. If state is stale, `terraform state list` to inspect.

**Cleanup didn't run**: Delete resources manually in Hetzner Console, or run `terraform destroy` from the `terraform/` directory.
