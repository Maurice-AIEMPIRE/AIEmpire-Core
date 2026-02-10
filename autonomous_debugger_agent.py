#!/usr/bin/env python3
"""
AUTONOMOUS DEBUGGER AGENT
Finds bugs, analyzes root causes, fixes them automatically

Workflow:
  Error Detection → Stack Trace Analysis → Root Cause → Fix Generation → Verification
"""

import asyncio
import subprocess
import re
import json
from typing import Dict, List, Any
from datetime import datetime

class AutoDebugger:
    """Autonomous debugging agent - fixes problems on its own"""

    def __init__(self):
        self.model = "deepseek-r1:8b"
        self.ollama_url = "http://localhost:11434/api/generate"
        self.fixes_applied = []
        self.success_rate = 0.0

    async def scan_for_errors(self) -> List[Dict[str, Any]]:
        """Scan codebase for errors"""
        errors = []

        # Scan 1: Python syntax errors
        result = subprocess.run(
            ["find", "/Users/maurice/AIEmpire-Core", "-name", "*.py", "-type", "f"],
            capture_output=True,
            text=True
        )

        python_files = result.stdout.strip().split("\n")

        for file in python_files[:50]:  # Limit to first 50 files
            if not file:
                continue

            try:
                result = subprocess.run(
                    ["python3", "-m", "py_compile", file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode != 0:
                    errors.append({
                        "type": "syntax_error",
                        "file": file,
                        "error": result.stderr.strip(),
                        "severity": "high",
                        "fixable": True
                    })
            except:
                pass

        # Scan 2: Runtime errors (check logs)
        errors.extend(await self._scan_logs())

        # Scan 3: Dependency issues
        errors.extend(await self._check_dependencies())

        return errors

    async def _scan_logs(self) -> List[Dict[str, Any]]:
        """Scan application logs"""
        errors = []

        log_paths = [
            "/Users/maurice/AIEmpire-Core/logs",
            "/tmp/app.log",
        ]

        for log_path in log_paths:
            try:
                result = subprocess.run(
                    ["grep", "-E", "ERROR|CRITICAL|Exception", log_path],
                    capture_output=True,
                    text=True
                )

                if result.stdout:
                    for line in result.stdout.split("\n")[:5]:  # Last 5 errors
                        if line.strip():
                            errors.append({
                                "type": "log_error",
                                "source": log_path,
                                "message": line.strip(),
                                "severity": "medium"
                            })
            except:
                pass

        return errors

    async def _check_dependencies(self) -> List[Dict[str, Any]]:
        """Check for missing dependencies"""
        errors = []

        result = subprocess.run(
            ["pip", "check"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            for line in result.stdout.split("\n"):
                if "requires" in line or "conflict" in line:
                    errors.append({
                        "type": "dependency_error",
                        "message": line.strip(),
                        "severity": "medium",
                        "fixable": True
                    })

        return errors

    async def analyze_error(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error using Ollama (FREE)"""

        prompt = f"""
You are an expert Python debugger. Analyze this error and provide a fix:

Error Type: {error.get('type')}
Severity: {error.get('severity')}
Message: {error.get('message', error.get('error', ''))}
File: {error.get('file', 'unknown')}

Provide:
1. Root cause analysis
2. Exact fix (code snippet if applicable)
3. How to verify it works
4. Prevention strategy

Format as JSON:
{{
  "root_cause": "...",
  "fix": "...",
  "code_snippet": "...",
  "verification": "...",
  "prevention": "...",
  "confidence": 0.0-1.0
}}
"""

        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.3  # Lower for accurate fixes
                    },
                    timeout=300.0
                )

                result = response.json()
                response_text = result.get("response", "")

                # Extract JSON
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return {"error": "Could not parse response"}

        except Exception as e:
            return {"error": str(e)}

    async def apply_fix(self, error: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """Automatically apply fix"""

        file_path = error.get("file")
        fix_code = analysis.get("code_snippet", "")

        if not file_path or not fix_code or not file_path.endswith(".py"):
            return False

        try:
            # Read file
            with open(file_path, "r") as f:
                content = f.read()

            # Find line number
            error_msg = error.get("error", "")
            line_match = re.search(r"line (\d+)", error_msg)

            if line_match:
                line_num = int(line_match.group(1))

                # Apply fix (simple line replacement)
                lines = content.split("\n")
                if 0 <= line_num - 1 < len(lines):
                    # Backup original
                    with open(f"{file_path}.bak", "w") as f:
                        f.write(content)

                    # Apply fix
                    lines[line_num - 1] = fix_code
                    with open(file_path, "w") as f:
                        f.write("\n".join(lines))

                    print(f"✅ Applied fix to {file_path}:{line_num}")
                    self.fixes_applied.append({
                        "file": file_path,
                        "line": line_num,
                        "timestamp": datetime.now().isoformat()
                    })

                    return True
        except Exception as e:
            print(f"⚠️  Could not apply fix: {e}")

        return False

    async def verify_fix(self, file_path: str) -> bool:
        """Verify fix works"""

        if not file_path.endswith(".py"):
            return True

        try:
            result = subprocess.run(
                ["python3", "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"✅ Fix verified: {file_path}")
                return True
            else:
                print(f"❌ Fix failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"⚠️  Verification error: {e}")
            return False

    async def run(self):
        """Main autodebugger loop"""

        print("\n" + "="*60)
        print("🐛 AUTONOMOUS DEBUGGER AGENT STARTING")
        print("="*60)

        iteration = 0

        while True:
            iteration += 1
            print(f"\n[Scan {iteration}] {datetime.now().strftime('%H:%M:%S')}")

            try:
                # Scan for errors
                errors = await self.scan_for_errors()

                if errors:
                    print(f"Found {len(errors)} issues:")

                    for error in errors[:5]:  # Fix top 5
                        print(f"\n  🔍 Analyzing: {error.get('type')}")

                        # Analyze
                        analysis = await self.analyze_error(error)

                        if "error" not in analysis:
                            # Try to apply fix
                            if await self.apply_fix(error, analysis):
                                # Verify fix
                                await self.verify_fix(error.get("file"))
                        else:
                            print(f"    ⚠️  Could not analyze: {analysis['error']}")
                else:
                    print("✅ No errors found")

                print(f"\n📈 Total fixes applied: {len(self.fixes_applied)}")

                # Wait before next scan
                await asyncio.sleep(120)

            except Exception as e:
                print(f"❌ Debugger error: {e}")
                await asyncio.sleep(30)

async def main():
    debugger = AutoDebugger()
    await debugger.run()

if __name__ == "__main__":
    asyncio.run(main())
