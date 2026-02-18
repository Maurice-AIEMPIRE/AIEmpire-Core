#!/usr/bin/env python3
"""
GODMODE PROGRAMMER - 4-Role Local AI Router
=============================================
Routes tasks to 4 specialized roles via local Ollama models.
Each role works in its own git branch. Merge only after QA pass.

Usage:
    python godmode/router.py "Fix the import errors in brain_system/"
    python godmode/router.py --file issues.txt
    python godmode/router.py --status
    python godmode/router.py --merge agent/fixer/fix-imports

Roles:
    ARCHITECT → Struktur, Interfaces, API-Design
    FIXER     → Bugs, Tracebacks, Edge-Cases
    CODER     → Feature-Implementierung
    QA        → Tests, Lint, Review
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================
# CONFIG
# ============================================

GODMODE_DIR = Path(__file__).parent
CONFIG_PATH = GODMODE_DIR / "config.json"
LOG_DIR = GODMODE_DIR / "logs"
REPO_ROOT = GODMODE_DIR.parent


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


CONFIG = load_config()
OLLAMA_URL = CONFIG["ollama"]["base_url"]


# ============================================
# OLLAMA CLIENT
# ============================================


def ollama_available():
    """Check if Ollama is running."""
    try:
        import urllib.request

        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def ollama_chat(model, system_prompt, user_message, temperature=0.3, max_tokens=4096):
    """Send a chat request to Ollama and return the response."""
    import urllib.request

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
    ).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode())
            return result.get("message", {}).get("content", "")
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================
# TASK ROUTER — decides which role handles a task
# ============================================


def classify_task(task_description):
    """Classify a task into the right role based on keywords."""
    desc_lower = task_description.lower()
    routing = CONFIG["task_routing"]

    # Check error/fix keywords first (highest priority)
    for kw in routing["error_keywords"]:
        if kw.lower() in desc_lower:
            return "fixer"

    # Architecture keywords
    for kw in routing["architecture_keywords"]:
        if kw.lower() in desc_lower:
            return "architect"

    # QA keywords
    for kw in routing["qa_keywords"]:
        if kw.lower() in desc_lower:
            return "qa"

    # Feature keywords
    for kw in routing["feature_keywords"]:
        if kw.lower() in desc_lower:
            return "coder"

    # Default: coder
    return "coder"


def classify_multi(task_description):
    """Determine if multiple roles should be involved."""
    roles_needed = set()
    desc_lower = task_description.lower()
    routing = CONFIG["task_routing"]

    for kw in routing["error_keywords"]:
        if kw.lower() in desc_lower:
            roles_needed.add("fixer")
    for kw in routing["architecture_keywords"]:
        if kw.lower() in desc_lower:
            roles_needed.add("architect")
    for kw in routing["qa_keywords"]:
        if kw.lower() in desc_lower:
            roles_needed.add("qa")
    for kw in routing["feature_keywords"]:
        if kw.lower() in desc_lower:
            roles_needed.add("coder")

    if not roles_needed:
        roles_needed.add("coder")

    return list(roles_needed)


# ============================================
# GIT BRANCH MANAGEMENT
# ============================================


def git_current_branch():
    """Get current git branch."""
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def git_create_branch(branch_name):
    """Create and checkout a new branch from main."""
    # Save current branch
    current = git_current_branch()

    # Create branch from main
    subprocess.run(["git", "checkout", "main"], cwd=REPO_ROOT, capture_output=True)
    subprocess.run(["git", "pull", "--rebase"], cwd=REPO_ROOT, capture_output=True)
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Branch might already exist
        subprocess.run(["git", "checkout", branch_name], cwd=REPO_ROOT, capture_output=True)
    return current


def git_commit_and_return(message, return_branch="main"):
    """Stage all, commit, and return to previous branch."""
    subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message, "--allow-empty"],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    subprocess.run(["git", "checkout", return_branch], cwd=REPO_ROOT, capture_output=True)


# ============================================
# MERGE GATE — only merge if checks pass
# ============================================


def run_merge_checks():
    """Run all merge gate checks. Returns (passed, results)."""
    checks = CONFIG["merge_gate"]["required_checks"]
    results = []
    all_passed = True

    for cmd in checks:
        result = subprocess.run(cmd, shell=True, cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
        passed = result.returncode == 0
        results.append(
            {
                "command": cmd,
                "passed": passed,
                "output": (result.stdout + result.stderr)[:500],
            }
        )
        if not passed:
            all_passed = False

    return all_passed, results


def merge_branch(branch_name):
    """Merge a branch into main if merge gate passes."""
    # Switch to the branch and run checks
    current = git_current_branch()
    subprocess.run(["git", "checkout", branch_name], cwd=REPO_ROOT, capture_output=True)

    passed, results = run_merge_checks()

    if not passed:
        print(f"\n❌ MERGE BLOCKED for {branch_name}")
        for r in results:
            status = "✅" if r["passed"] else "❌"
            print(f"  {status} {r['command']}")
            if not r["passed"]:
                print(f"     → {r['output'][:200]}")
        subprocess.run(["git", "checkout", current], cwd=REPO_ROOT, capture_output=True)
        return False

    # Merge into main
    subprocess.run(["git", "checkout", "main"], cwd=REPO_ROOT, capture_output=True)
    result = subprocess.run(
        [
            "git",
            "merge",
            "--no-ff",
            branch_name,
            "-m",
            f"Merge {branch_name} (Godmode auto-merge)",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"\n✅ MERGED: {branch_name} → main")
        # Delete the branch
        subprocess.run(["git", "branch", "-d", branch_name], cwd=REPO_ROOT, capture_output=True)
        return True
    else:
        print(f"\n⚠️  MERGE CONFLICT: {branch_name}")
        print(result.stderr[:300])
        subprocess.run(["git", "merge", "--abort"], cwd=REPO_ROOT, capture_output=True)
        subprocess.run(["git", "checkout", current], cwd=REPO_ROOT, capture_output=True)
        return False


# ============================================
# TASK EXECUTION
# ============================================


def gather_context(role, task_description):
    """Gather relevant context for the role."""
    context_parts = []

    # Always include repo structure (top-level)
    result = subprocess.run(
        [
            "find",
            ".",
            "-maxdepth",
            "2",
            "-type",
            "f",
            "-name",
            "*.py",
            "-not",
            "-path",
            "./.venv/*",
            "-not",
            "-path",
            "./__pycache__/*",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    context_parts.append(f"=== Python files in repo ===\n{result.stdout[:2000]}")

    # Role-specific context
    if role == "fixer":
        # Include recent error logs
        report_dir = REPO_ROOT / "antigravity" / "_reports"
        if report_dir.exists():
            for f in sorted(report_dir.iterdir())[-3:]:
                try:
                    content = f.read_text()[:1000]
                    context_parts.append(f"=== Error Report: {f.name} ===\n{content}")
                except Exception:
                    pass

    elif role == "architect":
        # Include CLAUDE.md for architecture context
        claude_md = REPO_ROOT / "CLAUDE.md"
        if claude_md.exists():
            context_parts.append(f"=== Architecture Context ===\n{claude_md.read_text()[:3000]}")

    elif role == "qa":
        # Include git diff
        result = subprocess.run(
            ["git", "diff", "--stat", "main"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            context_parts.append(f"=== Git Diff (vs main) ===\n{result.stdout[:2000]}")

    return "\n\n".join(context_parts)


def execute_task(task_description, force_role=None):
    """Execute a task by routing it to the right role(s)."""
    if not ollama_available():
        print("❌ Ollama is not running! Start it with: ollama serve")
        sys.exit(1)

    # Classify task
    if force_role:
        roles = [force_role]
    else:
        roles = classify_multi(task_description)

    print(f"\n{'=' * 60}")
    print("🧠 GODMODE PROGRAMMER — Task Router")
    print(f"{'=' * 60}")
    print(f"📝 Task: {task_description[:100]}")
    print(f"🎯 Roles: {', '.join(r.upper() for r in roles)}")
    print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'=' * 60}\n")

    results = {}

    for role in roles:
        role_config = CONFIG["roles"][role]
        model = role_config["model"]
        system_prompt = role_config["system_prompt"]
        temperature = role_config["temperature"]
        max_tokens = role_config["max_tokens"]

        # Create branch
        timestamp = datetime.now().strftime("%m%d-%H%M")
        slug = task_description[:30].lower().replace(" ", "-").replace("/", "-")
        branch = f"{role_config['branch_prefix']}/{slug}-{timestamp}"

        print(f"🔄 [{role.upper()}] Using {model}...")
        print(f"   Branch: {branch}")

        # Gather context
        context = gather_context(role, task_description)
        full_prompt = f"""TASK: {task_description}

