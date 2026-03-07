#!/usr/bin/env python3
"""
AIEmpire CLI Bot
================
Lokale Bot-CLI mit Claude-äquivalenten Fähigkeiten
Nutzung: python3 aibot.py <command> [args...]

Commands:
  aibot.py read <path>                    - Datei lesen
  aibot.py edit <path> <old> <new>        - Datei bearbeiten
  aibot.py exec <command>                 - Befehl ausführen
  aibot.py grep <pattern> [glob]          - Code durchsuchen
  aibot.py git <subcommand> [args...]     - Git Operationen
  aibot.py bash <command>                 - Bash ausführen
  aibot.py analyze <task>                 - Ollama Analyse
  aibot.py interactive                    - Interaktiver Chat-Modus
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple

REPO_ROOT = Path(__file__).parent
OLLAMA_MODEL = "qwen2.5:1.5b"
OLLAMA_URL = "http://localhost:11434"

# ─── COLORS ──────────────────────────────────────────────────────────────────
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'

def print_status(msg: str, level: str = "info"):
    """Pretty print status messages."""
    icons = {"info": "ℹ️", "ok": "✅", "error": "❌", "warn": "⚠️", "think": "🤔"}
    colors = {"info": Colors.CYAN, "ok": Colors.GREEN, "error": Colors.RED,
              "warn": Colors.YELLOW, "think": Colors.BLUE}
    icon = icons.get(level, "•")
    color = colors.get(level, Colors.RESET)
    print(f"{color}{icon} {msg}{Colors.RESET}")

# ─── FILE OPERATIONS ──────────────────────────────────────────────────────────

def cmd_read(filepath: str) -> bool:
    """Read file with syntax highlighting."""
    try:
        path = REPO_ROOT / filepath
        if not path.exists():
            print_status(f"File not found: {filepath}", "error")
            return False

        content = path.read_text()
        lines = content.split('\n')

        print_status(f"Reading: {filepath} ({len(lines)} lines)", "ok")
        print(f"{Colors.DIM}─" * 60 + Colors.RESET)

        for i, line in enumerate(lines[:100], 1):
            line_num = f"{Colors.DIM}{i:4d}{Colors.RESET}"
            print(f"{line_num} │ {line}")

        if len(lines) > 100:
            print(f"{Colors.DIM}... ({len(lines) - 100} more lines)")
        print(f"{Colors.DIM}─" * 60 + Colors.RESET)
        return True

    except Exception as e:
        print_status(f"Error reading file: {e}", "error")
        return False

def cmd_edit(filepath: str, old_string: str, new_string: str) -> bool:
    """Edit file with validation."""
    try:
        path = REPO_ROOT / filepath
        if not path.exists():
            print_status(f"File not found: {filepath}", "error")
            return False

        content = path.read_text()
        if old_string not in content:
            print_status(f"String not found in {filepath}", "error")
            print_status(f"Looking for: {old_string[:50]}...", "error")
            return False

        new_content = content.replace(old_string, new_string)
        path.write_text(new_content)
        print_status(f"Updated: {filepath}", "ok")
        return True

    except Exception as e:
        print_status(f"Edit error: {e}", "error")
        return False

# ─── COMMAND EXECUTION ──────────────────────────────────────────────────────

def cmd_execute(command: str, cwd: Optional[str] = None) -> bool:
    """Execute command and show output."""
    try:
        print_status(f"Executing: {command}", "think")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd or str(REPO_ROOT)
        )

        output = result.stdout + result.stderr
        if output:
            print(f"{Colors.DIM}─" * 60 + Colors.RESET)
            print(output[:3000])
            if len(output) > 3000:
                print(f"{Colors.DIM}... ({len(output) - 3000} bytes more)")
            print(f"{Colors.DIM}─" * 60 + Colors.RESET)

        success = result.returncode == 0
        status = "ok" if success else "error"
        print_status(f"Exit code: {result.returncode}", status)
        return success

    except subprocess.TimeoutExpired:
        print_status("Command timeout (>60s)", "error")
        return False
    except Exception as e:
        print_status(f"Execution error: {e}", "error")
        return False

def cmd_bash(command: str) -> bool:
    """Alias for execute."""
    return cmd_execute(command)

# ─── CODE SEARCH ──────────────────────────────────────────────────────────

def cmd_grep(pattern: str, glob_pattern: str = "**/*.py") -> bool:
    """Search code with ripgrep."""
    try:
        print_status(f"Searching for: {pattern}", "think")
        result = subprocess.run(
            ["grep", "-rn", pattern, str(REPO_ROOT), "--include=*.py"],
            capture_output=True,
            text=True,
            timeout=10
        )

        matches = result.stdout.split('\n')[:30]
        total = len([m for m in matches if m])

        print(f"{Colors.DIM}─" * 60 + Colors.RESET)
        for match in matches:
            if match:
                print(f"{Colors.YELLOW}{match}{Colors.RESET}")
        print(f"{Colors.DIM}─" * 60 + Colors.RESET)

        print_status(f"Found {total} matches", "ok")
        return True

    except Exception as e:
        print_status(f"Search error: {e}", "error")
        return False

# ─── GIT OPERATIONS ──────────────────────────────────────────────────────

def cmd_git(subcommand: str, *args) -> bool:
    """Git operations."""
    try:
        cmd = f"git {subcommand} {' '.join(args)}".strip()
        print_status(f"Git: {cmd}", "think")

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT)
        )

        output = result.stdout + result.stderr
        if output:
            print(f"{Colors.DIM}─" * 60 + Colors.RESET)
            print(output)
            print(f"{Colors.DIM}─" * 60 + Colors.RESET)

        success = result.returncode == 0
        status = "ok" if success else "error"
        print_status(f"Git result: {status}", status)
        return success

    except Exception as e:
        print_status(f"Git error: {e}", "error")
        return False

# ─── OLLAMA ANALYSIS ──────────────────────────────────────────────────────

def cmd_analyze(task: str) -> bool:
    """Analyze with Ollama (free, local)."""
    try:
        print_status(f"Analyzing with Ollama ({OLLAMA_MODEL})...", "think")

        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL, task],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(REPO_ROOT)
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"{Colors.BLUE}{output}{Colors.RESET}")
            print_status("Analysis complete", "ok")
            return True
        else:
            print_status("Ollama error (is it running?)", "error")
            return False

    except FileNotFoundError:
        print_status("Ollama not installed. Install with: brew install ollama", "error")
        return False
    except Exception as e:
        print_status(f"Analysis error: {e}", "error")
        return False

# ─── INTERACTIVE MODE ──────────────────────────────────────────────────────

def interactive_mode():
    """Interactive chat-like mode."""
    print(f"{Colors.BOLD}═══════════════════════════════════════{Colors.RESET}")
    print(f"{Colors.BOLD}🤖 AIEmpire Bot - Interactive Mode{Colors.RESET}")
    print(f"{Colors.BOLD}═══════════════════════════════════════{Colors.RESET}")
    print("Commands: read, edit, exec, grep, git, bash, analyze, help, quit")
    print()

    while True:
        try:
            user_input = input(f"{Colors.CYAN}> {Colors.RESET}").strip()
            if not user_input:
                continue

            if user_input == "quit" or user_input == "exit":
                print_status("Goodbye!", "info")
                break

            if user_input == "help":
                print(__doc__)
                continue

            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if cmd == "read":
                cmd_read(args)
            elif cmd == "edit":
                # parse: edit path old_string new_string
                edit_parts = args.split("|||", 2)
                if len(edit_parts) == 3:
                    cmd_edit(edit_parts[0].strip(), edit_parts[1].strip(), edit_parts[2].strip())
                else:
                    print_status("Format: edit path ||| old_string ||| new_string", "error")
            elif cmd == "exec":
                cmd_execute(args)
            elif cmd == "bash":
                cmd_bash(args)
            elif cmd == "grep":
                grep_parts = args.split(maxsplit=1)
                cmd_grep(grep_parts[0], grep_parts[1] if len(grep_parts) > 1 else "**/*.py")
            elif cmd == "git":
                git_parts = args.split(maxsplit=1)
                git_cmd = git_parts[0] if git_parts else "status"
                git_args = git_parts[1] if len(git_parts) > 1 else ""
                cmd_git(git_cmd, git_args)
            elif cmd == "analyze":
                cmd_analyze(args)
            else:
                print_status(f"Unknown command: {cmd}", "error")

        except KeyboardInterrupt:
            print()
            print_status("Interrupted", "info")
            break
        except Exception as e:
            print_status(f"Error: {e}", "error")

# ─── MAIN ──────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        interactive_mode()
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    if command == "read" and args:
        cmd_read(args[0])
    elif command == "edit" and len(args) >= 3:
        cmd_edit(args[0], args[1], args[2])
    elif command == "exec" and args:
        cmd_execute(" ".join(args))
    elif command == "bash" and args:
        cmd_bash(" ".join(args))
    elif command == "grep" and args:
        cmd_grep(args[0], args[1] if len(args) > 1 else "**/*.py")
    elif command == "git" and args:
        cmd_git(args[0], *args[1:])
    elif command == "analyze" and args:
        cmd_analyze(" ".join(args))
    elif command == "interactive":
        interactive_mode()
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
