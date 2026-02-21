# Cost

## Per run

A benchmark run creates all configured instances for ~10 minutes. At current Hetzner prices this costs a few cents per run.

Exact pricing depends on which instances are configured in `config/instances.yaml`.

## Worst case

If cleanup fails and instances keep running, the maximum cost equals the sum of monthly prices for all configured instances. Check `config/instances.yaml` for current pricing.

Set a billing alert in Hetzner Console (e.g. €10) as a safety net.

## Why Hetzner

- Simple, predictable pricing
- No hidden fees (egress, API calls)
- Cheapest entry-level instances among major providers
- Good price/performance ratio
