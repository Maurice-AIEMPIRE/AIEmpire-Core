#!/usr/bin/env python3
"""
Report Collector
=================
Collects all errors/issues from the repo into a standardized format.
Runs: compileall, ruff, pytest – and parses output into unified reports.

Usage:
    python3 antigravity/collect_reports.py
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table

from antigravity.config import PROJECT_ROOT, REPORTS_DIR

console = Console()


def _run(cmd: str) -> tuple[int, str]:
    """Run a command and return (returncode, combined output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=120
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, f"TIMEOUT: Command took >120s: {cmd[:80]}"


def collect_compile_errors() -> list[dict]:
    """Run python -m compileall and collect syntax errors."""
    console.print("[cyan]🔍 Collecting compile errors...[/cyan]")
    rc, output = _run("python3 -m compileall . -q 2>&1 | grep -i error || true")

    issues = []
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Parse "Compiling './path/file.py'..." or "SyntaxError: ..."
        match = re.search(r"['\"]\.?/?(.+?\.py)['\"]", line)
        filepath = match.group(1) if match else "unknown"

        issues.append({
            "type": "compile_error",
            "file": filepath,
            "line": 0,
            "message": line[:200],
            "tool": "compileall",
            "severity": "critical",
            "cluster": "syntax",
        })

    console.print(f"  Found {len(issues)} compile errors")
    return issues


def collect_ruff_errors() -> list[dict]:
    """Run ruff check and collect lint errors."""
    console.print("[cyan]🔍 Collecting ruff lint errors...[/cyan]")
    rc, output = _run("ruff check . --output-format json --select E,F,I 2>/dev/null || echo '[]'")

    issues = []
    try:
        ruff_results = json.loads(output) if output.strip().startswith("[") else []
    except json.JSONDecodeError:
        ruff_results = []

    for item in ruff_results:
        # Map ruff severity
        code = item.get("code", "")
        if code.startswith("F"):
            severity = "high"
            cluster = "import_error" if "import" in item.get("message", "").lower() else "logic_error"
        elif code.startswith("E"):
            severity = "medium"
            cluster = "style"
        else:
            severity = "low"
            cluster = "style"

        issues.append({
            "type": "lint_error",
            "file": item.get("filename", "unknown"),
            "line": item.get("location", {}).get("row", 0),
            "message": f"[{code}] {item.get('message', '')}",
            "tool": "ruff",
            "severity": severity,
            "cluster": cluster,
        })

    console.print(f"  Found {len(issues)} ruff errors")
    return issues


def collect_pytest_errors() -> list[dict]:
    """Run pytest and collect test failures."""
    console.print("[cyan]🔍 Collecting test failures...[/cyan]")
    rc, output = _run("pytest -q --tb=line --no-header 2>&1 || true")

    issues = []
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Parse "FAILED tests/test_foo.py::test_bar - AssertionError: ..."
        if "FAILED" in line or "ERROR" in line:
            match = re.search(r"([\w/]+\.py)(?:::(\w+))?", line)
            filepath = match.group(1) if match else "unknown"

            issues.append({
                "type": "test_failure",
                "file": filepath,
                "line": 0,
                "message": line[:200],
                "tool": "pytest",
                "severity": "high",
                "cluster": "test_failure",
            })

    console.print(f"  Found {len(issues)} test failures")
    return issues


def collect_import_errors() -> list[dict]:
    """Check for import errors by trying to import all Python files."""
    console.print("[cyan]🔍 Checking for import errors...[/cyan]")

    issues = []
    py_files = list(Path(PROJECT_ROOT).rglob("*.py"))
    py_files = [f for f in py_files if ".venv" not in str(f) and "__pycache__" not in str(f)]

    for py_file in py_files[:100]:  # limit to avoid slowness
        rel_path = py_file.relative_to(PROJECT_ROOT)
        module_path = str(rel_path).replace("/", ".").replace(".py", "")

        rc, output = _run(f"python3 -c 'import {module_path}' 2>&1")
        if rc != 0 and "Error" in output:
            # Extract just the error line
            error_lines = [line for line in output.split("\n") if "Error" in line]
            error_msg = error_lines[-1] if error_lines else output[-200:]

            # Determine cluster
            if "ModuleNotFoundError" in output:
                cluster = "missing_deps"
            elif "ImportError" in output:
                cluster = "import_cycle"
            elif "SyntaxError" in output:
                cluster = "syntax"
            else:
                cluster = "init_error"

            issues.append({
                "type": "import_error",
                "file": str(rel_path),
                "line": 0,
                "message": error_msg[:200],
                "tool": "import_check",
                "severity": "critical",
                "cluster": cluster,
            })

    console.print(f"  Found {len(issues)} import errors")
    return issues


def collect_all() -> list[dict]:
    """Run all collectors and combine results."""
    console.print("\n[bold magenta]📊 ANTIGRAVITY REPORT COLLECTOR[/bold magenta]\n")

    all_issues = []
    all_issues.extend(collect_compile_errors())
    all_issues.extend(collect_ruff_errors())
    all_issues.extend(collect_pytest_errors())
    all_issues.extend(collect_import_errors())

    return all_issues


def save_report(issues: list[dict]):
    """Save the collected issues to _reports/."""
    report_dir = Path(REPORTS_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)

    # Save full report
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_issues": len(issues),
        "by_severity": {
            "critical": len([i for i in issues if i["severity"] == "critical"]),
            "high": len([i for i in issues if i["severity"] == "high"]),
            "medium": len([i for i in issues if i["severity"] == "medium"]),
            "low": len([i for i in issues if i["severity"] == "low"]),
        },
        "by_cluster": {},
        "issues": issues,
    }

    # Count by cluster
    for issue in issues:
        cluster = issue["cluster"]
        report["by_cluster"][cluster] = report["by_cluster"].get(cluster, 0) + 1

    report_file = report_dir / "full_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    console.print(f"\n[green]✓[/green] Full report saved: {report_file}")
    return report


def print_summary(report: dict):
    """Print a summary table."""
    table = Table(title="\n📊 ISSUE SUMMARY", border_style="magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="bold")

    for cluster, count in sorted(report["by_cluster"].items(), key=lambda x: -x[1]):
        table.add_row(cluster, str(count))

    table.add_row("─" * 20, "─" * 5)
    table.add_row("[bold]TOTAL[/bold]", f"[bold]{report['total_issues']}[/bold]")

    console.print(table)

    # Severity breakdown
    sev = report["by_severity"]
    console.print(f"\n  [red]🔴 Critical: {sev['critical']}[/red]")
    console.print(f"  [yellow]🟡 High: {sev['high']}[/yellow]")
    console.print(f"  [blue]🔵 Medium: {sev['medium']}[/blue]")
    console.print(f"  [dim]⚪ Low: {sev['low']}[/dim]\n")


def main():
    issues = collect_all()
    report = save_report(issues)
    print_summary(report)


if __name__ == "__main__":
    main()
