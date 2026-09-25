"""
Divergence Scanner - find CEX-DEX price gaps and extreme funding.

For each coin:
- CEX-DEX divergence: the Coinbase price against the on-chain price
  (Chainlink or Uniswap). The API covers about 15 large tokens; for any
  other it answers 400 with the list of covered tokens.
- Funding: the latest Hyperliquid funding rate, annualized. Hyperliquid pays
  funding every hour, so the annual rate is the hourly rate x 24 x 365.

Cost: cex_dex (about $0.02) + funding (about $0.01) = about $0.03 per coin,
      so the default BTC ETH SOL scan is about $0.09. The SDK stops paying
      at $1.00 per run unless you raise CEREBRUS_MAX_SPEND_USD.
      --dry-run is free: it reads the funding rate from /demo/{coin} (3 coins
      at most, the demo's limit per minute) and skips CEX-DEX, which has no
      free equivalent.
Tip: run it once a day, not every 5 minutes.

Paying needs the pay extra and a dedicated, low-balance Base wallet:

    pip install "cerebrus-pulse[pay]>=0.4"
    export CEREBRUS_WALLET_KEY="<private key of that wallet>"

Usage:
    python scanner.py --dry-run
    python scanner.py
    python scanner.py BTC ETH SOL LINK AAVE --min-divergence-bps 30
"""

import argparse
import os
import sys

import httpx
from cerebrus_pulse import (
    INDICATIVE_PRICES_USD,
    CerebrusPulse,
    CerebrusPulseError,
    PaymentRequired,
    PulseResponse,
)

API = "https://api.cerebruspulse.xyz"
DEFAULT_COINS = ["BTC", "ETH", "SOL"]
HOURS_PER_YEAR = 24 * 365  # Hyperliquid pays funding every hour
DEMO_LIMIT = 3  # /demo allows 3 requests a minute per IP


def free_get(path):
    """GET a free endpoint such as /demo/BTC. It never pays."""
    with httpx.Client(base_url=API, timeout=30) as http:
        resp = http.get(path)
    resp.raise_for_status()
    return resp.json()


def make_client():
    """A client that pays when CEREBRUS_WALLET_KEY is set, else one that reports prices."""
    key = os.environ.get("CEREBRUS_WALLET_KEY")
    return CerebrusPulse(wallet_key=key) if key else CerebrusPulse()


def explain_payment(e):
    print(f"\n  Not paid: {e.detail}")
    for term in e.terms:
        print(f"  The API asks ${term.price_usd} USDC on {term.network}, paid to {term.pay_to}")


def annualized_pct(hourly_rate):
    return hourly_rate * HOURS_PER_YEAR * 100


def scan(coins, get_divergence, get_funding_rate):
    """One row per coin. A failed call leaves its field None; a 402 stops the scan."""
    rows = []
    for coin in coins:
        row = {"coin": coin, "spread_bps": None, "direction": None, "rate": None}
        if get_divergence is not None:
            try:
                div = get_divergence(coin).divergence
                row["spread_bps"], row["direction"] = div.spread_bps, div.direction
            except PaymentRequired:
                raise
            except (CerebrusPulseError, httpx.HTTPError) as e:
                print(f"  {coin}: no CEX-DEX data ({e})")
        try:
            row["rate"] = get_funding_rate(coin)
        except PaymentRequired:
            raise
        except (CerebrusPulseError, httpx.HTTPError) as e:
            print(f"  {coin}: no funding data ({e})")
        rows.append(row)
    return rows


