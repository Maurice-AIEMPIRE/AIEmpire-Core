#!/usr/bin/env python3
"""
PLAYGROUND SCIENTIST (SCHERZO MOVEMENT)
Role: Runs small experiments to gain information.
Focus: HYPOTHESIS -> METRIC -> DECISION.
"""

import os
import time
import subprocess
import random
from pathlib import Path
from datetime import datetime

# Config
INBOX_DIR = Path(__file__).parent / "docs" / "inbox"
INBOX_DIR.mkdir(parents=True, exist_ok=True)
MODEL = "phi4-mini:latest"

HYPOTHESES = [
    "H1: Aggressive copy converts 20% better than polite copy.",
    "H2: Posting at 2 AM captures US West Coast engineers.",
    "H3: 'How-to' threads get more bookmarks than 'Why-to'.",
    "H4: Memes with code snippets go viral faster.",
    "H5: DMs with 'Value First' get 3x more replies.",
]

def generate_local(prompt):
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_experiment():
    print(f"🧪 SCIENTIST RUNNING EXPERIMENT...")
    
    hypothesis = random.choice(HYPOTHESES)
    print(f"🔬 Testing: {hypothesis}")
    
    prompt = f"""
    Design a RIGOROUS experiment to test this hypothesis:
    "{hypothesis}"
    
    Structure:
    1. HYPOTHESIS: State clearly.
    2. EVIDENCE REQUIRED: What data points do we need?
    3. FASTEST EXPERIMENT: Smallest test to get 80% confidence.
    4. METRIC: Exact number to watch (e.g. CTR > 2%).
    5. DECISION RULE: If X, then Y.
    
    Format: Markdown.
    """
    
    design = generate_local(prompt)
    
    if design:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = INBOX_DIR / f"EXP_{timestamp}.md"
        
        with open(filename, "w") as f:
            f.write(f"# EXPERIMENT DESIGN\n")
            f.write(f"**Date**: {timestamp}\n\n")
            f.write(design)
            f.write("\n\n---\nSTATUS: READY FOR EXECUTION")
            
        print(f"✅ Hypothesis Logged: {filename.name}")
        return True
    
    return False

if __name__ == "__main__":
    run_experiment()
