# Trading Journal — Analyze Trades with Claude

Use Claude Desktop to review a trade against what the market data shows.

## Setup

Make sure [Cerebrus Pulse MCP is configured](../01-quick-setup/) in Claude Desktop, with a wallet key for the paid tools.

## When to journal

Cerebrus Pulse returns **current** market data, not history: it cannot tell you what RSI was last Tuesday. Journal right after a trade closes, or while a position is still open, so the data still describes the market you traded.

## Prompt Template

After a trade, paste your entry and exit details and ask Claude to analyze them:

```
I just closed this trade on BTC:
- Entry: $67,200 (long)
- Exit: $66,800 (stopped out, -0.6%)
- Timeframe: 1h
- Thesis: RSI bounce from oversold

Using Cerebrus Pulse data as it stands now, tell me:
1. Where is the 1h RSI now, and is it still near oversold?
2. What do the 4h and 1d trends show? Was I trading against the higher timeframes?
3. Where are the estimated liquidation clusters? Was my stop sitting near one?
4. What is funding doing? Are longs crowded?
5. What should I look for next time to avoid this?
```

## Why This Works

Most traders journal what they *felt* during a trade. This pulls objective data:
- Is your signal actually there, or did you imagine it?
- Are the higher timeframes aligned with the trade or fighting it?
- Is crowded positioning (funding) working against you?
- Are liquidation clusters near your stop?

Claude turns the data into lessons for the next trade.

## Cost

One journal analysis calls about four paid tools: `cerebrus_pulse` ($0.025) + `cerebrus_funding` ($0.01) + `cerebrus_liquidations` ($0.03) + `cerebrus_sentiment` ($0.01) = **about $0.075** in USDC. Prices are indicative, as the API published them on 2026-09-24; the API's payment terms say what is charged.
