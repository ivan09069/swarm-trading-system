#!/usr/bin/env python3
"""Quick test of keymatcher derivation"""

print("Testing hdwallet derivation...")

try:
    from hdwallet import HDWallet
    from hdwallet.symbols import ETH
    
    seed = "army van defense carry jealous true garbage claim echo media make crunch"
    
    hdw = HDWallet(symbol=ETH)
    hdw.from_mnemonic(seed)
    hdw.from_path("m/44'/60'/0'/0/0")
    
    addr = hdw.p2pkh_address()
    print(f"Address: {addr}")
    print("hdwallet WORKS!")
except Exception as e:
    print(f"hdwallet ERROR: {e}")

print("\nTesting keymatcher worker...")

try:
    import asyncio
    from worker_keymatcher import KeyMatcherWorker, get_derive_func
    
    func = get_derive_func()
    if func:
        addr, pk = func(seed, "m/44'/60'/0'/0/0")
        print(f"Derived: {addr}")
    else:
        print("No derive function!")
except Exception as e:
    print(f"KeyMatcher ERROR: {e}")
    import traceback
    traceback.print_exc()
