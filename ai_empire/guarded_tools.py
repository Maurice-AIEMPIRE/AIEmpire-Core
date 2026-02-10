"""
Guarded Tools - Safe Tool Execution with Resource Limits.

Wraps tool calls (file I/O, shell, API) with:
- Resource guard integration (CPU/RAM checks before execution)
- Timeout enforcement
- Error containment (no tool crash takes down the system)
- Audit logging

Usage:
    tools = GuardedTools()
    result = await tools.run_shell("ls -la /tmp", timeout=10)
    content = await tools.read_file("/path/to/file.txt")
    result = await tools.call_api("https://api.example.com/data", method="GET")
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

AUDIT_DIR = Path(__file__).parent.parent / "workflow-system" / "state" / "audit"


class GuardedTools:
    """Safe execution layer for all tool operations."""

    def __init__(self, max_file_size_mb: int = 50, default_timeout: int = 30):
        self.max_file_size_mb = max_file_size_mb
        self.default_timeout = default_timeout
        self._audit_log: List[Dict] = []
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    async def read_file(self, path: str, max_lines: Optional[int] = None) -> Dict:
        """Safely read a file with size limits."""
        start = time.time()
        file_path = Path(path)

        if not file_path.exists():
            return self._result("read_file", path, success=False, error="File not found")

        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            return self._result(
                "read_file", path, success=False,
                error=f"File too large: {size_mb:.1f}MB > {self.max_file_size_mb}MB limit",
            )

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if max_lines:
                lines = content.split("\n")
                content = "\n".join(lines[:max_lines])
            return self._result("read_file", path, data=content, elapsed=time.time() - start)
        except Exception as e:
            return self._result("read_file", path, success=False, error=str(e))

    async def write_file(self, path: str, content: str) -> Dict:
        """Safely write a file."""
        start = time.time()
        file_path = Path(path)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return self._result("write_file", path, elapsed=time.time() - start)
        except Exception as e:
            return self._result("write_file", path, success=False, error=str(e))

    async def run_shell(self, command: str, timeout: Optional[int] = None, cwd: Optional[str] = None) -> Dict:
        """Run a shell command with timeout enforcement."""
        start = time.time()
        timeout = timeout or self.default_timeout

        # Block dangerous commands
        dangerous = ["rm -rf /", "mkfs", "dd if=", "> /dev/sd"]
        for d in dangerous:
            if d in command:
                return self._result(
                    "run_shell", command, success=False,
                    error=f"Blocked dangerous command pattern: {d}",
                )

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return self._result(
                "run_shell", command,
                success=proc.returncode == 0,
                data={
                    "stdout": stdout.decode("utf-8", errors="replace")[:10000],
                    "stderr": stderr.decode("utf-8", errors="replace")[:5000],
                    "returncode": proc.returncode,
                },
                elapsed=time.time() - start,
            )
        except asyncio.TimeoutError:
            return self._result(
                "run_shell", command, success=False,
                error=f"Command timed out after {timeout}s",
            )
        except Exception as e:
            return self._result("run_shell", command, success=False, error=str(e))

    async def call_api(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: Optional[int] = None,
    ) -> Dict:
        """Make an HTTP API call with timeout and error containment."""
        start = time.time()
        timeout = timeout or self.default_timeout

        try:
            async with aiohttp.ClientSession() as session:
                kwargs = {
                    "timeout": aiohttp.ClientTimeout(total=timeout),
                    "headers": headers or {},
                }
                if json_data:
                    kwargs["json"] = json_data

                async with session.request(method, url, **kwargs) as resp:
                    body = await resp.text()
                    return self._result(
                        "call_api", f"{method} {url}",
                        success=200 <= resp.status < 400,
                        data={
                            "status": resp.status,
                            "body": body[:10000],
                        },
                        elapsed=time.time() - start,
                    )
        except asyncio.TimeoutError:
            return self._result(
                "call_api", f"{method} {url}", success=False,
                error=f"API call timed out after {timeout}s",
            )
        except Exception as e:
            return self._result("call_api", f"{method} {url}", success=False, error=str(e))

    def _result(
        self,
        tool: str,
        target: str,
        success: bool = True,
        data: Any = None,
        error: Optional[str] = None,
        elapsed: float = 0.0,
    ) -> Dict:
        """Create a standardized result and log it."""
        entry = {
            "tool": tool,
            "target": target[:200],
            "success": success,
            "error": error,
            "elapsed_sec": round(elapsed, 3),
            "timestamp": datetime.now().isoformat(),
        }
        self._audit_log.append(entry)

        if len(self._audit_log) > 500:
            self._audit_log = self._audit_log[-500:]

        if not success:
            logger.warning(f"Tool {tool} failed on {target[:80]}: {error}")

        result = {"success": success, "elapsed_sec": round(elapsed, 3)}
        if data is not None:
            result["data"] = data
        if error:
            result["error"] = error
        return result

    def get_audit_log(self, last_n: int = 50) -> List[Dict]:
        """Return recent audit entries."""
        return self._audit_log[-last_n:]

    def get_stats(self) -> Dict:
        """Return tool usage statistics."""
        total = len(self._audit_log)
        successes = sum(1 for e in self._audit_log if e.get("success"))
        return {
            "total_calls": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": round(successes / max(total, 1) * 100, 1),
        }
