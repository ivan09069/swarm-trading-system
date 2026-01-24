#!/usr/bin/env python3
"""
WORKER 2: SWARM SENTINEL
AI-powered trading agent using Groq for analysis
"""

import asyncio
import json
from typing import Dict, List
from datetime import datetime

class SentinelWorker:
    def __init__(self, results_queue, groq_key: str, rpc_url: str):
        self.results_queue = results_queue
        self.groq_key = groq_key
        self.rpc_url = rpc_url
        self.running = False
        self.signals_generated = 0
        
    async def get_token_data(self, token_address: str) -> Dict:
        """Fetch token data from chain"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Get basic token info via RPC
                resp = await client.post(self.rpc_url, json={
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [{"to": token_address, "data": "0x95d89b41"}, "latest"],
                    "id": 1
                }, timeout=10)
                return resp.json()
        except:
            return {}
    
    async def analyze_with_groq(self, market_data: str) -> Dict:
        """Use Groq to analyze market conditions"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.groq_key}"},
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": "You are a DeFi trading analyst. Analyze data and output JSON: {action: BUY/SELL/HOLD, confidence: 0-100, reason: string}"},
                            {"role": "user", "content": market_data}
                        ],
                        "max_tokens": 150
                    },
                    timeout=15
                )
                content = resp.json()["choices"][0]["message"]["content"]
                return json.loads(content) if "{" in content else {"action": "HOLD", "confidence": 0}
        except Exception as e:
            return {"action": "HOLD", "confidence": 0, "error": str(e)}

    async def monitor_dex_prices(self):
        """Monitor DEX prices for opportunities"""
        # Popular Base DEX tokens to watch
        WATCH_TOKENS = [
            ("WETH", "0x4200000000000000000000000000000000000006"),
            ("USDC", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
            ("AERO", "0x940181a94A35A4569E4529A3CDfB74e38FD98631"),
        ]
        
        while self.running:
            try:
                for name, addr in WATCH_TOKENS:
                    data = await self.get_token_data(addr)
                    
                    # Simplified analysis - in production would include price feeds
                    analysis = await self.analyze_with_groq(
                        f"Token: {name}, Address: {addr}, Data: {json.dumps(data)[:200]}"
                    )
                    
                    if analysis.get("confidence", 0) > 70:
                        self.signals_generated += 1
                        await self.results_queue.put({
                            "worker": "sentinel",
                            "type": "trade_signal",
                            "data": {
                                "token": name,
                                "address": addr,
                                "action": analysis.get("action"),
                                "confidence": analysis.get("confidence"),
                                "reason": analysis.get("reason", ""),
                                "timestamp": datetime.now().isoformat()
                            }
                        })
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                await self.results_queue.put({
                    "worker": "sentinel",
                    "type": "error",
                    "data": str(e)
                })
                await asyncio.sleep(10)
    
    async def run(self):
        self.running = True
        print("📈 Sentinel: Starting market monitoring...")
        await self.monitor_dex_prices()
    
    def stop(self):
        self.running = False
