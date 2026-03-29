# Crypto Research Agent

A LangChain agent that answers natural language questions about crypto markets using live data from Cerebrus Pulse.

## Install

```bash
pip install langchain-cerebrus-pulse langchain-openai langchain
```

## Setup

```bash
export OPENAI_API_KEY="your-openai-key"
export CEREBRUS_WALLET_KEY="your-base-wallet-key"
```

## Run

```bash
python research_agent.py "Is BTC overbought right now?"
python research_agent.py "Which coins have the most extreme funding rates?"
python research_agent.py "What does the ETH liquidation heatmap look like?"
python research_agent.py "Give me a full market overview"
```

## How It Works

The agent has access to 8 Cerebrus Pulse tools. When you ask a question, it decides which tools to call, fetches real-time data, and synthesizes an answer.

For "Is BTC overbought?", the agent might:
1. Call `cerebrus_pulse("BTC")` — get RSI, EMAs, Bollinger position
2. Call `cerebrus_sentiment()` — check overall market fear/greed
3. Call `cerebrus_funding("BTC")` — see if longs are crowded
4. Combine everything into a nuanced answer with specific numbers

Cost per question: typically $0.03-$0.15 depending on how many tools the agent calls.

## Customize

Swap `gpt-4o-mini` for any LangChain-compatible LLM. Add or remove tools based on your needs. Modify the system prompt to change the analysis style.
