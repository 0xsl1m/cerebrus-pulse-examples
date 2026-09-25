# Getting Started with Cerebrus Pulse

Your first API calls, from free endpoints to paid analysis. The runnable version of this page is [`getting_started.py`](getting_started.py).

## Install

```bash
pip install "cerebrus-pulse>=0.4"          # free endpoints; paid ones report their price
pip install "cerebrus-pulse[pay]>=0.4"     # + automatic payment in USDC on Base
```

## Try it free first

```bash
python getting_started.py --dry-run
```

This calls only `/health` and `/demo/BTC`. The demo is the same analysis as `pulse("BTC")` for 1h and 4h, cached for up to 60 seconds and limited to 3 requests a minute. No wallet, no payment.

## Step 1: Free endpoints (no wallet)

```python
from cerebrus_pulse import CerebrusPulse

client = CerebrusPulse()

health = client.health()
print(f"API status: {health['status']}")

coins = client.coins()
print(f"Tracking {len(coins)} coins: {', '.join(coins[:10])}")
```

## Step 2: Paid analysis (USDC on Base)

Use a **dedicated, low-balance** Base wallet that holds a little USDC, never your main wallet. x402 payments are gasless for the payer, so it needs no ETH.

```bash
export CEREBRUS_WALLET_KEY="<private key of that wallet>"
```

```python
import os
from cerebrus_pulse import CerebrusPulse

client = CerebrusPulse(wallet_key=os.environ["CEREBRUS_WALLET_KEY"])

# Technical analysis, about $0.025
pulse = client.pulse("BTC", timeframes="1h,4h")
print(f"BTC price: ${pulse.price:,.2f}")
print(f"RSI (1h): {pulse.timeframes['1h'].indicators.rsi_14:.1f}")
print(f"Trend (1h): {pulse.timeframes['1h'].indicators.trend.label}")
print(f"Confluence: {pulse.confluence.score:.2f} on a 0-1 scale ({pulse.confluence.bias})")

# Sentiment, about $0.01: a bucketed label, very_bearish ... very_bullish
sentiment = client.sentiment()
print(f"Market sentiment: {sentiment.label}")

# Funding, about $0.01. Hyperliquid pays funding every hour.
funding = client.funding("BTC")
print(f"BTC funding: {funding.current_rate:.5%} per hour")
print(f"Annualized: {funding.current_rate * 24 * 365:.2%}")

print(f"Spent: ${client.spent_usd} USDC")
```

The SDK checks every payment before signing it: at most $0.10 per call and $1.00 per client by default (`CEREBRUS_MAX_PAYMENT_USD`, `CEREBRUS_MAX_SPEND_USD`), and only to the API's published payee.

## Without a wallet

Paid endpoints raise `PaymentRequired`, which carries the price the API asked for:

```python
from cerebrus_pulse import CerebrusPulse, PaymentRequired

try:
    CerebrusPulse().pulse("BTC")
except PaymentRequired as e:
    print(f"Costs ${e.price_usd} USDC")
```

## What each endpoint costs

Indicative prices in USDC, as the API published them on 2026-09-24. The API sets the price: its 402 terms say what is charged.

| Method | Cost | What you get |
|--------|------|-------------|
| `health()` | Free | API status |
| `coins()` | Free | Supported Hyperliquid perpetuals |
| `/demo/{coin}` | Free | `pulse()` for 1h and 4h, cached, 3 requests a minute |
| `pulse(coin)` | $0.025 | RSI, EMAs, Bollinger, VWAP, trend, regime, confluence |
| `sentiment()` | $0.01 | Bucketed market sentiment label |
| `funding(coin)` | $0.01 | Current, average, min and max funding rate |
| `screener()` | $0.06 | Scan every coin for signals |
| `liquidations(coin)` | $0.03 | Estimated liquidation clusters and cascade risk |
| `bundle(coin)` | $0.05 | pulse, sentiment and funding in one call |

## Next Steps

- [Multi-Timeframe Analysis](../02-multi-timeframe/) — compare signals across timeframes
- [Liquidation Heatmap](../03-liquidation-heatmap/) — see where leverage is clustered
- [MCP Server Setup](../../mcp/01-quick-setup/) — use it from Claude Desktop
