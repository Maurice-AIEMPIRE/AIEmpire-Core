#!/usr/bin/env python3
"""
Swarm Runner – The 4-Model Router
===================================
Orchestrates all 4 Godmode Programmer agents:
  1. Architect  → Structure, Interfaces, APIs
  2. Fixer      → Bugs, Tracebacks, edge-cases
  3. Coder      → Feature implementation
  4. QA/Reviewer → Tests, Lint, Security

Usage:
    python3 antigravity/swarm_run.py --mode fix-first
    python3 antigravity/swarm_run.py --models 4 --mode feature-sprint
    python3 antigravity/swarm_run.py --task "Fix all import errors"
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from antigravity.config import (
    ARCHITECT, FIXER, CODER, QA_REVIEWER,
    MODES, ISSUES_FILE, REPORTS_DIR, PROJECT_ROOT,
)
from antigravity.ollama_client import get_client
from antigravity.agent_runner import run_agent, run_merge_checks, AgentResult

console = Console()


def load_issues() -> list[dict]:
    """Load issues from ISSUES.json if it exists."""
    if os.path.exists(ISSUES_FILE):
        with open(ISSUES_FILE) as f:
            return json.load(f)
    return []


def load_reports() -> str:
    """Load all report files and combine them into context."""
    context_parts = []
    reports_path = Path(REPORTS_DIR)

    if reports_path.exists():
        for report_file in sorted(reports_path.glob("*.json")):
            try:
                with open(report_file) as f:
                    data = json.load(f)
                context_parts.append(f"--- Report: {report_file.name} ---")
                if isinstance(data, list):
                    for item in data[:50]:  # limit
                        context_parts.append(json.dumps(item, indent=2))
                else:
                    context_parts.append(json.dumps(data, indent=2)[:2000])
            except Exception:
                pass

        for report_file in sorted(reports_path.glob("*.txt")):
            try:
                content = report_file.read_text()[:3000]
                context_parts.append(f"--- Report: {report_file.name} ---\n{content}")
            except Exception:
                pass

    return "\n".join(context_parts) if context_parts else ""


def get_repo_structure() -> str:
    """Get a summary of the repo structure for the Architect."""
    import subprocess
    result = subprocess.run(
        "find . -type f -name '*.py' | grep -v __pycache__ | grep -v .venv | sort | head -80",
        shell=True, capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    return f"Python files in repo:\n{result.stdout}"


def route_task_to_agent(task: str) -> str:
    """Simple keyword-based task router."""
    task_lower = task.lower()

    # Fixer signals
    fixer_keywords = [
        "error", "bug", "fix", "traceback", "exception", "crash",
        "importerror", "attributeerror", "typeerror", "nonetype",
        "broken", "failing", "regression",
    ]
    if any(kw in task_lower for kw in fixer_keywords):
        return "fixer"

    # Architect signals
    arch_keywords = [
        "structure", "refactor", "architect", "design", "interface",
        "api", "reorganize", "dependency", "migration",
    ]
    if any(kw in task_lower for kw in arch_keywords):
        return "architect"

    # QA signals
    qa_keywords = [
        "test", "review", "lint", "check", "audit", "security",
        "quality", "coverage",
    ]
    if any(kw in task_lower for kw in qa_keywords):
        return "qa"

    # Default to coder
    return "coder"


def run_swarm(
    task: str,
    mode: str = "fix-first",
    max_agents: int = 4,
    use_branches: bool = True,
    auto_route: bool = True,
) -> list[AgentResult]:
    """
    Run the full Godmode Programmer swarm.

    Args:
        task: Main task description
        mode: Operating mode (fix-first, feature-sprint, review-all, full-parallel)
        max_agents: Max number of agents to use
        use_branches: Whether agents work in separate git branches
        auto_route: If True, automatically route to best agent; if False, run all in order

    Returns:
        List of AgentResult from each agent
    """
    mode_config = MODES.get(mode, MODES["fix-first"])

    console.print(Panel(
        f"[bold magenta]⚡ GODMODE PROGRAMMER SWARM ⚡[/bold magenta]\n\n"
        f"[cyan]Mode:[/cyan] {mode} – {mode_config['description']}\n"
        f"[cyan]Task:[/cyan] {task[:200]}\n"
        f"[cyan]Agents:[/cyan] {max_agents}\n"
        f"[cyan]Branches:[/cyan] {'Yes' if use_branches else 'No'}",
        title="[bold]ANTIGRAVITY[/bold]",
        border_style="magenta"
    ))

    # Check Ollama health
    client = get_client()
    if not client.health_check():
        console.print("[bold red]❌ Ollama is not running! Start with: ollama serve[/bold red]")
        return []

    console.print("[green]✓[/green] Ollama connection OK\n")

    # Load context
    context_parts = []
    reports = load_reports()
    if reports:
        context_parts.append(reports)
        console.print(f"[green]✓[/green] Loaded reports ({len(reports)} chars)")

    # Route or run all
    agent_map = {
        "architect": ARCHITECT,
        "fixer": FIXER,
        "coder": CODER,
        "qa": QA_REVIEWER,
    }

    if auto_route and not mode_config.get("parallel"):
        # Smart routing: send to best matching agent
        target_role = route_task_to_agent(task)
        agents_to_run = [agent_map[target_role]]
        console.print(f"[cyan]🎯 Auto-routed to:[/cyan] {target_role.upper()}")
    else:
        # Run agents in mode-defined order
        agents_to_run = [agent_map[role] for role in mode_config["order"][:max_agents]]

    # Add repo structure for architect
    if any(a.role == "architect" for a in agents_to_run):
        context_parts.append(get_repo_structure())

    context = "\n\n".join(context_parts) if context_parts else None

    # Execute agents
    results = []
    task_id = f"swarm-{int(time.time())}"

    for i, agent in enumerate(agents_to_run, 1):
        console.print(f"\n[bold]─── Agent {i}/{len(agents_to_run)}: {agent.name} ───[/bold]")

        # Add previous results as context for later agents
        if results:
            prev_context = "\n\n".join([
                f"=== Ergebnis von {r.agent_name} ===\n{r.content[:1000]}"
                for r in results if r.success
            ])
            agent_context = f"{context}\n\n{prev_context}" if context else prev_context
        else:
            agent_context = context

        result = run_agent(
            agent=agent,
            task=task,
            context=agent_context,
            task_id=f"{task_id}-{agent.role}",
            use_branch=use_branches,
            client=client,
        )
        results.append(result)

    # Run merge checks
    if use_branches:
        run_merge_checks()

    # Summary
    _print_summary(results)

    # Save results
    _save_results(results, task, mode)

    return results


def _print_summary(results: list[AgentResult]):
    """Print a summary table of all agent results."""
    table = Table(title="\n⚡ SWARM RESULTS", border_style="magenta")
    table.add_column("Agent", style="cyan")
    table.add_column("Model", style="dim")
    table.add_column("Status", style="bold")
    table.add_column("Tokens", justify="right")
    table.add_column("Time", justify="right")
    table.add_column("Branch")

    for r in results:
        status = "[green]✓ OK[/green]" if r.success else f"[red]✗ {r.error[:30]}[/red]"
        table.add_row(
            r.agent_name,
            r.model,
            status,
            str(r.tokens_used),
            f"{r.duration_seconds:.1f}s",
            r.branch or "–",
        )

    console.print(table)

    total_tokens = sum(r.tokens_used for r in results)
    total_time = sum(r.duration_seconds for r in results)
    console.print(f"\n[dim]Total: {total_tokens} tokens, {total_time:.1f}s[/dim]\n")


def _save_results(results: list[AgentResult], task: str, mode: str):
    """Save swarm results to _reports."""
    report_dir = Path(REPORTS_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "task": task,
        "mode": mode,
        "agents": [r.to_dict() for r in results],
        "total_tokens": sum(r.tokens_used for r in results),
        "total_duration": sum(r.duration_seconds for r in results),
    }

    report_file = report_dir / f"swarm_{int(time.time())}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    console.print(f"[dim]Report saved: {report_file}[/dim]")


def main():
    parser = argparse.ArgumentParser(
        description="Godmode Programmer – 4-Model Swarm Runner"
    )
    parser.add_argument(
        "--task", "-t",
        type=str,
        default="Analysiere das Repo und identifiziere die Top-5 kritischsten Issues.",
        help="Task description for the swarm"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=list(MODES.keys()),
        default="fix-first",
        help="Operating mode"
    )
    parser.add_argument(
        "--models", "-n",
        type=int,
        default=4,
        help="Number of agents to use"
    )
    parser.add_argument(
        "--no-branch",
        action="store_true",
        help="Don't create git branches"
    )
    parser.add_argument(
        "--no-route",
        action="store_true",
        help="Don't auto-route, run all agents in order"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status and exit"
    )

    args = parser.parse_args()

    if args.status:
        _show_status()
        return

    run_swarm(
        task=args.task,
        mode=args.mode,
        max_agents=args.models,
        use_branches=not args.no_branch,
        auto_route=not args.no_route,
    )


def _show_status():
    """Show current system status."""

    console.print(Panel(
        "[bold cyan]GODMODE PROGRAMMER – SYSTEM STATUS[/bold cyan]",
        border_style="cyan"
    ))

    client = get_client()

    # Ollama
    if client.health_check():
        console.print("[green]✓[/green] Ollama: Running")
        models = client.list_models()
        for m in models:
            console.print(f"  [dim]• {m['id']}[/dim]")
    else:
        console.print("[red]✗[/red] Ollama: NOT RUNNING")

    # Reports
    reports_path = Path(REPORTS_DIR)
    if reports_path.exists():
        report_count = len(list(reports_path.glob("*")))
        console.print(f"[green]✓[/green] Reports: {report_count} files")
    else:
        console.print("[yellow]○[/yellow] Reports: none yet")

    # Issues
    issues = load_issues()
    if issues:
        console.print(f"[green]✓[/green] Issues: {len(issues)} tracked")
    else:
        console.print("[yellow]○[/yellow] Issues: none tracked yet")

    console.print()


if __name__ == "__main__":
    main()
