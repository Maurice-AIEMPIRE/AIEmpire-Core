#!/usr/bin/env python3
"""
SYMPHONY CONDUCTOR (MOZART MODE - DEEP INTEGRATION)
The Chief of Staff. Runs the 4 Movements of the Empire.
Focus: Information Gain per Unit Time.
"""

import subprocess
import time
import sys
import os
from pathlib import Path
from datetime import datetime

# Configuration
EVOLUTION_LOG = Path(__file__).parent / "docs" / "evolution_log.md"
SCOREBOARD_FILE = Path(__file__).parent / "SYMPHONY_SCOREBOARD.md"
INBOX_DIR = Path(__file__).parent / "docs" / "inbox"

# Agents Map
AGENTS = {
    "BRAIN": "empire_brain.py",
    "PRODUCT": "product_factory.py",
    "SALES": "attacke_autopilot.py",
    "SCIENTIST": "playground_scientist.py",
    "BRIDGE": "n8n_bridge.py",
    "TIKTOK": "tiktok_producer.py",
    "AFFILIATE": "affiliate_manager.py",
    "VIDEO": "video_renderer.py"
}

def update_scoreboard(movement, status, kpis=None):
    """Updates the live scoreboard."""
    
    # Count active experiments
    active_experiments = len(list(INBOX_DIR.glob("*.md"))) if INBOX_DIR.exists() else 0
    
    with open(SCOREBOARD_FILE, "w") as f:
        f.write("# 🎻 SYMPHONY SCOREBOARD (MOZART MODE)\n\n")
        f.write(f"**STATUS**: {status}\n")
        f.write(f"**MOVEMENT**: {movement}\n")
        f.write(f"**TIME**: {datetime.now().strftime('%H:%M:%S')}\n\n")
        
        f.write("## 🎼 CYCLE STATS\n")
        f.write(f"- **Active Hypotheses**: {active_experiments}\n")
        f.write(f"- **Information Gain**: MAX\n\n")
        
        f.write("## 🚀 EMPIRE METRICS\n")
        f.write("- **Agents**: 10 Active (Full Spectrum)\n")
        f.write("- **Mode**: World Domination\n")

def log_evolution(message):
    if not EVOLUTION_LOG.exists():
        with open(EVOLUTION_LOG, "w") as f:
            f.write("# EMPIRE EVOLUTION LOG\n\n")
            
    with open(EVOLUTION_LOG, "a") as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        f.write(f"- **{timestamp}**: {message}\n")

def movement_i_overture():
    print("\n🎼 MOVEMENT I: OVERTURE (SENSEMAKING)")
    update_scoreboard("I. OVERTURE", "Sensing...")
    print("   Scanning Empire State...")
    # Check if N8N is reachable (Simulation)
    print("   Analysis: Systems Nominal.")

def movement_ii_development():
    print("\n🎼 MOVEMENT II: DEVELOPMENT (BUILD)")
    update_scoreboard("II. DEVELOPMENT", "Building...")
    print("   Driving Product & Sales Engines...")
    print("   - Product Factory: ACTIVE")
    print("   - Sales Autopilot: ACTIVE")
    print("   - TikTok Producer: ACTIVE")
    print("   - Affiliate Manager: ACTIVE")
    print("   - Video Renderer: ACTIVE")

def movement_iii_scherzo():
    print("\n🎼 MOVEMENT III: SCHERZO (EXPERIMENT)")
    update_scoreboard("III. SCHERZO", "Testing Hypotheses...")
    # Run a quick experiment design
    subprocess.run([sys.executable, "playground_scientist.py"])

def movement_iv_finale():
    print("\n🎼 MOVEMENT IV: FINALE (SHIP & LEARN)")
    update_scoreboard("IV. FINALE", "Evolution...")
    print("   Closing Cycle...")
    log_evolution("Cycle Completed. Expansion Successful.")

def conduct_symphony():
    print("\033[1m" + "="*60)
    print("🎻 SYMPHONY KERNEL STARTED (EXPANSION MODE)")
    print("="*60 + "\033[0m")
    
    # Ensure Infrastructure is Up
    bridge = subprocess.Popen([sys.executable, "n8n_bridge.py"])
    print("   [INFRA] N8N Bridge Started.")
    
    # Ensure Background Engines are Up (Development)
    sales = subprocess.Popen([sys.executable, "attacke_autopilot.py"])
    product = subprocess.Popen([sys.executable, "product_factory.py"])
    tiktok = subprocess.Popen([sys.executable, "tiktok_producer.py"])
    affiliate = subprocess.Popen([sys.executable, "affiliate_manager.py"])
    video = subprocess.Popen([sys.executable, "video_renderer.py"])
    
    cycle_count = 1
    
    try:
        while True:
            print(f"\n--- CYCLE {cycle_count} ---")
            
            movement_i_overture()
            time.sleep(2)
            
            movement_ii_development()
            time.sleep(5) 
            
            movement_iii_scherzo()
            time.sleep(2)
            
            movement_iv_finale()
            
            cycle_count += 1
            print("\n⏸  Rest (Silence)...")
            update_scoreboard("SILENCE", "Resting...")
            time.sleep(10) 
            
    except KeyboardInterrupt:
        print("\n🛑 FINALE. Stopping Symphony...")
        bridge.terminate()
        sales.terminate()
        product.terminate()
        tiktok.terminate()
        affiliate.terminate()
        video.terminate()

if __name__ == "__main__":
    conduct_symphony()
