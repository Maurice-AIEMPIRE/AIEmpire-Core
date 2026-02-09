#!/usr/bin/env python3
"""
UNIFIED PIPELINE - Connects all AI Empire components.
Pipeline: [Orchestrator] -> [Lead Machine] -> [Atomic Reactor] -> [Kimi Swarm]
Output:   data/pipeline/

Usage:
  python connect_workflows.py status    # Show connected components
  python connect_workflows.py run       # Execute one pipeline cycle
  python connect_workflows.py pipeline  # Run continuously (30min intervals)
"""
import asyncio, argparse, json, logging, os, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_DIR, LEAD_DIR = ROOT / "workflow-system", ROOT / "x-lead-machine"
REACTOR_DIR, SWARM_DIR = ROOT / "atomic-reactor", ROOT / "kimi-swarm"
PIPELINE_DIR = ROOT / "data" / "pipeline"
LOG_DIR, RESULTS_DIR = PIPELINE_DIR / "logs", PIPELINE_DIR / "results"

for d in [PIPELINE_DIR, LOG_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
for p in [WORKFLOW_DIR, LEAD_DIR, REACTOR_DIR, SWARM_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / f"pipeline_{datetime.now():%Y%m%d}.log", encoding="utf-8"),
              logging.StreamHandler()])
log = logging.getLogger("pipeline")


def _check(name: str, d: Path, files: list[str]) -> dict:
    ok = d.is_dir() and all((d / f).is_file() for f in files)
    return {"name": name, "path": str(d), "ready": ok}

def check_all() -> list[dict]:
    return [
        _check("Workflow System", WORKFLOW_DIR, ["orchestrator.py", "resource_guard.py"]),
        _check("X-Lead-Machine", LEAD_DIR, ["post_generator.py", "generate_week.py"]),
        _check("Atomic Reactor", REACTOR_DIR, ["run_tasks.py"]),
        _check("Kimi Swarm", SWARM_DIR, ["swarm_100k.py"]),
    ]

# ── Pipeline stages ───────────────────────────────────────

async def stage_orchestrator() -> dict:
    """Stage 1: Run workflow orchestrator audit step."""
    log.info("STAGE 1/4 - Workflow Orchestrator (audit)")
    try:
        from state.context import get_context_for_step, append_step_result
        from steps import step1_audit
        from orchestrator import call_model
        context = get_context_for_step("audit")
        raw = await call_model("audit", step1_audit.SYSTEM_PROMPT, step1_audit.build_prompt(context))
        result = step1_audit.parse_result(raw)
        append_step_result("audit", result)
        log.info("Audit complete: %s", result.get("summary", "done")[:80])
        return {"status": "ok", "step": "audit", "summary": result.get("summary", "")}
    except Exception as exc:
        log.error("Orchestrator failed: %s", exc)
        return {"status": "error", "error": str(exc)}


async def stage_lead_machine() -> dict:
    """Stage 2: Generate content via X-Lead-Machine."""
    log.info("STAGE 2/4 - X-Lead-Machine (post generation)")
    try:
        from post_generator import generate_post, TRENDS, STYLES
        import random
        topic, style = random.choice(TRENDS), random.choice(list(STYLES.keys()))
        post = await generate_post(topic, style)
        if "error" in post:
            raise RuntimeError(post["error"])
        out = RESULTS_DIR / f"lead_post_{datetime.now():%Y%m%d_%H%M%S}.json"
        out.write_text(json.dumps(post, indent=2, ensure_ascii=False))
        log.info("Post generated: %s [%s]", topic[:40], style)
        return {"status": "ok", "topic": topic, "style": style, "file": str(out)}
    except Exception as exc:
        log.error("Lead machine failed: %s", exc)
        return {"status": "error", "error": str(exc)}


async def stage_atomic_reactor() -> dict:
    """Stage 3: Run research tasks via Atomic Reactor."""
    log.info("STAGE 3/4 - Atomic Reactor (research tasks)")
    try:
        from run_tasks import execute_task, TASKS_DIR, REPORTS_DIR
        import yaml
        REPORTS_DIR.mkdir(exist_ok=True)
        task_files = sorted(TASKS_DIR.glob("*.yaml"))
        if not task_files:
            log.warning("No YAML tasks in %s", TASKS_DIR)
            return {"status": "skip", "reason": "no tasks"}
        with open(task_files[0]) as f:
            task = yaml.safe_load(f)
        result = await execute_task(task)
        out = RESULTS_DIR / f"reactor_{task.get('id', 'x')}_{datetime.now():%Y%m%d_%H%M%S}.json"
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        log.info("Reactor '%s' -> %s", task.get("title", "?")[:40], result["status"])
        return {"status": "ok", "task": task.get("title"), "file": str(out)}
    except Exception as exc:
        log.error("Atomic reactor failed: %s", exc)
        return {"status": "error", "error": str(exc)}


