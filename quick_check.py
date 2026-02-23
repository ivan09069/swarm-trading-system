#!/usr/bin/env python3
"""Quick balance check for specific addresses"""
import asyncio
import aiohttp
import json
import os

CHAINS = {
    "ETH": "https://eth.llamarpc.com",
    "Base": "https://mainnet.base.org", 
    "Polygon": "https://polygon-rpc.com",
    "BSC": "https://bsc-dataseed.binance.org",
    "Arbitrum": "https://arb1.arbitrum.io/rpc",
    "Optimism": "https://mainnet.optimism.io",
}

def load_addresses():
    # Try env var first
    raw = os.environ.get("QUICK_CHECK_ADDRESSES", "")
    if raw:
        try:
            return json.loads(raw)
        except Exception as e:
            print(f"Warning: QUICK_CHECK_ADDRESSES parse error: {e}")

    # Try JSON file
    path = os.environ.get("ADDRESSES_FILE", "addresses.json")
    if os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: addresses file parse error: {e}")

    print("Warning: No addresses configured. Set QUICK_CHECK_ADDRESSES or ADDRESSES_FILE.")
    return []

ADDRESSES = [(a["address"], a["label"], a.get("key", "UNKNOWN")) for a in load_addresses()]

async def check_balance(session, chain, rpc, address):
    try:
        payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}
        async with session.post(rpc, json=payload, timeout=10) as resp:
            data = await resp.json()
            if "result" in data:
                wei = int(data["result"], 16)
                return wei / 1e18
    except:
        pass
    return 0.0

async def main():
    print("Checking balances across all chains...")
    async with aiohttp.ClientSession() as session:
        for addr, label, key in ADDRESSES:
            print(f"\n{label}: {addr}")
            print(f"  Key: {'available' if key != 'UNKNOWN' else 'UNKNOWN'}")
            total = 0
            for chain, rpc in CHAINS.items():
                bal = await check_balance(session, chain, rpc, addr)
                if bal > 0:
                    print(f"  {chain}: {bal:.8f}")
                    total += bal
            if total == 0:
                print("  No balance found")
            else:
                print(f"  TOTAL: {total:.8f}")

asyncio.run(main())
