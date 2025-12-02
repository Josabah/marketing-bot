#!/bin/bash
# Script to start the Marketing Campaign Bot

set -euo pipefail
cd "$(dirname "$0")"

echo "🚀 Starting Marketing Campaign Bot..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found!"
    exit 1
fi

# Start the bot (uses modular main.py)
exec python3 main.py

