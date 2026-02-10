#!/usr/bin/env python3
"""
GUERILLA GROWTH AGENT (THE SNIPER)
Tactics:
1. Trend Jacking (Simulated)
2. Reply Scripts (For Elon, etc.)
3. Polarizing Hot Takes
"""

import os
import time
import subprocess
import random
from pathlib import Path
from datetime import datetime

# Config
QUEUE_FILE = Path(__file__).parent / "GUERILLA_QUEUE.md"
MODEL = "phi4-mini:latest"
INTERVAL_MINUTES = 5 # 100X MODE

TARGET_ACCOUNTS = ["@elonmusk", "@sama", "@paulg", "@levelsio"]

def generate_local(prompt):
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_guerilla():
    print(f"🥷 GUERILLA AGENT ACTIVE")
    print("="*60)
    
    if not QUEUE_FILE.exists():
        with open(QUEUE_FILE, "w") as f:
            f.write("# GUERILLA WARFARE LOG\n\n")

    while True:
        print(f"[{datetime.now().strftime('%H:%M')}] Scouting Targets...")
        
        # Tactic 1: Reply Sniper
        target = random.choice(TARGET_ACCOUNTS)
        prompt = f"""
        Imagine {target} just tweeted something about AI/Future.
        Write a witty, high-value reply that disagrees slightly to get attention.
        Goal: Get likes from their audience.
        Max 280 chars.
        """
        reply = generate_local(prompt)
        
        # Tactic 2: Polarizing Take
        prompt2 = """
        Write a controversial opinion about AI Agents.
        Something that makes devs angry but founders happy.
        Short. Punchy.
        """
        hot_take = generate_local(prompt2)
        
        if reply and hot_take:
            with open(QUEUE_FILE, "a") as f:
                timestamp = datetime.now().strftime('%H:%M')
                f.write(f"## {timestamp} - SNIPER TARGET: {target}\n")
                f.write(f"**Reply Script:**\n> {reply}\n\n")
                f.write(f"## {timestamp} - HOT TAKE\n")
                f.write(f"**Tweet:**\n> {hot_take}\n\n")
                f.write("---\n")
            
            print(f"✅ Scripts generated in {QUEUE_FILE.name}")
        
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    run_guerilla()
