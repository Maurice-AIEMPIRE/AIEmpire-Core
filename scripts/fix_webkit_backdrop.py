#!/usr/bin/env python3
"""
Fix backdrop-filter CSS issues by adding -webkit-backdrop-filter prefix.

This script:
1. Finds all HTML and CSS files recursively
2. Identifies backdrop-filter properties without -webkit- prefix
3. Adds the -webkit-backdrop-filter prefix appropriately
4. Is idempotent (safe to run multiple times)
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


class BackdropFilterFixer:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.files_processed = 0
        self.files_fixed = 0
        self.fixes_applied = 0
        self.report = []

    def find_html_css_files(self) -> List[Path]:
        """Find all HTML and CSS files recursively."""
        files = []
        for pattern in ["**/*.html", "**/*.css"]:
            files.extend(self.root_path.glob(pattern))
        return sorted(files)

    def has_webkit_variant(self, text: str, start_pos: int, end_pos: int) -> bool:
        """Check if -webkit-backdrop-filter exists near the backdrop-filter property."""
        # Look within a reasonable range (same CSS rule block)
        search_start = max(0, start_pos - 200)
        search_end = min(len(text), end_pos + 200)
        search_text = text[search_start:search_end]

        # Look for -webkit-backdrop-filter
        if "-webkit-backdrop-filter" in search_text:
            return True
        return False

    def extract_backdrop_filter_value(self, line: str) -> str:
        """Extract the value of backdrop-filter property."""
        match = re.search(r'backdrop-filter\s*:\s*([^;}"]+)', line)
        if match:
            return match.group(1).strip()
        return ""

    def fix_css_block(self, content: str) -> Tuple[str, int]:
        """Fix backdrop-filter in CSS blocks."""
        fixes = 0
        lines = content.split("\n")
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this line has backdrop-filter
            if "backdrop-filter:" in line and "-webkit-backdrop-filter" not in line:
                # Extract the value
                value_match = re.search(r"backdrop-filter\s*:\s*([^;]+(?:;)?)", line)
                if value_match:
                    value = value_match.group(1).strip()

                    # Check if webkit variant exists nearby (in previous or next lines)
                    text_around = "\n".join(lines[max(0, i - 3) : min(len(lines), i + 4)])
                    if "-webkit-backdrop-filter" not in text_around:
                        # Add webkit version
                        # Determine indentation
                        indent_match = re.match(r"^(\s*)", line)
                        indent = indent_match.group(1) if indent_match else ""

                        # Insert webkit-backdrop-filter before the standard property
                        webkit_line = (
                            f"{indent}-webkit-backdrop-filter: {value.replace('backdrop-filter: ', '').rstrip(';')};"
                        )
                        new_lines.append(webkit_line)
                        fixes += 1

            new_lines.append(line)
            i += 1

        return "\n".join(new_lines), fixes

    def fix_inline_style(self, content: str) -> Tuple[str, int]:
        """Fix backdrop-filter in inline styles."""
        fixes = 0

        # Pattern to find style attributes with backdrop-filter
        def replace_style(match):
            nonlocal fixes
            full_match = match.group(0)
            style_content = match.group(1)

            # Check if -webkit-backdrop-filter already exists
            if "-webkit-backdrop-filter" in style_content:
                return full_match

            # Check if backdrop-filter exists
            if "backdrop-filter:" in style_content:
                # Extract backdrop-filter value
                bf_match = re.search(r"backdrop-filter:\s*([^;]+)", style_content)
                if bf_match:
                    bf_value = bf_match.group(1).strip()
                    # Add -webkit version
                    if not bf_value.endswith(";"):
                        bf_value += ";"
                    new_style = f"-webkit-backdrop-filter: {bf_value} {style_content}"
                    fixes += 1
                    return f'style="{new_style}"'

            return full_match

        # Match style attributes
        pattern = r'style="([^"]*backdrop-filter[^"]*)"'
        new_content = re.sub(pattern, replace_style, content)

        return new_content, fixes

    def process_file(self, file_path: Path) -> Tuple[bool, int]:
        """Process a single file and return (was_modified, num_fixes)."""
        try:
            # Read file
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                original_content = f.read()

            content = original_content
            total_fixes = 0

            # Fix inline styles
            content, inline_fixes = self.fix_inline_style(content)
            total_fixes += inline_fixes

            # Fix CSS blocks
            content, css_fixes = self.fix_css_block(content)
            total_fixes += css_fixes

            # Write back if changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return True, total_fixes

            return False, 0

        except Exception as e:
            self.report.append(f"ERROR processing {file_path}: {e}")
            return False, 0

    def run(self):
        """Run the fixer on all files."""
        files = self.find_html_css_files()

        if not files:
            print("No HTML or CSS files found!")
            return

        print(f"Found {len(files)} HTML/CSS files to process...")
        print("-" * 70)

        for file_path in files:
            self.files_processed += 1
            was_fixed, num_fixes = self.process_file(file_path)

            if was_fixed:
                self.files_fixed += 1
                self.fixes_applied += num_fixes
                rel_path = file_path.relative_to(self.root_path)
                self.report.append(f"FIXED: {rel_path} ({num_fixes} fix{'es' if num_fixes != 1 else ''})")
                print(f"✓ {rel_path}")

        # Print summary
        print("-" * 70)
        print("\nSUMMARY REPORT")
        print("=" * 70)
        print(f"Files processed: {self.files_processed}")
        print(f"Files fixed: {self.files_fixed}")
        print(f"Total fixes applied: {self.fixes_applied}")
        print("=" * 70)

        if self.report:
            print("\nDETAILED CHANGES:")
            for line in self.report:
                print(line)
        else:
            print("\nNo changes needed - all backdrop-filter properties already have webkit prefixes!")


def main():
    root_path = "/sessions/awesome-dreamy-einstein/mnt/AIEmpire-Core"

    if not os.path.isdir(root_path):
        print(f"Error: Root path does not exist: {root_path}")
        sys.exit(1)

    fixer = BackdropFilterFixer(root_path)
    fixer.run()


if __name__ == "__main__":
    main()
