# Runbook: When Things Go Wrong

## Quick Fixes

### Cleanup Failed - Resources Still Running

**Symptom**: Workflow failed, servers still show in Hetzner Console or AWS Console.

**Auto-fix**: Scheduled cleanup workflows run every 6 hours and will clean up anything older than 2 hours (Hetzner) or tagged `cloud-bench` resources (AWS).

**Manual fix (Hetzner)**:
```bash
# Install hcloud CLI
brew install hcloud  # macOS
# or download from https://github.com/hetznercloud/cli/releases

# Set your token
export HCLOUD_TOKEN="your-token"

# List cloud-bench servers
hcloud server list | grep cloud-bench

# Delete specific server
hcloud server delete <server-name>

# Or delete all cloud-bench servers
hcloud server list -o json | jq -r '.[] | select(.name | contains("cloud-bench")) | .id' | xargs -I {} hcloud server delete {}
```

**Manual fix (AWS)**:
```bash
# Using AWS CLI
export AWS_DEFAULT_REGION=eu-central-1

# List cloud-bench instances
aws ec2 describe-instances --filters "Name=tag:Project,Values=cloud-bench" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' --output table

# Terminate specific instance
aws ec2 terminate-instances --instance-ids <instance-id>

# Terminate all cloud-bench instances
aws ec2 describe-instances --filters "Name=tag:Project,Values=cloud-bench" "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].InstanceId' --output text | xargs aws ec2 terminate-instances --instance-ids
```

### SSH Connection Failures

**Symptom**: "Failed to connect to the host via ssh"

**Check**:
1. Your IP may have changed mid-run (rare but happens)
2. Hetzner's firewall may not have updated
3. Instance is still booting

**Fix**: Just re-run the workflow. The IP whitelist is regenerated each run.

### Terraform State Locked/Corrupted

**Symptom**: "Error acquiring the state lock" or weird plan output

**Fix**:
```bash
cd terraform
rm -f terraform.tfstate.lock.info
terraform init
# If state is really broken, delete it (you'll need to manually clean up resources)
rm terraform.tfstate
```

### Cost Guard Blocked My Run

**Symptom**: "Estimated cost $X exceeds limit"

**Fix**: You're trying to run too many instances at once. Either:
1. Run with fewer instances
2. Increase `MAX_COST_USD` in `.github/workflows/cost-guard.yml` (not recommended)
3. Use `skip_cost_guard: true` (not recommended unless you know what you're doing)

### Frontend Shows "Something Went Wrong"

**Symptom**: Error boundary caught an error

**Check**:
1. Open browser console (F12) for details
2. Check that `benchmark-data.json` exists in `frontend/public/data/`
3. Verify JSON is valid: `cat frontend/public/data/benchmark-data.json | jq .`

**Fix**: Re-run the process job: `python scripts/process_results.py ...`

## Emergency Stop

If you need to stop everything RIGHT NOW:

1. Go to Actions tab → Cancel any running workflows
2. **Hetzner**: Go to Hetzner Console → Delete all `cloud-bench-*` servers, SSH keys, and firewalls
3. **AWS**: Go to EC2 Console (eu-central-1) → Terminate all instances tagged `cloud-bench`, delete associated security groups and key pairs

## Preventing Issues

- **Always** wait for cleanup job to finish (green checkmark)
- Don't run multiple benchmarks simultaneously (concurrency group prevents this)
- Set a billing alert in Hetzner Console at €10 and in AWS Budgets at $10
- The orphan cleanup workflows run every 6 hours as safety net

## Getting Help

If stuck, check:
1. Workflow logs in GitHub Actions
2. Hetzner Console / AWS EC2 Console for resource status
3. `terraform/terraform.tfstate` if running locally
