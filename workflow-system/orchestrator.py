#!/usr/bin/env python3
"""
OPUS 4.6 WORKFLOW SYSTEM - Orchestrator
The 5-Step Compound Loop that makes AI work compound over time.

Step 1 - AUDIT:      Map workflows, score by time/energy/feasibility
Step 2 - ARCHITECT:  Plan multiple approaches, rank by simplicity
Step 3 - ANALYST:    Engineering review with tradeoffs
Step 4 - REFINERY:   Convergence loop until quality threshold
Step 5 - COMPOUNDER: Weekly review, pattern library, next priorities

Usage:
  python orchestrator.py                    # Run all 5 steps
  python orchestrator.py --step audit       # Run single step
  python orchestrator.py --step refinery    # Run from step 4
  python orchestrator.py --new-cycle        # Start new weekly cycle
  python orchestrator.py --status           # Show current state
"""

import asyncio
import aiohttp
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from state.context import (
    load_state, save_state, append_step_result,
    get_context_for_step, advance_cycle, add_pattern,
    load_pattern_library,
)
from steps import step1_audit, step2_architect, step3_analyst, step4_refinery, step5_compounder
from resource_guard import ResourceGuard
from ollama_engine import OllamaEngine

# Global Ollama Engine (lazy init)
_ollama_engine = None

def _get_ollama():
    global _ollama_engine
    if _ollama_engine is None:
        _ollama_engine = OllamaEngine()
    return _ollama_engine

# ── Mode Configuration ──────────────────────────────────────
# OFFLINE_MODE=true (default): Ollama lokal, $0 Kosten
# OFFLINE_MODE=false: Kimi Cloud, Fallback wenn Ollama versagt
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "true").lower() == "true"

# API Configuration
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Model selection: Ollama for offline, Kimi as fallback
if OFFLINE_MODE:
    MODEL_CONFIG = {
        "audit":     {"provider": "ollama", "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")},
        "architect": {"provider": "ollama", "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")},
        "analyst":   {"provider": "ollama", "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")},
        "refinery":  {"provider": "ollama", "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")},
        "compounder":{"provider": "ollama", "model": os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")},
    }
else:
    MODEL_CONFIG = {
        "audit":     {"provider": "kimi",   "model": "moonshot-v1-32k"},
        "architect": {"provider": "kimi",   "model": "moonshot-v1-32k"},
        "analyst":   {"provider": "kimi",   "model": "moonshot-v1-32k"},
        "refinery":  {"provider": "kimi",   "model": "moonshot-v1-32k"},
        "compounder":{"provider": "kimi",   "model": "moonshot-v1-32k"},
    }

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STEPS = {
    "audit": step1_audit,
    "architect": step2_architect,
    "analyst": step3_analyst,
    "refinery": step4_refinery,
    "compounder": step5_compounder,
}

STEP_ORDER = ["audit", "architect", "analyst", "refinery", "compounder"]


async def call_model(step_name: str, system_prompt: str, user_prompt: str) -> str:
    """Call the configured model for a step. Ollama first, Kimi fallback."""
    config = MODEL_CONFIG[step_name]

    # ── OLLAMA (lokal, $0) ──────────────────────────────────
    if config["provider"] == "ollama":
        engine = _get_ollama()
        print(f"    Mode: OFFLINE (Ollama {config['model']})")

        resp = await engine.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ], model=config["model"])

        if resp.success:
            print(f"    Tokens: {resp.tokens:,} | {resp.duration_ms:.0f}ms | Cost: $0.00")
            return resp.content

        # Ollama failed → Fallback zu Kimi
        print(f"    Ollama failed: {resp.error}")
        if not MOONSHOT_API_KEY:
            raise RuntimeError(f"Ollama failed and no MOONSHOT_API_KEY for fallback: {resp.error}")
        print(f"    Fallback → Kimi Cloud...")
        config = {"provider": "kimi", "model": "moonshot-v1-32k"}

    # ── KIMI (Cloud, guenstig) ──────────────────────────────
    if config["provider"] == "kimi":
        if not MOONSHOT_API_KEY:
            raise ValueError("MOONSHOT_API_KEY not set")

        print(f"    Mode: CLOUD (Kimi {config['model']})")
        url = "https://api.moonshot.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MOONSHOT_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4000,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    cost = (tokens / 1000) * 0.001
                    print(f"    Tokens: {tokens:,} | Cost: ${cost:.4f}")
                    return content
                else:
                    text = await resp.text()
                    raise RuntimeError(f"API error {resp.status}: {text[:200]}")

    raise ValueError(f"Unknown provider: {config['provider']}")


