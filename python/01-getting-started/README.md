# Getting Started with Cerebrus Pulse

Your first API calls — from free endpoints to paid analysis.

## Install

```bash
pip install cerebrus-pulse
```

## Step 1: Free Endpoints (No Wallet)

```python
from cerebrus_pulse import CerebrusPulse

client = CerebrusPulse()

# List available coins
coins = client.coins()
print(f"Tracking {len(coins)} coins:")
for coin in coins[:10]:
    print(f"  {coin}")

# Health check
health = client.health()
print(f"\nAPI Status: {health['status']}")
```

## Step 2: Paid Analysis (USDC on Base)

Set your wallet key and get real analysis:

```bash
export CEREBRUS_WALLET_KEY="your-base-wallet-private-key"
```

```python
import os
from cerebrus_pulse import CerebrusPulse

client = CerebrusPulse(wallet_key=os.environ.get("CEREBRUS_WALLET_KEY"))

# Technical analysis — $0.025
pulse = client.pulse("BTC", timeframes="1h,4h")
print(f"BTC Price: ${pulse.price:,.2f}")
print(f"RSI (1h): {pulse.timeframes['1h'].indicators.rsi_14:.1f}")
print(f"Trend: {pulse.timeframes['1h'].indicators.trend.label}")
print(f"Confluence: {pulse.confluence.score} ({pulse.confluence.bias})")

# Sentiment — $0.01
sentiment = client.sentiment()
print(f"\nMarket Sentiment: {sentiment.label} ({sentiment.score}/100)")

# Funding rates — $0.01
funding = client.funding("BTC")
print(f"\nBTC Funding: {funding.current_rate:.4%}")
print(f"Annualized: {funding.annualized:.2%}")
```

## What Each Endpoint Costs

| Endpoint | Cost | What You Get |
|----------|------|-------------|
| `coins()` | Free | List of 50+ tradeable pairs |
| `health()` | Free | API status |
| `pulse(coin)` | $0.025 | RSI, EMAs, BB, VWAP, trend, regime, confluence |
| `sentiment()` | $0.01 | Fear/greed, momentum, funding bias |
| `funding(coin)` | $0.01 | Current + historical rates, annualized |
| `screener()` | $0.06 | Scan all 50+ coins for signals |
| `liquidations(coin)` | $0.03 | Leverage clusters + cascade risk |
| `bundle(coin)` | $0.05 | pulse + sentiment + funding (9% discount) |

## Next Steps

- [Multi-Timeframe Analysis](../02-multi-timeframe/) — Compare signals across timeframes
- [Liquidation Heatmap](../03-liquidation-heatmap/) — Visualize where leverage is clustered
- [MCP Server Setup](../../mcp/01-quick-setup/) — Use with Claude Desktop
