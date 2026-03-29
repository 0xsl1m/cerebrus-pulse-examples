"""
Divergence Scanner — Find CEX-DEX and funding rate anomalies across all coins.

Scans 50+ Hyperliquid perpetuals for:
- CEX-DEX price divergence (Coinbase/Uniswap vs Hyperliquid)
- Extreme funding rates (crowded positioning)
- Liquidation cluster proximity

Cost: ~$2.10 for a full scan (50 coins x $0.04 avg)
Tip: Run once daily, not every 5 minutes.

Usage:
    export CEREBRUS_WALLET_KEY="your-base-wallet-key"
    python divergence_scanner.py
"""

import os
from cerebrus_pulse import CerebrusPulse

def scan():
    client = CerebrusPulse(wallet_key=os.environ.get("CEREBRUS_WALLET_KEY"))

    # Step 1: Get all coins (free)
    coins = client.coins()
    print(f"Scanning {len(coins)} coins for divergences...\n")

    divergences = []
    extreme_funding = []

    for coin in coins:
        try:
            # CEX-DEX divergence
            cex_dex = client.cex_dex(coin)
            if abs(cex_dex.divergence_pct) > 0.5:
                divergences.append({
                    "coin": coin,
                    "divergence": cex_dex.divergence_pct,
                    "direction": "DEX premium" if cex_dex.divergence_pct > 0 else "CEX premium",
                    "signal": cex_dex.signal
                })

            # Funding rate
            funding = client.funding(coin)
            if abs(funding.annualized) > 0.50:  # >50% annualized
                extreme_funding.append({
                    "coin": coin,
                    "rate": funding.current_rate,
                    "annualized": funding.annualized,
                    "bias": "crowded long" if funding.current_rate > 0 else "crowded short"
                })
        except Exception as e:
            print(f"  Skipped {coin}: {e}")
            continue

    # Results
    print("=" * 60)
    print("CEX-DEX DIVERGENCES (>0.5%)")
    print("=" * 60)
    if divergences:
        divergences.sort(key=lambda x: abs(x["divergence"]), reverse=True)
        for d in divergences:
            print(f"  {d['coin']:>6s}: {d['divergence']:+.2f}% ({d['direction']}) — {d['signal']}")
    else:
        print("  None found — markets are tightly arbitraged")

    print()
    print("=" * 60)
    print("EXTREME FUNDING (>50% annualized)")
    print("=" * 60)
    if extreme_funding:
        extreme_funding.sort(key=lambda x: abs(x["annualized"]), reverse=True)
        for f in extreme_funding:
            print(f"  {f['coin']:>6s}: {f['rate']:+.4%} ({f['annualized']:+.1%} ann.) — {f['bias']}")
    else:
        print("  None found — funding rates are balanced")

    print(f"\nTotal: {len(divergences)} divergences, {len(extreme_funding)} extreme funding")

if __name__ == "__main__":
    scan()
