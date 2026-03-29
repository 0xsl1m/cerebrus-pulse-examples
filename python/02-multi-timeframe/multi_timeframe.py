"""
Multi-Timeframe Analysis — Compare signals across 1h, 4h, and 1d.

Helps spot timeframe alignment (all bullish = stronger signal)
and divergence (mixed = caution) before entering a trade.

Cost: $0.025 per call (one call covers all requested timeframes)

Usage:
    export CEREBRUS_WALLET_KEY="your-base-wallet-key"
    python multi_timeframe.py BTC
    python multi_timeframe.py ETH SOL DOGE
"""

import sys
import os
from cerebrus_pulse import CerebrusPulse

def analyze(client, coin):
    pulse = client.pulse(coin, timeframes="1h,4h,1d")

    print(f"\n{'=' * 50}")
    print(f"  {coin} @ ${pulse.price:,.2f}")
    print(f"{'=' * 50}")

    headers = f"  {'':12s} {'1h':>10s} {'4h':>10s} {'1d':>10s}"
    print(headers)
    print(f"  {'-' * 44}")

    for metric in ["rsi_14", "trend.label", "bb_position"]:
        label = metric.replace(".", " ").replace("_", " ").title()
        vals = []
        for tf in ["1h", "4h", "1d"]:
            ind = pulse.timeframes[tf].indicators
            if "." in metric:
                parts = metric.split(".")
                val = getattr(getattr(ind, parts[0], None), parts[1], "—")
            else:
                val = getattr(ind, metric, "—")
            if isinstance(val, float):
                val = f"{val:.1f}"
            vals.append(str(val))
        print(f"  {label:12s} {vals[0]:>10s} {vals[1]:>10s} {vals[2]:>10s}")

    # Confluence
    c = pulse.confluence
    print(f"\n  Confluence: {c.score}/100 ({c.bias})")

    # Timeframe alignment check
    trends = [pulse.timeframes[tf].indicators.trend.label for tf in ["1h", "4h", "1d"]]
    if len(set(trends)) == 1:
        print(f"  Alignment:  ALL {trends[0].upper()} — strong signal")
    else:
        print(f"  Alignment:  MIXED ({', '.join(trends)}) — use caution")

def main():
    coins = sys.argv[1:] if len(sys.argv) > 1 else ["BTC"]
    client = CerebrusPulse(wallet_key=os.environ.get("CEREBRUS_WALLET_KEY"))

    for coin in coins:
        try:
            analyze(client, coin.upper())
        except Exception as e:
            print(f"\n  {coin.upper()}: Error — {e}")

if __name__ == "__main__":
    main()
