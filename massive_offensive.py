#!/usr/bin/env python3
"""
MASSIVE REVENUE OFFENSIVE - OPERATION SURVIVAL (FREE LOCAL MODE)
Generates massive amount of content with HARD SELL CTAs using LOCAL OLLAMA.
NO API COSTS.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
import subprocess

# Config
PAYPAL_EMAIL = "mauricepfeifer@icloud.com"
OUTPUT_FILE = Path(__file__).parent / "MASSIVE_MARKETING_BLITZ.md"
MODEL = "phi4-mini:latest" # Fits in 3.8GB RAM

def generate_local(prompt):
    """Generate text using local Ollama model via CLI."""
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Ollama Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def run_offensive():
    print(f"🚀 LAUNCHING MASSIVE REVENUE OFFENSIVE (LOCAL MODE)")
    print(f"💰 TARGET: PayPal {PAYPAL_EMAIL}")
    print(f"🤖 MODEL: {MODEL}")
    print("="*60)

    # 1. Generate 20 Hard Sell Posts via Local Ollama
    print("\n[1/2] Generating HARD SELL Posts locally...")
    
    posts = []
    topics = [
        "Why you are losing money without AI", 
        "My AI Empire Revenue Reveal", 
        "The 500€ Investment that changed my life",
        "Stop being poor. Automate.",
        "I will build your AI system. 5 Spots."
    ] * 4 # 20 posts

    for topic in topics:
        print(f"  generating post for: {topic}...", end="", flush=True)
        
        prompt = f"""You are an aggressive sales copywriter. Write a LinkedIn/X post about: "{topic}".
        
        THE OFFER:
        - Product: "Local AI Agent Setup + 1h Strategy Call"
        - Price: 500€ (One-time)
        - Benefit: private, fee-free AI on your own computer. No monthly fees. 100% Data Privacy.
        
        RULES:
        - Short, punchy sentences.
        - Aggressive, confident tone.
        - NO hashtags in the text.
        - MANDATORY CTA at the end: "Pay 500€ via PayPal to {PAYPAL_EMAIL} for the setup." or "DM 'SCALE' to apply."
        - Max 280 words.
        
        GO!"""
        
        content = generate_local(prompt)
        if content:
            posts.append(content)
            print(" Done.")
        else:
            print(" Failed.")

    # 2. Compile the BLITZ Document
    print(f"\n📝 Compiling {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, "w") as f:
        f.write("# 🚨 MASSIVE REVENUE OFFENSIVE: BLITZ MODE (LOCAL AI)\n\n")
        f.write(f"**PAYMENT TARGET:** {PAYPAL_EMAIL}\n")
        f.write(f"**GOAL:** IMMEDIATE CASHFLOW\n")
        f.write(f"**MODEL:** {MODEL}\n\n")
        
        f.write("## 📢 HARD SELL POSTS (COPY & PASTE NOW)\n\n")
        for i, post in enumerate(posts, 1):
            f.write(f"### POST {i}\n")
            f.write(f"```\n{post}\n```\n\n")
            f.write("---\n")

    print("\n" + "="*60)
    print("✅ OFFENSIVE PREPARED.")
    print(f"📂 OPEN THIS FILE AND START POSTING: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_offensive())
