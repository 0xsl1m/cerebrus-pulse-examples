"""
Crypto Research Agent — LangChain agent with Cerebrus Pulse tools.

Ask natural language questions about crypto markets and get answers
backed by real-time data from 50+ Hyperliquid perpetuals.

Usage:
    export OPENAI_API_KEY="your-openai-key"
    export CEREBRUS_WALLET_KEY="your-base-wallet-key"
    python research_agent.py "Is BTC overbought right now?"
"""

import sys
import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
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

def create_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    tools = [
        CerebrusListCoinsTool(),
        CerebrusPulseTool(),
        CerebrusSentimentTool(),
        CerebrusFundingTool(),
        CerebrusLiquidationsTool(),
        CerebrusStressTool(),
        CerebrusCexDexTool(),
        CerebrusScreenerTool(),
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a crypto research analyst with access to real-time 
market data from Cerebrus Pulse. When answering questions:

1. Always check the actual data — don't guess or use stale knowledge
2. Cite specific numbers (RSI values, funding rates, divergence %)
3. Explain what the data means for traders
4. Flag conflicting signals when you see them
5. End with a clear, actionable summary

Available data: technical analysis (RSI, EMAs, Bollinger Bands, trend, regime), 
sentiment, funding rates, liquidation heatmaps, market stress, CEX-DEX divergence, 
and a screener for scanning all 50+ coins."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python research_agent.py \"your question about crypto\"")
        print()
        print("Examples:")
        print('  python research_agent.py "Is BTC overbought?"')
        print('  python research_agent.py "Which altcoins have extreme funding rates?"')
        print('  python research_agent.py "What does the liquidation heatmap look like for ETH?"')
        print('  python research_agent.py "Give me a full market overview"')
        return

    agent = create_agent()
    question = " ".join(sys.argv[1:])
    result = agent.invoke({"input": question})
    print("\n" + "=" * 60)
    print(result["output"])

if __name__ == "__main__":
    main()
