"""
Liquidation Heatmap — Visualize leverage clusters and cascade risk.

Shows where liquidation orders are concentrated by leverage tier,
helping you identify potential squeeze zones and support/resistance.

Cost: $0.03 per coin

Usage:
    export CEREBRUS_WALLET_KEY="your-base-wallet-key"
    python liquidation_heatmap.py BTC
    python liquidation_heatmap.py ETH --json
"""

import sys
import os
import json
from cerebrus_pulse import CerebrusPulse

def display_heatmap(coin, liq):
    print(f"\n{'=' * 60}")
    print(f"  {coin} Liquidation Heatmap")
    print(f"  Price: ${liq.price:,.2f}")
    print(f"{'=' * 60}")

    print(f"\n  {'Leverage':>10s} {'Long Liq $':>14s} {'Short Liq $':>14s} {'Risk':>8s}")
    print(f"  {'-' * 50}")

    for tier in liq.tiers:
        long_val = f"${tier.long_liquidation:,.0f}" if tier.long_liquidation else "—"
        short_val = f"${tier.short_liquidation:,.0f}" if tier.short_liquidation else "—"

        # Visual risk bar
        risk_level = tier.cascade_risk or 0
        bar = "#" * int(risk_level * 10)

        print(f"  {tier.leverage:>8s}x {long_val:>14s} {short_val:>14s} {bar:>8s}")

    if hasattr(liq, "cascade_risk"):
        print(f"\n  Overall Cascade Risk: {liq.cascade_risk}")
    if hasattr(liq, "nearest_cluster"):
        nc = liq.nearest_cluster
        print(f"  Nearest Cluster: ${nc.price:,.2f} ({nc.direction}, {nc.distance_pct:+.1f}%)")

def main():
    coins = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    as_json = "--json" in sys.argv
    coins = coins or ["BTC"]

    client = CerebrusPulse(wallet_key=os.environ.get("CEREBRUS_WALLET_KEY"))

    for coin in coins:
        try:
            liq = client.liquidations(coin.upper())
            if as_json:
                print(json.dumps(liq.to_dict(), indent=2))
            else:
                display_heatmap(coin.upper(), liq)
        except Exception as e:
            print(f"  {coin.upper()}: Error — {e}")

if __name__ == "__main__":
    main()
