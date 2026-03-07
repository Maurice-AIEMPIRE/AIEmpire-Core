"""
Merge Gate - Ensures quality before merging agent branches
"""

import subprocess
import sys
from pathlib import Path
from typing import Any


class MergeGate:
    def __init__(self, repo_path: Path = Path.cwd()) -> None:
        self.repo = repo_path

    def run_checks(self, branch: str) -> dict[str, Any]:
        """Run all quality checks"""
        results: dict[str, Any] = {}

        print(f"\n🔍 Running quality checks for branch: {branch}")

        # 1. Compile Check
        print("  → Checking Python compilation...")
        compile_result = subprocess.run(
            ["python3", "-m", "compileall", "-q", "."],
            capture_output=True,
            text=True,
            cwd=self.repo,
        )
        results["compile"] = compile_result.returncode == 0
        results["compile_output"] = compile_result.stderr

        # 2. Lint Check (if ruff is available)
        print("  → Running linter...")
        lint_result = subprocess.run(
            ["ruff", "check", ".", "--quiet"],
            capture_output=True,
            text=True,
            cwd=self.repo,
        )
        # ruff returns 0 if no issues, 1 if issues found
        results["lint"] = lint_result.returncode == 0
        results["lint_output"] = lint_result.stdout
        results["lint_available"] = True

        # If ruff not available, skip
        if "command not found" in lint_result.stderr or "No such file" in lint_result.stderr:
            results["lint_available"] = False
            results["lint"] = True  # Don't fail if linter not installed

        # 3. Tests (if pytest available)
        print("  → Running tests...")
        test_result = subprocess.run(
            ["pytest", "-q", "--tb=short", "--maxfail=5"],
            capture_output=True,
            text=True,
            cwd=self.repo,
            timeout=60,
        )
        results["tests"] = test_result.returncode == 0
        results["test_output"] = test_result.stdout
        results["test_available"] = True

        # If pytest not available or no tests, skip
        if "command not found" in test_result.stderr or "no tests ran" in test_result.stdout.lower():
            results["test_available"] = False
            results["tests"] = True  # Don't fail if no tests

        # 4. Diff stats
        print("  → Analyzing changes...")
        diff_result = subprocess.run(
            ["git", "diff", "main", branch, "--stat"],
            capture_output=True,
            text=True,
            cwd=self.repo,
        )
        results["diff"] = diff_result.stdout

        # 5. Check for merge conflicts
        merge_check = subprocess.run(
            ["git", "merge-tree", "main", branch],
            capture_output=True,
            text=True,
            cwd=self.repo,
        )
        results["has_conflicts"] = "CONFLICT" in merge_check.stdout

        return results

    def approve_merge(self, branch: str) -> tuple[bool, str]:
        """Check if branch can be merged"""
        checks = self.run_checks(branch)

        print(f"\n{'=' * 60}")
        print(f"🔍 Merge Gate Results for: {branch}")
        print(f"{'=' * 60}")

        # Compile check
        status = "✅ PASS" if checks["compile"] else "❌ FAIL"
        print(f"  Compile:  {status}")
        if not checks["compile"]:
            compile_err = str(checks["compile_output"])
            print(f"    Error: {compile_err[:200]}")

        # Lint check
        if checks["lint_available"]:
            status = "✅ PASS" if checks["lint"] else "⚠️  WARN"
            print(f"  Lint:     {status}")
            if not checks["lint"] and checks["lint_output"]:
                lint_out = str(checks["lint_output"])
                print(f"    Issues: {lint_out[:200]}")
        else:
            print("  Lint:     ⊘ SKIP (ruff not installed)")

        # Test check
        if checks["test_available"]:
            status = "✅ PASS" if checks["tests"] else "❌ FAIL"
            print(f"  Tests:    {status}")
            if not checks["tests"]:
                test_out = str(checks["test_output"])
                print(f"    Output: {test_out[:200]}")
        else:
            print("  Tests:    ⊘ SKIP (no tests found)")

        # Conflicts check
        status = "❌ CONFLICTS" if checks["has_conflicts"] else "✅ CLEAN"
        print(f"  Conflicts: {status}")

        # Diff stats
        print("\n📊 Changes:")
        if checks["diff"]:
            print(f"  {checks['diff']}")
        else:
            print("  No changes detected")

        print(f"{'=' * 60}")

        # Decision logic
        blocking_issues: list[str] = []

        if not checks["compile"]:
            blocking_issues.append("Compilation errors detected")

        if checks["has_conflicts"]:
            blocking_issues.append("Merge conflicts detected")

        # Tests are blocking only if they exist and fail
        if checks["test_available"] and not checks["tests"]:
            blocking_issues.append("Test failures detected")

        if blocking_issues:
            reason = "\n  - ".join([""] + blocking_issues)
            print(f"\n🚫 MERGE BLOCKED:{reason}")
            return False, reason

        # Warnings (non-blocking)
        warnings: list[str] = []
        if checks["lint_available"] and not checks["lint"]:
            warnings.append("Linting issues (non-blocking)")

        if warnings:
            warning_msg = "\n  - ".join([""] + warnings)
            print(f"\n⚠️  WARNINGS:{warning_msg}")

        print("\n✅ ALL CHECKS PASSED - Safe to merge")
        return True, "All quality checks passed"

    def merge_branch(self, branch: str, auto_merge: bool = False) -> None:
        """Merge branch if checks pass"""
        approved, reason = self.approve_merge(branch)

        if not approved:
            print(f"\n🚫 Merge blocked for {branch}")
            print(f"   Reason: {reason}")
            sys.exit(1)

        if auto_merge:
            print(f"\n🔄 Auto-merging {branch} into main...")

            # Checkout main
            subprocess.run(["git", "checkout", "main"], cwd=self.repo)

            # Merge with no-ff (create merge commit)
            merge_result = subprocess.run(
                [
                    "git",
                    "merge",
                    "--no-ff",
                    "-m",
                    f"Merge {branch} (auto-approved by merge gate)",
                    branch,
                ],
                capture_output=True,
                text=True,
                cwd=self.repo,
            )

            if merge_result.returncode == 0:
                print(f"✅ Successfully merged {branch} into main")
            else:
                print(f"❌ Merge failed: {merge_result.stderr}")
                sys.exit(1)
        else:
            print("\n✅ Ready to merge")
            print(f"   Run: git checkout main && git merge --no-ff {branch}")


def main() -> None:
    if len(sys.argv) < 2:
        print("""
🚦 Merge Gate - Quality Control for Agent Branches

Usage:
  python merge_gate.py <branch_name> [--auto]

Options:
  --auto    Automatically merge if all checks pass

Examples:
  python merge_gate.py agent/fixer/import-fixes
  python merge_gate.py agent/coder/new-feature --auto

Checks:
  ✓ Python compilation (blocking)
  ✓ Linting (warning only)
  ✓ Tests (blocking if tests exist)
  ✓ Merge conflicts (blocking)
""")
        sys.exit(1)

    branch = sys.argv[1]
    auto = "--auto" in sys.argv

    gate = MergeGate()
    gate.merge_branch(branch, auto_merge=auto)


if __name__ == "__main__":
    main()
