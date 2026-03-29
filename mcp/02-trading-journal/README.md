# Trading Journal — Analyze Trades with Claude

Use Claude Desktop to review your trades against what the market data actually showed.

## Setup

Make sure [Cerebrus Pulse MCP is configured](../01-quick-setup/) in Claude Desktop.

## Prompt Template

After a trade, paste your entry/exit details and ask Claude to analyze:

```
I took this trade on BTC:
- Entry: $67,200 (long)
- Exit: $66,800 (stopped out, -0.6%)
- Timeframe: 1h
- Thesis: RSI bounce from oversold

Can you pull the current BTC technical analysis and tell me:
1. What was the RSI at the time? Was it actually oversold?
2. What did the higher timeframes (4h, 1d) show? Was I trading against the trend?
3. Where were the liquidation clusters? Did I get caught in a squeeze?
4. What was funding? Were longs crowded?
5. What should I look for next time to avoid this?
```

## Why This Works

Most traders journal what they *felt* during a trade. This approach pulls objective data:
- Was your signal actually there, or did you imagine it?
- Were higher timeframes aligned or fighting you?
- Did crowded positioning (funding) work against you?
- Were liquidation clusters near your stop?

Claude synthesizes all of this into actionable lessons for future trades.

## Cost

One journal analysis: ~$0.10-$0.15 (pulse + funding + liquidations + sentiment).
