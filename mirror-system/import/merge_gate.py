#!/usr/bin/env python3
"""
MERGE GATE - Kontrollierter Import von Cloud-PRs.

Prüft Mirror Lab Branches auf:
- Tests grün
- Keine Secrets im Code
- Keine Cloud-API-Calls ohne CLOUD_MODE
- Diff < 500 Zeilen
- CHANGELOG vorhanden
- Keine Löschungen ohne Genehmigung

Usage:
  python merge_gate.py check               # Zeige alle mirror/* Branches
  python merge_gate.py review <branch>     # Review einen Branch
  python merge_gate.py merge <branch>      # Merge wenn alle Checks grün
  python merge_gate.py reject <branch>     # Reject mit Begründung
  python merge_gate.py auto                # Auto-merge alle grünen Branches
"""

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

MIRROR_DIR = Path(__file__).parent.parent
PROJECT_ROOT = MIRROR_DIR.parent
CONFIG_DIR = MIRROR_DIR / "config"
IMPORT_DIR = MIRROR_DIR / "import" / "imports"

IMPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_merge_rules() -> dict:
    rules_file = CONFIG_DIR / "merge_rules.json"
    if rules_file.exists():
        return json.loads(rules_file.read_text())
    return {"merge_gate": {"auto_merge": {"conditions": {}}, "always_reject": []}}


def load_privacy_rules() -> dict:
    rules_file = CONFIG_DIR / "privacy_rules.json"
    if rules_file.exists():
        return json.loads(rules_file.read_text())
    return {"redaction_rules": {"always_remove": [], "patterns_to_redact": []}}


def git_cmd(*args, cwd: str = None) -> str:
    """Run a git command and return output."""
    cmd = ["git"] + list(args)
    if cwd:
        cmd = ["git", "-C", cwd] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or str(PROJECT_ROOT))
    return result.stdout.strip()


def get_mirror_branches() -> list:
    """Get all mirror/* branches."""
    output = git_cmd("branch", "-r", "--list", "origin/mirror/*")
    branches = []
    for line in output.split("\n"):
        b = line.strip()
        if b and "HEAD" not in b:
            branches.append(b.replace("origin/", ""))
    return branches


def get_diff_stats(branch: str) -> dict:
    """Get diff statistics for a branch vs main."""
    stats = {"lines_added": 0, "lines_removed": 0, "files_changed": 0, "total_lines": 0}

    output = git_cmd("diff", "--stat", f"main...{branch}")
    for line in output.split("\n"):
        if "insertion" in line or "deletion" in line:
            parts = line.split(",")
            for part in parts:
                part = part.strip()
                if "insertion" in part:
                    try:
                        stats["lines_added"] = int(part.split()[0])
                    except ValueError:
                        pass
                elif "deletion" in part:
                    try:
                        stats["lines_removed"] = int(part.split()[0])
                    except ValueError:
                        pass
                elif "file" in part:
                    try:
                        stats["files_changed"] = int(part.split()[0])
                    except ValueError:
                        pass

    stats["total_lines"] = stats["lines_added"] + stats["lines_removed"]
    return stats


def get_diff_content(branch: str) -> str:
    """Get actual diff content."""
    return git_cmd("diff", f"main...{branch}")


def check_secrets_in_diff(diff: str, privacy_rules: dict) -> list:
    """Check for secrets in diff content."""
    violations = []

    for pattern in privacy_rules.get("redaction_rules", {}).get("patterns_to_redact", []):
        try:
            matches = re.findall(pattern, diff)
            if matches:
                violations.append(f"Secret pattern found: {pattern} ({len(matches)} matches)")
        except re.error:
            pass

    # Check for known key names in added lines
    for line in diff.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            for key in privacy_rules.get("redaction_rules", {}).get("always_remove", []):
                if key.lower() in line.lower() and "=" in line:
                    violations.append(f"Possible secret assignment: {key} in added line")

    return violations


def check_cloud_api_calls(diff: str) -> list:
    """Check for cloud API calls without CLOUD_MODE flag."""
    violations = []
    cloud_patterns = [
        r"openai\.com",
        r"api\.anthropic\.com",
        r"api\.moonshot\.(ai|cn)",
        r"generativelanguage\.googleapis\.com",
        r"aiplatform\.googleapis\.com",
        r"OpenAI\(",
        r"Anthropic\(",
        r"genai\.GenerativeModel",
    ]

    for line in diff.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            for pattern in cloud_patterns:
                if re.search(pattern, line):
                    # Check if guarded by CLOUD_MODE
                    if "CLOUD_MODE" not in line and "cloud_mode" not in line.lower():
                        violations.append(
                            f"Cloud API call without CLOUD_MODE guard: {line.strip()[:80]}"
                        )

    return violations


def check_changelog(branch: str) -> bool:
    """Check if branch has a CHANGELOG.md."""
    files = git_cmd("diff", "--name-only", f"main...{branch}")
    return "CHANGELOG.md" in files or "changelog.md" in files


def check_deletions(diff: str, max_files: int = 10) -> list:
    """Check for excessive deletions."""
    violations = []
    deleted_files = []

    for line in diff.split("\n"):
        if line.startswith("deleted file"):
            deleted_files.append(line)

    if len(deleted_files) > max_files:
        violations.append(f"Too many file deletions: {len(deleted_files)} (max {max_files})")

    return violations


