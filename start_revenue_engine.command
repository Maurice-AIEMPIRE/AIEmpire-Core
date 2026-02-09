#!/bin/bash

# ==============================================================================
# 🚀 AI EMPIRE: REVENUE ENGINE STARTUP SCRIPT
# ==============================================================================
# This script launches the Kimi Swarm Revenue Engine.
# Double-click to start generating revenue assets!

# 1. Setup Environment
cd "$(dirname "$0")" || exit
echo "📂 Working Directory: $(pwd)"

# Check for virtual environment
if [ -d "kimi-swarm/venv" ]; then
    source kimi-swarm/venv/bin/activate
    echo "✅ Virtual Environment Activated"
else
    echo "❌ Virtual Environment NOT FOUND!"
    echo "   Please run 'python3 -m venv kimi-swarm/venv' first."
    echo "   Press any key to exit..."
    read -n 1
    exit 1
fi

# 2. Check Configuration
echo "🔍 Checking Configuration..."

if [ -z "$MOONSHOT_API_KEY" ]; then
    echo "⚠️  MOONSHOT_API_KEY is not set in your environment."
    echo "   Please enter your Moonshot API Key (hidden input):"
    read -s MOONSHOT_API_KEY
    export MOONSHOT_API_KEY
fi

if [ -z "$MOONSHOT_API_KEY" ]; then
    echo "❌ No API Key provided. Exiting."
    read -n 1
    exit 1
fi

# 3. Launch the Swarm
echo "🚀 Launching Kimi Swarm 500k Revenue Engine..."
echo "stats will appear below..."
echo "----------------------------------------------------------------"

# Run the python script (using the modified iCloud version)
python3 kimi-swarm/swarm_500k.py --test

echo "----------------------------------------------------------------"
echo "✅ Execution Complete."
echo "📂 Check your iCloud Drive > AI_Empire_Revenue folder for results."
echo "   Press any key to close this window..."
read -n 1
