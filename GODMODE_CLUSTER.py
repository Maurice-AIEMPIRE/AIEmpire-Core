#!/usr/bin/env python3
"""
GODMODE CLUSTER ORCHESTRATOR (7-AGENT EMPIRE)
Launches and manages the entire AI Empire.
1. SALES (Attacke Autopilot) - Viral Mode
2. PRODUCT (Factory)
3. STRATEGY (Brain)
4. PIPELINE (Funnel Architect)
5. GUERILLA (Growth Sniper)
6. ARTICLES (Authority Writer)
7. BRIDGE (N8N Connector)
"""

import subprocess
import time
import sys
import os
import signal
from pathlib import Path

# Agents Configuration
AGENTS = [
    {"name": "SALES", "script": "attacke_autopilot.py", "color": "\033[92m"},   # Green
    {"name": "PRODUCT", "script": "product_factory.py", "color": "\033[94m"},  # Blue
    {"name": "BRAIN", "script": "empire_brain.py", "color": "\033[95m"},       # Purple
    {"name": "PIPELINE", "script": "funnel_architect.py", "color": "\033[96m"}, # Cyan
    {"name": "GUERILLA", "script": "guerilla_growth.py", "color": "\033[91m"}, # Red
    {"name": "ARTICLES", "script": "x_article_writer.py", "color": "\033[93m"}, # Yellow
    {"name": "BRIDGE", "script": "n8n_bridge.py", "color": "\033[97m"}         # White
]

PROCESSES = []

def launch_cluster():
    print("\033[1m" + "="*60)
    print("🚨 LAUNCHING GODMODE CLUSTER (7 AGENTS)")
    print("="*60 + "\033[0m")

    # Launch Agents
    for agent in AGENTS:
        script_path = str(Path(__file__).parent / agent["script"])
        print(f"🚀 Starting {agent['color']}{agent['name']}\033[0m Agent...")
        
        try:
            p = subprocess.Popen(
                [sys.executable, script_path],
                start_new_session=True 
            )
            PROCESSES.append({"p": p, "name": agent["name"]})
            print(f"   [PID: {p.pid}] Started.")
        except Exception as e:
            print(f"❌ Failed to start {agent['name']}: {e}")
            
        time.sleep(1) # Stagger start

    print("\n✅ EMPIRE ACTIVE.")
    print("Press Ctrl+C to STOP THE EMPIRE.\n")

    try:
        while True:
            # Simple monitoring loop
            for proc in PROCESSES:
                if proc["p"].poll() is not None:
                    # Optional: Auto-restart logic could go here
                    pass
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 SHUTTING DOWN CLUSTER...")
        for proc in PROCESSES:
            try:
                os.killpg(os.getpgid(proc["p"].pid), signal.SIGTERM)
                print(f"   Killed {proc['name']}")
            except Exception:
                pass
        print("Done.")

if __name__ == "__main__":
    launch_cluster()
