# Quick Setup — Cerebrus Pulse in Claude Desktop

Get crypto intelligence inside Claude Desktop in 2 minutes. Needs `cerebrus-pulse-mcp` 0.5.2 or later.

## Step 1: Check it works (free)

With [uv](https://docs.astral.sh/uv/) there is nothing to install; `uvx` runs the server directly:

```bash
uvx cerebrus-pulse-mcp --json health
uvx cerebrus-pulse-mcp --json list-coins
```

Both are free. `health` should report `"status": "ok"`. This is the dry run: nothing is paid.

Prefer pip? `pip install cerebrus-pulse-mcp`, then run `cerebrus-pulse-mcp --json health`.

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

Claude will call `cerebrus_list_coins` (free) and list the Hyperliquid perpetuals.

Without a wallet, paid tools still answer: they return the price, network and payee instead of data, so you can see what a call would cost before paying for anything.

## Step 4: Enable Paid Analysis

Paid tools cost $0.01 to $0.06 each, in USDC on Base, over [x402](https://x402.org). Since 0.5.2 the x402 client ships with the package, so the same `uvx` command can pay; there is no extra to install. Add a wallet key and, if you like, tighter limits:

```json
{
  "mcpServers": {
    "cerebrus-pulse": {
      "command": "uvx",
      "args": ["cerebrus-pulse-mcp"],
      "env": {
        "CEREBRUS_WALLET_KEY": "<private key of a dedicated, low-balance Base wallet>",
        "CEREBRUS_MAX_PAYMENT_USD": "0.10",
        "CEREBRUS_MAX_SPEND_USD": "1.00"
      }
    }
  }
}
```

The key sits in plain text in this file, so use a hot wallet that holds a few dollars of USDC on Base and nothing else. It needs no ETH: x402 payments are gasless for the payer.

Auto-payment checks every payment before signing it:

| Variable | Default | Meaning |
|---|---|---|
| `CEREBRUS_MAX_PAYMENT_USD` | `0.10` | Most one call may cost. The priciest tool is $0.06. |
| `CEREBRUS_MAX_SPEND_USD` | `1.00` | Total the server may sign until it restarts. |
| `CEREBRUS_ALLOWED_PAYTO` | the published Cerebrus Pulse Base address | Who may be paid. |

Only USDC on Base is paid automatically. A refused payment comes back as `"status": "payment_blocked"` with the reason, and nothing is signed.

Now try:

> "Give me a full technical analysis of BTC"

> "Where are the ETH liquidation clusters?"

> "What's the overall market stress level right now?"

## Also Works With

- **Cursor**: the same `mcpServers` block in `.cursor/mcp.json`
- **Windsurf**: the same block in its MCP config
- **Claude Code**: `claude mcp add cerebrus-pulse -- uvx cerebrus-pulse-mcp`, or the same `mcpServers` block in a project's `.mcp.json`

## Troubleshooting

**"Tool not found"** — Restart Claude Desktop after editing the config.

**`payment_required`** — The tool works, but no wallet is configured. Set `CEREBRUS_WALLET_KEY`.

**`payment_blocked`** — A spend limit refused the payment; the reason says which one. Restart the server to reset `CEREBRUS_MAX_SPEND_USD`.

**Server fails to start** — Run `uvx cerebrus-pulse-mcp --json health` in a terminal to see the error. Make sure `uvx` is on your PATH and you get 0.5.2 or later (`uvx cerebrus-pulse-mcp@latest --json health`).

## Next Steps

- [Trading Journal](../02-trading-journal/) — review your trades against live data
- [Market Scanner](../03-market-scanner/) — a daily scan for opportunities
