"""
AI EMPIRE CONTROL API
Central nervous system connecting all Empire subsystems.
Runs on your Mac, accessible from iPhone over local network.
"""
import os
import sys
import json
import subprocess
import httpx
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Add project root to path for antigravity imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from antigravity.config import GITHUB_TOKEN as _GITHUB_TOKEN

app = FastAPI(title="AI Empire Control API", version="1.0.0")

# CORS — allow iPhone + any local device
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths ──
EMPIRE_ROOT = Path(__file__).parent.parent
GOLD_NUGGETS_DIR = EMPIRE_ROOT / "gold-nuggets"
BRAIN_DIR = EMPIRE_ROOT / "brain-system" / "brains"
TASKS_DIR = EMPIRE_ROOT / "atomic-reactor" / "tasks"
DOCS_DIR = EMPIRE_ROOT / "docs"
MOBILE_DIR = EMPIRE_ROOT / "mobile-command-center"

# ── GitHub Config ──
GITHUB_OWNER = "mauricepfeifer-ctrl"
GITHUB_REPO = "AIEmpire-Core"
GITHUB_TOKEN = _GITHUB_TOKEN

# ── WebSocket connections ──
active_connections: list[WebSocket] = []

# ── Models ──
class ActionRequest(BaseModel):
    action: str
    params: Optional[dict] = {}

class TaskUpdate(BaseModel):
    task_id: str
    status: str  # pending, in_progress, completed

class NoteCreate(BaseModel):
    title: str
    content: str
    category: str = "general"

# ── Serve Mobile App ──
if MOBILE_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(MOBILE_DIR), html=True), name="mobile")

@app.get("/")
async def root():
    if (MOBILE_DIR / "index.html").exists():
        return FileResponse(str(MOBILE_DIR / "index.html"))
    return {"status": "AI Empire Control API", "version": "1.0.0"}

# ══════════════════════════════════════
# SYSTEM STATUS
# ══════════════════════════════════════
@app.get("/api/health")
async def health_check():
    """Full system health check"""
    checks = {}

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get("http://localhost:11434/api/tags")
            models = r.json().get("models", [])
            checks["ollama"] = {"status": "active", "models": [m["name"] for m in models]}
    except Exception:
        checks["ollama"] = {"status": "offline", "models": []}

    # CRM
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get("http://localhost:3500/api/stats")
            checks["crm"] = {"status": "active", "data": r.json()}
    except Exception:
        checks["crm"] = {"status": "offline"}

    # Redis
    try:
        result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True, timeout=3)
        checks["redis"] = {"status": "active" if result.stdout.strip() == "PONG" else "offline"}
    except Exception:
        checks["redis"] = {"status": "offline"}

    # PostgreSQL
    try:
        result = subprocess.run(["pg_isready"], capture_output=True, text=True, timeout=3)
        checks["postgresql"] = {"status": "active" if result.returncode == 0 else "offline"}
    except Exception:
        checks["postgresql"] = {"status": "offline"}

    # OpenClaw
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get("http://localhost:18789/health")
            checks["openclaw"] = {"status": "active"}
    except Exception:
        checks["openclaw"] = {"status": "offline"}

    # GitHub Actions
    if GITHUB_TOKEN:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(
                    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs?per_page=5",
                    headers={"Authorization": f"token {GITHUB_TOKEN}"}
                )
                runs = r.json().get("workflow_runs", [])
                checks["github_actions"] = {
                    "status": "active",
                    "recent_runs": [{"name": r["name"], "status": r["status"], "conclusion": r.get("conclusion")} for r in runs]
                }
        except Exception:
            checks["github_actions"] = {"status": "unknown"}
    else:
        checks["github_actions"] = {"status": "no_token"}

    # Brain System files
    brains = list(BRAIN_DIR.glob("*.md")) if BRAIN_DIR.exists() else []
    checks["brain_system"] = {"status": "active", "brains": len(brains)}

    active = sum(1 for v in checks.values() if v.get("status") == "active")
    total = len(checks)

    return {
        "timestamp": datetime.now().isoformat(),
        "overall": "healthy" if active >= 4 else "degraded" if active >= 2 else "critical",
        "active_services": active,
        "total_services": total,
        "services": checks
    }

