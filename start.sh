#!/bin/bash
# SWARM LAUNCHER FOR TERMUX/DEBIAN
# Run inside Debian proot

echo "=== SWARM SYSTEM SETUP ==="

# Install dependencies if needed
pip3 install --break-system-packages httpx eth-account mnemonic python-dotenv web3 2>/dev/null

# Load environment
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Check for Groq API key
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  GROQ_API_KEY not set"
    echo "   Set it with: export GROQ_API_KEY=your_key"
    echo "   Or add to .env file"
    echo ""
fi

# Run the swarm
echo "🚀 Starting Swarm..."
python3 main.py
