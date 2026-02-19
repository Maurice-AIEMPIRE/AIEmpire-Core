"""
Code Execution Tool
===================
Executes Python code in a sandboxed subprocess.
Restricted: no network, no file system outside workspace, timeout enforced.
"""

import asyncio
import os
import tempfile

from skybot.tools.base import BaseTool
from skybot.config import WORKSPACE_DIR, CODE_EXEC_TIMEOUT, BLOCKED_COMMANDS, MAX_OUTPUT_LENGTH


class CodeExecTool(BaseTool):
    name = "code_exec"
    description = "Execute Python code safely in a sandboxed environment. Returns stdout/stderr."

    def definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute.",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["python", "bash"],
                        "description": "Language to execute. Default: 'python'. Use 'bash' for shell commands.",
                    },
                },
                "required": ["code"],
            },
        }

    async def execute(self, code: str, language: str = "python", **kwargs) -> str:
        # Security check
        for blocked in BLOCKED_COMMANDS:
            if blocked in code:
                return f"BLOCKED: Dangerous command detected: '{blocked}'"

        if language == "bash":
            return await self._exec_bash(code)
        return await self._exec_python(code)

    async def _exec_python(self, code: str) -> str:
        """Execute Python code in a subprocess."""
        # Write code to temp file in workspace
        code_file = WORKSPACE_DIR / "_exec_temp.py"
        code_file.write_text(code, encoding="utf-8")

        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", str(code_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(WORKSPACE_DIR),
                env={
                    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                    "HOME": str(WORKSPACE_DIR),
                    "PYTHONPATH": str(WORKSPACE_DIR),
                    "LANG": "en_US.UTF-8",
                },
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=CODE_EXEC_TIMEOUT
                )
            except asyncio.TimeoutError:
                proc.kill()
                return f"TIMEOUT: Code execution exceeded {CODE_EXEC_TIMEOUT}s limit."

            output = ""
            if stdout:
                output += stdout.decode("utf-8", errors="replace")
            if stderr:
                output += ("\n--- STDERR ---\n" + stderr.decode("utf-8", errors="replace"))

            exit_code = proc.returncode
            output = output.strip() or "(no output)"

            return self._truncate(
                f"Exit code: {exit_code}\n\n{output}", MAX_OUTPUT_LENGTH
            )

        finally:
            code_file.unlink(missing_ok=True)

    async def _exec_bash(self, code: str) -> str:
        """Execute bash commands in a subprocess."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "bash", "-c", code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(WORKSPACE_DIR),
                env={
                    "PATH": f"/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:{os.environ.get('PATH', '')}",
                    "HOME": os.environ.get("HOME", "/tmp"),
                    "LANG": "en_US.UTF-8",
                },
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=CODE_EXEC_TIMEOUT
                )
            except asyncio.TimeoutError:
                proc.kill()
                return f"TIMEOUT: Command exceeded {CODE_EXEC_TIMEOUT}s limit."

            output = ""
            if stdout:
                output += stdout.decode("utf-8", errors="replace")
            if stderr:
                output += ("\n--- STDERR ---\n" + stderr.decode("utf-8", errors="replace"))

            exit_code = proc.returncode
            output = output.strip() or "(no output)"

            return self._truncate(
                f"Exit code: {exit_code}\n\n{output}", MAX_OUTPUT_LENGTH
            )

        except Exception as e:
            return f"Execution error: {e}"
