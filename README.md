
```
     ░█████╗░███████╗██████╗░███████╗██████╗░██████╗░██╗░░░██╗░██████╗
     ██╔══██╗██╔════╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██║░░░██║██╔════╝
     ██║░░╚═╝█████╗░░██████╔╝█████╗░░██████╦╝██████╔╝██║░░░██║╚█████╗░
     ██║░░██╗██╔══╝░░██╔══██╗██╔══╝░░██╔══██╗██╔══██╗██║░░░██║░╚═══██╗
     ╚█████╔╝███████╗██║░░██║███████╗██████╦╝██║░░██║╚██████╔╝██████╔╝
     ░╚════╝░╚══════╝╚═╝░░╚═╝╚══════╝╚═════╝░╚═╝░░╚═╝░╚═════╝░╚═════╝░

     ─────╮    ╭──╮         ╭──╮    ╭──╮         ╭──╮    ╭─────
          │    │  │         │  │    │  │         │  │    │
     ─────╯────╯  ╰─────────╯  ╰────╯  ╰─────────╯  ╰────╯─────

              ██████╗░██╗░░░██╗██╗░░░░░░██████╗███████╗
              ██╔══██╗██║░░░██║██║░░░░░██╔════╝██╔════╝
              ██████╔╝██║░░░██║██║░░░░░╚█████╗░█████╗░░
              ██╔═══╝░██║░░░██║██║░░░░░░╚═══██╗██╔══╝░░
              ██║░░░░░╚██████╔╝███████╗██████╔╝███████╗
              ╚═╝░░░░░░╚═════╝░╚══════╝╚═════╝░╚══════╝

          crypto intelligence for AI agents · x402 micropayments
```

# Cerebrus Pulse Examples

[![Cerebrus Pulse](https://img.shields.io/pypi/v/cerebrus-pulse)](https://pypi.org/project/cerebrus-pulse/) [![MCP Server](https://img.shields.io/pypi/v/cerebrus-pulse-mcp)](https://pypi.org/project/cerebrus-pulse-mcp/)

Practical examples for building crypto intelligence into AI agents and trading tools using [Cerebrus Pulse](https://cerebruspulse.xyz).

## What is Cerebrus Pulse?

A real-time crypto analysis API covering 50+ Hyperliquid perpetuals. Technical indicators, liquidation heatmaps, sentiment, funding rates, cross-chain stress — accessible via MCP server, Python SDK, or LangChain tools. Pay per query in USDC over [x402](https://x402.org): no API keys, no subscriptions.

## Examples

Every script has a free `--dry-run` that calls only the API's free `/health` and `/demo/{coin}` endpoints. Try that first: no wallet, no payment. Costs below are indicative, in USDC, as the API published them on 2026-09-24; the API's payment terms say what is charged.

| Example | What it shows | Paid calls per run | Cost per run | Free `--dry-run` uses |
|---------|---------------|--------------------|--------------|-----------------------|
| [Getting Started](python/01-getting-started/) | Free endpoints, then technical analysis, sentiment and funding for one coin. Without a wallet, the price a paid call asks for. | pulse, sentiment, funding | about $0.045 | `/health`, `/demo/BTC` |
| [Multi-Timeframe Analysis](python/02-multi-timeframe/) | RSI, trend, Bollinger position and bias side by side for 1h, 4h and 1d, and whether the timeframes align | 1 pulse per coin | about $0.025 per coin | `/demo/{coin}` (1h and 4h only) |
| [Liquidation Heatmap](python/03-liquidation-heatmap/) | Estimated liquidation clusters above and below price, cascade risk, nearest cluster | 1 liquidations per coin | about $0.03 per coin | `/health` |
| [Divergence Scanner](python/05-divergence-scanner/) | CEX-DEX price gaps and extreme funding across a list of coins | cex_dex + funding per coin | about $0.03 per coin; $0.09 for the default BTC, ETH, SOL | `/demo/{coin}` (funding only) |
| [Crypto Research Agent](langchain/01-research-agent/) | A LangChain 1.x agent that picks among 8 Cerebrus Pulse tools to answer a question | the agent decides, typically 2-4 | about $0.03-$0.15 a question, plus your model provider | `/health`; no model call |
| [MCP Quick Setup](mcp/01-quick-setup/) | Cerebrus Pulse in Claude Desktop, Cursor, Windsurf or Claude Code, with spend limits | none | free | `uvx cerebrus-pulse-mcp --json health` |
| [Trading Journal](mcp/02-trading-journal/) | A prompt that has Claude review a trade against current market data | pulse, funding, liquidations, sentiment | about $0.075 | — |
| [Market Scanner](mcp/03-market-scanner/) | A morning-briefing prompt: screener, then a closer look at 3-5 coins | screener, 3-5 pulse, stress, funding | about $0.19-$0.26 | — |

Without a wallet, a paid call is not an error you have to debug: the scripts stop at the API's `402 Payment Required` and print the price it asked for.

## Prerequisites

```bash
# Python SDK 0.4+ (the scripts in python/)
pip install "cerebrus-pulse[pay]>=0.4"

# LangChain tools 0.4+ and LangChain 1.x (langchain/)
pip install "langchain-cerebrus-pulse[pay]>=0.4" "langchain>=1,<2" langchain-openai

# MCP server 0.5.2+ (mcp/): nothing to install with uv
uvx cerebrus-pulse-mcp --json health
```

Drop `[pay]` if you only want the free calls and the dry runs.

## Paying safely

Paid calls need USDC on Base in a **dedicated, low-balance** wallet, never your main one; x402 payments are gasless for the payer, so it needs no ETH. Give the scripts its key in `CEREBRUS_WALLET_KEY`. The SDK checks every payment before signing it:

- no single payment above `CEREBRUS_MAX_PAYMENT_USD` (default $0.10; the priciest endpoint is $0.06),
- no more than `CEREBRUS_MAX_SPEND_USD` per run (default $1.00),
- and only to the API's published payee.

See the [x402 payment guide](https://cerebruspulse.xyz/guides/x402-payments).

## Free Endpoints (No Wallet Needed)

```python
import httpx
from cerebrus_pulse import CerebrusPulse, PulseResponse

client = CerebrusPulse()
health = client.health()        # Free: API status
coins = client.coins()          # Free: the supported perpetuals

# Free demo: pulse() for 1h and 4h, cached up to 60 s, 3 requests a minute
demo = PulseResponse.from_dict(httpx.get("https://api.cerebruspulse.xyz/demo/BTC").json())
print(demo.price, demo.confluence.bias)
```

## Tests

The tests run every example against a mocked API built from real engine output, so they touch neither the network nor a wallet:

```bash
pip install -r tests/requirements.txt
python -m pytest -q
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
