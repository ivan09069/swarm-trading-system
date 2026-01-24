#!/usr/bin/env python3
"""
WORKER 1: KEY MATCHER v4 - DEEP SCAN
120,000+ addresses across all common derivation paths
"""

import asyncio
from typing import List, Dict, Tuple

HIGH_VALUE_TARGETS = [
    "0x3685a08e2e4855cfcf126b2c791a5c32a1f8e0e3",
    "0x488e3a4bbbb2386ba619eed88319e807c3ddb6c2", 
    "0xf1da71f8b01a9b35e1a193649c5512f36f2755db",
    "0x58bbfee7d62674856851a553aa75a1ee5d86bec6",
    "0x9660503aaedbdb262794ec4f0a659e0e8a8a20c3",
]

SEEDS = [
    ("Seed1", "cousin beach mesh utility maximum error limit pumpkin giggle craft name rookie"),
    ("Seed2", "napkin dream juice smoke salmon talk host disease name honey tray tag"),
    ("Seed3", "oven maze fuel select pulp ghost average tourist plunge erosion swift predict"),
    ("Seed4", "fall enroll impose retreat whip street journey notable tray resemble come often"),
    ("Seed5", "cover jar female achieve repair noodle lyrics shine sniff treat desk shadow because chuckle book nephew endorse napkin peasant crystal arch label chalk clever"),
    ("Seed6", "express useful talent one smile style pretty popular century sphere error green"),
    ("Seed7", "army van defense carry jealous true garbage claim echo media make crunch"),
    ("Seed8", "impulse gossip matrix tuna acoustic brisk stock fish area coil stable fantasy"),
    ("Seed10", "sponsor name tail honey split cradle laundry tiny flash two weather stone"),
    ("Seed11", "fiscal lucky ceiling resource peasant nerve afraid around whip panic apple maximum reunion rate leaf leave genre display often fork cup brisk relief weekend"),
]

# All common derivation paths
DERIVATION_PATHS = [
    ("ETH Standard", "m/44'/60'/0'/0/{}"),
    ("ETH Ledger", "m/44'/60'/0'/{}"),
    ("ETH Legacy", "m/44'/60'/{}'/0/0"),
    ("ETH Account", "m/44'/60'/{}'/0'/0"),
    ("Polygon", "m/44'/137'/0'/0/{}"),
    ("BSC", "m/44'/56'/0'/0/{}"),
]

MAX_INDEX = 2000  # Deep scan

def get_derive_func():
    try:
        from hdwallet import HDWallet
        from hdwallet.symbols import ETH
        def derive(seed: str, path: str):
            try:
                hdw = HDWallet(symbol=ETH)
                hdw.from_mnemonic(seed)
                hdw.from_path(path)
                return hdw.p2pkh_address().lower(), hdw.private_key()
            except:
                return None, None
        return derive
    except:
        pass
    try:
        from eth_account import Account
        Account.enable_unaudited_hdwallet_features()
        def derive(seed: str, path: str):
            try:
                acct = Account.from_mnemonic(seed, account_path=path)
                return acct.address.lower(), acct.key.hex()
            except:
                return None, None
        return derive
    except:
        return None

DERIVE_FUNC = None


class KeyMatcherWorker:
    def __init__(self, results_queue):
        self.results_queue = results_queue
        self.running = False
        self.matches_found = []
        self.addresses_checked = 0
        self.derive_func = None
        
    async def check_match(self, address: str, privkey: str, seed_name: str, path: str):
        if not address:
            return False
        for target in HIGH_VALUE_TARGETS:
            if address == target.lower():
                match = {"address": address, "privkey": privkey, "seed": seed_name, "path": path}
                self.matches_found.append(match)
                await self.results_queue.put({"worker": "keymatcher", "type": "key_match", "data": match})
                print(f"\n🎯🎯🎯 MATCH FOUND! 🎯🎯🎯")
                print(f"   Address: {address}")
                print(f"   Seed: {seed_name}")
                print(f"   Path: {path}")
                print(f"   Key: {privkey[:20]}...")
                return True
        return False

    async def run(self, max_index: int = MAX_INDEX):
        global DERIVE_FUNC
        self.running = True
        
        if DERIVE_FUNC is None:
            DERIVE_FUNC = get_derive_func()
        self.derive_func = DERIVE_FUNC
        
        if not self.derive_func:
            print("🔑 KeyMatcher: No derivation library!")
            return
        
        total = len(SEEDS) * len(DERIVATION_PATHS) * max_index
        print(f"🔑 DEEP SCAN: {len(SEEDS)} seeds × {len(DERIVATION_PATHS)} paths × {max_index} indices = {total:,} addresses")
        print(f"🔑 Targets: {len(HIGH_VALUE_TARGETS)}")
        
        for seed_name, seed_phrase in SEEDS:
            if not self.running:
                break
            print(f"🔑 Scanning {seed_name}...")
            
            for path_name, path_template in DERIVATION_PATHS:
                if not self.running:
                    break
                    
                for i in range(max_index):
                    path = path_template.format(i)
                    address, privkey = self.derive_func(seed_phrase, path)
                    
                    if address:
                        self.addresses_checked += 1
                        await self.check_match(address, privkey, seed_name, path)
                    
                    if self.addresses_checked % 2000 == 0:
                        pct = (self.addresses_checked / total) * 100
                        print(f"🔑 Progress: {self.addresses_checked:,}/{total:,} ({pct:.1f}%) - {len(self.matches_found)} matches")
                    
                    if self.addresses_checked % 100 == 0:
                        await asyncio.sleep(0.001)
        
        print(f"\n🔑 SCAN COMPLETE: {self.addresses_checked:,} checked, {len(self.matches_found)} MATCHES")
        if self.matches_found:
            print("🎯 MATCHED ADDRESSES:")
            for m in self.matches_found:
                print(f"   {m['address']} <- {m['seed']} @ {m['path']}")
        
        await self.results_queue.put({
            "worker": "keymatcher", 
            "type": "complete",
            "data": {"checked": self.addresses_checked, "matches": self.matches_found}
        })
        self.running = False

    def stop(self):
        self.running = False
