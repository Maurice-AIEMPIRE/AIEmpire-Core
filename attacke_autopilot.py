#!/usr/bin/env python3
"""
SALES AUTOPILOT (SYMPHONY EDITION)
Role: Drive traffic to the Knowledge Blueprints.
Action: Viral Posts + Replies.
"""

import os
import time
import subprocess
import random
import webbrowser
import urllib.parse
from pathlib import Path
from datetime import datetime

# Config
QUEUE_FILE = Path(__file__).parent / "LIVE_QUEUE.md"
MODEL = "phi4-mini:latest"
INTERVAL_MINUTES = 10 # 100X MODE
GOLD_NUGGETS_FILE = Path(__file__).parent / "SYSTEM_GOLD_NUGGETS.md"
AUTO_OPEN_BROWSER = True # Set to False if it gets annoying

def generate_local(prompt):
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_sales():
    print(f"🚀 SALES AUTOPILOT ACTIVE (BLUEPRINT MODE)")
    
    while True:
        timestamp = datetime.now().strftime('%H:%M')
        print(f"[{timestamp}] generating Sales Post...")
        
        prompt = f"""
        Write a viral tweet to sell my 'Knowledge Blueprint'.
        Context: I have 5 Autonomous AI Agents running my business 24/7.
        They build products, write code, and manage sales.
        
        Angle: "Stop manually working. Build a System."
        
        Call To Action (MANDATORY): 
        "Want the Blueprint? 
        1. Follow
        2. Comment 'SYSTEM'
        3. I'll DM you the link."
        
        Keep it aggressive and high-status, but TRUTHFUL.
        """
        
        content = generate_local(prompt)
        
        if content:
            if not QUEUE_FILE.exists():
                with open(QUEUE_FILE, "w") as f:
                    f.write("# LIVE CONTENT QUEUE\n\n")
            
            with open(QUEUE_FILE, "a") as f:
                f.write(f"## {timestamp} - BLUEPRINT PROMO\n")
                f.write(f"{content}\n")
                f.write("---\n")
                
            print("✅ Post added to Queue.")
            
            if AUTO_OPEN_BROWSER:
                tweet_text = urllib.parse.quote(content)
                url = f"https://twitter.com/intent/tweet?text={tweet_text}"
                print(f"🔗 Opening Tweet: {url}")
                webbrowser.open(url)
        
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    run_sales()
