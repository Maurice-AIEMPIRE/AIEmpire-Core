"""
Walkthrough Generator
======================
Generates post-task summaries and documentation.
Creates structured walkthroughs after task completion.

Inspired by Google Antigravity's walkthrough.md artifact system.

Usage:
    wg = WalkthroughGenerator()
    walkthrough = wg.generate(
        task_id="fix-auth",
        title="Fixed JWT Auth Bug",
        changes={"empire_api/auth.py": "Fixed token validation"},
        test_results="All 12 tests passing",
    )
    wg.save(walkthrough)
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).parent.parent
WALKTHROUGHS_DIR = PROJECT_ROOT / "antigravity" / "_walkthroughs"
WALKTHROUGHS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Walkthrough:
    """A task completion walkthrough/summary."""
    task_id: str
    title: str
    summary: str = ""
    changes: dict[str, str] = field(default_factory=dict)  # file: description
    test_results: str = ""
    screenshots: list[str] = field(default_factory=list)
    confidence: float = 0.0
    duration_minutes: float = 0.0
    created_at: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")


class WalkthroughGenerator:
    """Generates and stores task walkthroughs."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or WALKTHROUGHS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        task_id: str,
        title: str,
        summary: str = "",
        changes: Optional[dict[str, str]] = None,
        test_results: str = "",
        screenshots: Optional[list[str]] = None,
        confidence: float = 0.9,
        duration_minutes: float = 0.0,
        tags: Optional[list[str]] = None,
    ) -> Walkthrough:
        """Generate a walkthrough for a completed task."""
        wt = Walkthrough(
            task_id=task_id,
            title=title,
            summary=summary,
            changes=changes or {},
            test_results=test_results,
            screenshots=screenshots or [],
            confidence=confidence,
            duration_minutes=duration_minutes,
            tags=tags or [],
        )
        return wt

    def save(self, walkthrough: Walkthrough) -> Path:
        """Save walkthrough as both JSON and Markdown."""
        # Save JSON
        json_path = self.output_dir / f"{walkthrough.task_id}.json"
        with open(json_path, "w") as f:
            json.dump({
                "task_id": walkthrough.task_id,
                "title": walkthrough.title,
                "summary": walkthrough.summary,
                "changes": walkthrough.changes,
                "test_results": walkthrough.test_results,
                "screenshots": walkthrough.screenshots,
                "confidence": walkthrough.confidence,
                "duration_minutes": walkthrough.duration_minutes,
                "created_at": walkthrough.created_at,
                "tags": walkthrough.tags,
            }, f, indent=2)

        # Generate Markdown
        md_path = self.output_dir / f"{walkthrough.task_id}.md"
        md_content = self._render_markdown(walkthrough)
        md_path.write_text(md_content)

        return md_path

    def get(self, task_id: str) -> Optional[Walkthrough]:
        """Load a walkthrough by task ID."""
        json_path = self.output_dir / f"{task_id}.json"
        if not json_path.exists():
            return None
        with open(json_path) as f:
            data = json.load(f)
        return Walkthrough(**data)

    def list_walkthroughs(self, limit: int = 20) -> list[dict[str, Any]]:
        """List all walkthroughs."""
        walkthroughs = []
        for path in sorted(self.output_dir.glob("*.json"), reverse=True):
            with open(path) as f:
                data = json.load(f)
            walkthroughs.append({
                "task_id": data.get("task_id", path.stem),
                "title": data.get("title", ""),
                "confidence": data.get("confidence", 0),
                "files_changed": len(data.get("changes", {})),
                "created_at": data.get("created_at", ""),
            })
            if len(walkthroughs) >= limit:
                break
        return walkthroughs

    def status_report(self) -> str:
        """Get formatted walkthrough status."""
        wts = self.list_walkthroughs()
        if not wts:
            return "No walkthroughs generated yet."

        lines = [
            "=" * 60,
            "WALKTHROUGH STATUS",
            "=" * 60,
        ]

        for wt in wts[:10]:
            conf = f"{wt['confidence']:.0%}"
            lines.append(
                f"  [{conf}] {wt['task_id']:25s} | "
                f"{wt['files_changed']:2d} files | {wt['title'][:30]}"
            )

        lines.append(f"\n  Total: {len(wts)} walkthroughs")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _render_markdown(self, wt: Walkthrough) -> str:
        """Render a walkthrough as Markdown."""
        lines = [
            f"# Walkthrough: {wt.title}",
            "",
            f"**Task ID**: {wt.task_id}",
            f"**Date**: {wt.created_at}",
            f"**Confidence**: {wt.confidence:.0%}",
        ]

        if wt.duration_minutes:
            lines.append(f"**Duration**: {wt.duration_minutes:.0f} min")

        if wt.tags:
            lines.append(f"**Tags**: {', '.join(wt.tags)}")

        if wt.summary:
            lines.extend(["", "## Summary", "", wt.summary])

        if wt.changes:
            lines.extend(["", "## Changes Made", ""])
            for filepath, description in wt.changes.items():
                lines.append(f"- **`{filepath}`**: {description}")

        if wt.test_results:
            lines.extend(["", "## Test Results", "", f"```\n{wt.test_results}\n```"])

        if wt.screenshots:
            lines.extend(["", "## Screenshots", ""])
            for ss in wt.screenshots:
                lines.append(f"![screenshot]({ss})")

        lines.append("")
        return "\n".join(lines)
