# Setup Guide

## Prerequisites

- GitHub account (for Actions-based benchmarking)
- Account with one or more providers: Hetzner Cloud, AWS, OVHcloud, Oracle Cloud (OCI), Google Cloud Platform (GCP), Microsoft Azure

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
- Project ID (found in Public Cloud > Project Settings)

### 3. Add secrets to GitHub

**Repository Settings > Secrets and variables > Actions** — add:
- `OVH_OPENSTACK_USERNAME`
- `OVH_OPENSTACK_PASSWORD`
- `OVH_CLOUD_PROJECT_ID`

### 4. Set a budget alert

In OVHcloud Control Panel, set a budget alert as a safety net.

### 5. Run

Go to **Actions > Run Benchmarks > Run workflow**. Select provider `ovhcloud` and region `DE1`.

Note: OVHcloud uses the OpenStack API and does not support security groups. Instances are protected by SSH key authentication only.

## OCI (Oracle Cloud) Setup

### 1. Create an Oracle Cloud account

Sign up at [cloud.oracle.com](https://cloud.oracle.com/). New accounts get an Always Free tier plus $300 in credits for 30 days.

### 2. Create a dedicated compartment

Compartments isolate resources and let you scope permissions tightly.

**Identity & Security > Compartments > Create Compartment**:
- Name: `cloud-bench`
- Description: Cloud benchmark resources

Note the **Compartment OCID** — this is your `OCI_COMPARTMENT_ID`.

### 3. Create a dedicated user and group

**Identity & Security > Users > Create User**:
- Name: `cloud-bench`
- Description: Cloud-bench automation user

**Identity & Security > Groups > Create Group**:
- Name: `cloud-bench-group`
- Add the `cloud-bench` user to this group

### 4. Create a least-privilege policy

**Identity & Security > Policies > Create Policy** (create it in the root compartment):
- Name: `cloud-bench-policy`
- Statements (one per line):

```
Allow group cloud-bench-group to manage virtual-network-family in compartment cloud-bench
Allow group cloud-bench-group to manage instance-family in compartment cloud-bench
Allow group cloud-bench-group to read app-catalog-listing in compartment cloud-bench
Allow group cloud-bench-group to use image-family in compartment cloud-bench
```

This grants only what the Terraform module needs: VCN/subnet/security list/gateway (virtual-network-family), compute instances (instance-family), and Ubuntu image lookup (image-family, app-catalog-listing) — scoped to the `cloud-bench` compartment only.

### 5. Generate an API signing key

Navigate to the `cloud-bench` user: **Identity & Security > Users > cloud-bench > API keys > Add API key**.

Choose "Generate API key pair", download the private key (`.pem`), and note the **fingerprint**.

### 6. Collect required identifiers

| Secret | Where to find it |
|---|---|
| `OCI_TENANCY_OCID` | Profile > Tenancy — copy the OCID |
| `OCI_USER_OCID` | Identity > Users > cloud-bench — copy the OCID |
| `OCI_FINGERPRINT` | Shown after adding the API key (`aa:bb:cc:...`) |
| `OCI_PRIVATE_KEY` | The `.pem` file content (including BEGIN/END lines) |
| `OCI_COMPARTMENT_ID` | Identity > Compartments > cloud-bench — copy the OCID |

### 7. Add secrets to GitHub

**Repository Settings > Secrets and variables > Actions** — add all five secrets above.

### 8. Set a budget alert

In OCI Console, go to **Billing & Cost Management > Budgets** and create a budget at e.g. $10.

### 9. Run

Go to **Actions > Run Benchmarks > Run workflow**. Select provider `oci` and region `eu-frankfurt-1`.

## GCP Setup

### 1. Create a dedicated GCP project

In [Google Cloud Console](https://console.cloud.google.com/), create a new project (e.g., "cloud-bench"). This isolates resources and makes billing tracking easier.

### 2. Enable required APIs

Navigate to **APIs & Services > Library** and enable:
- Compute Engine API
- Cloud Billing API (for automated pricing updates)

### 3. Create a service account

**IAM & Admin > Service Accounts > Create Service Account**:
- Name: `cloud-bench`
- Description: Cloud benchmark automation

Grant the following roles:
- **Compute Admin** (for creating instances and firewall rules)
- **Compute Viewer** (read-only access to compute resources)
- **Billing Account Viewer** (for pricing data)

### 4. Create and download a service account key

**IAM & Admin > Service Accounts > cloud-bench > Keys > Add Key > Create New Key**.

Choose JSON format and download the key file.

### 5. Collect required identifiers

| Secret | Where to find it |
|---|---|
| `GCP_PROJECT_ID` | Project selector dropdown — the project ID (not name) |
| `GCP_CREDENTIALS` | The entire JSON content of the downloaded key file |

### 6. Add secrets to GitHub

**Repository Settings > Secrets and variables > Actions** — add:
- `GCP_PROJECT_ID` — the project ID string
- `GCP_CREDENTIALS` — the full JSON service account key

### 7. Set a budget alert

In GCP Console, go to **Billing > Budgets & alerts** and create a budget at e.g. $10.

### 8. Run

Go to **Actions > Run Benchmarks > Run workflow**. Select provider `gcp` and region `europe-west3`.

## Azure Setup

### 1. Create a dedicated resource group (optional but recommended)

In [Azure Portal](https://portal.azure.com/), a dedicated subscription or resource group makes cost tracking and cleanup straightforward. The Terraform module creates its own resource group per run, so no manual group creation is required.

### 2. Create a service principal

```bash
az ad sp create-for-rbac --name cloud-bench \
  --role Contributor \
  --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID>
```

This outputs `appId` (client ID), `password` (client secret), `tenant` (tenant ID). Note them — the password is shown only once.

### 3. Collect required identifiers

| Secret | Where to find it |
|---|---|
| `AZURE_SUBSCRIPTION_ID` | Azure Portal → Subscriptions — copy the Subscription ID |
| `AZURE_CLIENT_ID` | Output `appId` from the `az ad sp create-for-rbac` command |
| `AZURE_CLIENT_SECRET` | Output `password` from the `az ad sp create-for-rbac` command |
| `AZURE_TENANT_ID` | Output `tenant` from the `az ad sp create-for-rbac` command |

### 4. Add secrets to GitHub

**Repository Settings > Secrets and variables > Actions** — add all four secrets above.

### 5. Set a budget alert

In Azure Portal, go to **Cost Management + Billing > Budgets** and create a budget at e.g. $10.

### 6. Run

Go to **Actions > Run Benchmarks > Run workflow**. Select provider `azure` and region `westeurope`.

## Local Run (Cloud Provisioning)

Run the full benchmark pipeline locally (provisions cloud instances, runs benchmarks, processes results):

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

# OCI
export OCI_TENANCY_OCID="ocid1.tenancy.oc1..xxx"
export OCI_USER_OCID="ocid1.user.oc1..xxx"
export OCI_FINGERPRINT="aa:bb:cc:..."
export OCI_PRIVATE_KEY="$(cat ~/.oci/oci_api_key.pem)"
export OCI_COMPARTMENT_ID="ocid1.compartment.oc1..xxx"
PROVIDER=oci ./scripts/run-local.sh

# GCP
export GCP_PROJECT_ID="your-project-id"
export GCP_CREDENTIALS="$(cat /path/to/service-account-key.json)"
PROVIDER=gcp ./scripts/run-local.sh

# Azure
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
PROVIDER=azure ./scripts/run-local.sh
```

The script auto-detects your IP for the firewall/security group. It provisions, benchmarks, processes results, and prompts to destroy.

## Local Run (No Cloud)

To benchmark your own machine without cloud credentials:

```bash
sudo bash scripts/run-local-bench.sh
```

See [local-benchmark.md](local-benchmark.md) for details.

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

# OCI
terraform plan -var="run_id=test" -var="cloud_provider=oci" -var='allowed_ssh_ips=["YOUR_IP/32"]'

# GCP
terraform plan -var="run_id=test" -var="cloud_provider=gcp" -var='allowed_ssh_ips=["YOUR_IP/32"]'

# Azure
terraform plan -var="run_id=test" -var="cloud_provider=azure" -var='allowed_ssh_ips=["YOUR_IP/32"]'
```

## Troubleshooting

See [runbook.md](runbook.md) for common issues and fixes.