async def run_step(step_name: str, context: dict = None) -> dict:
    """Execute a single workflow step."""
    step_module = STEPS[step_name]

    if context is None:
        context = get_context_for_step(step_name)

    print(f"\n{'='*60}")
    print(f"  STEP: {step_name.upper()}")
    print(f"  Cycle: #{context.get('cycle', 0)}")
    print(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    prompt = step_module.build_prompt(context)
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  Calling model...")

    raw = await call_model(step_name, step_module.SYSTEM_PROMPT, prompt)
    result = step_module.parse_result(raw)

    # Save to state
    append_step_result(step_name, result)

    # Save raw output
    out_file = OUTPUT_DIR / f"{step_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"  Result: {result.get('summary', 'done')}")
    print(f"  Saved: {out_file.name}")

    return result


async def run_refinery_loop(context: dict = None) -> dict:
    """Run the convergence loop for Step 4."""
    if context is None:
        context = get_context_for_step("refinery")

    print(f"\n{'='*60}")
    print(f"  STEP: REFINERY (Convergence Loop)")
    print(f"  Max iterations: {step4_refinery.MAX_ITERATIONS}")
    print(f"  Target score: {step4_refinery.TARGET_SCORE}")
    print(f"  Convergence threshold: {step4_refinery.CONVERGENCE_THRESHOLD}")
    print(f"{'='*60}")

    previous_score = 0.0
    previous_result = None

    for i in range(1, step4_refinery.MAX_ITERATIONS + 1):
        print(f"\n  --- Iteration {i}/{step4_refinery.MAX_ITERATIONS} ---")

        prompt = step4_refinery.build_prompt(
            context, iteration=i,
            previous_score=previous_score,
            previous_result=previous_result,
        )

        raw = await call_model("refinery", step4_refinery.SYSTEM_PROMPT, prompt)
        result = step4_refinery.parse_result(raw)

        converged, current_score = step4_refinery.check_convergence(result, previous_score)
        delta = current_score - previous_score

        print(f"  Score: {current_score}/10 (delta: {delta:+.1f})")
        print(f"  Converged: {converged}")

        if converged:
            print(f"  Convergence reached at iteration {i}!")
            break

        previous_score = current_score
        previous_result = result

    # Save final refinery result
    append_step_result("refinery", result)
    out_file = OUTPUT_DIR / f"refinery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"  Final result saved: {out_file.name}")

    return result


async def run_full_loop() -> dict:
    """Run all 5 steps in sequence. Context accumulates."""
    start = time.time()
    guard = ResourceGuard()

    print("""
╔══════════════════════════════════════════════════════════╗
║         OPUS 4.6 WORKFLOW SYSTEM - FULL LOOP            ║
║         5 Steps. Context compounds. Patterns emerge.    ║
║         Resource Guard: ACTIVE                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    state = load_state()
    print(f"Cycle: #{state.get('cycle', 0)}")
    print(f"Patterns in library: {len(state.get('patterns', []))}")
    print(f"Prior improvements: {len(state.get('improvements', []))}")
    print(f"Guard: {guard.format_status()}")

    results = {}

    # Step 1: AUDIT
    async with guard.check() as gs:
        if gs.paused:
            print("GUARD: System overloaded. Aborting loop.")
            return {"status": "aborted_by_guard", "guard": guard.get_status()}
    results["audit"] = await run_step("audit")

    # Step 2: ARCHITECT (feeds from audit)
    async with guard.check():
        pass
    results["architect"] = await run_step("architect")

    # Step 3: ANALYST (feeds from architect + audit)
    async with guard.check():
        pass
    results["analyst"] = await run_step("analyst")

    # Step 4: REFINERY (convergence loop)
    async with guard.check():
        pass
    results["refinery"] = await run_refinery_loop()

    # Step 5: COMPOUNDER (weekly review of entire cycle)
    async with guard.check():
        pass
    results["compounder"] = await run_step("compounder")

    # Extract and persist new patterns from compounder
    if not results["compounder"].get("parse_error"):
        for pattern in step5_compounder.extract_patterns(results["compounder"]):
            add_pattern(pattern)

    elapsed = time.time() - start

    print(f"""
╔══════════════════════════════════════════════════════════╗
║                    LOOP COMPLETE                        ║
╠══════════════════════════════════════════════════════════╣
║  Steps completed: 5/5                                   ║
║  Duration: {elapsed:.0f}s{' ' * (46 - len(f'{elapsed:.0f}s'))}║
║  New patterns: {len(step5_compounder.extract_patterns(results.get('compounder', {})))}{' ' * (43 - len(str(len(step5_compounder.extract_patterns(results.get('compounder', {}))))))}║
╚══════════════════════════════════════════════════════════╝
    """)

    # Save full loop result
    loop_file = OUTPUT_DIR / f"full_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    loop_file.write_text(json.dumps({
        "cycle": state.get("cycle", 0),
        "duration_sec": elapsed,
        "steps": {k: v.get("summary", "") for k, v in results.items()},
        "completed_at": datetime.now().isoformat(),
    }, indent=2, ensure_ascii=False))

    return results


def show_status():
    """Display current workflow state."""
    state = load_state()
    patterns = load_pattern_library()

    mode = "OFFLINE (Ollama)" if OFFLINE_MODE else "CLOUD (Kimi)"
    model = MODEL_CONFIG["audit"]["model"]
    print(f"""
╔══════════════════════════════════════════════════════════╗
║             WORKFLOW SYSTEM STATUS                       ║
╠══════════════════════════════════════════════════════════╣
  Mode:           {mode}
  Model:          {model}
  Cycle:          #{state.get('cycle', 0)}
  Created:        {state.get('created', 'N/A')}
  Last updated:   {state.get('updated', 'N/A')}
  Steps done:     {len(state.get('steps_completed', []))}
  Patterns:       {len(patterns)}
  Improvements:   {len(state.get('improvements', []))}
╚══════════════════════════════════════════════════════════╝
    """)

    if state.get("steps_completed"):
        print("  Recent steps:")
        for s in state["steps_completed"][-5:]:
            print(f"    [{s['step'].upper():12s}] {s.get('summary', '')[:60]}")

    if patterns:
        print(f"\n  Pattern Library ({len(patterns)} entries):")
        for p in patterns[-5:]:
            print(f"    - {p.get('name', 'unnamed')}: {p.get('description', '')[:50]}")


async def main():
    parser = argparse.ArgumentParser(
        description="Opus 4.6 Workflow System - 5-Step Compound Loop"
    )
    parser.add_argument(
        "--step", choices=STEP_ORDER,
        help="Run a single step (default: run all 5)"
    )
    parser.add_argument(
        "--new-cycle", action="store_true",
        help="Start a new weekly cycle (archives current state)"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show current workflow state"
    )
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.new_cycle:
        cycle = advance_cycle()
        print(f"New cycle started: #{cycle}")
        return

    if args.step:
        if args.step == "refinery":
            await run_refinery_loop()
        else:
            await run_step(args.step)
    else:
        await run_full_loop()


if __name__ == "__main__":
    asyncio.run(main())
