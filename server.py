#!/usr/bin/env python3
"""BaseOracle MCP Server v1.0.0 — Port 11701
Base Network Intelligence for AI Agents.
Base is Coinbase's L2 on Ethereum (OP Stack). ETH/cbETH price,
gas intelligence, protocol TVL, RWA on Base, stablecoin check,
wallet intelligence, DeFi yields, contract verification.
Evidence-grade data for institutional L2 finance and Coinbase ecosystem.
"""
import os, sys, json, logging, aiohttp, asyncio
from datetime import datetime, timezone

sys.path.insert(0, "/root/whitelabel")
from shared.utils.mcp_base import WhitelabelMCPServer

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [BaseOracle] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler("/root/whitelabel/logs/baseoracle.log", mode="a")])
logger = logging.getLogger("BaseOracle")

PRODUCT_NAME = "BaseOracle"
VERSION      = "1.0.0"
PORT_MCP     = 11701
PORT_HEALTH  = 11702

BASE_RPC   = "https://mainnet.base.org"
BASESCAN   = "https://api.basescan.org/api"
LLAMA      = "https://api.llama.fi"
LLAMA_Y    = "https://yields.llama.fi"
CG         = "https://api.coingecko.com/api/v3"
BASESCAN_KEY = os.getenv("BASESCAN_API_KEY", "YourApiKeyToken")
HEADERS    = {"User-Agent": "BaseOracle-ToolOracle/1.0", "Accept": "application/json"}

def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

async def get(url, params=None, timeout=15):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, headers=HEADERS,
                             timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                if r.status == 200:
                    return await r.json(content_type=None)
                return {"error": f"HTTP {r.status}"}
    except Exception as e:
        return {"error": str(e)}

