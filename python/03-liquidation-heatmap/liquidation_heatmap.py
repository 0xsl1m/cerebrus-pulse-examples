"""
Liquidation Heatmap - see where leveraged positions would be liquidated.

Shows the API's estimated liquidation clusters by leverage tier, above price
(shorts) and below it (longs), with the cascade risk and nearest cluster.
The zones are estimates, built from open interest, leverage tiers, funding
skew and a 24h VWAP entry, not from actual positions.

Cost: about $0.03 USDC per coin.
      --dry-run is free: it checks /health and prints what a paid run would
      cost. The heatmap has no free equivalent.

Paying needs the pay extra and a dedicated, low-balance Base wallet:

    pip install "cerebrus-pulse[pay]>=0.4"
    export CEREBRUS_WALLET_KEY="<private key of that wallet>"

Usage:
    python liquidation_heatmap.py --dry-run BTC
    python liquidation_heatmap.py BTC
    python liquidation_heatmap.py ETH --json
"""

import argparse
import json
import os
import sys

from cerebrus_pulse import (
    INDICATIVE_PRICES_USD,
    CerebrusPulse,
    CerebrusPulseError,
    PaymentRequired,
)

BAR_WIDTH = 20


def make_client():
    """A client that pays when CEREBRUS_WALLET_KEY is set, else one that reports prices."""
    key = os.environ.get("CEREBRUS_WALLET_KEY")
    return CerebrusPulse(wallet_key=key) if key else CerebrusPulse()


def explain_payment(e):
    print(f"\n  Not paid: {e.detail}")
    for term in e.terms:
        print(f"  The API asks ${term.price_usd} USDC on {term.network}, paid to {term.pay_to}")


def display_heatmap(liq):
    price = "-" if liq.price is None else f"${liq.price:,.2f}"
    print(f"\n{'=' * 64}")
    print(f"  {liq.coin} Liquidation Heatmap (estimated)")
    print(f"  Price: {price}")
    print(f"{'=' * 64}")

    zones = liq.long_zones + liq.short_zones
    largest = max((z.estimated_liq_usd for z in zones), default=0)

    def row(side, z):
        bar = "#" * max(1, round(BAR_WIDTH * z.estimated_liq_usd / largest)) if largest else ""
        print(f"  {side:<6s}{z.price:>14,.2f} {z.leverage:>5s} "
              f"{z.estimated_liq_usd:>16,.0f} {z.proximity_pct:>6.2f}%  {bar}")

    print(f"\n  {'Side':<6s}{'Liq price':>14s} {'Lev':>5s} {'Est. liq $':>16s} {'Away':>7s}")
    print(f"  {'-' * 62}")
    for z in sorted(liq.short_zones, key=lambda z: z.price, reverse=True):
        row("short", z)
    print(f"  {'':6s}{price:>14s}  <- price now")
    for z in sorted(liq.long_zones, key=lambda z: z.price, reverse=True):
        row("long", z)

    s = liq.summary
    print(f"\n  Cascade risk:       {s.cascade_risk}")
    print(f"  Long:short split:   {s.long_short_ratio}")
    print(f"  Within 5% of price: ${s.total_at_risk_5pct:,.0f}")
    nc = s.nearest_cluster
    if nc:
        print(f"  Nearest cluster:    {nc.get('side')} liquidations at ${nc.get('price', 0):,.2f}, "
              f"{nc.get('distance_pct')}% away (about ${nc.get('estimated_volume', 0):,.0f})")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Estimated liquidation clusters for a coin.")
    parser.add_argument("coins", nargs="*", default=["BTC"], help="coin tickers (default BTC)")
    parser.add_argument("--json", action="store_true", help="print the raw API response")
    parser.add_argument("--dry-run", action="store_true",
                        help="free: check /health and show the cost, never pay")
    args = parser.parse_args(argv)
    coins = [c.upper() for c in args.coins]
    cost = INDICATIVE_PRICES_USD["liquidations"] * len(coins)

    if args.dry_run:
        try:
            health = CerebrusPulse().health()
        except CerebrusPulseError as e:
            print(f"API check failed: {e}")
            return 1
        print(f"API status: {health.get('status')} (version {health.get('version')})")
        print(f"A paid run would call liquidations() for {', '.join(coins)}: about ${cost} USDC.")
        return 0

    try:
        client = make_client()
    except (ImportError, ValueError) as e:
        print(f"Cannot set up payment: {e}")
        return 1
    if not args.json:
        print(f"{len(coins)} liquidations call(s), about ${cost} USDC.")

    status = 0
    for coin in coins:
        try:
            liq = client.liquidations(coin)
        except PaymentRequired as e:  # also PaymentBlocked: a spend limit said no
            explain_payment(e)
            print("  Set CEREBRUS_WALLET_KEY to pay, or run with --dry-run.")
            return 2
        except CerebrusPulseError as e:
            print(f"  {coin}: error - {e}")
            status = 1
            continue
        if args.json:
            print(json.dumps(liq.raw, indent=2))
        else:
            display_heatmap(liq)

    if client.can_pay and not args.json:
        print(f"\nSpent by this run: ${client.spent_usd} USDC")
    return status


if __name__ == "__main__":
    sys.exit(main())
