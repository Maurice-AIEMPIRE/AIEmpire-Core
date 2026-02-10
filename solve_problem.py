#!/usr/bin/env python3
"""
SOLVER AGENT (THE FREE CONSULTANT)
Interactive tool. You feed it a problem, it generates the solution + viral post.
Usage: python3 solve_problem.py "How do I get leads?"
"""

import sys
import subprocess
from pathlib import Path

MODEL = "phi4-mini:latest"
OUTPUT_DIR = Path(__file__).parent / "solutions"
OUTPUT_DIR.mkdir(exist_ok=True)

def generate_local(prompt):
    try:
        cmd = ["ollama", "run", MODEL, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def solve(problem):
    print(f"🧩 SOLVING: {problem}")
    print("..." * 5)
    
    # 1. Generate The Solution (Value)
    sol_prompt = f"""
    User Problem: {problem}.
    
    Act as a World-Class Consultant expert in AI Automation.
    Provide a concrete, step-by-step solution.
    No fluff. Pure actionable value.
    """
    solution = generate_local(sol_prompt)
    
    # 2. Generate The Viral Post (Marketing)
    post_prompt = f"""
    Context: I just solved this problem: "{problem}".
    Solution Summary: {solution[:200]}...
    
    Write a viral X/Twitter post.
    Hook: "Showed a client how to fix [Problem] in 5 mins."
    Body: The steps.
    CTA: "Reply with your problem. I solve it for free."
    """
    post = generate_local(post_prompt)
    
    # Save Output
    filename = OUTPUT_DIR / f"SOLUTION_{problem.replace(' ', '_')[:30]}.md"
    with open(filename, "w") as f:
        f.write(f"# SOLUTION: {problem}\n\n")
        f.write("## 💡 THE FIX\n")
        f.write(solution)
        f.write("\n\n---\n\n")
        f.write("## 🚀 VIRAL POST DRAFT\n")
        f.write("```\n")
        f.write(post)
        f.write("\n```")
        
    print(f"\n✅ DONE. Output saved to: {filename}")
    print("\n--- VIRAL POST PREVIEW ---\n")
    print(post)
    print("\n" + "="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 solve_problem.py 'Your Problem Here'")
        sys.exit(1)
    
    problem_input = " ".join(sys.argv[1:])
    solve(problem_input)
