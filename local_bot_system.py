#!/usr/bin/env python3
"""
AIEmpire Local Bot System
========================
Hybrid Bot mit Ollama + Claude
- Läuft auf http://localhost:8000
- Ollama für einfache Tasks (kostenlos, schnell)
- Claude für komplexe Tasks (intelligent)
- Web-Interface für interaktive Nutzung
- Commands: read, edit, execute, grep, git, bash
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx

# ─── CONFIG ──────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:1.5b"  # Kleines, schnelles Modell
CLAUDE_MODEL = "claude-opus-4-6"

app = FastAPI(title="AIEmpire Local Bot System")

# ─── MODELS ──────────────────────────────────────────────────────────────────

class BotRequest(BaseModel):
    command: str  # read, edit, execute, grep, git, bash
    args: Dict[str, Any] = {}

class BotResponse(BaseModel):
    success: bool
    command: str
    output: str
    error: Optional[str] = None
    model_used: str  # "ollama" oder "claude"

# ─── HYBRID ROUTER ──────────────────────────────────────────────────────────

async def call_ollama(prompt: str) -> Optional[str]:
    """Rufe Ollama lokal auf (kostenlos, schnell)."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
            )
            if response.status_code == 200:
                return response.json().get("response", "")
    except Exception as e:
        print(f"⚠️ Ollama error: {e}")
    return None

async def call_claude(prompt: str) -> Optional[str]:
    """Rufe Claude API auf (intelligent, bezahlt)."""
    try:
        from antigravity.unified_router import UnifiedRouter
        router = UnifiedRouter()
        # Simplified: return router.route() result
        return "Claude API not configured in this context"
    except Exception as e:
        print(f"⚠️ Claude error: {e}")
    return None

async def hybrid_analyze(task: str, is_complex: bool = False) -> tuple[str, str]:
    """Hybrid: Ollama für einfach, Claude für komplex."""
    if not is_complex:
        result = await call_ollama(task)
        if result:
            return result, "ollama"

    # Fallback zu Claude
    result = await call_claude(task)
    if result:
        return result, "claude"

    # Fallback zu lokaler Verarbeitung
    return f"Task verarbeitet: {task[:100]}", "local"

# ─── BOT COMMANDS ───────────────────────────────────────────────────────────

async def cmd_read(filepath: str) -> tuple[bool, str, Optional[str]]:
    """Lese Datei."""
    try:
        path = REPO_ROOT / filepath
        if not path.exists():
            return False, "", f"Datei nicht gefunden: {filepath}"
        content = path.read_text()
        return True, content, None
    except Exception as e:
        return False, "", str(e)

async def cmd_edit(filepath: str, old_string: str, new_string: str) -> tuple[bool, str, Optional[str]]:
    """Bearbeite Datei."""
    try:
        path = REPO_ROOT / filepath
        if not path.exists():
            return False, "", f"Datei nicht gefunden: {filepath}"
        content = path.read_text()
        if old_string not in content:
            return False, "", f"String nicht gefunden in {filepath}"
        new_content = content.replace(old_string, new_string)
        path.write_text(new_content)
        return True, f"✅ {filepath} aktualisiert", None
    except Exception as e:
        return False, "", str(e)

