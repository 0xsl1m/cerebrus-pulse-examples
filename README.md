# Cerebrus Pulse Examples

[![Cerebrus Pulse](https://img.shields.io/pypi/v/cerebrus-pulse)](https://pypi.org/project/cerebrus-pulse/) [![MCP Server](https://img.shields.io/pypi/v/cerebrus-pulse-mcp)](https://pypi.org/project/cerebrus-pulse-mcp/)

Practical examples for building crypto intelligence into AI agents and trading tools using [Cerebrus Pulse](https://cerebruspulse.xyz).

## What is Cerebrus Pulse?

A real-time crypto analysis API covering 50+ Hyperliquid perpetuals. Technical indicators, liquidation heatmaps, sentiment, funding rates, cross-chain stress — accessible via MCP server, Python SDK, or LangChain tools. Pays per query with USDC micropayments (x402), no API keys needed.

## Examples

### MCP Server (Claude Desktop, Cursor, Windsurf)

| Example | Description |
|---------|-------------|
| [Quick Setup](mcp/01-quick-setup/) | Get Cerebrus Pulse running in Claude Desktop in 2 minutes |
| [Trading Journal](mcp/02-trading-journal/) | Have Claude analyze your trades with real market data |
| [Market Scanner](mcp/03-market-scanner/) | Daily scan of all 50+ coins for actionable signals |

### Python SDK

| Example | Description |
|---------|-------------|
| [Getting Started](python/01-getting-started/) | First API call, free endpoints, basic analysis |
| [Multi-Timeframe Analysis](python/02-multi-timeframe/) | Compare 1h vs 4h vs 1d signals for a coin |
| [Liquidation Heatmap](python/03-liquidation-heatmap/) | Visualize leverage clusters and cascade risk zones |
| [Portfolio Dashboard](python/04-portfolio-dashboard/) | Track multiple positions with real-time technicals |
| [Divergence Scanner](python/05-divergence-scanner/) | Find CEX-DEX and funding rate divergences across all coins |

### LangChain Agent

| Example | Description |
|---------|-------------|
| [Crypto Research Agent](langchain/01-research-agent/) | Build a LangChain agent that answers crypto questions with live data |
| [Trading Signal Bot](langchain/02-signal-bot/) | Autonomous agent that monitors markets and reports opportunities |

## Prerequisites

```bash
# Python SDK
pip install cerebrus-pulse

# MCP Server
pip install cerebrus-pulse-mcp

# LangChain Tools
pip install langchain-cerebrus-pulse
```

For paid endpoints, you need USDC on Base. See the [x402 payment guide](https://cerebruspulse.xyz/guides/x402-payments).

## Free Endpoints (No Wallet Needed)

Every example starts with free calls so you can try before paying:

```python
from cerebrus_pulse import CerebrusPulse

client = CerebrusPulse()
coins = client.coins()          # Free — list 50+ trading pairs
health = client.health()        # Free — check API status
```

## Links

- [Documentation](https://cerebruspulse.xyz)
- [MCP Server](https://github.com/0xsl1m/cerebrus-pulse-mcp)
- [Python SDK](https://github.com/0xsl1m/cerebrus-pulse-python)
- [LangChain Tools](https://github.com/0xsl1m/langchain-cerebrus-pulse)

## Disclaimer

These examples are for educational purposes. Nothing here is financial advice. Crypto trading involves substantial risk. You are responsible for your own decisions.

## License

MIT

