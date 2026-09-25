"""
Multi-Timeframe Analysis - compare signals across 1h, 4h and 1d.

Helps spot timeframe alignment (every timeframe trending the same way is a
stronger signal) and divergence (mixed = caution) before entering a trade.

Cost: about $0.025 USDC per coin. One pulse call covers every timeframe.
      --dry-run is free: it reads /demo/{coin}, the same analysis for 1h and
      4h only, cached for up to 60 s and limited to 3 requests a minute.

Paying needs the pay extra and a dedicated, low-balance Base wallet:

    pip install "cerebrus-pulse[pay]>=0.4"
    export CEREBRUS_WALLET_KEY="<private key of that wallet>"

Usage:
    python multi_timeframe.py --dry-run BTC
    python multi_timeframe.py BTC
    python multi_timeframe.py ETH SOL DOGE
"""

import argparse
import os
import sys

import httpx
from cerebrus_pulse import (
    INDICATIVE_PRICES_USD,
    CerebrusPulse,
    CerebrusPulseError,
    PaymentBlocked,
    PaymentRequired,
    PulseResponse,
)

API = "https://api.cerebruspulse.xyz"
TIMEFRAMES = ("1h", "4h", "1d")
DEMO_TIMEFRAMES = ("1h", "4h")  # what /demo/{coin} returns
DEMO_LIMIT = 3  # /demo allows 3 requests a minute per IP

# (row label, how to read it from a timeframe's indicators)
METRICS = [
    ("RSI 14", lambda ind: ind.rsi_14),
    ("RSI zone", lambda ind: ind.rsi_zone),
    ("Trend", lambda ind: ind.trend.label if ind.trend else None),
    ("BB pos", lambda ind: ind.bollinger.position_pct if ind.bollinger else None),  # 0 lower, 1 upper band
    ("ATR %", lambda ind: ind.atr_pct),
]


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
    if isinstance(e, PaymentBlocked):  # a wallet is set; this client's spend limits said no
        print("  Nothing was signed. The limits are CEREBRUS_MAX_SPEND_USD (total per run), "
              "CEREBRUS_MAX_PAYMENT_USD (per call) and CEREBRUS_ALLOWED_PAYTO.")
    elif type(e) is PaymentRequired:  # no wallet
        print("  Run with --dry-run for the free version, or set CEREBRUS_WALLET_KEY to pay.")


def cell(value):
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def analyze(pulse, timeframes=TIMEFRAMES):
    price = "-" if pulse.price is None else f"${pulse.price:,.2f}"
    print(f"\n{'=' * 50}")
    print(f"  {pulse.coin} @ {price}")
    print(f"{'=' * 50}")

    print(f"  {'':12s}" + "".join(f"{tf:>14s}" for tf in timeframes))
    print(f"  {'-' * (12 + 14 * len(timeframes))}")

    for label, read in METRICS:
        vals = [cell(read(pulse.timeframes[tf].indicators)) if tf in pulse.timeframes else "-"
                for tf in timeframes]
        print(f"  {label:12s}" + "".join(f"{v:>14s}" for v in vals))

    # The API scores each timeframe; per_timeframe is in the raw response.
    per_tf = pulse.raw.get("confluence", {}).get("per_timeframe", {})
    biases = [cell(per_tf.get(tf, {}).get("bias")) for tf in timeframes]
    print(f"  {'Bias':12s}" + "".join(f"{b:>14s}" for b in biases))

    c = pulse.confluence
    scored_on = next(iter(pulse.timeframes), "-")  # the top-level score is the first timeframe's
    print(f"\n  Confluence: {c.score:.2f} on a 0-1 scale ({c.bias}, scored on {scored_on})")

    # Timeframe alignment check: trend direction is 1, 0 or -1
    directions = {tf: pulse.timeframes[tf].indicators.trend.direction
                  for tf in timeframes
                  if tf in pulse.timeframes and pulse.timeframes[tf].indicators.trend}
    if len(directions) < 2:
        print("  Alignment:  not enough timeframes to compare")
    elif all(d > 0 for d in directions.values()):
        print(f"  Alignment:  ALL BULLISH ({', '.join(directions)}) - strong signal")
    elif all(d < 0 for d in directions.values()):
        print(f"  Alignment:  ALL BEARISH ({', '.join(directions)}) - strong signal")
    else:
        mixed = ", ".join(f"{tf} {pulse.timeframes[tf].indicators.trend.label}" for tf in directions)
        print(f"  Alignment:  MIXED ({mixed}) - use caution")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare signals across 1h, 4h and 1d.")
    parser.add_argument("coins", nargs="*", default=["BTC"], help="coin tickers (default BTC)")
    parser.add_argument("--dry-run", action="store_true",
                        help="free: read /demo/{coin} (1h and 4h) instead of paying for pulse")
    args = parser.parse_args(argv)
    coins = [c.upper() for c in args.coins]

    if args.dry_run:
        if len(coins) > DEMO_LIMIT:
            print(f"The free demo allows {DEMO_LIMIT} requests a minute: using {', '.join(coins[:DEMO_LIMIT])}")
            coins = coins[:DEMO_LIMIT]
        timeframes = DEMO_TIMEFRAMES
        fetch = lambda coin: PulseResponse.from_dict(free_get(f"/demo/{coin}"))
        cost = INDICATIVE_PRICES_USD["pulse"] * len(coins)
        print(f"Dry run: free /demo data, 1h and 4h only. A paid run with 1d costs about ${cost} USDC.")
    else:
        try:
            client = make_client()
        except (ImportError, ValueError) as e:
            print(f"Cannot set up payment: {e}")
            return 1
        timeframes = TIMEFRAMES
        fetch = lambda coin: client.pulse(coin, timeframes=",".join(TIMEFRAMES))
        cost = INDICATIVE_PRICES_USD["pulse"] * len(coins)
        print(f"{len(coins)} pulse call(s), about ${cost} USDC.")

    status = 0
    for coin in coins:
        try:
            analyze(fetch(coin), timeframes)
        except PaymentRequired as e:  # also PaymentBlocked: a spend limit said no
            explain_payment(e)
            return 2
        except (CerebrusPulseError, httpx.HTTPError) as e:
            print(f"\n  {coin}: error - {e}")
            status = 1

    if not args.dry_run and client.can_pay:
        print(f"\nSpent by this run: ${client.spent_usd} USDC")
    return status


if __name__ == "__main__":
    sys.exit(main())
