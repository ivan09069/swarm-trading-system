#!/usr/bin/env python3
"""
WORKER 1: KEY MATCHER v4 - DEEP SCAN
120,000+ addresses across all common derivation paths
"""

import asyncio
import json
import os
from typing import List, Dict, Tuple

def load_seeds():
    # Try JSON file
    path = os.environ.get("SEEDS_FILE", "seeds.json")
    if os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
                return [(s["name"], s["phrase"]) for s in data]
        except Exception as e:
            print(f"Warning: seeds file parse error: {e}")

    # Try env var JSON
    raw = os.environ.get("KEYMATCHER_SEEDS_JSON", "")
    if raw:
        try:
            data = json.loads(raw)
            return [(s["name"], s["phrase"]) for s in data]
        except Exception as e:
            print(f"Warning: KEYMATCHER_SEEDS_JSON parse error: {e}")

    # Fallback: indexed env vars
    seeds = []
    i = 0
    while True:
        name = os.environ.get(f"SEED_{i}_NAME")
        phrase = os.environ.get(f"SEED_{i}_PHRASE")
        if not name or not phrase:
            break
        seeds.append((name, phrase))
        i += 1
    if seeds:
        return seeds

    print("Warning: No seeds configured. Set SEEDS_FILE, KEYMATCHER_SEEDS_JSON, or SEED_{i}_NAME/SEED_{i}_PHRASE env vars.")
    return []

def load_targets():
    # Try JSON file
    path = os.environ.get("TARGETS_FILE", "targets.json")
    if os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: targets file parse error: {e}")

    # Try env var JSON
    raw = os.environ.get("HIGH_VALUE_TARGETS_JSON", "")
    if raw:
        try:
            return json.loads(raw)
        except Exception as e:
            print(f"Warning: HIGH_VALUE_TARGETS_JSON parse error: {e}")

    print("Warning: No targets configured. Set TARGETS_FILE or HIGH_VALUE_TARGETS_JSON.")
    return []

HIGH_VALUE_TARGETS = load_targets()
SEEDS = load_seeds()

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
                print(f"   Key: {'available' if privkey else 'UNKNOWN'}")
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
