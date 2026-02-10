#!/usr/bin/env python3
"""
ARTICLE WRITER AGENT (AUTHORITY)
Writes long-form Deep Dives for X (Articles).
Runs in background.
"""

import os
import time
import subprocess
import random
from pathlib import Path
from datetime import datetime

# Config
ARTICLES_DIR = Path(__file__).parent / "articles"
ARTICLES_DIR.mkdir(exist_ok=True)
MODEL = "phi4-mini:latest"
INTERVAL_MINUTES = 60 # 100X MODE

TOPICS = [
    "The End of Manual Labor: Agents Explained",
    "How I Built a 100k Empire with Local AI",
    "Why N8N + Python is the Ultimate Stack",
    "The Psychology of High-Ticket Sales",
    "Godmode: The Future of Solopreneurship"
]

def generate_local(prompt):
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_articles():
    print(f"📝 ARTICLE AGENT ACTIVE")
    print(f"📂 DIR: {ARTICLES_DIR}")
    print("="*60)

    count = 1
    while True:
        topic = random.choice(TOPICS)
        print(f"[{datetime.now().strftime('%H:%M')}] Writing Article: {topic}...")
        
        prompt = f"""
        Write a Long-Form Article for X (2000 words).
        Topic: {topic}.
        Tone: Authoritative, Visionary, slightly aggressive/confident.
        Structure:
        - Hook (Bold statement)
        - The Old Way vs The New Way
        - Deep Technical Insight
        - Future Prediction
        - Call to Action
        
        Format: Markdown.
        """
        
        content = generate_local(prompt)
        
        if content:
            filename = ARTICLES_DIR / f"ARTICLE_{count}_{topic.replace(' ', '_')}.md"
            with open(filename, "w") as f:
                f.write(f"# {topic}\n\n")
                f.write(content)
            
            print(f"✅ Published: {filename.name}")
            count += 1
            time.sleep(INTERVAL_MINUTES * 60)
        else:
            time.sleep(60)

if __name__ == "__main__":
    run_articles()
