# Configuration

All instance types, specs, and pricing are defined in `config/instances.yaml`. This is the single source of truth — Terraform, Ansible, scoring, and the frontend all read from it dynamically.

## File Structure

```yaml
providers:
  <provider>:
    currency: EUR|USD           # Native currency for this provider
    default_region: <region_id>
    regions:
      <region_id>:
        name: "Human Readable Name"
    instances:
      - id: <instance_id>        # Must match the cloud provider's flavor/type ID
        name: "Display Name"
        arch: X86|ARM64
        vcpu: <number>
        ram_gb: <number>
        disk_gb: <number>
        pricing:
          hourly: <price>         # In provider's native currency
          monthly: <price>

exchange_rates:
  eur_to_usd: 1.1555            # Updated by pricing workflow
  usd_to_eur: 0.8654
  last_updated: '2026-03-20'
  source: Frankfurter API (ECB data)
```

## Current Providers

| Provider | Currency | Default Region | Instances |
|----------|----------|---------------|-----------|
| Hetzner  | EUR | fsn1 (Falkenstein) | 8 (cx23, cx33, cax11, cax21, cpx22, cpx32, ccx13, ccx23) |
| AWS      | USD | eu-central-1 (Frankfurt) | 6 (t3.micro, t3.small, t4g.micro, t4g.small, c7i-flex.large, m7i-flex.large) |
| OVHcloud | EUR | DE1 (Frankfurt) | 5 (d2-4, b3-8, c3-4, c3-8, r3-16) |

## Adding Instances

Add entries to the `instances` list. No code changes needed — everything picks them up automatically.

```yaml
# Hetzner example
- id: cx23
  name: CX23
  arch: X86
  vcpu: 2
  ram_gb: 4
  disk_gb: 40
  pricing:
    hourly: 0.0048
    monthly: 2.99

# AWS example
- id: t3.small
  name: t3.small
  arch: X86
  vcpu: 2
  ram_gb: 2
  disk_gb: 20
  pricing:
    hourly: 0.024
    monthly: 17.28

# OVHcloud example
- id: d2-4
  name: D2-4
  arch: X86
  vcpu: 2
  ram_gb: 4
  disk_gb: 50
  pricing:
    hourly: 0.0198
    monthly: 14.26
```

The `id` must match the provider's instance type/flavor name exactly (e.g. `cx23`, `t3.micro`, `d2-4`).

## Adding Regions

Add to the `regions` map. Use the provider's region code as the key.

```yaml
# Hetzner (fsn1, nbg1, hel1, ash, hil)
regions:
  fsn1:
    name: Falkenstein

# AWS
regions:
  eu-central-1:
    name: Frankfurt

# OVHcloud
regions:
  DE1:
    name: Frankfurt
```

## Adding Providers

1. Add the provider config to `instances.yaml` with `currency`, `default_region`, `regions`, and `instances`
2. Create a Terraform module at `terraform/modules/<provider>/`
3. Update the `cloud_provider` validation in `terraform/variables.tf`
4. Add the provider's credentials to GitHub Secrets
5. Add a cleanup workflow for orphaned resources

## Pricing Updates

Pricing is updated automatically by the `update-pricing` workflow, which fetches live prices from each provider's API and exchange rates from the ECB.

```bash
# Update all providers
python scripts/update_pricing.py --provider all

# Update a specific provider
python scripts/update_pricing.py --provider aws

# Dry run (no changes written)
python scripts/update_pricing.py --provider all --dry-run
```

APIs used:
- **Hetzner**: `api.hetzner.cloud/v1/pricing` (public, no auth)
- **AWS**: `api.pricing.us-east-1.amazonaws.com` (requires AWS credentials)
- **OVHcloud**: `api.ovh.com/v1/order/catalog/public/cloud` (public, no auth)
- **Exchange rates**: Frankfurter API (ECB data)

## Validation

```bash
# YAML syntax
python -c "import yaml; yaml.safe_load(open('config/instances.yaml'))"

# Terraform
cd terraform && terraform init && terraform validate
```

The `validate.yml` CI workflow checks config validity on every push and PR.
