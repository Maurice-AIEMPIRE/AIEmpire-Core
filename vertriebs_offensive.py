#!/usr/bin/env python3
"""
VERTRIEBS-OFFENSIVE (DIRK KREUTER STYLE) - LOCAL AI GENERATOR
Generates aggressive German sales content using local models.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
import subprocess
import time

# Config
PAYPAL_EMAIL = "mauricepfeifer@icloud.com"
OUTPUT_FILE = Path(__file__).parent / "VERTRIEBS_OFFENSIVE_MASTERPLAN.md"
MODEL = "phi4-mini:latest" 

# Offers
OFFERS = {
    "HIGH": {"name": "AI Empire Komplette Integration", "price": "2.500€", "value": "Wir bauen dein komplettes System."},
    "MID": {"name": "Automation Audit & Roadmap", "price": "500€", "value": "Wir finden deine Geld-Lecks."},
    "LOW": {"name": "Das AI Blueprint", "price": "49€", "value": "Die Anleitung zum Selbermachen."}
}

def generate_local(prompt):
    """Generate text using local Ollama model via CLI."""
    try:
        # Dirk Kreuter Persona Injection
        system_prompt = (
            "Du bist der härteste Verkaufstrainer Deutschlands (Style: Dirk Kreuter). "
            "Du bist direkt, aggressiv, voller Energie. "
            "Du hasst Ausreden. Du liebst Umsatz. "
            "Du sprichst Deutsch. Du nutzt kurze, harte Sätze. "
            "Dein Ziel: CLOSING."
        )
        
        full_prompt = f"{system_prompt}\n\nAUFGABE: {prompt}"
        
        cmd = ["ollama", "run", MODEL, full_prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Ollama Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def run_offensive():
    print(f"🚀 STARTING VERTRIEBS-OFFENSIVE (DIRK KREUTER MODE)")
    print(f"💰 ZIEL: PayPal {PAYPAL_EMAIL}")
    print(f"🤖 MODEL: {MODEL}")
    print("="*60)
    
    with open(OUTPUT_FILE, "w") as f:
        f.write("# 🚀 VERTRIEBS-OFFENSIVE: DER MASTERPLAN\n\n")
        f.write(f"**STATUS:** ATTACKE\n")
        f.write(f"**PAYMENT:** {PAYPAL_EMAIL}\n\n")

    # 1. Generate Pain Posts (The "Wake Up Call")
    print("\n[1/4] Generiere 'Schmerz & Wahrheit' Posts...")
    topics_pain = [
        "Warum du ohne AI in 2 Jahren pleite bist",
        "Deine Konkurrenz lacht über deine manuellen Prozesse",
        "Aufschieberitis kostet dich jeden Tag 500€"
    ]
    
    with open(OUTPUT_FILE, "a") as f:
        f.write("## 1. PHASE: SCHMERZ & WAHRHEIT (Wake Up Calls)\n\n")
        
    for topic in topics_pain:
        print(f"  > Thema: {topic}...", end="", flush=True)
        prompt = f"""Schreibe einen LinkedIn/X Post über: "{topic}".
        
        REGELN:
        - Provoziere!
        - Mach dem Leser klar, dass er Geld verliert.
        - Ende mit CTA: "Hör auf zu jammern. Buch das Audit für {OFFERS['MID']['price']}."
        - Keine Hashtags im Text.
        """
        content = generate_local(prompt)
        if content:
            with open(OUTPUT_FILE, "a") as f:
                f.write(f"### POST: {topic}\n```\n{content}\n```\n\n")
            print(" ✅")
        else:
            print(" ❌")

    # 2. Generate Social Proof (The "Results")
    print("\n[2/4] Generiere 'Ergebnisse' Posts...")
    topics_proof = [
        "Wie wir 500€ an einem Vormittag automatisiert haben",
        "Vom 60-Stunden-Sklaven zum AI-Unternehmer",
    ]
    
    with open(OUTPUT_FILE, "a") as f:
        f.write("## 2. PHASE: BEWEISE (Case Studies)\n\n")

    for topic in topics_proof:
        print(f"  > Thema: {topic}...", end="", flush=True)
        prompt = f"""Schreibe eine kurze Case Study über: "{topic}".
        
        REGELN:
        - Zahlen, Daten, Fakten.
        - Zeige das Ergebnis.
        - CTA: "Willst du das auch? {OFFERS['HIGH']['name']} für {OFFERS['HIGH']['price']}. Schreib mir 'SCALE'."
        """
        content = generate_local(prompt)
        if content:
            with open(OUTPUT_FILE, "a") as f:
                f.write(f"### POST: {topic}\n```\n{content}\n```\n\n")
            print(" ✅")
        else:
            print(" ❌")

    # 3. The Irresistible Offer (The "Pitch")
    print("\n[3/4] Generiere 'Das Angebot' Posts...")
    
    with open(OUTPUT_FILE, "a") as f:
        f.write("## 3. PHASE: DAS ANGEBOT (Closing)\n\n")
        
    for level, offer in OFFERS.items():
        print(f"  > Pitching: {offer['name']}...", end="", flush=True)
        prompt = f"""Verkaufe dieses Angebot aggressiv:
        Name: {offer['name']}
        Preis: {offer['price']}
        Wert: {offer['value']}
        
        REGELN:
        - Mach es unwiderstehlich.
        - Verknappe es (nur 3 Plätze).
        - CTA: "PayPal an {PAYPAL_EMAIL}."
        """
        
        content = generate_local(prompt)
        if content:
            with open(OUTPUT_FILE, "a") as f:
                f.write(f"### PITCH: {offer['name']}\n```\n{content}\n```\n\n")
            print(" ✅")
        else:
            print(" ❌")

    # 4. DM Script
    print("\n[4/4] Generiere DM Closing Script...")
    prompt = f"""Erstelle ein DM Skript um Kalt-Leads zu closen.
    Ziel: {OFFERS['MID']['name']} für {OFFERS['MID']['price']} verkaufen.
    
    STRUKTUR:
    1. Opener (Nicht nervig, aber direkt).
    2. Qualifizierung (Hast du Budget?).
    3. Der Pitch (Lösung präsentieren).
    4. Closing (PayPal Link schicken).
    """
    content = generate_local(prompt)
    if content:
        with open(OUTPUT_FILE, "a") as f:
            f.write(f"## 4. DM CLOSING SCRIPT\n```\n{content}\n```\n\n")
        print(" ✅")
    else:
        print(" ❌")


    print("\n" + "="*60)
    print("✅ VERTRIEBS-OFFENSIVE BEREIT.")
    print(f"📂 DEIN MASTERPLAN: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_offensive())