# ══════════════════════════════════════
# GOLD NUGGETS
# ══════════════════════════════════════
@app.get("/api/nuggets")
async def get_nuggets():
    """Get all gold nuggets"""
    nuggets = []
    if GOLD_NUGGETS_DIR.exists():
        for f in sorted(GOLD_NUGGETS_DIR.glob("GOLD_*.md")):
            content = f.read_text(encoding="utf-8", errors="ignore")
            title = content.split("\n")[0].replace("#", "").strip() if content else f.stem
            nuggets.append({
                "id": f.stem,
                "title": title,
                "file": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "preview": content[:300] if content else ""
            })
    return {"count": len(nuggets), "nuggets": nuggets}

@app.get("/api/nuggets/{nugget_id}")
async def get_nugget(nugget_id: str):
    """Get single nugget content"""
    for f in GOLD_NUGGETS_DIR.glob("*.md"):
        if f.stem == nugget_id:
            return {"id": f.stem, "content": f.read_text(encoding="utf-8", errors="ignore")}
    raise HTTPException(404, "Nugget not found")

# ══════════════════════════════════════
# BRAIN SYSTEM
# ══════════════════════════════════════
@app.get("/api/brains")
async def get_brains():
    """Get all brain modules"""
    brains = []
    brain_meta = {
        "00_brainstem": {"name": "Brainstem", "role": "Der Wächter", "model": "Bash Scripts", "icon": "🛡"},
        "01_neocortex": {"name": "Neocortex", "role": "Der Visionär", "model": "Kimi K2.5", "icon": "🔭"},
        "02_prefrontal": {"name": "Prefrontal", "role": "Der CEO", "model": "Claude", "icon": "👑"},
        "03_temporal": {"name": "Temporal", "role": "Der Mund", "model": "Kimi K2.5", "icon": "📢"},
        "04_parietal": {"name": "Parietal", "role": "Die Zahlen", "model": "Ollama", "icon": "📊"},
        "05_limbic": {"name": "Limbic", "role": "Der Antrieb", "model": "Ollama", "icon": "🔥"},
        "06_cerebellum": {"name": "Cerebellum", "role": "Die Hände", "model": "Ollama", "icon": "🔨"},
        "07_hippocampus": {"name": "Hippocampus", "role": "Das Gedächtnis", "model": "SQLite", "icon": "💾"},
    }
    if BRAIN_DIR.exists():
        for f in sorted(BRAIN_DIR.glob("*.md")):
            meta = brain_meta.get(f.stem, {"name": f.stem, "role": "Unknown", "model": "Unknown", "icon": "🧠"})
            content = f.read_text(encoding="utf-8", errors="ignore")
            brains.append({**meta, "id": f.stem, "file": f.name, "preview": content[:200]})
    return {"count": len(brains), "brains": brains}

# ══════════════════════════════════════
# TASKS (Atomic Reactor)
# ══════════════════════════════════════
@app.get("/api/tasks")
async def get_tasks():
    """Get all task definitions"""
    tasks = []
    if TASKS_DIR.exists():
        for f in sorted(TASKS_DIR.glob("*.yaml")):
            content = f.read_text(encoding="utf-8", errors="ignore")
            tasks.append({"id": f.stem, "file": f.name, "content": content})
    return {"count": len(tasks), "tasks": tasks}

