"""
Getting Started - your first Cerebrus Pulse calls, free and paid.

    --dry-run   Free. Calls /health and /demo/{coin} only. No wallet, no payment.
    (default)   Free /health and /coins, then three paid calls for one coin:
                pulse ($0.025) + sentiment ($0.01) + funding ($0.01), about $0.045.

Without a wallet the paid calls are not paid: each one stops at the API's
402 and this script prints the price the API asked for. To pay, install the
pay extra and point it at a dedicated, low-balance Base wallet holding USDC:

    pip install "cerebrus-pulse[pay]>=0.4"
    export CEREBRUS_WALLET_KEY="<private key of that wallet>"

The SDK refuses any single payment over $0.10 and more than $1.00 per run
unless you raise CEREBRUS_MAX_PAYMENT_USD / CEREBRUS_MAX_SPEND_USD.

Usage:
    python getting_started.py --dry-run
    python getting_started.py ETH
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
HOURS_PER_YEAR = 24 * 365  # Hyperliquid pays funding every hour


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


def num(value, spec=".2f"):
    return "-" if value is None else format(value, spec)


def show_pulse(pulse):
    print(f"  {pulse.coin} price: ${num(pulse.price, ',.2f')}")
    for tf, data in pulse.timeframes.items():
        ind = data.indicators
        trend = ind.trend.label if ind.trend else "unknown"
        print(f"  {tf:>3s}  RSI {num(ind.rsi_14, '.1f')} ({ind.rsi_zone}), trend {trend}")
    c = pulse.confluence
    print(f"  Confluence: {c.score:.2f} on a 0-1 scale, {c.bias}")


def dry_run(coin):
    print("Dry run: free endpoints only, nothing is paid.\n")
    health = CerebrusPulse().health()
    print(f"API status: {health.get('status')} (version {health.get('version')})")

    print(f"\nFree demo analysis for {coin} (1h and 4h, cached up to 60 s):")
    show_pulse(PulseResponse.from_dict(free_get(f"/demo/{coin}")))

    cost = sum(INDICATIVE_PRICES_USD[m] for m in ("pulse", "sentiment", "funding"))
    print(f"\nA full run adds pulse, sentiment and funding for {coin}: about ${cost} USDC.")
    return 0


def full_run(coin):
    try:
        client = make_client()
    except (ImportError, ValueError) as e:
        print(f"Cannot set up payment: {e}")
        return 1

    health = client.health()
    print(f"API status: {health.get('status')} (version {health.get('version')})")
    coins = client.coins()
    print(f"Tracking {len(coins)} coins, for example {', '.join(coins[:8])}")

    print(f"\nPaid analysis for {coin}:")
    try:
        pulse = client.pulse(coin, timeframes="1h,4h")  # about $0.025
        show_pulse(pulse)

        sentiment = client.sentiment()  # about $0.01
        print(f"  Market sentiment: {sentiment.label}")

        funding = client.funding(coin)  # about $0.01
        rate = funding.current_rate
        apr = None if rate is None else rate * HOURS_PER_YEAR * 100
        print(f"  Funding: {num(rate, '.5%')} per hour, {num(apr)}% annualized")
    except PaymentRequired as e:  # also PaymentBlocked: a spend limit said no
        explain_payment(e)
        print("  Run with --dry-run for the free version, or set CEREBRUS_WALLET_KEY to pay.")
        return 2
    except CerebrusPulseError as e:
        print(f"  Error: {e}")
        return 1

    if client.can_pay:
        print(f"\nSpent by this run: ${client.spent_usd} USDC")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="First Cerebrus Pulse calls, free and paid.")
    parser.add_argument("coin", nargs="?", default="BTC", help="coin ticker (default BTC)")
    parser.add_argument("--dry-run", action="store_true",
                        help="free: call /health and /demo/{coin} only, never pay")
    args = parser.parse_args(argv)
    coin = args.coin.upper()
    try:
        return dry_run(coin) if args.dry_run else full_run(coin)
    except (CerebrusPulseError, httpx.HTTPError) as e:
        print(f"Request failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