async def stage_kimi_swarm(count: int = 20) -> dict:
    """Stage 4: Scale leads via Kimi Swarm."""
    log.info("STAGE 4/4 - Kimi Swarm (%d agents)", count)
    try:
        from swarm_100k import KimiSwarm
        if not os.getenv("MOONSHOT_API_KEY"):
            raise RuntimeError("MOONSHOT_API_KEY not set")
        swarm = KimiSwarm()
        await swarm.init_session()
        try:
            await swarm.run_batch(start_id=0, count=count)
        finally:
            await swarm.close_session()
        stats = {k: swarm.stats[k] for k in ("completed", "failed", "tokens_used")}
        stats["cost_usd"] = round(swarm.stats["cost_usd"], 4)
        stats["by_type"] = swarm.stats["by_type"]
        out = RESULTS_DIR / f"swarm_{datetime.now():%Y%m%d_%H%M%S}.json"
        out.write_text(json.dumps(stats, indent=2))
        log.info("Swarm: %d ok, %d fail, $%.4f", stats["completed"], stats["failed"], stats["cost_usd"])
        return {"status": "ok", **stats, "file": str(out)}
    except Exception as exc:
        log.error("Kimi swarm failed: %s", exc)
        return {"status": "error", "error": str(exc)}

# ── Pipeline runner ───────────────────────────────────────

async def run_cycle() -> dict:
    """Execute one full pipeline cycle."""
    start, cycle_id = time.monotonic(), datetime.now().strftime("%Y%m%d_%H%M%S")
    log.info("=" * 60)
    log.info("PIPELINE CYCLE %s START", cycle_id)
    log.info("=" * 60)
    try:
        from resource_guard import ResourceGuard
        guard = ResourceGuard()
        gs = guard.get_status()
        log.info("Guard: %s", guard.format_status())
        if gs["paused"]:
            log.warning("System overloaded - skipping cycle")
            return {"cycle": cycle_id, "status": "skipped_overload", "guard": gs}
    except Exception:
        log.info("Resource guard unavailable, proceeding")

    results = {}
    results["orchestrator"] = await stage_orchestrator()
    results["lead_machine"] = await stage_lead_machine()
    results["atomic_reactor"] = await stage_atomic_reactor()
    results["kimi_swarm"] = await stage_kimi_swarm()

    elapsed = time.monotonic() - start
    summary = {
        "cycle": cycle_id, "duration_sec": round(elapsed, 1),
        "stages": {k: v.get("status", "?") for k, v in results.items()},
        "details": results, "completed_at": datetime.now().isoformat(),
    }
    out = RESULTS_DIR / f"cycle_{cycle_id}.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    ok = sum(1 for v in results.values() if v.get("status") == "ok")
    log.info("CYCLE %s DONE %.1fs | %d/4 ok | %s", cycle_id, elapsed, ok, out)
    return summary


async def run_pipeline(interval: int = 1800) -> None:
    """Run continuously with given interval (seconds)."""
    log.info("CONTINUOUS MODE - interval %ds", interval)
    n = 0
    while True:
        n += 1
        log.info("--- iteration %d ---", n)
        try:
            await run_cycle()
        except Exception as exc:
            log.error("Cycle %d crashed: %s", n, exc)
        log.info("Next in %dm. Ctrl+C to stop.", interval // 60)
        await asyncio.sleep(interval)

# ── CLI ───────────────────────────────────────────────────

def cmd_status() -> None:
    components, api_ok = check_all(), bool(os.getenv("MOONSHOT_API_KEY"))
    print("\n" + "=" * 60)
    print("  AI EMPIRE UNIFIED PIPELINE - STATUS")
    print("=" * 60 + "\n")
    for c in components:
        print(f"  [{'OK' if c['ready'] else 'MISSING':7s}] {c['name']:20s}  {c['path']}")
    print(f"\n  [{'OK' if api_ok else 'MISSING':7s}] MOONSHOT_API_KEY")
    print(f"  [{'OK':7s}] Pipeline dir          {PIPELINE_DIR}")
    print(f"  [{'OK':7s}] Log dir               {LOG_DIR}\n")
    ready = all(c["ready"] for c in components) and api_ok
    print(f"  {'All systems connected. Ready to run.' if ready else 'Some components missing. Fix before running.'}\n")


def main() -> None:
    p = argparse.ArgumentParser(description="AI Empire Unified Pipeline")
    p.add_argument("command", choices=["status", "run", "pipeline"])
    p.add_argument("--interval", type=int, default=1800, help="Seconds between cycles (default 1800)")
    p.add_argument("--swarm-count", type=int, default=20, help="Agents per swarm batch (default 20)")
    a = p.parse_args()
    if a.command == "status":
        cmd_status()
    elif a.command == "run":
        asyncio.run(run_cycle())
    elif a.command == "pipeline":
        try:
            asyncio.run(run_pipeline(interval=a.interval))
        except KeyboardInterrupt:
            log.info("Pipeline stopped by user.")


if __name__ == "__main__":
    main()
