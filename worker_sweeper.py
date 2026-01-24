#!/usr/bin/env python3
"""
WORKER 4: BALANCE SWEEPER
Multi-chain balance checker and sweeper
"""

import asyncio
from typing import Dict, List
from datetime import datetime

# RPC endpoints for different chains
CHAIN_RPCS = {
    "base": "https://mainnet.base.org",
    "ethereum": "https://eth.llamarpc.com",
    "polygon": "https://polygon-rpc.com",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "bsc": "https://bsc-dataseed.binance.org",
}

# Known controlled wallets
CONTROLLED_WALLETS = [
    {
        "address": "0x7adBdd339eC411A5B3364BFD6563548d57721fD9",
        "privkey": "fbdef321518cf5d3eb5736831b2ba591ec9d41be8adc01d2e5569202d7e3b975",
        "name": "Seed2_Napkin"
    },
    {
        "address": "0x90A66EEA7c4e6918678E1c6c5D193746468217a2",
        "privkey": "8db29399650a9bae618e0b44ce720e1b8967c068b976d0a427b7a38c60f9997b",
        "name": "Seed10_Sponsor"
    },
]

class SweeperWorker:
    def __init__(self, results_queue, command_queue):
        self.results_queue = results_queue
        self.command_queue = command_queue
        self.running = False
        self.balances_found = []
        self.total_value_usd = 0.0

    async def get_balance(self, address: str, rpc_url: str, chain: str) -> float:
        """Get native token balance"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(rpc_url, json={
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }, timeout=10)
                result = resp.json().get("result", "0x0")
                return int(result, 16) / 1e18
        except:
            return 0.0
    
    async def check_all_chains(self, wallet: Dict) -> List[Dict]:
        """Check balance on all chains"""
        results = []
        address = wallet["address"]
        
        for chain, rpc in CHAIN_RPCS.items():
            balance = await self.get_balance(address, rpc, chain)
            
            if balance > 0.0001:  # Dust threshold
                results.append({
                    "address": address,
                    "chain": chain,
                    "balance": balance,
                    "privkey": wallet.get("privkey"),
                    "name": wallet.get("name")
                })
        
        return results
    
    async def sweep_wallet(self, target: Dict):
        """Sweep funds from wallet to destination"""
        # This would execute the actual sweep transaction
        # For safety, just log the opportunity
        print(f"💸 SWEEP READY: {target['address'][:10]}... on {target.get('chain', 'unknown')}")
        print(f"   Balance: {target.get('balance', 0)} native")
        # Actual sweep would use web3.py to send transaction

    async def run(self):
        """Main worker loop"""
        self.running = True
        print("💰 Sweeper: Starting multi-chain balance scan...")
        
        # Initial scan of known wallets
        for wallet in CONTROLLED_WALLETS:
            results = await self.check_all_chains(wallet)
            
            for r in results:
                self.balances_found.append(r)
                await self.results_queue.put({
                    "worker": "sweeper",
                    "type": "balance_found",
                    "data": {
                        "address": r["address"],
                        "chain": r["chain"],
                        "balance": r["balance"],
                        "value_usd": r["balance"] * 2500,  # Rough ETH price estimate
                        "name": r["name"]
                    }
                })
        
        # Listen for commands from orchestrator
        while self.running:
            try:
                # Check for new sweep commands
                try:
                    cmd = await asyncio.wait_for(
                        self.command_queue.get(), 
                        timeout=5.0
                    )
                    
                    if cmd.get("action") == "sweep":
                        await self.sweep_wallet(cmd.get("target", {}))
                        
                    elif cmd.get("action") == "scan":
                        # New wallet to scan
                        wallet = cmd.get("wallet", {})
                        results = await self.check_all_chains(wallet)
                        for r in results:
                            self.balances_found.append(r)
                            
                except asyncio.TimeoutError:
                    pass
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Sweeper error: {e}")
                await asyncio.sleep(5)
    
    def stop(self):
        self.running = False
