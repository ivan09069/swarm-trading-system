#!/usr/bin/env python3
"""
SWARM LAUNCHER v1.1 - Fixed env loading
"""

import asyncio
import os
import sys
from datetime import datetime

# Load .env file manually
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    print(f"  Loaded: {key}={value[:20]}...")

load_env()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import ReasoningAgent, RESULTS_QUEUE, COMMAND_QUEUES
from worker_keymatcher import KeyMatcherWorker
from worker_sentinel import SentinelWorker
from worker_mempool import MempoolWorker
from worker_sweeper import SweeperWorker

# Get config AFTER loading env
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
BASE_RPC = os.environ.get("BASE_RPC", "https://mainnet.base.org")

async def main():
    print("=" * 60)
    print("🐝 SWARM SYSTEM v1.1")
    print("=" * 60)
    print(f"Groq API: {'✅ ' + GROQ_KEY[:20] + '...' if GROQ_KEY else '❌ Missing'}")
    print(f"Base RPC: {BASE_RPC}")
    print("=" * 60)
    
    COMMAND_QUEUES["sweeper"] = asyncio.Queue()
    
    orchestrator = ReasoningAgent(GROQ_KEY)
    keymatcher = KeyMatcherWorker(RESULTS_QUEUE)
    sentinel = SentinelWorker(RESULTS_QUEUE, GROQ_KEY, BASE_RPC)
    mempool = MempoolWorker(RESULTS_QUEUE, BASE_RPC)
    sweeper = SweeperWorker(RESULTS_QUEUE, COMMAND_QUEUES["sweeper"])

    print("\n🚀 Launching workers...")
    
    try:
        await asyncio.gather(
            orchestrator.orchestrate(),
            keymatcher.run(max_index=100),
            sentinel.run(),
            mempool.run(),
            sweeper.run(),
        )
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        orchestrator.stop()
        keymatcher.stop()
        sentinel.stop()
        mempool.stop()
        sweeper.stop()

if __name__ == "__main__":
    asyncio.run(main())
