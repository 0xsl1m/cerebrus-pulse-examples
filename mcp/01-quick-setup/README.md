# Quick Setup — Cerebrus Pulse in Claude Desktop

Get crypto intelligence inside Claude Desktop in 2 minutes.

## Step 1: Install

```bash
pip install cerebrus-pulse-mcp
```

Or if you prefer [uv](https://docs.astral.sh/uv/):

```bash
# No install needed — uvx runs it directly
uvx cerebrus-pulse-mcp
```

## Step 2: Configure Claude Desktop

Open your Claude Desktop config:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add:

```json
{
  "mcpServers": {
    "cerebrus-pulse": {
      "command": "uvx",
      "args": ["cerebrus-pulse-mcp"]
    }
  }
}
```

Restart Claude Desktop.

## Step 3: Try It

Open Claude and ask:

> "What coins does Cerebrus Pulse track?"

Claude will call `cerebrus_list_coins` (free) and show you all 50+ Hyperliquid perpetuals.

## Step 4: Enable Paid Analysis

For technical analysis, sentiment, and other paid tools, set your wallet key:

```json
{
  "mcpServers": {
    "cerebrus-pulse": {
      "command": "uvx",
      "args": ["cerebrus-pulse-mcp"],
      "env": {
        "CEREBRUS_WALLET_KEY": "your-base-wallet-private-key"
      }
    }
  }
}
```

Now try:

> "Give me a full technical analysis of BTC"

> "Where are the ETH liquidation clusters?"

> "What's the overall market stress level right now?"

## Also Works With

- **Cursor**: Add to MCP settings in `.cursor/mcp.json`
- **Windsurf**: Add to MCP config
- **Claude Code**: Add to `~/.claude/settings.json` under `mcpServers`

## Troubleshooting

**"Tool not found"** — Restart Claude Desktop after editing the config.

**"Payment required"** — The tool is working but needs a wallet for paid endpoints. Set `CEREBRUS_WALLET_KEY`.

**"Connection refused"** — Make sure `uvx` is in your PATH. Try running `uvx cerebrus-pulse-mcp` in a terminal first.

## Next Steps

- [Trading Journal](../02-trading-journal/) — Analyze your trades with live data
- [Market Scanner](../03-market-scanner/) — Daily scan for opportunities
