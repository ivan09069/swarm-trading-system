#!/usr/bin/env python3
"""Quick balance check for specific addresses"""
import asyncio
import aiohttp

CHAINS = {
    "ETH": "https://eth.llamarpc.com",
    "Base": "https://mainnet.base.org", 
    "Polygon": "https://polygon-rpc.com",
    "BSC": "https://bsc-dataseed.binance.org",
    "Arbitrum": "https://arb1.arbitrum.io/rpc",
    "Optimism": "https://mainnet.optimism.io",
}

ADDRESSES = [
    ("0x7adBdd339eC411A5B3364BFD6563548d57721fD9", "Seed2_Napkin", "fbdef321518cf5d3eb5736831b2ba591ec9d41be8adc01d2e5569202d7e3b975"),
    ("0x90A66EEA7c4e6918678E1c6c5D193746468217a2", "Seed10_Sponsor", "8db29399650a9bae618e0b44ce720e1b8967c068b976d0a427b7a38c60f9997b"),
    ("0x3685a08e2e4855cfcf126b2c791a5c32a1f8e0e3", "HighValue_Target1", "UNKNOWN"),
    ("0x58BBfee7D62674856851A553AA75A1eE5d86Bec6", "HighValue_Target2", "UNKNOWN"),
]

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
            print(f"  Key: {key[:20]}..." if key != "UNKNOWN" else "  Key: UNKNOWN")
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