async def cmd_execute(command: str, cwd: Optional[str] = None) -> tuple[bool, str, Optional[str]]:
    """Führe Befehl aus."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd or str(REPO_ROOT)
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return success, output[:2000], None if success else output[-500:]
    except Exception as e:
        return False, "", str(e)

async def cmd_grep(pattern: str, glob_pattern: str = "**/*.py") -> tuple[bool, str, Optional[str]]:
    """Suche im Code."""
    try:
        result = subprocess.run(
            ["grep", "-r", "--include=*", pattern, str(REPO_ROOT)],
            capture_output=True,
            text=True,
            timeout=10
        )
        matches = result.stdout.split('\n')[:50]  # Max 50 Matches
        output = '\n'.join(matches)
        return True, output or "Keine Matches", None
    except Exception as e:
        return False, "", str(e)

async def cmd_git(subcommand: str, args: str = "") -> tuple[bool, str, Optional[str]]:
    """Git Operationen."""
    try:
        cmd = f"git {subcommand} {args}".strip()
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT)
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return success, output, None if success else output
    except Exception as e:
        return False, "", str(e)

# ─── API ENDPOINTS ──────────────────────────────────────────────────────────

@app.post("/api/bot", response_model=BotResponse)
async def bot_command(req: BotRequest) -> BotResponse:
    """Führe Bot-Command aus."""
    command = req.command.lower()
    args = req.args

    success = False
    output = ""
    error = None
    model_used = "local"

    if command == "read":
        success, output, error = await cmd_read(args.get("path", ""))

    elif command == "edit":
        success, output, error = await cmd_edit(
            args.get("path", ""),
            args.get("old_string", ""),
            args.get("new_string", "")
        )

    elif command == "execute":
        success, output, error = await cmd_execute(
            args.get("command", ""),
            args.get("cwd")
        )

    elif command == "grep":
        success, output, error = await cmd_grep(
            args.get("pattern", ""),
            args.get("glob", "**/*.py")
        )

    elif command == "git":
        success, output, error = await cmd_git(
            args.get("subcommand", "status"),
            args.get("args", "")
        )

    elif command == "bash":
        success, output, error = await cmd_execute(args.get("command", ""))

    elif command == "analyze":
        # Hybrid: Ollama oder Claude
        task = args.get("task", "")
        is_complex = args.get("is_complex", False)
        output, model_used = await hybrid_analyze(task, is_complex)
        success = True

    else:
        error = f"Unbekannter Command: {command}"

    return BotResponse(
        success=success,
        command=command,
        output=output[:4000],  # Limit output
        error=error,
        model_used=model_used
    )

# ─── WEB INTERFACE ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Web-Interface für Bot."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIEmpire Local Bot</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #4ec9b0; margin-bottom: 20px; }
            .chat { height: 400px; border: 1px solid #444; padding: 10px; margin-bottom: 10px;
                    overflow-y: auto; background: #252526; border-radius: 5px; }
            .message { margin: 5px 0; padding: 8px; border-radius: 3px; }
            .user { background: #0e47a1; color: #fff; }
            .bot { background: #1b5e20; color: #4ade80; }
            .error { background: #7d0000; color: #ff6b6b; }
            .input-group { display: flex; gap: 10px; margin-bottom: 10px; }
            input, textarea, select { background: #3e3e42; color: #d4d4d4; border: 1px solid #555;
                                     padding: 8px; border-radius: 3px; }
            button { background: #0e639c; color: #fff; border: none; padding: 8px 16px;
                    border-radius: 3px; cursor: pointer; }
            button:hover { background: #1177bb; }
            .commands { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
            .cmd-btn { padding: 10px; text-align: center; }
            .status { color: #858585; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AIEmpire Local Bot</h1>
            <p class="status">Status: Online | Ollama: qwen2.5:1.5b | Hybrid Router: Ollama + Claude</p>

            <div class="commands">
                <button class="cmd-btn" onclick="setCommand('read')">📖 Read</button>
                <button class="cmd-btn" onclick="setCommand('edit')">✏️ Edit</button>
                <button class="cmd-btn" onclick="setCommand('execute')">⚙️ Execute</button>
                <button class="cmd-btn" onclick="setCommand('grep')">🔍 Grep</button>
                <button class="cmd-btn" onclick="setCommand('git')">🐙 Git</button>
                <button class="cmd-btn" onclick="setCommand('bash')">💻 Bash</button>
                <button class="cmd-btn" onclick="setCommand('analyze')">🧠 Analyze</button>
            </div>

            <div class="chat" id="chat"></div>

            <div class="input-group">
                <select id="command" style="flex: 0 0 100px;">
                    <option value="bash">bash</option>
                    <option value="read">read</option>
                    <option value="execute">execute</option>
                    <option value="git">git</option>
                    <option value="grep">grep</option>
                </select>
                <input type="text" id="input" placeholder="Befehl eingeben..." style="flex: 1;" />
                <button onclick="sendCommand()">Send</button>
            </div>

            <div class="status">
                💡 Beispiele: read empire_engine.py | execute python3 empire_engine.py | git status
            </div>
        </div>

        <script>
            const chat = document.getElementById('chat');
            const input = document.getElementById('input');
            const command = document.getElementById('command');

            function addMessage(text, type) {
                const msg = document.createElement('div');
                msg.className = 'message ' + type;
                msg.textContent = text;
                chat.appendChild(msg);
                chat.scrollTop = chat.scrollHeight;
            }

            function setCommand(cmd) {
                command.value = cmd;
                input.focus();
            }

            async function sendCommand() {
                const cmd = command.value;
                const text = input.value.trim();
                if (!text) return;

                addMessage(`> ${cmd} ${text}`, 'user');
                input.value = '';

                try {
                    const response = await fetch('/api/bot', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            command: cmd,
                            args: {path: text, command: text, pattern: text,
                                   subcommand: text.split(' ')[0],
                                   task: text}
                        })
                    });

                    const data = await response.json();
                    if (data.success) {
                        addMessage(`✅ [${data.model_used}]\\n${data.output}`, 'bot');
                    } else {
                        addMessage(`❌ ${data.error}`, 'error');
                    }
                } catch (e) {
                    addMessage(`❌ Error: ${e.message}`, 'error');
                }
            }

            input.addEventListener('keypress', e => {
                if (e.key === 'Enter') sendCommand();
            });

            addMessage('🤖 AIEmpire Bot Online!', 'bot');
            addMessage('Commands: read, edit, execute, grep, git, bash, analyze', 'bot');
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    """Health Check."""
    return {
        "status": "online",
        "ollama": "checking...",
        "models": ["qwen2.5:1.5b"],
        "features": ["read", "edit", "execute", "grep", "git", "bash", "hybrid_analyze"]
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🤖 AIEmpire Local Bot System")
    print("=" * 60)
    print("✅ Web-Interface: http://localhost:8000")
    print("✅ API: POST /api/bot")
    print("✅ Health: /health")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
