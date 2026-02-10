#!/usr/bin/env python3
"""
PRODUCT FACTORY (SYMPHONY EDITION)
Role: Builds Knowledge Blueprints (Courses).
Output: products/COURSE_NAME/MODULE_XX.md
"""

import os
import time
import subprocess
import random
from pathlib import Path

# Config
PRODUCTS_DIR = Path(__file__).parent / "products"
PRODUCTS_DIR.mkdir(exist_ok=True)
MODEL = "phi4-mini:latest"
INTERVAL_MINUTES = 5 # 100X MODE

COURSES = {
    "AI_Setup_Blueprint": [
        "01_introduction_to_local_ai.md",
        "02_installing_ollama_python.md",
        "03_your_first_agent_script.md",
        "04_bonus_automation_ideas.md"
    ],
    "Viral_Velocity": [
        "01_the_algorithm_secrets.md",
        "02_automating_tweets_with_python.md",
        "03_the_reply_guy_strategy.md",
        "04_visuals_that_convert.md",
        "05_launching_your_growth_engine.md"
    ],
    "Automated_Cashflow": [
        "01_n8n_basics_masterclass.md",
        "02_connecting_stripe_paypal.md",
        "03_the_perfect_sales_funnel.md",
        "04_automating_dm_sales.md",
        "05_scaling_to_10k.md"
    ]
}

def generate_local(prompt):
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_factory():
    print(f"📦 PRODUCT FACTORY ACTIVE (COURSE MODE)")
    print(f"📂 DIR: {PRODUCTS_DIR}")
    
    while True:
        # Pick a random course and module
        course_name = random.choice(list(COURSES.keys()))
        module_file = random.choice(COURSES[course_name])
        
        course_dir = PRODUCTS_DIR / course_name
        course_dir.mkdir(exist_ok=True)
        
        target_file = course_dir / module_file
        
        if not target_file.exists():
            print(f"🏗 Building: {course_name} / {module_file}...")
            
            prompt = f"""
            Write a high-value Course Module.
            Course: {course_name.replace('_', ' ')}
            Module: {module_file.replace('_', ' ').replace('.md', '')}
            
            Format: Markdown.
            Tone: Actionable, No Fluff, "Do this, then that".
            Include code snippets if relevant.
            """
            
            content = generate_local(prompt)
            
            if content:
                with open(target_file, "w") as f:
                    f.write(f"# {module_file.replace('_', ' ').upper()}\n\n")
                    f.write(content)
                print(f"✅ Created: {target_file.name}")
            else:
                print("❌ Generation failed.")
        
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    run_factory()
