#!/usr/bin/env python3
"""
AFFILIATE MANAGER (DIRK KREUTER PARTNERSHIP)
Role: Scans for opportunities to sell "Implementation" to Dirk's audience.
Strategy: "You learned Sales? We handle the Automation."
"""

import os
import time
import subprocess
import random
from pathlib import Path
from datetime import datetime

# Config
QUEUE_FILE = Path(__file__).parent / "LIVE_QUEUE.md"
MODEL = "phi4-mini:latest"
INTERVAL_MINUTES = 45

TARGET_KEYWORDS = ["Sales", "Closing", "Cold Call", "Dirk Kreuter", "Vertrieb"]

def generate_local(prompt):
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_affiliate():
    print(f"🤝 AFFILIATE MANAGER ACTIVE (TARGET: DIRK KREUTER)")
    
    while True:
        keyword = random.choice(TARGET_KEYWORDS)
        print(f"🔍 Scanning for: {keyword}...")
        
        prompt = f"""
        Write a high-value Reply to a user interested in "{keyword}".
        Context: They likely follow Dirk Kreuter.
        
        Your Angle: "Sales is great, but Automation scales it."
        Offer: "My 5-Agent System handles the outreach for you."
        
        Call To Action: "Check the Blueprint in my Bio."
        Tone: Professional, Respectful, Rich.
        """
        
        content = generate_local(prompt)
        
        if content:
            timestamp = datetime.now().strftime('%H:%M')
            with open(QUEUE_FILE, "a") as f:
                f.write(f"## {timestamp} - AFFILIATE SNIPE ({keyword})\n")
                f.write(f"{content}\n")
                f.write("---\n")
            
            print("✅ Affiliate Reply Queued.")
        
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    run_affiliate()
