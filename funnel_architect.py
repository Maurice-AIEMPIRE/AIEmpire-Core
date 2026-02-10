#!/usr/bin/env python3
"""
FUNNEL ARCHITECT AGENT (PIPELINE)
Structures viral traffic into a concrete sales process.
1. Defines Daily Avatar.
2. Generates Outreach Scripts.
3. Tracks Pipeline Status.
"""

import os
import time
import subprocess
import random
from pathlib import Path
from datetime import datetime

# Config
DASHBOARD_FILE = Path(__file__).parent / "PIPELINE_DASHBOARD.md"
LEADS_DIR = Path(__file__).parent / "leads"
LEADS_DIR.mkdir(exist_ok=True)
MODEL = "phi4-mini:latest"
INTERVAL_MINUTES = 15 # 100X MODE

AVATARS = [
    "Agency Owners struggling with fulfillment",
    "SaaS Founders needing growth",
    "Consultants wanting to scale",
    "E-com Brands needing support"
]

def generate_local(prompt):
    """Generate text using local Ollama model."""
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_funnel():
    print(f"🌪 FUNNEL ARCHITECT ACTIVE")
    print(f"📊 DASHBOARD: {DASHBOARD_FILE}")
    print("="*60)

    while True:
        print(f"[{datetime.now().strftime('%H:%M')}] Architecting Pipeline...")
        
        # 1. Select Daily Avatar
        avatar = random.choice(AVATARS)
        
        # 2. Generate Outreach Strategy
        prompt = f"""
        Target Avatar: {avatar}.
        Goal: Sell 'AI Empire Integration' (2.5k).
        
        Create a 3-step DM Sequence:
        1. Icebreaker (Compliment + Question)
        2. Value Drop (Link to a 'Gold Nugget' asset)
        3. The Ask (Call booking)
        
        Format: Markdown.
        """
        
        strategy = generate_local(prompt)
        
        if strategy:
            # Update Dashboard
            with open(DASHBOARD_FILE, "w") as f:
                f.write(f"# PIPELINE DASHBOARD - {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write(f"## 🎯 DAILY TARGET: {avatar}\n\n")
                f.write("## 📢 OUTREACH STRATEGY\n")
                f.write(strategy)
                f.write("\n\n## 💰 PIPELINE STATUS\n")
                f.write("- Leads Generated: [TRACKING]\n")
                f.write("- DMs Sent: [TRACKING]\n")
                f.write("- Closings: [TRACKING]\n")
            
            print("✅ Dashboard Updated.")
            
            # Create a specific Lead List for this avatar
            lead_file = LEADS_DIR / f"LEADS_{datetime.now().strftime('%Y%m%d')}_{avatar.replace(' ', '_')}.md"
            with open(lead_file, "w") as f:
                f.write(f"# LEADS: {avatar}\n\n")
                f.write("Paste profile URLs here:\n\n")
            
        else:
            print("❌ Strategy Gen Error.")

        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    run_funnel()
