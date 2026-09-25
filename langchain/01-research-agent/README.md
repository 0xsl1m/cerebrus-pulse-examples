# Crypto Research Agent

A LangChain agent that answers natural language questions about crypto markets using live data from Cerebrus Pulse.

## Install

```bash
pip install "langchain-cerebrus-pulse[pay]>=0.4" "langchain>=1,<2" langchain-openai
```

Needs `langchain-cerebrus-pulse` 0.4 and `langchain` 1.x: the agent is built with `langchain.agents.create_agent`, which replaced `AgentExecutor` and `create_tool_calling_agent`.

## Try it free first

```bash
python research_agent.py --dry-run
```

No model call and no payment: it builds the tools, lists what each one costs, and checks the API's free `/health`.

## Setup

```bash
export OPENAI_API_KEY="your-openai-key"
export CEREBRUS_WALLET_KEY="<private key of a dedicated, low-balance Base wallet>"
```

Use a wallet that holds a few dollars of USDC on Base and nothing else. Without `CEREBRUS_WALLET_KEY` the paid tools don't pay; they return the price to the agent instead, and the agent says what it couldn't get.

## Run

```bash
python research_agent.py "Is BTC overbought right now?"
python research_agent.py "Which coins have the most extreme funding rates?"
python research_agent.py "What does the ETH liquidation heatmap look like?"
python research_agent.py "Give me a full market overview"
```

## How It Works

The agent has 8 Cerebrus Pulse tools, all sharing one `CerebrusPulse` client, so they pay from, and count against, one budget. When you ask a question, the model decides which tools to call, fetches the data, and writes an answer.

For "Is BTC overbought?", the agent might:
1. Call `cerebrus_pulse` for BTC: RSI, EMAs, Bollinger position ($0.025)
2. Call `cerebrus_sentiment`: the market-wide sentiment label ($0.01)
3. Call `cerebrus_funding` for BTC: are longs crowded? ($0.01)
4. Combine everything into an answer with specific numbers

## Cost

Each paid tool call costs 1 to 6 cents in USDC; a typical question uses 2 to 4 of them, about $0.03 to $0.15. The SDK refuses any single payment over $0.10 and stops at $1.00 per run by default (`CEREBRUS_MAX_PAYMENT_USD`, `CEREBRUS_MAX_SPEND_USD`). The script prints what the run spent. Your model provider bills separately.

| Tool | Price |
|------|-------|
| `cerebrus_list_coins` | Free |
| `cerebrus_pulse` | $0.025 |
| `cerebrus_sentiment` | $0.01 |
| `cerebrus_funding` | $0.01 |
| `cerebrus_liquidations` | $0.03 |
| `cerebrus_stress` | $0.02 |
| `cerebrus_cex_dex` | $0.02 |
| `cerebrus_screener` | $0.06 |

Prices are indicative, as the API published them on 2026-09-24. The API's 402 terms say what is charged.

## Customize

Pick another model with `--model provider:model` or `CEREBRUS_AGENT_MODEL` (any tool-calling chat model LangChain can load, with that provider's LangChain package installed). Add or remove tools in `TOOLS`, or change `SYSTEM_PROMPT` to change the analysis style.