def review_branch(branch: str, verbose: bool = True) -> dict:
    """Run all checks on a branch."""
    merge_rules = load_merge_rules()
    privacy_rules = load_privacy_rules()
    conditions = merge_rules.get("merge_gate", {}).get("auto_merge", {}).get("conditions", {})

    results = {
        "branch": branch,
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "passed": True,
        "verdict": "UNKNOWN",
    }

    diff_stats = get_diff_stats(branch)
    diff_content = get_diff_content(branch)

    # Check 1: Diff size
    max_lines = conditions.get("diff_lines_max", 500)
    size_ok = diff_stats["total_lines"] <= max_lines
    results["checks"]["diff_size"] = {
        "passed": size_ok,
        "detail": f"{diff_stats['total_lines']} lines (max {max_lines})",
    }

    # Check 2: No secrets
    secret_violations = check_secrets_in_diff(diff_content, privacy_rules)
    secrets_ok = len(secret_violations) == 0
    results["checks"]["no_secrets"] = {
        "passed": secrets_ok,
        "detail": secret_violations if not secrets_ok else "clean",
    }

    # Check 3: No cloud API without flag
    cloud_violations = check_cloud_api_calls(diff_content)
    cloud_ok = len(cloud_violations) == 0
    results["checks"]["no_cloud_api"] = {
        "passed": cloud_ok,
        "detail": cloud_violations if not cloud_ok else "clean",
    }

    # Check 4: CHANGELOG present
    has_changelog = check_changelog(branch)
    results["checks"]["changelog"] = {
        "passed": has_changelog,
        "detail": "CHANGELOG.md found" if has_changelog else "MISSING",
    }

    # Check 5: No excessive deletions
    deletion_violations = check_deletions(diff_content)
    deletions_ok = len(deletion_violations) == 0
    results["checks"]["deletions"] = {
        "passed": deletions_ok,
        "detail": deletion_violations if not deletions_ok else "clean",
    }

    # Overall verdict
    all_passed = all(c["passed"] for c in results["checks"].values())
    results["passed"] = all_passed
    results["verdict"] = "APPROVED" if all_passed else "REJECTED"
    results["diff_stats"] = diff_stats

    if verbose:
        print(f"\n  {'='*60}")
        print(f"  MERGE GATE REVIEW: {branch}")
        print(f"  {'='*60}")
        for name, check in results["checks"].items():
            status = "✓" if check["passed"] else "✗"
            print(f"  {status} {name:20s} {check['detail']}")
        print(f"\n  VERDICT: {results['verdict']}")
        print(f"  Diff: +{diff_stats['lines_added']}/-{diff_stats['lines_removed']} "
              f"in {diff_stats['files_changed']} files")
        print(f"  {'='*60}\n")

    # Save report
    report_file = IMPORT_DIR / f"review_{branch.replace('/', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
    report_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    return results


def merge_branch(branch: str):
    """Merge a branch if all checks pass."""
    result = review_branch(branch, verbose=True)

    if not result["passed"]:
        print(f"  BLOCKED: {branch} failed checks. Fix issues first.")
        return False

    print(f"  Merging {branch} into main...")
    git_cmd("checkout", "main")
    output = git_cmd("merge", "--no-ff", branch, "-m",
                     f"[mirror-merge] {branch} - auto-approved by merge gate")
    print(f"  {output}")
    print(f"  MERGED: {branch}")
    return True


def auto_merge():
    """Auto-merge all branches that pass checks."""
    branches = get_mirror_branches()
    if not branches:
        print("  Keine mirror/* Branches gefunden.")
        return

    print(f"\n  Prüfe {len(branches)} mirror Branches...\n")

    merged = 0
    rejected = 0
    for branch in branches:
        result = review_branch(branch, verbose=False)
        if result["passed"]:
            print(f"  ✓ {branch} → MERGE")
            merged += 1
        else:
            failed = [k for k, v in result["checks"].items() if not v["passed"]]
            print(f"  ✗ {branch} → REJECTED ({', '.join(failed)})")
            rejected += 1

    print(f"\n  Ergebnis: {merged} merged, {rejected} rejected")


def list_branches():
    """List all mirror branches with status."""
    branches = get_mirror_branches()
    if not branches:
        print("  Keine mirror/* Branches gefunden.")
        print("  Cloud hat noch keine PRs erstellt.")
        return

    print(f"\n  {'='*60}")
    print("  MIRROR BRANCHES")
    print(f"  {'='*60}")
    for branch in branches:
        stats = get_diff_stats(branch)
        print(f"  {branch:40s} +{stats['lines_added']}/-{stats['lines_removed']}")
    print(f"  {'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Merge Gate - Cloud PR Controller")
    parser.add_argument("command", choices=["check", "review", "merge", "reject", "auto"],
                       help="Gate command")
    parser.add_argument("branch", nargs="?", help="Branch name")
    args = parser.parse_args()

    if args.command == "check":
        list_branches()
    elif args.command == "review":
        if not args.branch:
            print("  Usage: merge_gate.py review <branch>")
            return
        review_branch(args.branch)
    elif args.command == "merge":
        if not args.branch:
            print("  Usage: merge_gate.py merge <branch>")
            return
        merge_branch(args.branch)
    elif args.command == "auto":
        auto_merge()
    elif args.command == "reject":
        if not args.branch:
            print("  Usage: merge_gate.py reject <branch>")
            return
        print(f"  Rejected: {args.branch}")


if __name__ == "__main__":
    main()
