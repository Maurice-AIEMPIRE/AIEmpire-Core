#!/usr/bin/env python3
"""
REDACTOR - Entfernt Secrets und Private Daten aus Texten/Dateien.

Nutzt privacy_rules.json für die Regeln.
Kann standalone oder als Modul verwendet werden.

Usage:
  python redactor.py <file>           # Redact a single file (stdout)
  python redactor.py <dir> --output <out_dir>  # Redact entire directory
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_rules() -> dict:
    rules_file = CONFIG_DIR / "privacy_rules.json"
    if rules_file.exists():
        return json.loads(rules_file.read_text())
    return {"redaction_rules": {"always_remove": [], "patterns_to_redact": []}}


def redact(text: str, rules: dict | None = None) -> str:
    """Redact sensitive information from text."""
    if rules is None:
        rules = load_rules()

    result = text

    # Remove known env var values
    for key in rules.get("redaction_rules", {}).get("always_remove", []):
        val = os.getenv(key, "")
        if val and len(val) > 4:
            result = result.replace(val, f"[REDACTED:{key}]")

    # Remove regex patterns
    for pattern in rules.get("redaction_rules", {}).get("patterns_to_redact", []):
        try:
            result = re.sub(pattern, "[REDACTED]", result)
        except re.error:
            pass

    return result


def is_exportable(path: Path, rules: dict | None = None) -> bool:
    """Check if a file path is allowed for export."""
    if rules is None:
        rules = load_rules()

    path_str = str(path)
    for blocked in rules.get("redaction_rules", {}).get("paths_never_export", []):
        if blocked.startswith("*"):
            if path_str.endswith(blocked[1:]):
                return False
        elif blocked in path_str:
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Redact sensitive data from files")
    parser.add_argument("path", help="File or directory to redact")
    parser.add_argument("--output", help="Output directory (for directory mode)")
    args = parser.parse_args()

    rules = load_rules()
    path = Path(args.path)

    if path.is_file():
        content = path.read_text(errors="replace")
        print(redact(content, rules))
    elif path.is_dir():
        out_dir = Path(args.output) if args.output else Path("redacted_output")
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for f in path.rglob("*"):
            if f.is_file() and is_exportable(f, rules):
                try:
                    content = f.read_text(errors="replace")
                    redacted = redact(content, rules)
                    out_file = out_dir / f.relative_to(path)
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text(redacted)
                    count += 1
                except (UnicodeDecodeError, OSError):
                    pass
        print(f"Redacted {count} files to {out_dir}", file=sys.stderr)
    else:
        print(f"Path not found: {path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
