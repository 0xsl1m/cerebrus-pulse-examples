"""
Crypto Research Agent - a LangChain agent with Cerebrus Pulse tools.

Ask natural language questions about crypto markets and get answers
backed by real-time data from 50+ Hyperliquid perpetuals.

Cost: the agent picks the tools. Each paid tool call costs 1 to 6 cents in
USDC and a typical question uses 2 to 4 of them, about $0.03 to $0.15. The
SDK caps it: at most $0.10 per call and $1.00 per run by default
(CEREBRUS_MAX_PAYMENT_USD, CEREBRUS_MAX_SPEND_USD). Your model provider
bills separately.

Without CEREBRUS_WALLET_KEY the paid tools do not pay: they hand the agent the
price instead, and it answers from what it could get.

--dry-run is free: no model call and no payment. It builds the tools, lists
their prices and checks /health.

Usage:
    pip install "langchain-cerebrus-pulse[pay]>=0.4" "langchain>=1,<2" langchain-openai
    export OPENAI_API_KEY="your-openai-key"
    export CEREBRUS_WALLET_KEY="<private key of a dedicated, low-balance Base wallet>"
    python research_agent.py "Is BTC overbought right now?"
    python research_agent.py --dry-run
"""

import argparse
import os
import sys

from cerebrus_pulse import INDICATIVE_PRICES_USD, CerebrusPulse, CerebrusPulseError
from langchain.agents import create_agent
from langchain_cerebrus_pulse import (
    CerebrusListCoinsTool,
    CerebrusPulseTool,
    CerebrusSentimentTool,
    CerebrusFundingTool,
    CerebrusLiquidationsTool,
    CerebrusStressTool,
    CerebrusCexDexTool,
    CerebrusScreenerTool,
)

# Any tool-calling chat model LangChain can load, as "provider:model".
DEFAULT_MODEL = os.environ.get("CEREBRUS_AGENT_MODEL", "openai:gpt-4o-mini")

TOOLS = (
    CerebrusListCoinsTool,
    CerebrusPulseTool,
    CerebrusSentimentTool,
    CerebrusFundingTool,
    CerebrusLiquidationsTool,
    CerebrusStressTool,
    CerebrusCexDexTool,
    CerebrusScreenerTool,
)

SYSTEM_PROMPT = """You are a crypto research analyst with access to real-time
market data from Cerebrus Pulse. When answering questions:

1. Always check the actual data - don't guess or use stale knowledge
2. Cite specific numbers (RSI values, funding rates, divergence in bps)
3. Explain what the data means for traders
4. Flag conflicting signals when you see them
5. End with a clear, actionable summary

Hyperliquid funding rates are hourly: annualize them as rate x 24 x 365.
If a tool returns payment_required, say which data you could not get and
what it would cost; do not invent it.

Available data: technical analysis (RSI, EMAs, Bollinger Bands, trend, regime),
sentiment, funding rates, liquidation heatmaps, market stress, CEX-DEX divergence,
and a screener for scanning all 50+ coins."""

EXAMPLES = [
    "Is BTC overbought?",
    "Which altcoins have extreme funding rates?",
    "What does the liquidation heatmap look like for ETH?",
    "Give me a full market overview",
]


def make_client():
    """A client that pays when CEREBRUS_WALLET_KEY is set, else one that reports prices."""
    key = os.environ.get("CEREBRUS_WALLET_KEY")
    return CerebrusPulse(wallet_key=key) if key else CerebrusPulse()


def build_tools(client):
    # One shared client: every tool pays from, and counts against, the same budget.
    return [tool(client=client) for tool in TOOLS]


def build_agent(model, client):
    return create_agent(model, tools=build_tools(client), system_prompt=SYSTEM_PROMPT)


def ask(agent, question):
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["messages"][-1].content


def tool_price(tool):
    endpoint = tool.name.removeprefix("cerebrus_")
    price = INDICATIVE_PRICES_USD.get(endpoint)
    return "free" if price is None else f"${price}"


def dry_run():
    print("Dry run: no model call, nothing is paid.\n")
    client = CerebrusPulse()
    for tool in build_tools(client):
        print(f"  {tool.name:24s}{tool_price(tool):>8s}")
    try:
        health = client.health()
    except CerebrusPulseError as e:
        print(f"\nAPI check failed: {e}")
        return 1
    print(f"\nAPI status: {health.get('status')} (version {health.get('version')})")
    print("Ask a question to run the agent; it chooses which of these tools to pay for.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ask a crypto question; the agent fetches live data.")
    parser.add_argument("question", nargs="*", help="your question about crypto markets")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"LangChain model id, provider:model (default {DEFAULT_MODEL})")
    parser.add_argument("--dry-run", action="store_true",
                        help="free: list the tools and check /health, no model call, never pay")
    args = parser.parse_args(argv)

    if args.dry_run:
        return dry_run()

    if not args.question:
        print('Usage: python research_agent.py "your question about crypto"')
        print()
        print("Examples:")
        for example in EXAMPLES:
            print(f'  python research_agent.py "{example}"')
        return 0

    try:
        client = make_client()
    except (ImportError, ValueError) as e:
        print(f"Cannot set up payment: {e}")
        return 1

    agent = build_agent(args.model, client)
    answer = ask(agent, " ".join(args.question))
    print("\n" + "=" * 60)
    print(answer)
    if client.can_pay:
        print(f"\nSpent on Cerebrus Pulse: ${client.spent_usd} USDC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
