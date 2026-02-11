"""
Multi-Replace Batch Editor
============================
Apply multiple replacements to files in a single operation.
Safer than sed - validates all replacements before applying.

Inspired by Google Antigravity's multi_replace_file_content tool.

Usage:
    mr = MultiReplace()
    mr.replace("config.py", [
        {"old": "localhost:3000", "new": "localhost:3333"},
        {"old": "DEBUG = True", "new": "DEBUG = False"},
    ])

    # Batch across multiple files
    mr.batch_replace({
        "config.py": [{"old": "v1", "new": "v2"}],
        "api.py": [{"old": "v1", "new": "v2"}],
    })
"""

import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class Replacement:
    """A single text replacement."""
    old: str
    new: str
    count: int = 0  # 0 = replace all occurrences
    applied: bool = False
    occurrences_found: int = 0


@dataclass
class ReplaceResult:
    """Result of a replace operation."""
    file: str
    success: bool
    replacements: list[Replacement] = field(default_factory=list)
    backup_path: str = ""
    error: str = ""
    lines_changed: int = 0


class MultiReplace:
    """
    Batch file editor with safety checks.

    Safety features:
    - Creates backup before editing
    - Validates all replacements exist in file
    - Reports exactly what changed
    - Supports dry-run mode
    """

    def __init__(self, root: Optional[Path] = None, backup: bool = True):
        self.root = root or PROJECT_ROOT
        self.backup = backup
        self.backup_dir = self.root / "antigravity" / "_backups"

    def replace(
        self,
        filepath: str,
        replacements: list[dict[str, str]],
        dry_run: bool = False,
    ) -> ReplaceResult:
        """
        Apply multiple replacements to a file.

        Args:
            filepath: Path relative to project root
            replacements: List of {"old": "...", "new": "..."}
            dry_run: If True, only report what would change
        """
        full_path = self.root / filepath
        result = ReplaceResult(file=filepath, success=False)

        if not full_path.exists():
            result.error = f"File not found: {filepath}"
            return result

        content = full_path.read_text()
        original = content

        # Validate all replacements first
        replace_objects = []
        for r in replacements:
            rep = Replacement(old=r["old"], new=r["new"], count=r.get("count", 0))
            rep.occurrences_found = content.count(rep.old)

            if rep.occurrences_found == 0:
                result.error = f"Pattern not found: {repr(rep.old[:50])}"
                result.replacements.append(rep)
                return result

            replace_objects.append(rep)

        # Apply replacements
        for rep in replace_objects:
            if rep.count > 0:
                content = content.replace(rep.old, rep.new, rep.count)
            else:
                content = content.replace(rep.old, rep.new)
            rep.applied = True

        # Count changed lines
        original_lines = original.splitlines()
        new_lines = content.splitlines()
        result.lines_changed = sum(
            1 for o, n in zip(original_lines, new_lines) if o != n
        ) + abs(len(new_lines) - len(original_lines))

        result.replacements = replace_objects

        if dry_run:
            result.success = True
            return result

        # Create backup
        if self.backup:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{Path(filepath).name}.{timestamp}.bak"
            backup_path = self.backup_dir / backup_name
            shutil.copy2(full_path, backup_path)
            result.backup_path = str(backup_path)

        # Write changes
        full_path.write_text(content)
        result.success = True

        return result

    def batch_replace(
        self,
        file_replacements: dict[str, list[dict[str, str]]],
        dry_run: bool = False,
    ) -> list[ReplaceResult]:
        """
        Apply replacements across multiple files.

        Args:
            file_replacements: {filepath: [{"old": "...", "new": "..."}]}
            dry_run: If True, only report what would change
        """
        results = []
        for filepath, replacements in file_replacements.items():
            result = self.replace(filepath, replacements, dry_run=dry_run)
            results.append(result)
        return results

    def rename_symbol(
        self,
        old_name: str,
        new_name: str,
        file_pattern: str = "*.py",
        dry_run: bool = True,
    ) -> list[ReplaceResult]:
        """
        Rename a symbol across the codebase.
        Default is dry_run=True for safety.
        """
        results = []

        for filepath in self.root.rglob(file_pattern):
            if any(d in filepath.parts for d in ["__pycache__", ".git", "node_modules", ".venv"]):
                continue

            try:
                content = filepath.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            if old_name not in content:
                continue

            rel_path = str(filepath.relative_to(self.root))
            result = self.replace(
                rel_path,
                [{"old": old_name, "new": new_name}],
                dry_run=dry_run,
            )
            results.append(result)

        return results

    def undo(self, result: ReplaceResult) -> bool:
        """Undo a replacement by restoring from backup."""
        if not result.backup_path:
            return False

        backup_path = Path(result.backup_path)
        if not backup_path.exists():
            return False

        target_path = self.root / result.file
        shutil.copy2(backup_path, target_path)
        return True

    def format_result(self, result: ReplaceResult) -> str:
        """Format a replace result as readable text."""
        status = "OK" if result.success else "FAILED"
        lines = [f"[{status}] {result.file} ({result.lines_changed} lines changed)"]

        for rep in result.replacements:
            applied = "applied" if rep.applied else "not applied"
            old_preview = repr(rep.old[:40])
            new_preview = repr(rep.new[:40])
            lines.append(
                f"  {old_preview} -> {new_preview} "
                f"({rep.occurrences_found} found, {applied})"
            )

        if result.error:
            lines.append(f"  ERROR: {result.error}")
        if result.backup_path:
            lines.append(f"  Backup: {result.backup_path}")

        return "\n".join(lines)
