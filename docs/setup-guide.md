# Setup Guide

## Prerequisites

- GitHub account
- Hetzner Cloud account, AWS account, and/or OVHcloud account

## Hetzner Setup

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

Go to **Actions > Run Benchmarks > Run workflow**. Select provider `hetzner`.

## AWS Setup

### 1. Create a dedicated IAM user

In AWS IAM, create a user (e.g. `cloud-bench`) with programmatic access. Attach a policy with permissions for:
- `ec2:*` (scoped to `cloud-bench` tagged resources if desired)
- `pricing:GetProducts` (for automated pricing updates)

### 2. Add secrets to GitHub

**Repository Settings > Secrets and variables > Actions** — add:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### 3. Set a budget alert

In AWS Budgets, create a cost budget at e.g. $10 as a safety net.

### 4. Run

Go to **Actions > Run Benchmarks > Run workflow**. Select provider `aws` and region `eu-central-1`.

## OVHcloud Setup

### 1. Create OpenStack credentials

In [OVHcloud Control Panel](https://www.ovh.com/manager/), go to **Public Cloud > Project Management > Users & Roles** and create a user with the appropriate rights.

### 2. Get OpenStack credentials

Download the OpenStack RC file or note the:
- Username (format: `user-xxxxx`)
- Password
- Project ID

### 3. Add secrets to GitHub

**Repository Settings > Secrets and variables > Actions** — add:
- `OVH_OPENSTACK_USERNAME`
- `OVH_OPENSTACK_PASSWORD`
- `OVH_CLOUD_PROJECT_ID`

### 4. Set a budget alert

In OVHcloud Control Panel, set a budget alert as a safety net.

### 5. Run

Go to **Actions > Run Benchmarks > Run workflow**. Select provider `ovhcloud` and region `DE1`.

## Local run

```bash
# Hetzner
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
```

The script auto-detects your IP for the firewall/security group. It provisions, benchmarks, processes results, and prompts to destroy.

## Verifying

```bash
cd terraform
terraform init
# Hetzner
terraform plan -var="run_id=test" -var="hcloud_token=$HCLOUD_TOKEN" -var='allowed_ssh_ips=["YOUR_IP/32"]'
# AWS
terraform plan -var="run_id=test" -var="cloud_provider=aws" -var='allowed_ssh_ips=["YOUR_IP/32"]'
# OVHcloud
terraform plan -var="run_id=test" -var="cloud_provider=ovhcloud" -var='allowed_ssh_ips=["YOUR_IP/32"]'
```

## Troubleshooting

**SSH failures**: The workflow auto-whitelists the runner IP. For local runs, check that `ALLOWED_SSH_IPS` is set correctly. AWS and OVHcloud use `ubuntu` as the SSH user (not `root`).

**Terraform errors**: Run `terraform init` and `terraform validate`. If state is stale, `terraform state list` to inspect.

**Cleanup didn't run**: Delete resources manually in Hetzner Console / AWS EC2 Console / OVHcloud Horizon, or run `terraform destroy` from the `terraform/` directory.
