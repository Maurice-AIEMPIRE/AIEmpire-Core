#!/usr/bin/env python3
"""
EMPIRE BRAIN AGENT (STRATEGY) - ENGLISH EDITION
Analyzes logs, optimizes prompts, and keeps the vision alive.
Runs periodically.
"""

import os
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Config
LOG_FILE = Path(__file__).parent / "EMPIRE_LOG.md"
QUEUE_FILE = Path(__file__).parent / "LIVE_QUEUE.md"
MODEL = "phi4-mini:latest"
INTERVAL_MINUTES = 15 # 100X MODE

def generate_local(prompt):
    """Generate text using local Ollama model."""
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_brain():
    print(f"🧠 EMPIRE BRAIN ACTIVE (ENGLISH)")
    print(f"📂 LOG: {LOG_FILE}")
    print("="*60)

    # Initialize Log
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w") as f:
            f.write("# EMPIRE STRATEGY LOG\n\n")

    while True:
        print(f"[{datetime.now().strftime('%H:%M')}] Analyzing Empire Status...")
        
        # Read recent activity from queue (Sales)
        activity = ""
        if QUEUE_FILE.exists():
            with open(QUEUE_FILE, "r") as f:
                activity = f.read()[-2000:] # Last 2000 chars
        else:
            activity = "No sales activity yet."

        prompt = f"""You are the strategic brain of an AI Empire.
        Analyze these recent sales logs:
        
        {activity}
        
        Identify 3 strategic improvements to increase sales conversion.
        Language: English.
        Keep it brief, bullet points."""
        
        insight = generate_local(prompt)
        
        if insight:
            with open(LOG_FILE, "a") as f:
                f.write(f"## Strategy Update {datetime.now().strftime('%H:%M')}\n")
                f.write(f"{insight}\n\n")
            print("✅ Strategy Updated in Log.")
        else:
            print("❌ Brain freeze (Generation Error).")
            
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    run_brain()
