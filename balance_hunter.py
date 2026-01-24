#!/usr/bin/env python3
"""
BALANCE HUNTER v1.0
Scans all derived addresses for ANY value across multiple chains
"""

import asyncio
import csv
import json
import sys
from datetime import datetime

# Free RPC endpoints
CHAINS = {
    "ETH": "https://eth.llamarpc.com",
    "Base": "https://mainnet.base.org", 
    "Polygon": "https://polygon-rpc.com",
    "BSC": "https://bsc-dataseed.binance.org",
    "Arbitrum": "https://arb1.arbitrum.io/rpc",
}

# Batch size for RPC calls
BATCH_SIZE = 50
RATE_LIMIT_DELAY = 0.5

class BalanceHunter:
    def __init__(self, addresses_file: str):
        self.addresses = []
        self.found = []
        self.scanned = 0
        self.load_addresses(addresses_file)
        
    def load_addresses(self, filepath: str):
        """Load addresses from CSV"""
        print(f"📂 Loading addresses from {filepath}...")
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = row.get('address_checksum') or row.get('address')
                privkey = row.get('privkey') or row.get('private_key')
                label = row.get('label', 'unknown')
                if addr and privkey:
                    self.addresses.append({
                        'address': addr,
                        'privkey': privkey,
                        'label': label
                    })
        print(f"✅ Loaded {len(self.addresses)} addresses with keys")

    async def check_balance(self, session, chain: str, rpc: str, address: str) -> float:
        """Check balance on a single chain"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"],
                "id": 1
            }
            async with session.post(rpc, json=payload, timeout=10) as resp:
                data = await resp.json()
                if "result" in data:
                    wei = int(data["result"], 16)
                    return wei / 1e18
        except Exception as e:
            pass
        return 0.0

    async def scan_address(self, session, addr_data: dict) -> dict:
        """Scan single address across all chains"""
        address = addr_data['address']
        results = {"address": address, "privkey": addr_data['privkey'], "label": addr_data['label'], "balances": {}}
        total_value = 0.0
        
        for chain, rpc in CHAINS.items():
            balance = await self.check_balance(session, chain, rpc, address)
            if balance > 0:
                results["balances"][chain] = balance
                # Rough USD estimates
                prices = {"ETH": 3500, "Base": 3500, "Polygon": 1, "BSC": 600, "Arbitrum": 3500}
                total_value += balance * prices.get(chain, 0)
        
        results["total_usd"] = total_value
        return results

    async def scan_batch(self, session, batch: list) -> list:
        """Scan a batch of addresses"""
        tasks = [self.scan_address(session, addr) for addr in batch]
        return await asyncio.gather(*tasks)

    async def hunt(self):
        """Main hunting loop"""
        import aiohttp
        
        print(f"\n🎯 BALANCE HUNTER STARTING")
        print(f"   Addresses: {len(self.addresses)}")
        print(f"   Chains: {', '.join(CHAINS.keys())}")
        print(f"   Est. time: ~{len(self.addresses) * len(CHAINS) * 0.1 / 60:.0f} minutes")
        print("=" * 50)
        
        start_time = datetime.now()
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(self.addresses), BATCH_SIZE):
                batch = self.addresses[i:i+BATCH_SIZE]
                results = await self.scan_batch(session, batch)
                
                for r in results:
                    self.scanned += 1
                    if r["total_usd"] > 0.01:  # More than 1 cent
                        self.found.append(r)
                        print(f"\n💰 FOUND VALUE!")
                        print(f"   Address: {r['address']}")
                        print(f"   Label: {r['label']}")
                        print(f"   Balances: {r['balances']}")
                        print(f"   Total: ${r['total_usd']:.2f}")
                        print(f"   Key: {r['privkey'][:16]}...")
                
                # Progress
                pct = (self.scanned / len(self.addresses)) * 100
                if self.scanned % 200 == 0:
                    elapsed = (datetime.now() - start_time).seconds
                    rate = self.scanned / max(elapsed, 1)
                    eta = (len(self.addresses) - self.scanned) / max(rate, 0.1)
                    print(f"⏳ {self.scanned}/{len(self.addresses)} ({pct:.1f}%) | Found: {len(self.found)} | ETA: {eta:.0f}s")
                
                await asyncio.sleep(RATE_LIMIT_DELAY)
        
        return self.found

    def save_results(self, filepath: str):
        """Save found wallets to file"""
        with open(filepath, 'w') as f:
            json.dump({
                "scan_time": datetime.now().isoformat(),
                "total_scanned": self.scanned,
                "total_found": len(self.found),
                "wallets": self.found
            }, f, indent=2)
        print(f"\n💾 Results saved to {filepath}")

    def print_summary(self):
        """Print final summary"""
        print("\n" + "=" * 50)
        print("🏁 SCAN COMPLETE")
        print("=" * 50)
        print(f"   Scanned: {self.scanned} addresses")
        print(f"   Found: {len(self.found)} with value")
        
        if self.found:
            total = sum(w['total_usd'] for w in self.found)
            print(f"   Total Value: ${total:.2f}")
            print("\n📋 RECOVERABLE WALLETS:")
            for w in sorted(self.found, key=lambda x: x['total_usd'], reverse=True):
                print(f"   ${w['total_usd']:.2f} - {w['address'][:20]}... ({w['label']})")
        else:
            print("   No value found in scanned addresses")


async def main():
    import sys
    
    # Default or arg
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "extended_derivation.csv"
    
    hunter = BalanceHunter(csv_file)
    
    if len(hunter.addresses) == 0:
        print("❌ No addresses loaded!")
        return
    
    await hunter.hunt()
    hunter.print_summary()
    hunter.save_results("found_wallets.json")


if __name__ == "__main__":
    asyncio.run(main())
