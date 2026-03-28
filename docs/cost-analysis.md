# Cost Analysis

## Per Run

A benchmark run provisions all configured instances for a single provider for ~10 minutes, then destroys them. Costs a few cents.

| Provider | Instances | Typical Cost |
|----------|-----------|-------------|
| Hetzner  | 8         | ~€0.05      |
| AWS      | 6         | ~$0.15      |
| OVHcloud | 5         | ~€0.15      |
| OCI      | 3         | ~$0.10      |

Exact cost depends on which instances are configured in `config/instances.yaml`. The cost-guard workflow estimates this before each run and blocks anything over $5 or 15 instances.

## Worst Case

If cleanup fails and instances keep running, the maximum hourly cost is the sum of all configured hourly prices:

| Provider | All instances hourly | All instances monthly |
|----------|---------------------|----------------------|
| Hetzner  | €0.1167             | €72.72               |
| AWS      | $0.2792             | $198.91              |
| OVHcloud | €0.2310             | €180.72              |
| OCI      | $0.0684             | $48.51               |

## Safety Nets

1. **Cost guard** — pre-run estimation blocks expensive configurations
2. **Billing alerts** — set in each provider's console (recommended: €10 / $10)
3. **Auto-cleanup** — `if: always()` in CI destroys infrastructure even on failure
4. **Orphan cleanup** — scheduled workflows terminate instances older than 2 hours
   - Hetzner: every 6 hours (automated)
   - AWS: every 6 hours (automated)
   - OVHcloud: manual trigger
   - OCI: manual trigger

## Provider Comparison

| | Hetzner | AWS | OVHcloud | OCI |
|---|---------|-----|----------|-----|
| Pricing | Simple, flat hourly/monthly | On-demand, region-dependent | Hourly consumption billing | Pay-as-you-go |
| Hidden fees | None | Egress, EBS IOPS (minimal for benchmarks) | None | Egress |
| Cheapest instance | €2.99/mo (CX23) | $6.91/mo (t4g.micro) | €14.26/mo (D2-4) | Free tier eligible |
| Cleanup | hcloud CLI / scheduled workflow | AWS CLI / scheduled workflow | OpenStack CLI / manual workflow | OCI CLI / manual workflow |
| Billing granularity | Hourly | Per-second | Hourly | Per-second |
