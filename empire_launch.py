#!/usr/bin/env python3
"""
Empire Launch – Master entry point for the Godmode Programmer system.
Usage:
    python3 empire_launch.py --status
    python3 empire_launch.py --collect
    python3 empire_launch.py --cluster
    python3 empire_launch.py --swarm "Fix all import errors"
    python3 empire_launch.py --dashboard
    python3 empire_launch.py --smoke-test
    python3 empire_launch.py --full-pipeline
"""

import argparse
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def run(cmd):
    print(f"\n{'=' * 60}\n▶ {cmd}\n{'=' * 60}")
    return subprocess.run(cmd, shell=True, cwd=PROJECT_ROOT).returncode


def cmd_status(args):
    """Show full system status."""
    from rich.console import Console
    from rich.panel import Panel

    c = Console()
    c.print(
        Panel(
            "[bold magenta]⚡ GODMODE PROGRAMMER – SYSTEM STATUS[/bold magenta]",
            border_style="magenta",
        )
    )

    # Ollama
    rc = subprocess.run("ollama list", shell=True, capture_output=True, text=True)
    if rc.returncode == 0:
        c.print("[green]✓[/green] Ollama: Running")
        for line in rc.stdout.strip().split("\n")[1:]:
            if line.strip():
                c.print(f"  [dim]{line.strip()}[/dim]")
    else:
        c.print("[red]✗[/red] Ollama: NOT RUNNING – start with: ollama serve")

    # Python
    c.print(f"[green]✓[/green] Python: {sys.version.split()[0]}")

    # Ruff
    rc2 = subprocess.run("ruff --version", shell=True, capture_output=True, text=True)
    if rc2.returncode == 0:
        c.print(f"[green]✓[/green] Ruff: {rc2.stdout.strip()}")

    # Pytest
    rc3 = subprocess.run("pytest --version", shell=True, capture_output=True, text=True)
    if rc3.returncode == 0:
        c.print("[green]✓[/green] Pytest: installed")

    # API check
    import httpx

    try:
        r = httpx.get("http://localhost:11434/v1/models", timeout=5)
        models = r.json().get("data", [])
        c.print(f"[green]✓[/green] Ollama API: {len(models)} models available")
    except Exception:
        c.print("[red]✗[/red] Ollama API: not responding")

    # Reports
    from pathlib import Path

    rp = Path(PROJECT_ROOT) / "antigravity" / "_reports"
    rcount = len(list(rp.glob("*"))) if rp.exists() else 0
    c.print(f"[green]✓[/green] Reports: {rcount} files")

    # Issues
    ip = Path(PROJECT_ROOT) / "antigravity" / "ISSUES.json"
    if ip.exists():
        import json

        data = json.loads(ip.read_text())
        c.print(f"[green]✓[/green] Issues: {data.get('total_issues', 0)} tracked in {data.get('total_tasks', 0)} tasks")

    c.print()


def cmd_smoke_test(args):
    """Run smoke tests."""
    results = []
    for cmd in [
        "python3 -m compileall . -q",
        "ruff check . --select E,F --quiet",
        "pytest -q --tb=short --no-header 2>/dev/null || true",
    ]:
        rc = run(cmd)
        results.append((cmd, rc == 0))
    print("\n" + "=" * 60)
    for cmd, ok in results:
        s = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {s}  {cmd}")


def main():
    p = argparse.ArgumentParser(description="Godmode Programmer – Empire Launch")
    p.add_argument("--status", action="store_true", help="Show system status")
    p.add_argument("--collect", action="store_true", help="Collect all reports")
    p.add_argument("--cluster", action="store_true", help="Cluster issues")
    p.add_argument("--swarm", type=str, help="Run swarm with task")
    p.add_argument("--dashboard", action="store_true", help="Build structure dashboard")
    p.add_argument("--smoke-test", action="store_true", help="Run smoke tests")
    p.add_argument("--merge-queue", action="store_true", help="Check merge queue")
    p.add_argument("--full-pipeline", action="store_true", help="Run full pipeline")
    p.add_argument("--mode", default="fix-first", help="Swarm mode")
    a = p.parse_args()

    if a.status:
        cmd_status(a)
    elif a.collect:
        run("python3 antigravity/collect_reports.py")
    elif a.cluster:
        run("python3 antigravity/cluster_issues.py")
    elif a.swarm:
        run(f'python3 antigravity/swarm_run.py --task "{a.swarm}" --mode {a.mode}')
    elif a.dashboard:
        run("python3 antigravity/structure_builder.py")
    elif a.smoke_test:
        cmd_smoke_test(a)
    elif a.merge_queue:
        run("python3 antigravity/merge_queue.py")
    elif a.full_pipeline:
        print("⚡ FULL PIPELINE: collect → cluster → swarm → dashboard")
        run("python3 antigravity/collect_reports.py")
        run("python3 antigravity/cluster_issues.py")
        run(f'python3 antigravity/swarm_run.py --task "Fix top priority issues" --mode {a.mode} --no-route')
        run("python3 antigravity/structure_builder.py")
    else:
        p.print_help()


if __name__ == "__main__":
    main()
