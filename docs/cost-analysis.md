# Cost Analysis

## Per Run

A benchmark run provisions all configured instances for a single provider for ~10 minutes, then destroys them. Costs a few cents.

| Provider | Instances | Typical Cost |
|----------|-----------|-------------|
| Hetzner  | 8         | ~€0.05      |
| AWS      | 6         | ~$0.15      |
| OVHcloud | 5         | ~€0.15      |
| OCI      | 3         | ~$0.10      |
| GCP      | 5         | ~$0.15      |
| Azure    | 7         | ~$0.15      |

Exact cost depends on which instances are configured in `config/instances.yaml`. The cost-guard workflow estimates this before each run and blocks anything over $5 or 15 instances.

## Worst Case

If cleanup fails and instances keep running, the maximum hourly cost is the sum of all configured hourly prices:

| Provider | All instances hourly | All instances monthly |
|----------|---------------------|----------------------|
| Hetzner  | €0.1537             | €95.92               |
| AWS      | $0.2763             | $198.91              |
| OVHcloud | €0.2751             | €198.07              |
| OCI      | $0.1200             | $86.40               |
| GCP      | $0.5420             | $390.25              |
| Azure    | $0.8082             | $581.90              |

## Safety Nets

1. **Cost guard** — pre-run estimation blocks expensive configurations
2. **Billing alerts** — set in each provider's console (recommended: €10 / $10)
3. **Auto-cleanup** — `if: always()` in CI destroys infrastructure even on failure
4. **Orphan cleanup** — scheduled workflows terminate instances older than 2 hours
   - Hetzner: manual trigger
   - AWS: manual trigger
   - OVHcloud: manual trigger
   - OCI: manual trigger
   - GCP: manual trigger
   - Azure: manual trigger

## Provider Comparison

| | Hetzner | AWS | OVHcloud | OCI | GCP | Azure |
|---|---------|-----|----------|-----|-----|-------|
| Pricing | Simple, flat hourly/monthly | On-demand, region-dependent | Hourly consumption billing | Pay-as-you-go | Per-second billing | Per-minute billing |
| Hidden fees | None | Egress, EBS IOPS (minimal for benchmarks) | None | Egress | Egress | Egress |
| Cheapest instance | €3.99/mo (CX23) | $6.91/mo (t4g.micro) | €14.83/mo (D2-4) | $25.92/mo (A2.Flex 2/4) | $64.19/mo (e2-standard-2) | $32.83/mo (Standard_B2ls_v2) |
| Cleanup | hcloud CLI / scheduled workflow | AWS CLI / scheduled workflow | OpenStack CLI / manual workflow | OCI CLI / manual workflow | gcloud CLI / scheduled workflow | az CLI / scheduled workflow |
| Billing granularity | Hourly | Per-second | Hourly | Per-second | Per-second | Per-minute |
