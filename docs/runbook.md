# Runbook

## Cleanup Failed — Resources Still Running

**Symptom**: Workflow failed, servers still running in provider console.

**Auto-fix**: Orphan cleanup workflows run every 6 hours (Hetzner, AWS) or manual trigger (OVHcloud) and clean up anything older than 2 hours tagged `cloud-bench`.

**Manual fix (Hetzner)**:
```bash
export HCLOUD_TOKEN="your-token"

# List cloud-bench servers
hcloud server list | grep cloud-bench

# Delete all cloud-bench servers
hcloud server list -o json | jq -r '.[] | select(.name | contains("cloud-bench")) | .id' \
  | xargs -I {} hcloud server delete {}
```

**Manual fix (AWS)**:
```bash
export AWS_DEFAULT_REGION=eu-central-1

# List cloud-bench instances
aws ec2 describe-instances --filters "Name=tag:project,Values=cloud-bench" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' --output table

# Terminate all cloud-bench instances
aws ec2 describe-instances --filters "Name=tag:project,Values=cloud-bench" "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].InstanceId' --output text \
  | xargs aws ec2 terminate-instances --instance-ids
```

**Manual fix (OVHcloud)**:
```bash
# Using OpenStack CLI
export OS_AUTH_URL=https://auth.cloud.ovh.net/v3
export OS_USERNAME="user-xxxxx"
export OS_PASSWORD="your-password"
export OS_PROJECT_ID="your-project-id"
export OS_REGION_NAME=DE1

# List cloud-bench instances
openstack server list | grep cloud-bench

# Delete all cloud-bench instances
openstack server list -f value -c ID -c Name | grep cloud-bench | awk '{print $1}' \
  | xargs -I {} openstack server delete {}
```

**Manual fix (OCI)**:
```bash
# Using OCI CLI
export OCI_TENANCY_OCID="ocid1.tenancy.oc1..xxx"
export OCI_USER_OCID="ocid1.user.oc1..xxx"
export OCI_FINGERPRINT="aa:bb:cc:..."
export OCI_PRIVATE_KEY="$(cat ~/.oci/oci_api_key.pem)"
export OCI_COMPARTMENT_ID="ocid1.compartment.oc1..xxx"
export OCI_REGION="eu-frankfurt-1"

# List cloud-bench instances
oci compute instance list --compartment-id $OCI_COMPARTMENT_ID \
  --lifecycle-state RUNNING --query "data[?contains(\"display-name\", 'cloud-bench')].{Name:\"display-name\", ID:id}" --output table

# Terminate all cloud-bench instances (run for each ID)
oci compute instance terminate --instance-id <INSTANCE_OCID> --force
```

## SSH Connection Failures

**Symptom**: "Failed to connect to the host via ssh"

**Causes**:
1. Runner IP changed mid-run
2. Firewall not yet updated
3. Instance still booting (especially OVHcloud and OCI — can take longer)

**Fix**: Re-run the workflow. The IP whitelist is regenerated each run. OVHcloud does not use security groups, so SSH failures there are usually boot timing. For OCI, the benchmark job now updates security lists with the new runner IP automatically.

## Terraform State Locked/Corrupted

**Symptom**: "Error acquiring the state lock" or unexpected plan output

**Fix**:
```bash
cd terraform
rm -f terraform.tfstate.lock.info
terraform init
# If state is really broken, delete it (manually clean up resources first)
rm terraform.tfstate
```

## Cost Guard Blocked My Run

**Symptom**: "Estimated cost $X exceeds limit"

**Fix**: You're trying to run too many or too expensive instances. Either:
1. Run with fewer instances (use the `instances` input to select specific ones)
2. Use `skip_cost_guard: true` in the workflow dispatch (not recommended)

The default limits are $5 per run and 15 instances max.

## Frontend Shows "Something Went Wrong"

**Symptom**: Error boundary caught an error

**Check**:
1. Open browser console (F12) for details
2. Verify `benchmark-data.json` exists in `frontend/public/data/`
3. Validate JSON: `cat frontend/public/data/benchmark-data.json | jq .`

**Fix**: Re-run the deploy step or manually run `merge_summaries.py` and `build_history.py`.

## Pricing Out of Date

**Symptom**: Dashboard shows old prices

**Fix**: Run the pricing update workflow (Actions > Update Pricing) or manually:
```bash
python scripts/update_pricing.py --provider all
```

This fetches live prices from all provider APIs and updates exchange rates from the ECB.

## Emergency Stop

If you need to stop everything immediately:

1. Go to **Actions** tab — cancel any running workflows
2. **Hetzner**: Hetzner Console → delete all `cloud-bench-*` servers, SSH keys, firewalls
3. **AWS**: EC2 Console (eu-central-1) → terminate all `cloud-bench` tagged instances, delete security groups and key pairs
4. **OVHcloud**: Horizon Dashboard (DE1) → delete all `cloud-bench-*` instances and key pairs
5. **OCI**: OCI Console → Compute → Instances → terminate all `cloud-bench-*` instances in your compartment

## Preventing Issues

- Always wait for the cleanup job to finish (green checkmark)
- Don't run multiple benchmarks simultaneously (concurrency group prevents this in CI)
- Set billing alerts: €10 in Hetzner, $10 in AWS, €10 in OVHcloud
- Keep pricing updated — stale prices affect value calculations
