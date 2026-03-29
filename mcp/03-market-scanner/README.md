# Market Scanner — Daily Signal Scan via Claude

Use Claude Desktop to scan all 50+ Hyperliquid coins for actionable setups, every morning.

## Setup

Make sure [Cerebrus Pulse MCP is configured](../01-quick-setup/) in Claude Desktop.

## Daily Prompt

Copy this into Claude:

```
Run a full market scan using Cerebrus Pulse. I want to find:

1. Coins with RSI below 30 or above 70 (oversold/overbought extremes)
2. Any coins showing timeframe alignment (same trend on 1h + 4h)
3. Extreme funding rates (anyone crowded?)
4. High market stress (cross-chain signal)

Use the screener first for a broad view, then drill into the top 3-5 
most interesting setups with individual pulse calls.

Format as a morning briefing I can scan in 2 minutes.
```

## What Happens

Claude will:
1. Call `cerebrus_screener` ($0.06) — scan all coins
2. Filter for your criteria
3. Call `cerebrus_pulse` ($0.025 each) on 3-5 interesting coins
4. Call `cerebrus_stress` ($0.015) — overall market health
5. Call `cerebrus_funding` ($0.01 each) on coins with positioning signals

Total cost: ~$0.20-$0.30 per morning scan.

## Variations

**Dip buyer scan:**
> "Find coins with RSI under 35 on the 4h, positive funding (market still bullish), 
> and a liquidation heatmap showing shorts clustered nearby."

**Momentum scan:**
> "Which coins have the strongest confluence scores? Show me the top 5 with 
> aligned trends across all timeframes."

**Risk-off check:**
> "What's the market stress index? Any USDC depeg risk? How extreme are 
> funding rates across the board? I want to know if I should reduce exposure."
