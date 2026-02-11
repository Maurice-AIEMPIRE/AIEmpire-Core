"""
Artifact Manager
=================
Structured storage for outputs, screenshots, generated content.
Each task/module gets an artifacts directory with metadata tracking.

Inspired by Google Antigravity's artifact system.

Usage:
    am = ArtifactManager()
    am.save("api-fix", "error_log.txt", content="Traceback...")
    am.save("api-fix", "screenshot.png", binary_path="/tmp/shot.png")
    artifacts = am.list_artifacts("api-fix")
    content = am.read("api-fix", "error_log.txt")
"""

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "antigravity" / "_artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


class ArtifactManager:
    """Manages structured artifact storage with metadata tracking."""

    def __init__(self, artifacts_dir: Optional[Path] = None):
        self.artifacts_dir = artifacts_dir or ARTIFACTS_DIR
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        task_id: str,
        filename: str,
        content: Optional[str] = None,
        binary_path: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Path:
        """
        Save an artifact for a task.

        Args:
            task_id: The task or module this artifact belongs to
            filename: Name for the artifact file
            content: Text content to save
            binary_path: Path to binary file to copy (images, videos)
            metadata: Optional metadata dict
        """
        task_dir = self.artifacts_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = task_dir / filename

        if content is not None:
            artifact_path.write_text(content)
        elif binary_path:
            shutil.copy2(binary_path, artifact_path)

        # Update manifest
        self._update_manifest(task_id, filename, metadata)

        return artifact_path

    def read(self, task_id: str, filename: str) -> Optional[str]:
        """Read a text artifact."""
        path = self.artifacts_dir / task_id / filename
        if not path.exists():
            return None
        return path.read_text()

    def get_path(self, task_id: str, filename: str) -> Path:
        """Get the full path to an artifact."""
        return self.artifacts_dir / task_id / filename

    def exists(self, task_id: str, filename: str) -> bool:
        """Check if an artifact exists."""
        return (self.artifacts_dir / task_id / filename).exists()

    def list_artifacts(self, task_id: str) -> list[dict[str, Any]]:
        """List all artifacts for a task."""
        manifest = self._load_manifest(task_id)
        return manifest.get("artifacts", [])

    def list_all_tasks(self) -> list[dict[str, Any]]:
        """List all tasks that have artifacts."""
        tasks = []
        for task_dir in sorted(self.artifacts_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            manifest = self._load_manifest(task_dir.name)
            artifact_count = len(manifest.get("artifacts", []))
            total_size = sum(
                (task_dir / a["filename"]).stat().st_size
                for a in manifest.get("artifacts", [])
                if (task_dir / a["filename"]).exists()
            )
            tasks.append({
                "task_id": task_dir.name,
                "artifacts": artifact_count,
                "total_size_kb": round(total_size / 1024, 1),
                "last_updated": manifest.get("updated_at", ""),
            })
        return tasks

    def delete(self, task_id: str, filename: str) -> bool:
        """Delete an artifact."""
        path = self.artifacts_dir / task_id / filename
        if path.exists():
            path.unlink()
            # Update manifest
            manifest = self._load_manifest(task_id)
            manifest["artifacts"] = [
                a for a in manifest.get("artifacts", [])
                if a["filename"] != filename
            ]
            self._save_manifest(task_id, manifest)
            return True
        return False

    def cleanup(self, task_id: str) -> int:
        """Remove all artifacts for a task. Returns count removed."""
        task_dir = self.artifacts_dir / task_id
        if not task_dir.exists():
            return 0
        count = sum(1 for f in task_dir.iterdir() if f.is_file() and f.name != "manifest.json")
        shutil.rmtree(task_dir)
        return count

    def generate_markdown_embed(self, task_id: str, filename: str, caption: str = "") -> str:
        """Generate markdown for embedding an artifact."""
        path = self.get_path(task_id, filename)
        ext = path.suffix.lower()

        if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
            cap = caption or filename
            return f"![{cap}]({path})"
        elif ext in (".md", ".txt", ".log"):
            content = self.read(task_id, filename)
            if content:
                return f"```\n{content[:500]}\n```"
        return f"[{filename}]({path})"

    def status_report(self) -> str:
        """Get formatted artifact status."""
        tasks = self.list_all_tasks()
        if not tasks:
            return "No artifacts stored yet."

        lines = [
            "=" * 60,
            "ARTIFACT MANAGER STATUS",
            "=" * 60,
        ]
        total_artifacts = 0
        total_size = 0.0

        for t in tasks:
            lines.append(
                f"  {t['task_id']:30s} | "
                f"{t['artifacts']:3d} files | "
                f"{t['total_size_kb']:8.1f} KB"
            )
            total_artifacts += t["artifacts"]
            total_size += t["total_size_kb"]

        lines.append(f"\n  Total: {total_artifacts} artifacts, {total_size:.1f} KB")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _load_manifest(self, task_id: str) -> dict:
        """Load artifact manifest for a task."""
        manifest_path = self.artifacts_dir / task_id / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                return json.load(f)
        return {"task_id": task_id, "artifacts": [], "created_at": "", "updated_at": ""}

    def _save_manifest(self, task_id: str, manifest: dict) -> None:
        """Save artifact manifest."""
        manifest_path = self.artifacts_dir / task_id / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

    def _update_manifest(
        self, task_id: str, filename: str, metadata: Optional[dict] = None
    ) -> None:
        """Update the manifest with a new or updated artifact."""
        manifest = self._load_manifest(task_id)
        now = time.strftime("%Y-%m-%dT%H:%M:%S")

        if not manifest["created_at"]:
            manifest["created_at"] = now
        manifest["updated_at"] = now

        # Check if artifact already exists in manifest
        existing = [a for a in manifest["artifacts"] if a["filename"] == filename]
        if existing:
            existing[0]["updated_at"] = now
            if metadata:
                existing[0]["metadata"] = metadata
        else:
            path = self.artifacts_dir / task_id / filename
            size = path.stat().st_size if path.exists() else 0
            manifest["artifacts"].append({
                "filename": filename,
                "size_bytes": size,
                "created_at": now,
                "updated_at": now,
                "metadata": metadata or {},
            })

        self._save_manifest(task_id, manifest)
