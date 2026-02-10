#!/usr/bin/env python3
"""
TIKTOK PRODUCER (FACELESS WEALTH)
Role: Writes scripts for "Dark Mode" viral TikToks.
Niche: AI Automation / Wealth.
Output: products/TIKTOK_SCRIPTS/
"""

import os
import time
import subprocess
import random
from pathlib import Path
from datetime import datetime

# Config
SCRIPTS_DIR = Path(__file__).parent / "products" / "TIKTOK_SCRIPTS"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
MODEL = "phi4-mini:latest"
INTERVAL_MINUTES = 30 # High Frequency

HOOKS = [
    "POV: You fired your boss.",
    "Stop scrolling. This AI tool is illegal.",
    "How I make $1k/day with 0 employees.",
    "The secret wealthy people aren't telling you.",
    "Your 9-5 is a trap. Here is the key."
]

def generate_local(prompt):
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_tiktok():
    print(f"🎬 TIKTOK PRODUCER ACTIVE (DARK MODE)")
    
    while True:
        hook = random.choice(HOOKS)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        print(f"🎥 Writing Script: {hook}...")
        
        prompt = f"""
        Write a viral 15-second TikTok script.
        Style: "Faceless Wealth" / Dark Aesthetics.
        
        Structure:
        1. VISUAL: Describe the stock footage (e.g. driving luxury car at night, coding on laptop).
        2. TEXT OVERLAY (The Hook): "{hook}"
        3. CAPTION: Detailed value prop.
        4. AUDIO: "Trending Phonk".
        
        Call To Action: "Link in Bio for the Blueprint."
        """
        
        content = generate_local(prompt)
        
        if content:
            filename = SCRIPTS_DIR / f"TIKTOK_{timestamp}.md"
            with open(filename, "w") as f:
                f.write(f"# TIKTOK SCRIPT: {hook}\n\n")
                f.write(content)
            print(f"✅ Script Saved: {filename.name}")
        
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    run_tiktok()
