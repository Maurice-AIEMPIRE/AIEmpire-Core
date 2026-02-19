"""
File Operations Tool
====================
Read, write, list, and delete files in the workspace directory.
Restricted to WORKSPACE_DIR only — no access outside.
"""

import os
from pathlib import Path

from skybot.tools.base import BaseTool
from skybot.config import WORKSPACE_DIR, MAX_OUTPUT_LENGTH


class FileOpsTool(BaseTool):
    name = "file_ops"
    description = "Read, write, list, or delete files in the agent workspace."

    def definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["read", "write", "list", "delete", "mkdir"],
                        "description": "File operation to perform.",
                    },
                    "path": {
                        "type": "string",
                        "description": "Relative file path within the workspace.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (only for 'write' action).",
                    },
                },
                "required": ["action", "path"],
            },
        }

    async def execute(self, action: str, path: str, content: str = "", **kwargs) -> str:
        # Resolve and validate path (must stay in workspace)
        target = self._safe_path(path)
        if target is None:
            return f"BLOCKED: Path '{path}' is outside the workspace."

        if action == "read":
            return await self._read(target)
        elif action == "write":
            return await self._write(target, content)
        elif action == "list":
            return await self._list(target)
        elif action == "delete":
            return await self._delete(target)
        elif action == "mkdir":
            return await self._mkdir(target)
        else:
            return f"Unknown action: {action}"

    def _safe_path(self, path: str) -> Path | None:
        """Resolve path and ensure it stays within WORKSPACE_DIR."""
        # Remove leading slashes to prevent absolute paths
        clean = path.lstrip("/").lstrip("\\")
        target = (WORKSPACE_DIR / clean).resolve()

        # Security: must be within workspace
        try:
            target.relative_to(WORKSPACE_DIR.resolve())
            return target
        except ValueError:
            return None

    async def _read(self, path: Path) -> str:
        if not path.exists():
            return f"File not found: {path.name}"
        if path.is_dir():
            return await self._list(path)
        try:
            content = path.read_text(encoding="utf-8")
            return self._truncate(f"File: {path.relative_to(WORKSPACE_DIR)}\n\n{content}", MAX_OUTPUT_LENGTH)
        except UnicodeDecodeError:
            size = path.stat().st_size
            return f"Binary file: {path.name} ({size} bytes)"
        except Exception as e:
            return f"Read error: {e}"

    async def _write(self, path: Path, content: str) -> str:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"Written: {path.relative_to(WORKSPACE_DIR)} ({len(content)} chars)"
        except Exception as e:
            return f"Write error: {e}"

    async def _list(self, path: Path) -> str:
        target = path if path.is_dir() else path.parent
        if not target.exists():
            return f"Directory not found: {target.name}"
        try:
            entries = sorted(target.iterdir())
            lines = [f"Directory: {target.relative_to(WORKSPACE_DIR)}/\n"]
            for entry in entries[:100]:  # Limit to 100 entries
                prefix = "d" if entry.is_dir() else "f"
                size = entry.stat().st_size if entry.is_file() else 0
                name = entry.name + ("/" if entry.is_dir() else "")
                lines.append(f"  [{prefix}] {name:40} {size:>8} bytes")
            if len(entries) > 100:
                lines.append(f"  ... and {len(entries) - 100} more")
            return "\n".join(lines)
        except Exception as e:
            return f"List error: {e}"

    async def _delete(self, path: Path) -> str:
        if not path.exists():
            return f"Not found: {path.name}"
        try:
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
                return f"Deleted directory: {path.relative_to(WORKSPACE_DIR)}"
            else:
                path.unlink()
                return f"Deleted: {path.relative_to(WORKSPACE_DIR)}"
        except Exception as e:
            return f"Delete error: {e}"

    async def _mkdir(self, path: Path) -> str:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return f"Created directory: {path.relative_to(WORKSPACE_DIR)}"
        except Exception as e:
            return f"Mkdir error: {e}"
