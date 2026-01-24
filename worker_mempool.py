#!/usr/bin/env python3
"""
WORKER 3: MEMPOOL MONITOR
Watches pending transactions for sniping opportunities
"""

import asyncio
import json
from datetime import datetime

# DEX Router addresses to monitor
DEX_ROUTERS = {
    "uniswap_v3": "0x2626664c2603336E57B271c5C0b26F421741e481",
    "aerodrome": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
    "baseswap": "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86",
}

# Function signatures for swaps
SWAP_SIGS = [
    "0x38ed1739",  # swapExactTokensForTokens
    "0x7ff36ab5",  # swapExactETHForTokens
    "0x18cbafe5",  # swapExactTokensForETH
    "0x5c11d795",  # swapExactTokensForTokensSupportingFeeOnTransferTokens
]

class MempoolWorker:
    def __init__(self, results_queue, rpc_url: str):
        self.results_queue = results_queue
        self.rpc_url = rpc_url
        self.running = False
        self.alerts_sent = 0
        self.pending_cache = set()
        
    async def get_pending_txs(self) -> list:
        """Get pending transactions from mempool"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.rpc_url, json={
                    "jsonrpc": "2.0",
                    "method": "eth_getBlockByNumber",
                    "params": ["pending", True],
                    "id": 1
                }, timeout=10)
                data = resp.json()
                return data.get("result", {}).get("transactions", [])
        except:
            return []

    def is_swap_tx(self, tx: dict) -> bool:
        """Check if transaction is a DEX swap"""
        to_addr = tx.get("to", "").lower()
        input_data = tx.get("input", "")[:10]
        
        is_dex = any(router.lower() == to_addr for router in DEX_ROUTERS.values())
        is_swap = any(sig in input_data for sig in SWAP_SIGS)
        
        return is_dex and is_swap
    
    def parse_swap(self, tx: dict) -> dict:
        """Parse swap transaction details"""
        return {
            "hash": tx.get("hash"),
            "from": tx.get("from"),
            "to": tx.get("to"),
            "value": int(tx.get("value", "0x0"), 16) / 1e18,
            "gas_price": int(tx.get("gasPrice", "0x0"), 16) / 1e9,
            "input": tx.get("input", "")[:66]
        }
    
    async def monitor(self):
        """Main monitoring loop"""
        while self.running:
            try:
                txs = await self.get_pending_txs()
                
                for tx in txs:
                    tx_hash = tx.get("hash", "")
                    
                    if tx_hash in self.pending_cache:
                        continue
                    
                    self.pending_cache.add(tx_hash)
                    
                    if self.is_swap_tx(tx):
                        swap_data = self.parse_swap(tx)
                        self.alerts_sent += 1
                        
                        await self.results_queue.put({
                            "worker": "mempool",
                            "type": "mempool_alert",
                            "data": {
                                "event": "SWAP_DETECTED",
                                "tx_hash": tx_hash,
                                "value_eth": swap_data["value"],
                                "gas_gwei": swap_data["gas_price"],
                                "timestamp": datetime.now().isoformat()
                            }
                        })
                
                # Keep cache manageable
                if len(self.pending_cache) > 10000:
                    self.pending_cache = set(list(self.pending_cache)[-5000:])
                
                await asyncio.sleep(1)  # Poll every second
                
            except Exception as e:
                await asyncio.sleep(5)
    
    async def run(self):
        self.running = True
        print("🔔 Mempool: Starting transaction monitoring...")
        await self.monitor()
    
    def stop(self):
        self.running = False