def report(rows, min_bps, min_apr):
    print(f"\n  {'Coin':<6s}{'CEX-DEX bps':>12s}  {'Premium':<8s}{'Funding/h':>12s}{'APR %':>9s}")
    print(f"  {'-' * 47}")
    for r in rows:
        bps = "-" if r["spread_bps"] is None else f"{r['spread_bps']:+.1f}"
        side = {"cex_premium": "CEX", "dex_premium": "DEX"}.get(r["direction"], "-")
        rate = "-" if r["rate"] is None else f"{r['rate']:+.5%}"
        apr = "-" if r["rate"] is None else f"{annualized_pct(r['rate']):+.2f}"
        print(f"  {r['coin']:<6s}{bps:>12s}  {side:<8s}{rate:>12s}{apr:>9s}")

    divergences = sorted((r for r in rows if r["spread_bps"] is not None
                          and abs(r["spread_bps"]) >= min_bps),
                         key=lambda r: abs(r["spread_bps"]), reverse=True)
    extreme = sorted((r for r in rows if r["rate"] is not None
                      and abs(annualized_pct(r["rate"])) >= min_apr),
                     key=lambda r: abs(r["rate"]), reverse=True)

    print()
    print("=" * 60)
    print(f"CEX-DEX DIVERGENCES (at least {min_bps:g} bps)")
    print("=" * 60)
    if divergences:
        for r in divergences:
            side = "DEX premium" if r["direction"] == "dex_premium" else "CEX premium"
            print(f"  {r['coin']:>6s}: {r['spread_bps']:+.1f} bps ({side})")
    else:
        print("  None found - markets are tightly arbitraged")

    print()
    print("=" * 60)
    print(f"EXTREME FUNDING (at least {min_apr:g}% annualized)")
    print("=" * 60)
    if extreme:
        for r in extreme:
            bias = "crowded long" if r["rate"] > 0 else "crowded short"
            apr = annualized_pct(r["rate"])
            print(f"  {r['coin']:>6s}: {r['rate']:+.5%}/h ({apr:+.1f}% a year) - {bias}")
    else:
        print("  None found - funding rates are balanced")

    print(f"\nTotal: {len(divergences)} divergences, {len(extreme)} extreme funding")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find CEX-DEX price gaps and extreme funding.")
    parser.add_argument("coins", nargs="*", default=DEFAULT_COINS,
                        help=f"coin tickers (default {' '.join(DEFAULT_COINS)})")
    parser.add_argument("--min-divergence-bps", type=float, default=50,
                        help="flag CEX-DEX gaps at least this wide, in basis points (default 50)")
    parser.add_argument("--min-funding-apr", type=float, default=50,
                        help="flag funding at least this high, in %% a year (default 50)")
    parser.add_argument("--dry-run", action="store_true",
                        help="free: funding from /demo/{coin} only, no CEX-DEX, never pay")
    args = parser.parse_args(argv)
    coins = [c.upper() for c in args.coins]
    per_coin = INDICATIVE_PRICES_USD["cex_dex"] + INDICATIVE_PRICES_USD["funding"]

    client = None
    if args.dry_run:
        if len(coins) > DEMO_LIMIT:
            coins = coins[:DEMO_LIMIT]
            print(f"The free demo allows {DEMO_LIMIT} requests a minute: using {', '.join(coins)}")
        print(f"Dry run: funding from the free /demo, no CEX-DEX. "
              f"A paid scan of {len(coins)} coin(s) costs about ${per_coin * len(coins)} USDC.")
        get_divergence = None

        def get_funding_rate(coin):  # /demo is pulse for 1h,4h, derivatives included
            return PulseResponse.from_dict(free_get(f"/demo/{coin}")).derivatives.funding_rate
    else:
        try:
            client = make_client()
        except (ImportError, ValueError) as e:
            print(f"Cannot set up payment: {e}")
            return 1
        print(f"Scanning {len(coins)} coin(s): about ${per_coin * len(coins)} USDC.")
        get_divergence = client.cex_dex
        get_funding_rate = lambda coin: client.funding(coin).current_rate

    try:
        rows = scan(coins, get_divergence, get_funding_rate)
    except PaymentRequired as e:  # also PaymentBlocked: a spend limit said no
        explain_payment(e)
        print("  Run with --dry-run for the free version, or set CEREBRUS_WALLET_KEY to pay.")
        return 2

    report(rows, args.min_divergence_bps, args.min_funding_apr)
    if client is not None and client.can_pay:
        print(f"Spent by this run: ${client.spent_usd} USDC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