# ══════════════════════════════════════
# ACTIONS — trigger things from iPhone
# ══════════════════════════════════════
@app.post("/api/actions")
async def trigger_action(req: ActionRequest):
    """Trigger system actions from mobile"""
    action = req.action
    result = {"action": action, "timestamp": datetime.now().isoformat()}

    if action == "health_check":
        return await health_check()

    elif action == "generate_content":
        # Trigger content generation via Ollama
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post("http://localhost:11434/api/generate", json={
                    "model": "qwen2.5-coder:7b",
                    "prompt": "Generate a viral tweet about AI automation for entrepreneurs. Max 280 chars. Just the tweet, no explanation.",
                    "stream": False
                })
                result["content"] = r.json().get("response", "")
                result["status"] = "success"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

    elif action == "start_crm":
        try:
            subprocess.Popen(["node", str(EMPIRE_ROOT / "crm" / "server.js")],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            result["status"] = "started"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

    elif action == "start_redis":
        try:
            r = subprocess.run(["brew", "services", "start", "redis"], capture_output=True, text=True)
            result["status"] = "success"
            result["output"] = r.stdout
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

    elif action == "start_postgresql":
        try:
            r = subprocess.run(["brew", "services", "start", "postgresql@16"], capture_output=True, text=True)
            result["status"] = "success"
            result["output"] = r.stdout
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

    elif action == "git_status":
        try:
            r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=str(EMPIRE_ROOT))
            result["status"] = "success"
            result["output"] = r.stdout
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

    elif action == "git_push":
        try:
            subprocess.run(["git", "add", "-A"], cwd=str(EMPIRE_ROOT))
            subprocess.run(["git", "commit", "-m", f"[Mobile] Auto-commit {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
                         cwd=str(EMPIRE_ROOT))
            r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, cwd=str(EMPIRE_ROOT))
            result["status"] = "success"
            result["output"] = r.stdout or r.stderr
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

    elif action == "trigger_workflow":
        workflow = req.params.get("workflow", "daily-content-engine.yml")
        if GITHUB_TOKEN:
            try:
                async with httpx.AsyncClient(timeout=10) as c:
                    r = await c.post(
                        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow}/dispatches",
                        headers={"Authorization": f"token {GITHUB_TOKEN}"},
                        json={"ref": "main"}
                    )
                    result["status"] = "triggered" if r.status_code == 204 else "error"
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
        else:
            result["status"] = "error"
            result["error"] = "No GITHUB_TOKEN set"

    elif action == "ollama_chat":
        prompt = req.params.get("prompt", "Hello")
        model = req.params.get("model", "qwen2.5-coder:7b")
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post("http://localhost:11434/api/generate", json={
                    "model": model, "prompt": prompt, "stream": False
                })
                result["response"] = r.json().get("response", "")
                result["status"] = "success"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

    elif action == "create_issue":
        title = req.params.get("title", "New Task")
        body = req.params.get("body", "")
        labels = req.params.get("labels", [])
        if GITHUB_TOKEN:
            try:
                async with httpx.AsyncClient(timeout=10) as c:
                    r = await c.post(
                        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues",
                        headers={"Authorization": f"token {GITHUB_TOKEN}"},
                        json={"title": title, "body": body, "labels": labels}
                    )
                    result["issue"] = r.json()
                    result["status"] = "created"
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)

    else:
        result["status"] = "unknown_action"

    # Notify all WebSocket clients
    for ws in active_connections:
        try:
            await ws.send_json({"type": "action_result", "data": result})
        except Exception:
            pass

    return result

# ══════════════════════════════════════
# GITHUB ISSUES (as tasks)
# ══════════════════════════════════════
@app.get("/api/issues")
async def get_issues(state: str = "open"):
    """Get GitHub issues"""
    if not GITHUB_TOKEN:
        return {"count": 0, "issues": [], "error": "No GITHUB_TOKEN"}
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues?state={state}&per_page=30",
                headers={"Authorization": f"token {GITHUB_TOKEN}"}
            )
            issues = r.json()
            return {"count": len(issues), "issues": [
                {"id": i["number"], "title": i["title"], "state": i["state"],
                 "labels": [label["name"] for label in i.get("labels", [])],
                 "created": i["created_at"], "updated": i["updated_at"]}
                for i in issues if "pull_request" not in i
            ]}
    except Exception as e:
        return {"count": 0, "issues": [], "error": str(e)}

# ══════════════════════════════════════
# GITHUB WORKFLOWS
# ══════════════════════════════════════
@app.get("/api/workflows")
async def get_workflows():
    """Get GitHub Actions workflows"""
    if not GITHUB_TOKEN:
        # Fallback: read from filesystem
        wf_dir = EMPIRE_ROOT / ".github" / "workflows"
        if wf_dir.exists():
            return {"workflows": [{"name": f.stem, "file": f.name} for f in wf_dir.glob("*.yml")]}
        return {"workflows": []}
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows",
                headers={"Authorization": f"token {GITHUB_TOKEN}"}
            )
            return r.json()
    except Exception as e:
        return {"error": str(e)}

# ══════════════════════════════════════
# REVENUE TRACKING
# ══════════════════════════════════════
REVENUE_FILE = EMPIRE_ROOT / "docs" / "revenue.json"