async def base_rpc(method, params=None):
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(BASE_RPC, json=body,
                              headers={"Content-Type": "application/json"},
                              timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    d = await r.json(content_type=None)
                    return d.get("result")
    except:
        pass
    return None

async def basescan(params, timeout=15):
    p = {"apikey": BASESCAN_KEY, **params}
    return await get(BASESCAN, p, timeout)

def risk_grade(score):
    if score >= 80: return "A"
    if score >= 60: return "B"
    if score >= 40: return "C"
    if score >= 20: return "D"
    return "F"

def wei_to_eth(hex_val):
    try:
        return round(int(hex_val, 16) / 1e18, 6)
    except:
        return 0

async def handle_overview(args):
    eth_price, tvl_data = await asyncio.gather(
        get(f"{CG}/simple/price", {"ids": "ethereum,coinbase-wrapped-staked-eth",
            "vs_currencies": "usd,eur", "include_24hr_change": "true",
            "include_market_cap": "true", "include_24hr_vol": "true"}),
        get(f"{LLAMA}/v2/chains"),
    )
    eth = eth_price.get("ethereum", {}) if isinstance(eth_price, dict) else {}
    cbeth = eth_price.get("coinbase-wrapped-staked-eth", {}) if isinstance(eth_price, dict) else {}
    base_tvl = 0
    if isinstance(tvl_data, list):
        for c in tvl_data:
            if c.get("name") == "Base":
                base_tvl = c.get("tvl", 0)
                break
    block_hex = await base_rpc("eth_blockNumber")
    block = int(block_hex, 16) if block_hex else 0
    gas_hex = await base_rpc("eth_gasPrice")
    gas_gwei = round(int(gas_hex, 16) / 1e9, 6) if gas_hex else None
    return {
        "chain": "Base", "network": "mainnet", "chain_id": 8453,
        "l2_stack": "OP Stack (Optimism)", "operator": "Coinbase",
        "timestamp": ts(),
        "eth_price": {"usd": eth.get("usd"), "eur": eth.get("eur"),
                      "change_24h": eth.get("usd_24h_change")},
        "cbeth_price": {"usd": cbeth.get("usd"), "eur": cbeth.get("eur"),
                        "vs_eth_premium": round(cbeth.get("usd", 0) / eth.get("usd", 1) - 1, 4)
                        if eth.get("usd") else None},
        "network_stats": {"latest_block": block, "total_tvl_usd": round(base_tvl, 2),
                          "gas_gwei": gas_gwei},
        "advantages": ["Low fees (OP Stack)", "Coinbase-backed", "EVM compatible",
                       "Ethereum security", "Growing RWA ecosystem"],
        "source": "CoinGecko + DefiLlama + Base RPC"
    }

async def handle_gas(args):
    gas_hex, eth_price = await asyncio.gather(
        base_rpc("eth_gasPrice"),
        get(f"{CG}/simple/price", {"ids": "ethereum", "vs_currencies": "usd"}),
    )
    eth_usd = eth_price.get("ethereum", {}).get("usd", 0) if isinstance(eth_price, dict) else 0
    gas_gwei = round(int(gas_hex, 16) / 1e9, 6) if gas_hex else 0.001

    def gwei_to_usd(gwei, gas_units):
        try:
            return round(float(gwei) * gas_units * 1e-9 * eth_usd, 6)
        except:
            return None

    return {
        "timestamp": ts(), "eth_price_usd": eth_usd,
        "gas_price_gwei": gas_gwei,
        "estimated_cost_usd": {
            "simple_transfer_21k": gwei_to_usd(gas_gwei, 21000),
            "erc20_transfer_65k": gwei_to_usd(gas_gwei, 65000),
            "uniswap_v3_swap_130k": gwei_to_usd(gas_gwei, 130000),
        },
        "l2_advantage": "Base fees are ~100-1000x cheaper than Ethereum mainnet",
        "settlement": "Settled to Ethereum every few minutes via OP Stack",
        "source": "Base RPC + CoinGecko"
    }

async def handle_contract_verify(args):
    contract = args.get("contract_address", "").strip()
    if not contract:
        return {"error": "contract_address required"}
    source, abi = await asyncio.gather(
        basescan({"module": "contract", "action": "getsourcecode", "address": contract}),
        basescan({"module": "contract", "action": "getabi", "address": contract}),
    )
    src_result = {}
    is_verified = False
    if isinstance(source, dict) and source.get("status") == "1":
        r = source.get("result", [{}])
        src_result = r[0] if isinstance(r, list) and r else {}
        is_verified = bool(src_result.get("SourceCode"))
    abi_ok = isinstance(abi, dict) and abi.get("status") == "1"
    score = 70 if is_verified else 20
    if abi_ok: score += 10
    return {
        "contract": contract, "chain": "Base", "verified": is_verified,
        "abi_available": abi_ok,
        "contract_name": src_result.get("ContractName"),
        "compiler": src_result.get("CompilerVersion"),
        "proxy": src_result.get("Proxy") == "1",
        "implementation": src_result.get("Implementation") or None,
        "risk_score": score, "risk_grade": risk_grade(score),
        "timestamp": ts(), "source": "BaseScan"
    }

async def handle_protocol_tvl(args):
    protocol = args.get("protocol", "").strip().lower()
    if not protocol:
        all_p = await get(f"{LLAMA}/protocols")
        base_p = []
        if isinstance(all_p, list):
            for p in all_p:
                if "Base" in p.get("chains", []):
                    tvl_raw = p.get("tvl")
                    tvl = tvl_raw[-1].get("totalLiquidityUSD") if isinstance(tvl_raw, list) and tvl_raw else tvl_raw
                    base_p.append({"name": p.get("name"), "slug": p.get("slug"),
                                   "tvl_usd": tvl, "category": p.get("category")})
            base_p.sort(key=lambda x: x.get("tvl_usd") or 0, reverse=True)
        return {"top_base_protocols": base_p[:20], "count": len(base_p),
                "timestamp": ts(), "source": "DefiLlama"}
    data = await get(f"{LLAMA}/protocol/{protocol}")
    if isinstance(data, dict) and "error" not in data:
        tvl_raw = data.get("tvl")
        tvl = tvl_raw[-1].get("totalLiquidityUSD") if isinstance(tvl_raw, list) and tvl_raw else tvl_raw
        return {"protocol": data.get("name"), "category": data.get("category"),
                "tvl_total_usd": tvl, "chains": data.get("chains", []),
                "change_1d": data.get("change_1d"), "change_7d": data.get("change_7d"),
                "timestamp": ts(), "source": "DefiLlama"}
    return {"error": f"Protocol '{protocol}' not found", "timestamp": ts()}

async def handle_stablecoin_check(args):
    symbol = args.get("symbol", "USDC").upper()
    BASE_STABLES = {
        "USDC":  "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        "USDBC": "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca",
        "DAI":   "0x50c5725949a6f0c72e6c4a641f24049a917db0cb",
        "WETH":  "0x4200000000000000000000000000000000000006",
    }
    contract = BASE_STABLES.get(symbol) or args.get("contract_address", "")
    if not contract:
        return {"known_stablecoins": list(BASE_STABLES.keys())}
    price_data = await get(f"{CG}/simple/token_price/base",
                           {"contract_addresses": contract, "vs_currencies": "usd"})
    price = None
    if isinstance(price_data, dict):
        price = price_data.get(contract.lower(), {}).get("usd")
    peg_target = 1.0 if symbol not in ("WETH",) else None
    peg_dev = abs(price - peg_target) if price and peg_target else None
    peg_status = "STABLE" if peg_dev is not None and peg_dev < 0.005 else \
                 "MINOR_DEVIATION" if peg_dev is not None and peg_dev < 0.02 else \
                 ("N/A" if not peg_target else "DEPEGGED")
    score = 90 if peg_status == "STABLE" else 50
    return {
        "symbol": symbol, "chain": "Base", "contract": contract,
        "price_usd": price,
        "peg_deviation_pct": round(peg_dev * 100, 4) if peg_dev is not None else None,
        "peg_status": peg_status, "risk_score": score, "risk_grade": risk_grade(score),
        "timestamp": ts(), "source": "CoinGecko"
    }

async def handle_rwa_on_base(args):
    RWA_BASE_PROTOCOLS = [
        "moonwell-base", "aave-v3", "compound-v3",
        "superstate", "ondo-finance", "backed-finance"
    ]
    slug = args.get("protocol", "").strip().lower()
    if slug:
        data = await get(f"{LLAMA}/protocol/{slug}")
        if isinstance(data, dict) and "error" not in data:
            tvl_raw = data.get("tvl")
            tvl = tvl_raw[-1].get("totalLiquidityUSD") if isinstance(tvl_raw, list) and tvl_raw else tvl_raw
            return {"protocol": data.get("name"), "category": data.get("category"),
                    "tvl_usd": tvl, "chains": data.get("chains", []),
                    "timestamp": ts(), "source": "DefiLlama"}
    results = []
    for s in RWA_BASE_PROTOCOLS:
        d = await get(f"{LLAMA}/protocol/{s}")
        if isinstance(d, dict) and "error" not in d and d.get("tvl"):
            tvl_raw = d.get("tvl")
            tvl = tvl_raw[-1].get("totalLiquidityUSD") if isinstance(tvl_raw, list) and tvl_raw else tvl_raw
            results.append({"protocol": d.get("name"), "category": d.get("category"),
                            "tvl_usd": tvl, "chains": d.get("chains", [])[:3]})
    results.sort(key=lambda x: x.get("tvl_usd") or 0, reverse=True)
    return {
        "rwa_and_lending_on_base": results,
        "base_advantages_for_rwa": [
            "Coinbase institutional backing",
            "EVM-compatible for existing RWA contracts",
            "Low-cost settlement vs Ethereum mainnet",
            "KYC/compliance via Coinbase identity layer",
            "cbETH as collateral for tokenized finance"
        ],
        "timestamp": ts(), "source": "DefiLlama"
    }

async def handle_defi_yields(args):
    min_tvl = args.get("min_tvl_usd", 500_000)
    limit = min(args.get("limit", 20), 50)
    pools = await get(f"{LLAMA_Y}/pools")
    data = pools.get("data", []) if isinstance(pools, dict) else []
    results = []
    for p in data:
        if p.get("chain", "").lower() == "base" and p.get("tvlUsd", 0) >= min_tvl:
            results.append({
                "pool": p.get("pool"), "project": p.get("project"),
                "symbol": p.get("symbol"), "apy_pct": round(p.get("apy") or 0, 2),
                "tvl_usd": round(p.get("tvlUsd") or 0, 0), "il_risk": p.get("ilRisk"),
            })
    results.sort(key=lambda x: x.get("tvl_usd", 0), reverse=True)
    return {"chain": "Base", "yields": results[:limit], "total_found": len(results),
            "timestamp": ts(), "source": "DefiLlama Yields"}

async def handle_wallet_intel(args):
    address = args.get("address", "").strip()
    if not address:
        return {"error": "address required"}
    bal_hex, txs = await asyncio.gather(
        base_rpc("eth_getBalance", [address, "latest"]),
        basescan({"module": "account", "action": "txlist",
                  "address": address, "page": "1", "offset": "10", "sort": "desc"}),
    )
    eth_bal = wei_to_eth(bal_hex) if bal_hex else 0
    price_data = await get(f"{CG}/simple/price", {"ids": "ethereum", "vs_currencies": "usd"})
    eth_usd = price_data.get("ethereum", {}).get("usd", 0) if isinstance(price_data, dict) else 0
    recent_txs = []
    if isinstance(txs, dict) and txs.get("status") == "1":
        for tx in (txs.get("result") or [])[:5]:
            recent_txs.append({
                "hash": tx.get("hash"), "from": tx.get("from"), "to": tx.get("to"),
                "value_eth": round(int(tx.get("value", "0")) / 1e18, 6),
                "timestamp": datetime.fromtimestamp(int(tx.get("timeStamp", 0)), tz=timezone.utc)
                             .strftime("%Y-%m-%dT%H:%M:%SZ")
            })
    return {
        "address": address, "chain": "Base",
        "eth_balance": eth_bal, "eth_balance_usd": round(eth_bal * eth_usd, 2),
        "recent_transactions": recent_txs,
        "timestamp": ts(), "source": "Base RPC + BaseScan"
    }

def build_server():
    server = WhitelabelMCPServer(
        product_name=PRODUCT_NAME, product_slug="baseoracle",
        version=VERSION, port_mcp=PORT_MCP, port_health=PORT_HEALTH,
    )
    server.register_tool("base_overview",
        "Base L2 ecosystem overview: ETH price, cbETH, gas, TVL, OP Stack info",
        {"type": "object", "properties": {}, "required": []}, handle_overview)
    server.register_tool("base_gas",
        "Base network gas tracker with USD cost estimates — much cheaper than Ethereum mainnet",
        {"type": "object", "properties": {}, "required": []}, handle_gas)
    server.register_tool("base_contract_verify",
        "Verify Base smart contract: source code, ABI, proxy detection on BaseScan",
        {"type": "object", "properties": {"contract_address": {"type": "string"}}, "required": ["contract_address"]}, handle_contract_verify)
    server.register_tool("base_protocol_tvl",
        "Base DeFi protocol TVL. Leave protocol empty for top-20 list.",
        {"type": "object", "properties": {"protocol": {"type": "string"}}, "required": []}, handle_protocol_tvl)
    server.register_tool("base_stablecoin_check",
        "Base stablecoin peg check: USDC, USDbC, DAI on Base L2",
        {"type": "object", "properties": {
            "symbol": {"type": "string", "description": "USDC, USDBC, DAI"},
            "contract_address": {"type": "string"}}, "required": []}, handle_stablecoin_check)
    server.register_tool("base_rwa",
        "Real-world assets and institutional lending on Base: Moonwell, Aave, Compound, RWA protocols",
        {"type": "object", "properties": {"protocol": {"type": "string"}}, "required": []}, handle_rwa_on_base)
    server.register_tool("base_defi_yields",
        "Top DeFi yield opportunities on Base filtered by TVL",
        {"type": "object", "properties": {
            "min_tvl_usd": {"type": "number", "default": 500000},
            "limit": {"type": "integer", "default": 20}}, "required": []}, handle_defi_yields)
    server.register_tool("base_wallet_intel",
        "Base wallet intelligence: ETH balance, recent transactions on Base L2",
        {"type": "object", "properties": {"address": {"type": "string"}}, "required": ["address"]}, handle_wallet_intel)
    return server

if __name__ == "__main__":
    srv = build_server()
    srv.run()