CONTEXT:
{context}

Provide your response as structured JSON per your role specification."""

        # Call Ollama
        start_time = time.time()
        response = ollama_chat(model, system_prompt, full_prompt, temperature, max_tokens)
        elapsed = time.time() - start_time

        print(f"   ⏱️  Response in {elapsed:.1f}s ({len(response)} chars)")

        # Parse response
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                try:
                    parsed = json.loads(response[json_start:json_end])
                except json.JSONDecodeError:
                    parsed = {"raw_response": response[:2000]}
            else:
                parsed = {"raw_response": response[:2000]}

        results[role] = {
            "model": model,
            "branch": branch,
            "response": parsed,
            "elapsed_seconds": round(elapsed, 1),
            "timestamp": datetime.now().isoformat(),
        }

        # Log the result
        log_result(role, task_description, results[role])

        print(f"   ✅ [{role.upper()}] Done\n")

    # Print summary
    print_summary(task_description, results)
    return results


# ============================================
# SUMMARY PRINTER
# ============================================


def print_summary(task_description, results):
    """Print a formatted summary of all role results."""
    print(f"\n{'=' * 60}")
    print("📊 GODMODE SUMMARY")
    print(f"{'=' * 60}")
    print(f"📝 Task: {task_description[:100]}")
    print(f"🎯 Roles executed: {len(results)}")
    print(f"⏰ Finished: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'─' * 60}")

    for role, data in results.items():
        model = data.get("model", "unknown")
        elapsed = data.get("elapsed_seconds", 0)
        response = data.get("response", {})

        print(f"\n🔹 [{role.upper()}] — {model} ({elapsed}s)")

        if isinstance(response, dict):
            if "error" in response:
                print(f"   ❌ Error: {response['error'][:200]}")
            elif "raw_response" in response:
                # Truncate raw response for display
                raw = response["raw_response"][:500]
                print(f"   📄 Raw response:\n   {raw[:300]}...")
            else:
                # Pretty-print key fields
                for key, val in list(response.items())[:5]:
                    val_str = str(val)[:150]
                    print(f"   • {key}: {val_str}")
        else:
            print(f"   📄 {str(response)[:300]}")

    # Log summary
    log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}_summary.jsonl"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(
            json.dumps(
                {
                    "task": task_description[:200],
                    "roles": list(results.keys()),
                    "total_time": sum(r.get("elapsed_seconds", 0) for r in results.values()),
                    "timestamp": datetime.now().isoformat(),
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    print(f"\n{'=' * 60}")
    print(f"💾 Logged to: {log_file}")
    print(f"{'=' * 60}\n")


# ============================================
# LOGGING
# ============================================


def log_result(role, task, result):
    """Log a task result to disk."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"{date}_{role}.jsonl"

    entry = {
        "task": task[:200],
        "result": result,
        "timestamp": datetime.now().isoformat(),
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ============================================
# STATUS DASHBOARD
# ============================================


def show_status():
    """Show status of all roles and pending branches."""
    print(f"\n{'=' * 60}")
    print("🧠 GODMODE PROGRAMMER — Status")
    print(f"{'=' * 60}\n")

    # Ollama status
    if ollama_available():
        print("✅ Ollama: RUNNING")
        # Show loaded models
        try:
            import urllib.request

            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
                print(f"   Models available: {', '.join(models)}")
        except Exception:
            pass
    else:
        print("❌ Ollama: NOT RUNNING")

    # Role configs
    print("\n📋 Roles:")
    for role, cfg in CONFIG["roles"].items():
        print(f"   {role.upper():12s} → {cfg['model']:25s} (temp={cfg['temperature']})")

    # Pending agent branches
    result = subprocess.run(
        ["git", "branch", "--list", "agent/*"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    branches = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]
    if branches:
        print(f"\n🌿 Agent Branches ({len(branches)}):")
        for b in branches:
            print(f"   {b}")
    else:
        print("\n🌿 No agent branches (all merged or none created yet)")

    # Recent logs
    if LOG_DIR.exists():
        logs = sorted(LOG_DIR.iterdir(), reverse=True)[:5]
        if logs:
            print("\n📝 Recent Logs:")
            for lf in logs:
                lines = sum(1 for _ in open(lf))
                print(f"   {lf.name} ({lines} entries)")

    # Merge gate checks
    print("\n🔒 Merge Gate Checks:")
    for cmd in CONFIG["merge_gate"]["required_checks"]:
        print(f"   • {cmd}")

    print()


# ============================================
# ISSUE COLLECTOR
# ============================================


def collect_issues():
    """Collect all issues from the repo and create a prioritized task queue."""
    print("\n🔍 Collecting issues from repo...\n")
    issues = []

    # 1. Check for Python syntax errors
    result = subprocess.run(
        ["python3", "-m", "compileall", ".", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.stderr:
        for line in result.stderr.strip().split("\n"):
            if line.strip():
                issues.append(
                    {
                        "type": "syntax_error",
                        "severity": "critical",
                        "message": line.strip(),
                        "owner": "fixer",
                    }
                )

    # 2. Check ruff lint
    result = subprocess.run(
        ["ruff", "check", ".", "--select", "E,F,I", "--output-format", "json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    try:
        lint_results = json.loads(result.stdout)
        for item in lint_results[:50]:  # Cap at 50
            issues.append(
                {
                    "type": "lint",
                    "severity": "warning",
                    "file": item.get("filename", ""),
                    "line": item.get("location", {}).get("row", 0),
                    "message": item.get("message", ""),
                    "code": item.get("code", ""),
                    "owner": "fixer",
                }
            )
    except (json.JSONDecodeError, TypeError):
        pass

    # 3. Check for missing imports
    result = subprocess.run(
        ["grep", "-rn", "^import\\|^from", "--include=*.py", "-l", "."],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    py_files = result.stdout.strip().split("\n")
    for pyf in py_files[:30]:
        if not pyf.strip() or ".venv" in pyf:
            continue
        check = subprocess.run(
            ["python3", "-c", f"import ast; ast.parse(open('{pyf}').read())"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            issues.append(
                {
                    "type": "parse_error",
                    "severity": "critical",
                    "file": pyf,
                    "message": check.stderr[:200],
                    "owner": "fixer",
                }
            )

    # Save issues
    issues_file = GODMODE_DIR / "ISSUES.json"
    with open(issues_file, "w") as f:
        json.dump(
            {
                "collected_at": datetime.now().isoformat(),
                "total": len(issues),
                "issues": issues,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    # Print summary
    by_severity = {}
    by_owner = {}
    for issue in issues:
        sev = issue.get("severity", "unknown")
        owner = issue.get("owner", "unassigned")
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_owner[owner] = by_owner.get(owner, 0) + 1

    print(f"📊 Found {len(issues)} issues:")
    for sev, count in sorted(by_severity.items()):
        icon = "🔴" if sev == "critical" else "🟡" if sev == "warning" else "⚪"
        print(f"   {icon} {sev}: {count}")

    print("\n👤 By role:")
    for owner, count in sorted(by_owner.items()):
        print(f"   {owner.upper()}: {count}")

    print(f"\n💾 Saved to: {issues_file}")
    return issues


# ============================================
# BATCH PROCESSOR
# ============================================


def process_issues_file(filepath):
    """Read tasks from a file and process them sequentially."""
    with open(filepath) as f:
        tasks = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"\n📋 Processing {len(tasks)} tasks from {filepath}\n")

    for i, task in enumerate(tasks, 1):
        print(f"\n{'=' * 60}")
        print(f"  Task {i}/{len(tasks)}")
        print(f"{'=' * 60}")
        execute_task(task)

    print(f"\n✅ All {len(tasks)} tasks processed!")


# ============================================
# CLI
# ============================================


def main():
    parser = argparse.ArgumentParser(
        description="🧠 Godmode Programmer — 4-Role Local AI Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python godmode/router.py "Fix import errors in brain_system/"
  python godmode/router.py --role fixer "TypeError in orchestrator.py line 45"
  python godmode/router.py --role architect "Design new plugin system"
  python godmode/router.py --file tasks.txt
  python godmode/router.py --collect
  python godmode/router.py --status
  python godmode/router.py --merge agent/fixer/fix-imports-0210
  python godmode/router.py --check
        """,
    )

    parser.add_argument("task", nargs="?", help="Task description")
    parser.add_argument(
        "--role",
        choices=["architect", "fixer", "coder", "qa"],
        help="Force a specific role",
    )
    parser.add_argument("--file", help="Read tasks from file (one per line)")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--collect", action="store_true", help="Collect all issues")
    parser.add_argument("--merge", help="Merge an agent branch into main")
    parser.add_argument("--check", action="store_true", help="Run merge gate checks only")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.collect:
        collect_issues()
    elif args.merge:
        merge_branch(args.merge)
    elif args.check:
        passed, results = run_merge_checks()
        for r in results:
            status = "✅" if r["passed"] else "❌"
            print(f"{status} {r['command']}")
            if not r["passed"]:
                print(f"   → {r['output'][:300]}")
        print(f"\n{'✅ ALL PASSED' if passed else '❌ CHECKS FAILED'}")
    elif args.file:
        process_issues_file(args.file)
    elif args.task:
        execute_task(args.task, force_role=args.role)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
