#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENDPOINTS = [
    "http://localhost:5678/healthz",
    "http://localhost:11434/api/tags",
    "http://localhost:18789/",
]


def run_shell(cmd: str, timeout: int = 6) -> tuple[int, str]:
    p = subprocess.run(["/bin/zsh", "-lc", cmd], capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout.strip()


def load_per_core() -> float:
    _, out = run_shell("uptime | awk -F'load averages?: ' '{print $2}' | awk '{print $1}' | tr -d ','")
    _, cores_raw = run_shell("sysctl -n hw.ncpu")
    try:
        load = float(out or "0")
        cores = int(cores_raw or "1")
        return load / max(1, cores)
    except ValueError:
        return 0.0


def memory_free_pct() -> float:
    _, out = run_shell("memory_pressure -Q 2>/dev/null | awk -F': ' '/System-wide memory free percentage/{gsub(\"%\",\"\",$2); print $2}' | head -n1")
    try:
        return float(out or "100")
    except ValueError:
        return 100.0


def endpoint_ok(url: str, timeout: int = 3) -> bool:
    req = Request(url, headers={"User-Agent": "ai-empire-preflight/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return 200 <= resp.status < 400
    except URLError:
        return False
    except Exception:
        return False


def evaluate(endpoints: list[str], max_load_per_core: float, min_memory_free_pct: float) -> dict:
    load_pc = load_per_core()
    mem_free = memory_free_pct()
    endpoint_checks = [{"url": u, "ok": endpoint_ok(u)} for u in endpoints]
    missing_endpoints = [e["url"] for e in endpoint_checks if not e["ok"]]

    blockers = []
    if load_pc > max_load_per_core:
        blockers.append(f"load_per_core>{max_load_per_core}")
    if mem_free < min_memory_free_pct:
        blockers.append(f"memory_free_pct<{min_memory_free_pct}")
    if missing_endpoints:
        blockers.append("missing_endpoints")

    decision = "run" if not blockers else "degrade"
    return {
        "generated_at": int(time.time()),
        "decision": decision,
        "reason_codes": blockers,
        "metrics": {
            "load_per_core": round(load_pc, 3),
            "memory_free_pct": round(mem_free, 2),
        },
        "endpoints": endpoint_checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight gate for heavy autopilot jobs")
    parser.add_argument("--endpoints", nargs="*", default=DEFAULT_ENDPOINTS)
    parser.add_argument("--max-load-per-core", type=float, default=float(os.getenv("MAX_LOAD_PER_CORE", "0.85")))
    parser.add_argument(
        "--min-memory-free-pct", type=float, default=float(os.getenv("MIN_MEMORY_FREE_PERCENT", "12"))
    )
    parser.add_argument("--output", default=str(ROOT / "automation/runs/preflight/latest.json"))
    args = parser.parse_args()

    result = evaluate(args.endpoints, args.max_load_per_core, args.min_memory_free_pct)
    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["decision"] == "run" else 2


if __name__ == "__main__":
    raise SystemExit(main())