@app.get("/api/revenue")
async def get_revenue():
    """Get revenue tracking data"""
    if REVENUE_FILE.exists():
        return json.loads(REVENUE_FILE.read_text())
    return {
        "current_month": 0,
        "target": 10000,
        "channels": {
            "gumroad": {"revenue": 0, "products": 0, "status": "setup"},
            "fiverr": {"revenue": 0, "gigs": 0, "status": "not_started"},
            "consulting": {"revenue": 0, "clients": 0, "status": "ready"},
            "x_twitter": {"revenue": 0, "followers": 0, "leads": 0, "status": "active"},
            "openclaw_skills": {"revenue": 0, "skills": 0, "status": "dev"},
            "youtube": {"revenue": 0, "videos": 0, "status": "not_started"},
        },
        "history": []
    }

@app.post("/api/revenue")
async def update_revenue(data: dict):
    """Update revenue data"""
    REVENUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    REVENUE_FILE.write_text(json.dumps(data, indent=2))
    return {"status": "saved"}

# ══════════════════════════════════════
# NOTES & QUICK CAPTURE
# ══════════════════════════════════════
NOTES_FILE = EMPIRE_ROOT / "docs" / "mobile_notes.json"

@app.get("/api/notes")
async def get_notes():
    if NOTES_FILE.exists():
        return json.loads(NOTES_FILE.read_text())
    return {"notes": []}

@app.post("/api/notes")
async def create_note(note: NoteCreate):
    notes = json.loads(NOTES_FILE.read_text()) if NOTES_FILE.exists() else {"notes": []}
    notes["notes"].insert(0, {
        "id": len(notes["notes"]) + 1,
        "title": note.title,
        "content": note.content,
        "category": note.category,
        "created": datetime.now().isoformat()
    })
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    NOTES_FILE.write_text(json.dumps(notes, indent=2))
    return {"status": "created", "note": notes["notes"][0]}

# ══════════════════════════════════════
# WEBSOCKET — real-time updates
# ══════════════════════════════════════
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back + broadcast
            for ws in active_connections:
                try:
                    await ws.send_text(data)
                except Exception:
                    pass
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# ══════════════════════════════════════
# SYSTEM INFO
# ══════════════════════════════════════
@app.get("/api/system")
async def system_info():
    """Get comprehensive system info"""
    # Count files
    total_files = sum(1 for _ in EMPIRE_ROOT.rglob("*") if _.is_file() and ".git" not in str(_))
    total_py = sum(1 for _ in EMPIRE_ROOT.rglob("*.py") if ".git" not in str(_))
    total_md = sum(1 for _ in EMPIRE_ROOT.rglob("*.md") if ".git" not in str(_))
    total_js = sum(1 for _ in EMPIRE_ROOT.rglob("*.js") if ".git" not in str(_))

    # Git info
    try:
        branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=str(EMPIRE_ROOT)).stdout.strip()
        commits = subprocess.run(["git", "rev-list", "--count", "HEAD"], capture_output=True, text=True, cwd=str(EMPIRE_ROOT)).stdout.strip()
        last_commit = subprocess.run(["git", "log", "-1", "--format=%s (%cr)"], capture_output=True, text=True, cwd=str(EMPIRE_ROOT)).stdout.strip()
    except Exception:
        branch, commits, last_commit = "unknown", "0", "unknown"

    return {
        "repo": f"{GITHUB_OWNER}/{GITHUB_REPO}",
        "branch": branch,
        "commits": int(commits) if commits.isdigit() else 0,
        "last_commit": last_commit,
        "files": {"total": total_files, "python": total_py, "markdown": total_md, "javascript": total_js},
        "subsystems": [
            "brain-system", "workflow-system", "kimi-swarm", "x-lead-machine",
            "crm", "atomic-reactor", "n8n-workflows", "openclaw-config",
            "gold-nuggets", "BMA_ACADEMY", "mobile-command-center"
        ]
    }

# ══════════════════════════════════════
# STARTUP
# ══════════════════════════════════════
if __name__ == "__main__":
    import socket
    # Get local IP for iPhone access
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "localhost"
    finally:
        s.close()

    print(f"""
╔══════════════════════════════════════════════╗
║        AI EMPIRE CONTROL API v1.0.0          ║
╠══════════════════════════════════════════════╣
║                                              ║
║  🖥  Mac:    http://localhost:3333            ║
║  📱 iPhone: http://{local_ip}:3333{' ' * (14 - len(local_ip))}║
║                                              ║
║  Öffne den iPhone-Link in Safari,            ║
║  dann: Teilen → Zum Home-Bildschirm         ║
║                                              ║
╚══════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="0.0.0.0", port=3333, log_level="info")
