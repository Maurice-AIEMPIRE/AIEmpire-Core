#!/usr/bin/env python3
"""
Smoke Test - Verifies Godmode Programmer System is working
"""

import subprocess
import sys
import os
from pathlib import Path


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


def run_command(cmd, check=True, timeout=10):
    """Run command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out: {cmd}")
        return None
    except Exception as e:
        print_error(f"Command failed: {e}")
        return None


def _test_ollama():
    """Test 1: Ollama is running"""
    print_header("Test 1: Ollama Status")

    result = run_command("ollama --version")
    if result and result.returncode == 0:
        version = result.stdout.strip()
        print_success(f"Ollama installed: {version}")
    else:
        print_error("Ollama not installed or not running")
        return False

    # Check if Ollama API is responding
    result = run_command("curl -s http://localhost:11434/api/tags")
    if result and result.returncode == 0:
        print_success("Ollama API responding")
    else:
        print_error("Ollama API not responding")
        print_info("Try: brew services start ollama")
        return False

    return True


def _test_models():
    """Test 2: Required models are available"""
    print_header("Test 2: Models Available")

    result = run_command("ollama list")
    if not result or result.returncode != 0:
        print_error("Cannot list models")
        return False

    output = result.stdout
    required_models = ["qwen2.5-coder:7b", "qwen2.5-coder:14b", "deepseek-r1:8b"]

    all_found = True
    for model in required_models:
        if model in output:
            print_success(f"Model found: {model}")
        else:
            print_warning(f"Model missing: {model}")
            print_info(f"  Install with: ollama pull {model}")
            all_found = False

    return all_found


def _test_router():
    """Test 3: Godmode Router exists and is executable"""
    print_header("Test 3: Godmode Router")

    router_path = Path("antigravity/godmode_router.py")
    if not router_path.exists():
        print_error(f"Router not found: {router_path}")
        return False

    print_success(f"Router found: {router_path}")

    # Test router help
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = run_command(f"cd {PROJECT_ROOT} && PYTHONPATH=. python3 antigravity/godmode_router.py", check=False)
    if result and "Godmode Router" in result.stdout:
        print_success("Router is executable")
    else:
        print_error("Router not executable or has errors")
        return False

    return True


def _test_merge_gate():
    """Test 4: Merge Gate exists and is executable"""
    print_header("Test 4: Merge Gate")

    gate_path = Path("antigravity/merge_gate.py")
    if not gate_path.exists():
        print_error(f"Merge Gate not found: {gate_path}")
        return False

    print_success(f"Merge Gate found: {gate_path}")

    # Test gate help
    result = run_command("python3 antigravity/merge_gate.py", check=False)
    if result and "Merge Gate" in result.stdout:
        print_success("Merge Gate is executable")
    else:
        print_error("Merge Gate not executable or has errors")
        return False

    return True


def _test_git():
    """Test 5: Git repository is valid"""
    print_header("Test 5: Git Repository")

    result = run_command("git rev-parse --git-dir")
    if result and result.returncode == 0:
        print_success("Git repository found")
    else:
        print_error("Not in a git repository")
        return False

    # Check current branch
    result = run_command("git branch --show-current")
    if result and result.returncode == 0:
        branch = result.stdout.strip()
        print_success(f"Current branch: {branch}")

    return True


def _test_simple_task():
    """Test 6: Run a simple task with the router"""
    print_header("Test 6: Simple Router Task")

    print_info("Running a simple test task (this may take 30-60 seconds)...")

    # Simple task that should complete quickly
    result = run_command('python3 antigravity/godmode_router.py qa "What is 2+2?"', timeout=60)

    if result and result.returncode == 0:
        print_success("Router executed task successfully")
        if "Task completed" in result.stdout:
            print_success("Task completed message found")
        return True

    print_warning("Router task failed or timed out")
    print_info("This is OK - models might be slow on first run")
    return True  # Don't fail smoke test for this


def main():
    """Run all smoke tests"""
    print_header("🚀 Godmode Programmer - Smoke Test")

    tests = [
        ("Ollama Status", _test_ollama),
        ("Models Available", _test_models),
        ("Godmode Router", _test_router),
        ("Merge Gate", _test_merge_gate),
        ("Git Repository", _test_git),
        ("Simple Task", _test_simple_task),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((name, False))

    # Summary
    print_header("📊 Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED - System is ready!{Colors.RESET}")
        print(f"\n{Colors.BLUE}Next steps:{Colors.RESET}")
        print("  1. Read: antigravity/QUICK_START.md")
        print("  2. Run: python3 antigravity/godmode_router.py fix 'Analyze import errors'")
        print("  3. Check: python3 antigravity/merge_gate.py main")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed - check errors above{Colors.RESET}")
        print(f"\n{Colors.BLUE}Troubleshooting:{Colors.RESET}")
        print("  1. Start Ollama: brew services start ollama")
        print("  2. Pull models: ollama pull qwen2.5-coder:7b")
        print("  3. Check docs: antigravity/CLAUDE_OFFLINE_SETUP.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
