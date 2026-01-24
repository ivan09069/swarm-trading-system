#!/usr/bin/env python3
from hdwallet import HDWallet
h = HDWallet(symbol="ETH")
h.from_mnemonic("abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about")
h.from_path("m/44'/60'/0'/0/0")
print("Address:", h.p2pkh_address())
print("OK")
