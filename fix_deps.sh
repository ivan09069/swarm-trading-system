#!/bin/bash
# FIX KEYMATCHER DEPENDENCIES
# Tries multiple options until one works

echo "=== Installing key derivation library ==="

# Option 1: hdwallet (usually pure Python, easiest)
echo "Trying hdwallet..."
pip3 install --break-system-packages hdwallet 2>/dev/null && echo "✅ hdwallet installed" && exit 0

# Option 2: bip_utils 
echo "Trying bip_utils..."
pip3 install --break-system-packages bip_utils 2>/dev/null && echo "✅ bip_utils installed" && exit 0

# Option 3: Old eth-account
echo "Trying eth-account 0.5.9..."
pip3 install --break-system-packages "eth-account==0.5.9" 2>/dev/null && echo "✅ eth-account installed" && exit 0

# Option 4: mnemonic + ecdsa for manual derivation
echo "Trying basic crypto libs..."
pip3 install --break-system-packages mnemonic ecdsa 2>/dev/null && echo "✅ basic libs installed" && exit 0

echo "❌ All options failed. Try installing Rust:"
echo "   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
