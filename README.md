# 🔵 baseOracle

**Base L2 Intelligence MCP Server** — 8 tools | Part of [ToolOracle](https://tooloracle.io)

![Tools](https://img.shields.io/badge/MCP_Tools-8-10B898?style=flat-square)
![Status](https://img.shields.io/badge/Status-Live-00C853?style=flat-square)
![Chain](https://img.shields.io/badge/Chain-Base_L2-0052FF?style=flat-square)
![Stack](https://img.shields.io/badge/Stack-OP_Stack-FF0420?style=flat-square)
![Tier](https://img.shields.io/badge/Tier-Free-2196F3?style=flat-square)

Base is Coinbase's L2 on Ethereum (OP Stack). ETH/cbETH price, gas intelligence (100-1000x cheaper than mainnet), protocol TVL, RWA on Base, stablecoin check, wallet intelligence, DeFi yields, contract verification.

## Quick Connect

```bash
npx -y mcp-remote https://feedoracle.io/mcp/baseoracle/
```

```json
{
  "mcpServers": {
    "baseoracle": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://feedoracle.io/mcp/baseoracle/"]
    }
  }
}
```

## Tools (8)

| Tool | Description |
|------|-------------|
| `base_overview` | Base L2 overview: ETH price, cbETH premium, gas, TVL, OP Stack info |
| `base_gas` | Gas tracker: ~0.006 gwei — 100-1000x cheaper than Ethereum mainnet |
| `base_contract_verify` | Contract verification: source code, ABI, proxy detection on BaseScan |
| `base_protocol_tvl` | Base DeFi protocol TVL (Aerodrome, Moonwell, Aave, Compound...) |
| `base_stablecoin_check` | Stablecoin peg check: USDC, USDbC, DAI on Base L2 |
| `base_rwa` | RWA and institutional lending on Base: Moonwell, Aave V3, Superstate |
| `base_defi_yields` | Top DeFi yields on Base filtered by TVL |
| `base_wallet_intel` | Wallet intelligence: ETH balance, recent transactions on Base |

## Why Base for Institutional Finance

- **Coinbase backing**: Institutional trust and compliance infrastructure
- **Ultra-low fees**: ~0.006 gwei vs Ethereum mainnet
- **EVM compatible**: All existing Ethereum contracts work on Base
- **Ethereum security**: Settles to Ethereum every few minutes via OP Stack
- **cbETH collateral**: Coinbase's liquid staking token for tokenized finance
- **KYC layer**: Coinbase identity for compliant institutional access

## Part of FeedOracle / ToolOracle

**Blockchain Oracle Suite:**
- [ethOracle](https://github.com/tooloracle/ethoracle) — Ethereum
- [xlmOracle](https://github.com/tooloracle/xlmoracle) — Stellar
- [xrplOracle](https://github.com/tooloracle/xrploracle) — XRP Ledger
- [bnbOracle](https://github.com/tooloracle/bnboracle) — BNB Chain
- [aptOracle](https://github.com/tooloracle/aptoracle) — Aptos
- [baseOracle](https://github.com/tooloracle/baseoracle) — Base L2 (this repo)

## Links

- 🌐 Live: `https://feedoracle.io/mcp/baseoracle/`
- 🏠 Platform: [feedoracle.io](https://feedoracle.io)

---
*Built by [FeedOracle](https://feedoracle.io) — Evidence by Design*
