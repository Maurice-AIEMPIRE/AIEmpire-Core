#!/usr/bin/env python3
"""
Safari Backdrop-Filter Fix - Automated Prefixer.

Scans all HTML/CSS files and ensures every `backdrop-filter` line
also has a corresponding `-webkit-backdrop-filter` line.

Idempotent: safe to run multiple times. Won't duplicate existing prefixes.

Usage:
    python scripts/fix_backdrop_filter.py              # Dry run (show changes)
    python scripts/fix_backdrop_filter.py --apply      # Apply changes
    python scripts/fix_backdrop_filter.py --check      # Exit 1 if fixes needed
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# File patterns to scan
SCAN_PATTERNS = ["**/*.html", "**/*.css", "**/*.htm", "**/*.scss"]

# Directories to skip
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".next", "dist", "build"}

# Regex to find backdrop-filter that isn't already prefixed
BACKDROP_RE = re.compile(r"^(\s*)(backdrop-filter\s*:\s*.+;)", re.MULTILINE)
WEBKIT_RE = re.compile(r"-webkit-backdrop-filter\s*:", re.MULTILINE)


def should_skip(path: Path) -> bool:
    """Check if path is in a skipped directory."""
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    return False


def find_files() -> list[Path]:
    """Find all HTML/CSS files in the project."""
    files = []
    for pattern in SCAN_PATTERNS:
        for f in PROJECT_ROOT.glob(pattern):
            if f.is_file() and not should_skip(f):
                files.append(f)
    return sorted(set(files))


def fix_content(content: str) -> tuple[str, int]:
    """Add -webkit-backdrop-filter where missing. Returns (new_content, fix_count)."""
    lines = content.split("\n")
    new_lines = []
    fixes = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line has backdrop-filter (non-webkit)
        match = re.match(r"^(\s*)(backdrop-filter\s*:\s*.+)", line)
        if match:
            indent = match.group(1)
            prop_value = match.group(2)

            # Check if -webkit- version is already present:
            # - on the same line (inline CSS)
            # - on the previous line
            # - on the next line
            has_webkit = "-webkit-backdrop-filter" in line
            if not has_webkit and new_lines:
                if "-webkit-backdrop-filter" in new_lines[-1]:
                    has_webkit = True
            if not has_webkit and i + 1 < len(lines):
                if "-webkit-backdrop-filter" in lines[i + 1]:
                    has_webkit = True

            if not has_webkit:
                # Insert -webkit- prefix BEFORE the standard property
                webkit_line = f"{indent}-webkit-{prop_value}"
                new_lines.append(webkit_line)
                fixes += 1

        new_lines.append(line)
        i += 1

    return "\n".join(new_lines), fixes


def main():
    parser = argparse.ArgumentParser(description="Fix Safari backdrop-filter compatibility")
    parser.add_argument("--apply", action="store_true", help="Apply fixes (default: dry run)")
    parser.add_argument("--check", action="store_true", help="Check mode: exit 1 if fixes needed")
    args = parser.parse_args()

    files = find_files()
    total_fixes = 0
    fixed_files = []

    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  SKIP {f}: {e}")
            continue

        # Only process files that contain backdrop-filter
        if "backdrop-filter" not in content:
            continue

        new_content, fix_count = fix_content(content)

        if fix_count > 0:
            total_fixes += fix_count
            fixed_files.append((f, fix_count))

            if args.apply:
                f.write_text(new_content, encoding="utf-8")
                print(f"  FIXED {f.relative_to(PROJECT_ROOT)} ({fix_count} prefixes added)")
            else:
                print(f"  NEEDS FIX {f.relative_to(PROJECT_ROOT)} ({fix_count} missing prefixes)")
        else:
            print(f"  OK    {f.relative_to(PROJECT_ROOT)}")

    print(f"\nSummary: {len(files)} files scanned, {len(fixed_files)} need fixes, {total_fixes} total prefixes")

    if args.check and total_fixes > 0:
        sys.exit(1)

    if not args.apply and total_fixes > 0:
        print("\nRun with --apply to fix.")


if __name__ == "__main__":
    main()
