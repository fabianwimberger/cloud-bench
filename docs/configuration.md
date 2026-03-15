# Configuration

All instance types, specs, and pricing are defined in `config/instances.yaml`. This is the single source of truth — the rest of the project reads from it dynamically.

## File structure

```yaml
providers:
  <provider>:
    currency: EUR|USD           # Native currency for this provider
    default_region: <region_id>
    regions:
      <region_id>:
        name: "Human Readable Name"
    instances:
      - id: <instance_id>        # Must match the cloud provider's type ID
        name: "Display Name"
        arch: X86|ARM64
        vcpu: <number>
        ram_gb: <number>
        disk_gb: <number>
        pricing:
          hourly: <price>         # In provider's native currency
          monthly: <price>

exchange_rates:
  usd_to_eur: 0.92               # Updated by pricing workflow
  eur_to_usd: 1.087
  last_updated: '2026-02-23T12:00:00'
  source: Frankfurter API (ECB data)
```

## Adding instances

Add entries to the `instances` list. No code changes needed — Terraform, Ansible, and the frontend all pick them up automatically.

```yaml
# Hetzner example
- id: cx33
  name: CX33
  arch: X86
  vcpu: 4
  ram_gb: 8
  disk_gb: 80
  pricing:
    hourly: 0.0096
    monthly: 5.988

# AWS example
- id: t3.medium
  name: t3.medium
  arch: X86
  vcpu: 2
  ram_gb: 4
  disk_gb: 20
  pricing:
    hourly: 0.0416
    monthly: 29.95
```

## Adding regions

Add to the `regions` map. Use the provider's region code as the key.

```yaml
# Hetzner
regions:
  fsn1:
    name: Falkenstein

# AWS
regions:
  eu-central-1:
    name: Frankfurt
```

## Adding providers

1. Add the provider config to `instances.yaml` with `currency` and `default_region`
2. Create a Terraform module at `terraform/modules/<provider>/`
3. Update the `cloud_provider` validation in `terraform/variables.tf`
4. Add the provider's credentials to GitHub Secrets
5. Add a cleanup workflow for orphaned resources

## Pricing updates

Pricing is updated automatically by the `update-pricing` workflow, which fetches live prices from each provider's API and updates exchange rates from the ECB.

```bash
# Update all providers
python scripts/update_pricing.py --provider all

# Update a specific provider
python scripts/update_pricing.py --provider aws
```

## Validation

```bash
python -c "import yaml; yaml.safe_load(open('config/instances.yaml'))"
cd terraform && terraform init && terraform validate
```
