# Cost

## Per run

A benchmark run creates all configured instances for a single provider for ~10 minutes. This costs a few cents per run.

Exact pricing depends on which instances are configured in `config/instances.yaml`.

| Provider | Typical run cost | Currency |
|----------|-----------------|----------|
| Hetzner  | ~€0.05          | EUR      |
| AWS      | ~$0.15          | USD      |
| OVHcloud | ~€0.15          | EUR      |

## Worst case

If cleanup fails and instances keep running, the maximum cost equals the sum of hourly prices for all configured instances. Check `config/instances.yaml` for current pricing.

**Safety nets:**
- Set a billing alert in Hetzner Console (e.g. €10)
- Set a budget alert in AWS Budgets (e.g. $10)
- Set a budget alert in OVHcloud Control Panel (e.g. €10)
- Orphan cleanup workflows run every 6 hours (Hetzner, AWS) or manual trigger (OVHcloud) as safety net

## Provider comparison

| | Hetzner | AWS | OVHcloud |
|---|---------|-----|----------|
| Pricing model | Simple, predictable | On-demand, region-dependent | Simple, hourly/monthly |
| Hidden fees | None | Egress, EBS IOPS (minimal for benchmarks) | None |
| Entry-level cost | ~€3.50/mo (CX23) | ~$24/mo (t4g.medium) | ~€20/mo (C3-4) |
| Cleanup | hcloud CLI / scheduled workflow | AWS CLI / scheduled workflow | OpenStack CLI / manual workflow |
