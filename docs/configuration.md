# Configuration

All instance types, specs, and pricing are defined in `config/instances.yaml`. This is the single source of truth — the rest of the project reads from it dynamically.

## File structure

```yaml
providers:
  <provider>:
    regions:
      <region_id>:
        name: "Human Readable Name"
    instances:
      - id: <instance_id>        # Must match the cloud provider's type ID
        name: "Display Name"
        arch: "Architecture"
        vcpu: <number>
        ram_gb: <number>
        disk_gb: <number>
        pricing:
          hourly_eur: <price>
          monthly_eur: <price>
```

## Adding instances

Add entries to the `instances` list. No code changes needed — Terraform, Ansible, and the frontend all pick them up automatically.

```yaml
- id: cx33
  name: "CX33"
  arch: "Intel"
  vcpu: 4
  ram_gb: 8
  disk_gb: 80
  pricing:
    hourly_eur: 0.0083
    monthly_eur: 5.99
```

## Adding regions

Add to the `regions` map. Use the provider's region code as the key.

```yaml
regions:
  fsn1:
    name: "Falkenstein"
```

## Adding providers

1. Add the provider config to `instances.yaml`
2. Create a Terraform module at `terraform/modules/<provider>/`
3. Update the `cloud_provider` validation in `terraform/variables.tf`
4. Add the provider's credentials to GitHub Secrets

## Validation

```bash
python -c "import yaml; yaml.safe_load(open('config/instances.yaml'))"
cd terraform && terraform init && terraform validate
```
