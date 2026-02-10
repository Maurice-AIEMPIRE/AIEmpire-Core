#!/usr/bin/env python3
"""
Merge Queue – Checks branches, runs gate checks, merges approved changes.
Usage: python3 antigravity/merge_queue.py
"""
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from rich.console import Console
from rich.table import Table
from antigravity.config import PROJECT_ROOT, MERGE_CHECKS
console = Console()

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=120)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, f"TIMEOUT: Command took >120s: {cmd[:80]}"

def get_agent_branches():
    _, out = run("git branch --list 'agent/*' 2>/dev/null")
    return [b.strip().lstrip("* ") for b in out.split("\n") if b.strip()]

def check_branch(branch):
    run(f"git checkout {branch} 2>/dev/null")
    results = []
    for check in MERGE_CHECKS:
        rc, out = run(check)
        results.append({"check": check, "passed": rc == 0, "output": out[:300]})
    run("git checkout main 2>/dev/null || git checkout master 2>/dev/null")
    return results

def main():
    console.print("[bold cyan]🔀 MERGE QUEUE[/bold cyan]\n")
    branches = get_agent_branches()
    if not branches:
        console.print("[yellow]No agent branches found.[/yellow]")
        return
    table = Table(title="Agent Branches", border_style="cyan")
    table.add_column("Branch")
    table.add_column("Checks")
    table.add_column("Status")
    for br in branches:
        results = check_branch(br)
        all_ok = all(r["passed"] for r in results)
        passed = sum(1 for r in results if r["passed"])
        status = "[green]✅ READY[/green]" if all_ok else "[red]❌ BLOCKED[/red]"
        table.add_row(br, f"{passed}/{len(results)}", status)
        if all_ok:
            console.print(f"  [green]→ {br} can be merged![/green]")
    console.print(table)

if __name__ == "__main__":
    main()
