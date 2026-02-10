#!/usr/bin/env python3
"""
Safari Compatibility Patcher — idempotent, repo-wide.

Handles two CSS properties that need -webkit- prefixes for Safari:
  1. backdrop-filter  → -webkit-backdrop-filter
  2. user-select: none → -webkit-user-select: none

Usage:
    python3 scripts/safari_compat_patch.py              # runs on repo root
    python3 scripts/safari_compat_patch.py /path/to/dir  # runs on specified path

Idempotent: safe to run multiple times, never creates duplicates.
"""

import re
import sys
from pathlib import Path

# Properties to prefix: (standard_property, webkit_property, value_filter)
# value_filter: None = any value, "none" = only when value is "none"
PATCH_RULES = [
    ("backdrop-filter", "-webkit-backdrop-filter", None),
    ("user-select", "-webkit-user-select", "none"),
]

SKIP_DIRS = {".venv", "venv", "node_modules", "__pycache__", ".git"}


def find_files(root: Path):
    """Find all HTML and CSS files, skipping virtual envs and node_modules."""
    for ext in ("*.html", "*.css"):
        for path in root.rglob(ext):
            if not any(skip in path.parts for skip in SKIP_DIRS):
                yield path


def already_prefixed(lines, idx, webkit_prop):
    """Check if the webkit variant exists within ±5 lines."""
    start = max(0, idx - 5)
    end = min(len(lines), idx + 6)
    block = "\n".join(lines[start:end])
    return webkit_prop in block


def patch_css_block(content: str) -> tuple[str, list[str]]:
    """Patch CSS in <style> blocks and .css files. Returns (new_content, list_of_fixes)."""
    fixes = []
    lines = content.split("\n")
    new_lines = []

    for i, line in enumerate(lines):
        for std_prop, webkit_prop, val_filter in PATCH_RULES:
            # Match the standard property but NOT the webkit version
            if std_prop + ":" in line and webkit_prop not in line:
                # Don't match if this IS the webkit version on this line
                if line.lstrip().startswith("-webkit-"):
                    continue

                # Extract value
                match = re.search(rf"{re.escape(std_prop)}\s*:\s*([^;\"}}]+)", line)
                if not match:
                    continue

                value = match.group(1).strip().rstrip(";")

                # Apply value filter if specified
                if val_filter and value != val_filter:
                    continue

                # Check nearby lines for existing webkit variant
                if already_prefixed(lines, i, webkit_prop):
                    continue

                # Determine indentation
                indent = re.match(r"^(\s*)", line).group(1)
                webkit_line = f"{indent}{webkit_prop}: {value};"

                new_lines.append(webkit_line)
                fixes.append(f"  L{i + 1}: +{webkit_prop}: {value}; (before {std_prop})")

        new_lines.append(line)

    return "\n".join(new_lines), fixes


def patch_inline_styles(content: str) -> tuple[str, list[str]]:
    """Patch inline style='...' attributes. Returns (new_content, list_of_fixes)."""
    fixes = []

    def replacer(m):
        style = m.group(1)
        additions = []
        for std_prop, webkit_prop, val_filter in PATCH_RULES:
            if std_prop + ":" in style and webkit_prop not in style:
                vmatch = re.search(rf"{re.escape(std_prop)}\s*:\s*([^;\"]+)", style)
                if not vmatch:
                    continue
                value = vmatch.group(1).strip().rstrip(";")
                if val_filter and value != val_filter:
                    continue
                additions.append(f"{webkit_prop}: {value};")
                fixes.append(f"  inline: +{webkit_prop}: {value};")

        if additions:
            prefix = " ".join(additions)
            return f'style="{prefix} {style}"'
        return m.group(0)

    new_content = re.sub(r'style="([^"]*)"', replacer, content)
    return new_content, fixes


def process_file(path: Path) -> list[str]:
    """Process one file. Returns list of fix descriptions (empty if no changes)."""
    try:
        original = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [f"  ERROR reading: {e}"]

    content = original
    all_fixes = []

    # Patch CSS blocks first, then inline styles
    content, css_fixes = patch_css_block(content)
    all_fixes.extend(css_fixes)

    content, inline_fixes = patch_inline_styles(content)
    all_fixes.extend(inline_fixes)

    if content != original:
        path.write_text(content, encoding="utf-8")

    return all_fixes


def main():
    # Determine root path
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    else:
        # Default: repo root (one level up from scripts/)
        root = Path(__file__).resolve().parent.parent

    if not root.is_dir():
        print(f"Error: not a directory: {root}")
        sys.exit(1)

    print(f"Safari Compat Patcher — scanning {root}")
    print("=" * 70)

    files = sorted(find_files(root))
    total_files = 0
    total_fixed = 0
    total_patches = 0

    for path in files:
        total_files += 1
        fixes = process_file(path)
        if fixes:
            total_fixed += 1
            total_patches += len(fixes)
            rel = path.relative_to(root)
            print(f"✓ {rel} ({len(fixes)} patch{'es' if len(fixes) != 1 else ''})")
            for f in fixes:
                print(f)

    print("=" * 70)
    print(f"Files scanned:  {total_files}")
    print(f"Files patched:  {total_fixed}")
    print(f"Total patches:  {total_patches}")

    if total_patches == 0:
        print("\nAll clear — no missing webkit prefixes found.")
    else:
        print(f"\nDone — {total_patches} webkit prefix(es) added.")


if __name__ == "__main__":
    main()
