#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  EMPIRE BOOT — Unified System Controller                        ║
║  ═══════════════════════════════════════                        ║
║  One command to rule them all.                                  ║
║                                                                  ║
║  python3 empire_boot.py              → Full system status       ║
║  python3 empire_boot.py start        → Start everything         ║
║  python3 empire_boot.py stop         → Stop everything          ║
║  python3 empire_boot.py health       → Deep health check        ║
║  python3 empire_boot.py repair       → Auto-repair all issues   ║
║  python3 empire_boot.py agents       → Launch agent swarm       ║
║  python3 empire_boot.py revenue      → Revenue dashboard        ║
║  python3 empire_boot.py auto         → Full autonomous cycle    ║
║                                                                  ║
║  Owner: Maurice Pfeifer — BMA-Meister + AI Architect            ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── Paths ─────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ─── Load .env ─────────────────────────────────────────────────────
def load_env():
    """Load .env without external deps."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val

load_env()


# ═══════════════════════════════════════════════════════════════════
# TERMINAL COLORS (no deps needed)
# ═══════════════════════════════════════════════════════════════════
class C:
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @staticmethod
    def ok(msg): return f"{C.GREEN}✓{C.RESET} {msg}"
    @staticmethod
    def fail(msg): return f"{C.RED}✗{C.RESET} {msg}"
    @staticmethod
    def warn(msg): return f"{C.YELLOW}⚠{C.RESET} {msg}"
    @staticmethod
    def info(msg): return f"{C.CYAN}→{C.RESET} {msg}"
    @staticmethod
    def head(msg): return f"\n{C.BOLD}{C.BLUE}{'─' * 60}{C.RESET}\n{C.BOLD}  {msg}{C.RESET}\n{C.BOLD}{C.BLUE}{'─' * 60}{C.RESET}"


# ═══════════════════════════════════════════════════════════════════
# SERVICE CHECKER
# ═══════════════════════════════════════════════════════════════════

def check_port(port: int) -> bool:
    """Check if something is listening on a port."""
    import socket
    try:
        with socket.create_connection(("localhost", port), timeout=2):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False


def check_ollama() -> dict:
    """Check Ollama status and models."""
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            data = r.json()
            models = [m["name"] for m in data.get("models", [])]
            return {"available": True, "models": models, "count": len(models)}
    except Exception:
        pass
    return {"available": False, "models": [], "count": 0}


def check_service(name: str, port: int) -> dict:
    """Check a service by port."""
    up = check_port(port)
    return {"name": name, "port": port, "running": up}


def check_api_keys() -> dict:
    """Check which API keys are configured."""
    keys = {}
    for key_name in ["GEMINI_API_KEY", "MOONSHOT_API_KEY", "KIMI_API_KEY",
                      "OPENROUTER_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY"]:
        val = os.getenv(key_name, "")
        keys[key_name] = bool(val and val != "your-key-here" and len(val) > 8)
    return keys


# ═══════════════════════════════════════════════════════════════════
# AI PROVIDER CHAIN
# ═══════════════════════════════════════════════════════════════════

async def query_ollama(prompt: str, model: str = "qwen2.5-coder:7b",
                       system: str = "", timeout: float = 60) -> dict:
    """Query Ollama directly."""
    import httpx
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(f"{url}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()
        return {
            "content": data.get("response", ""),
            "model": model,
            "provider": "ollama",
            "tokens": data.get("eval_count", 0),
            "success": True,
        }


async def query_kimi(prompt: str, model: str = "moonshot-v1-8k",
                     system: str = "", timeout: float = 30) -> dict:
    """Query Kimi/Moonshot API."""
    import httpx
    api_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY", "")
    if not api_key:
        raise ConnectionError("No Kimi/Moonshot API key")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages},
        )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        return {
            "content": content,
            "model": model,
            "provider": "kimi",
            "tokens": tokens,
            "success": True,
        }


async def query_gemini(prompt: str, model: str = "gemini-2.0-flash",
                       system: str = "", timeout: float = 30) -> dict:
    """Query Gemini via REST API (no SDK needed)."""
    import httpx
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or len(api_key) < 10:
        raise ConnectionError("No Gemini API key")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    parts = []
    if system:
        parts.append({"text": f"[System]: {system}\n\n{prompt}"})
    else:
        parts.append({"text": prompt})

    payload = {"contents": [{"parts": parts}]}

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
        return {
            "content": content,
            "model": model,
            "provider": "gemini",
            "tokens": tokens,
            "success": True,
        }


async def query_openrouter(prompt: str, model: str = "meta-llama/llama-3.1-8b-instruct:free",
                           system: str = "", timeout: float = 30) -> dict:
    """Query OpenRouter (free models available)."""
    import httpx
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ConnectionError("No OpenRouter API key")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://aiempire.local",
            },
            json={"model": model, "messages": messages},
        )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return {
            "content": content,
            "model": model,
            "provider": "openrouter",
            "tokens": data.get("usage", {}).get("total_tokens", 0),
            "success": True,
        }


async def smart_query(prompt: str, system: str = "",
                      prefer: str = "auto", timeout: float = 60) -> dict:
    """
    Smart AI query with automatic fallback chain:
    Ollama (free, local) → Kimi (free tier) → Gemini (Google) → OpenRouter (free)

    Args:
        prompt: The question/task
        system: System prompt (agent personality)
        prefer: "ollama", "kimi", "gemini", "openrouter", or "auto"
        timeout: Max seconds per provider

    Returns:
        dict with content, model, provider, tokens, success
    """
    providers = []

    if prefer == "auto":
        # Default chain: local first, then cloud
        providers = [
            ("ollama", query_ollama),
            ("kimi", query_kimi),
            ("gemini", query_gemini),
            ("openrouter", query_openrouter),
        ]
    elif prefer == "cloud":
        providers = [
            ("kimi", query_kimi),
            ("gemini", query_gemini),
            ("openrouter", query_openrouter),
            ("ollama", query_ollama),
        ]
    else:
        # Put preferred first, then the rest
        all_p = {
            "ollama": query_ollama,
            "kimi": query_kimi,
            "gemini": query_gemini,
            "openrouter": query_openrouter,
        }
        if prefer in all_p:
            providers = [(prefer, all_p.pop(prefer))]
            providers.extend(all_p.items())
        else:
            providers = list(all_p.items())

    errors = []
    for name, query_fn in providers:
        try:
            kwargs = {"prompt": prompt, "timeout": timeout}
            if system:
                kwargs["system"] = system
            result = await query_fn(**kwargs)
            return result
        except Exception as e:
            errors.append(f"{name}: {e}")

    return {
        "content": f"All providers failed: {'; '.join(errors)}",
        "model": "none",
        "provider": "none",
        "tokens": 0,
        "success": False,
    }


# ═══════════════════════════════════════════════════════════════════
# SYSTEM STATUS DASHBOARD
# ═══════════════════════════════════════════════════════════════════

def show_status():
    """Show full system status dashboard."""
    print(f"""
{C.BOLD}{C.MAGENTA}╔══════════════════════════════════════════════════════════════╗
║          AI EMPIRE — UNIFIED SYSTEM CONTROLLER               ║
║          Owner: Maurice Pfeifer — BMA + AI Architect         ║
╚══════════════════════════════════════════════════════════════╝{C.RESET}
""")

    # ─── Services ─────────────────────────────────────
    print(C.head("INFRASTRUCTURE SERVICES"))

    services = [
        ("Ollama (AI Models)", 11434),
        ("Redis (Cache)", 6379),
        ("PostgreSQL (Database)", 5432),
        ("n8n (Automation)", 5678),
        ("Empire API", 3333),
        ("CRM", 3500),
        ("Atomic Reactor", 8888),
    ]

    running = 0
    for name, port in services:
        up = check_port(port)
        if up:
            running += 1
        status = C.ok(f"{name} → Port {port}") if up else C.fail(f"{name} → Port {port}")
        print(f"  {status}")

    print(f"\n  {C.BOLD}{running}/{len(services)} services running{C.RESET}")

    # ─── Ollama Models ────────────────────────────────
    print(C.head("AI MODELS (Ollama)"))
    ollama = check_ollama()
    if ollama["available"]:
        count = ollama["count"]
        print(f"  {C.ok(f'Ollama online — {count} models loaded')}")
        for m in ollama["models"][:10]:
            print(f"    {C.DIM}• {m}{C.RESET}")
        if ollama["count"] > 10:
            print(f"    {C.DIM}... and {ollama['count'] - 10} more{C.RESET}")
    else:
        print(f"  {C.fail('Ollama offline — starte mit: ollama serve')}")

    # ─── API Keys ─────────────────────────────────────
    print(C.head("API KEYS & CLOUD PROVIDERS"))
    keys = check_api_keys()
    for key_name, configured in keys.items():
        provider = key_name.replace("_API_KEY", "").replace("_", " ").title()
        if configured:
            print(f"  {C.ok(provider)}")
        else:
            print(f"  {C.warn(f'{provider} — not configured')}")

    # ─── Project Stats ────────────────────────────────
    print(C.head("PROJECT STATS"))

    py_files = list(ROOT.rglob("*.py"))
    py_files = [f for f in py_files if ".venv" not in str(f) and "__pycache__" not in str(f)]

    total_lines = 0
    for f in py_files:
        try:
            total_lines += len(f.read_text().splitlines())
        except Exception:
            pass

    dirs = [d for d in ROOT.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))]

    print(f"  {C.info(f'Python files: {len(py_files)}')}")
    print(f"  {C.info(f'Total lines: {total_lines:,}')}")
    print(f"  {C.info(f'Subsystems: {len(dirs)}')}")
    print(f"  {C.info(f'Git branch: {_git_branch()}')}")

    # ─── Revenue Status ───────────────────────────────
    print(C.head("REVENUE CHANNELS"))

    channels = [
        ("Gumroad Products", "5 products ready", True),
        ("Fiverr/Upwork", "3 gigs defined", True),
        ("BMA + AI Consulting", "UNIQUE NICHE", True),
        ("Agent Builders Club", "29 EUR/month", True),
        ("X/Twitter Lead Gen", "3 personas", True),
    ]
    for name, desc, ready in channels:
        status = C.ok(f"{name} — {desc}") if ready else C.fail(f"{name} — {desc}")
        print(f"  {status}")

    # ─── Quick Actions ────────────────────────────────
    print(C.head("QUICK ACTIONS"))
    print(f"""
  {C.CYAN}python3 empire_boot.py start{C.RESET}    → Start all services
  {C.CYAN}python3 empire_boot.py stop{C.RESET}     → Stop all services
  {C.CYAN}python3 empire_boot.py health{C.RESET}   → Deep health check
  {C.CYAN}python3 empire_boot.py repair{C.RESET}   → Auto-repair issues
  {C.CYAN}python3 empire_boot.py agents{C.RESET}   → Launch agent swarm
  {C.CYAN}python3 empire_boot.py auto{C.RESET}     → Full autonomous cycle
  {C.CYAN}python3 empire_boot.py ask "..."{C.RESET} → Ask AI (smart routing)
""")


def _git_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(ROOT), stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return "unknown"


# ═══════════════════════════════════════════════════════════════════
# SERVICE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

def start_services():
    """Start all infrastructure services."""
    print(C.head("STARTING ALL SERVICES"))

    steps = [
        ("Ollama", "ollama serve", 11434, True),
        ("Redis", "redis-server --daemonize yes", 6379, False),
        ("PostgreSQL", "pg_ctl start -D /usr/local/var/postgresql@14 -l /tmp/pg.log", 5432, False),
    ]

    for name, cmd, port, bg in steps:
        if check_port(port):
            print(f"  {C.ok(f'{name} already running on port {port}')}")
            continue

        try:
            if bg:
                subprocess.Popen(
                    cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            else:
                subprocess.run(cmd.split(), capture_output=True, timeout=10)

            # Wait for startup
            for _ in range(10):
                time.sleep(1)
                if check_port(port):
                    break

            if check_port(port):
                print(f"  {C.ok(f'{name} started on port {port}')}")
            else:
                print(f"  {C.warn(f'{name} starting... (may need manual check)')}")
        except Exception as e:
            print(f"  {C.fail(f'{name}: {e}')}")

    print(f"\n  {C.info('All core services started.')}")
    print(f"  {C.DIM}Note: CRM, n8n, and API servers start separately.{C.RESET}")
    print(f"  {C.DIM}Use 'python3 empire_engine.py' for the revenue dashboard.{C.RESET}")


def stop_services():
    """Stop all services gracefully."""
    print(C.head("STOPPING ALL SERVICES"))

    cmds = [
        ("n8n", "pkill -f 'n8n start'"),
        ("Empire API", "pkill -f empire_api"),
        ("CRM", "pkill -f 'node.*crm'"),
        ("Ollama", "pkill -f 'ollama serve'"),
    ]

    for name, cmd in cmds:
        try:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            print(f"  {C.ok(f'{name} stopped')}")
        except Exception:
            print(f"  {C.warn(f'{name} — not running or could not stop')}")

    print(f"\n  {C.info('Services stopped. Redis and PostgreSQL left running (persistent data).')}")


# ═══════════════════════════════════════════════════════════════════
# HEALTH CHECK (DEEP)
# ═══════════════════════════════════════════════════════════════════

async def deep_health_check():
    """Run deep health check on all systems."""
    print(C.head("DEEP HEALTH CHECK"))
    issues = []

    # 1. Check Python imports
    print(f"\n  {C.BOLD}Python Imports:{C.RESET}")
    modules = [
        "antigravity.config",
        "antigravity.unified_router",
        "antigravity.empire_bridge",
        "antigravity.knowledge_store",
        "antigravity.cross_verify",
        "antigravity.planning_mode",
        "antigravity.sync_engine",
    ]
    for mod in modules:
        try:
            __import__(mod, fromlist=[""])
            print(f"    {C.ok(mod)}")
        except Exception as e:
            print(f"    {C.fail(f'{mod}: {e}')}")
            issues.append(f"Import failed: {mod}")

    # 2. Check Ollama connection
    print(f"\n  {C.BOLD}AI Providers:{C.RESET}")
    ollama = check_ollama()
    if ollama["available"]:
        ocount = ollama["count"]
        print(f"    {C.ok(f'Ollama: {ocount} models')}")

        # Quick inference test
        try:
            result = await query_ollama("Say 'ok' in one word", timeout=15)
            if result.get("success"):
                print(f"    {C.ok('Ollama inference: working')}")
            else:
                print(f"    {C.fail('Ollama inference: failed')}")
                issues.append("Ollama inference not working")
        except Exception as e:
            print(f"    {C.fail(f'Ollama inference: {e}')}")
            issues.append(f"Ollama inference error: {e}")
    else:
        print(f"    {C.fail('Ollama: offline')}")
        issues.append("Ollama not running")

    # 3. Check API keys
    keys = check_api_keys()
    for key_name, ok in keys.items():
        name = key_name.replace("_API_KEY", "")
        if ok:
            print(f"    {C.ok(f'{name}: configured')}")
        else:
            print(f"    {C.warn(f'{name}: not set')}")

    # 4. Check Knowledge Store
    print(f"\n  {C.BOLD}Data Stores:{C.RESET}")
    try:
        from antigravity.knowledge_store import KnowledgeStore
        ks = KnowledgeStore()
        items = ks.search("")
        print(f"    {C.ok(f'Knowledge Store: {len(items)} items')}")
    except Exception as e:
        print(f"    {C.fail(f'Knowledge Store: {e}')}")
        issues.append(f"Knowledge Store error: {e}")

    # 5. Check .env
    print(f"\n  {C.BOLD}Configuration:{C.RESET}")
    env_path = ROOT / ".env"
    if env_path.exists():
        lines = [l for l in env_path.read_text().splitlines() if l.strip() and not l.startswith("#")]
        print(f"    {C.ok(f'.env: {len(lines)} entries')}")
    else:
        print(f"    {C.fail('.env: missing!')}")
        issues.append(".env file missing")

    # 6. Summary
    print(C.head("HEALTH SUMMARY"))
    if not issues:
        print(f"  {C.GREEN}{C.BOLD}ALL SYSTEMS HEALTHY{C.RESET}")
    else:
        print(f"  {C.YELLOW}{C.BOLD}{len(issues)} ISSUE(S) FOUND:{C.RESET}")
        for issue in issues:
            print(f"    {C.fail(issue)}")
        print(f"\n  {C.info('Run: python3 empire_boot.py repair')}")

    return issues


# ═══════════════════════════════════════════════════════════════════
# AUTO-REPAIR
# ═══════════════════════════════════════════════════════════════════

def auto_repair():
    """Auto-repair common issues."""
    print(C.head("AUTO-REPAIR"))
    fixed = 0

    # 1. Ensure .env exists with defaults
    env_path = ROOT / ".env"
    if not env_path.exists():
        print(f"  {C.info('Creating .env with defaults...')}")
        env_path.write_text("""# AI Empire Configuration
# ────────────────────────
GOOGLE_CLOUD_PROJECT=ai-empire-486415
GOOGLE_CLOUD_REGION=europe-west4
VERTEX_AI_ENABLED=false
OFFLINE_MODE=false
OLLAMA_BASE_URL=http://localhost:11434

# API Keys (add yours here)
# GEMINI_API_KEY=
# MOONSHOT_API_KEY=
# KIMI_API_KEY=
# OPENROUTER_API_KEY=
# GROQ_API_KEY=
""")
        fixed += 1
        print(f"  {C.ok('.env created')}")

    # 2. Ensure critical directories exist
    for d in ["empire_data", "empire_data/scans", "empire_data/content",
              "empire_data/leads", "empire_data/revenue",
              "antigravity/_knowledge", "antigravity/_state", "antigravity/_reports"]:
        path = ROOT / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            fixed += 1
            print(f"  {C.ok(f'Created: {d}/')}")

    # 3. Check for __init__.py in all packages
    for pkg in ["antigravity", "workflow_system", "brain_system", "kimi_swarm",
                "x_lead_machine", "atomic_reactor", "empire_api", "crm"]:
        init_path = ROOT / pkg / "__init__.py"
        if (ROOT / pkg).exists() and not init_path.exists():
            init_path.write_text(f'"""Package: {pkg}"""\n')
            fixed += 1
            print(f"  {C.ok(f'Created: {pkg}/__init__.py')}")

    # 4. Fix git if needed
    lock_path = ROOT / ".git" / "index.lock"
    if lock_path.exists():
        lock_path.unlink()
        fixed += 1
        print(f"  {C.ok('Removed stale git index.lock')}")

    # 5. Compile check (syntax errors)
    print(f"\n  {C.info('Running syntax check...')}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "compileall", str(ROOT), "-q"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"  {C.ok('All Python files compile correctly')}")
        else:
            print(f"  {C.warn('Some files have syntax issues:')}")
            print(f"    {C.DIM}{result.stderr[:300]}{C.RESET}")
    except Exception:
        pass

    print(C.head("REPAIR SUMMARY"))
    print(f"  {C.BOLD}Fixed {fixed} issue(s){C.RESET}")
    if fixed == 0:
        print(f"  {C.GREEN}System is clean — no repairs needed.{C.RESET}")


# ═══════════════════════════════════════════════════════════════════
# AGENT SWARM LAUNCHER
# ═══════════════════════════════════════════════════════════════════

async def launch_agents():
    """Launch the autonomous agent swarm."""
    print(C.head("AGENT SWARM LAUNCHER"))

    # Check if Ollama is available
    ollama = check_ollama()
    if not ollama["available"]:
        print(f"  {C.fail('Ollama not available — agents need AI models')}")
        print(f"  {C.info('Start Ollama first: ollama serve')}")
        return

    acount = ollama["count"]
    print(f"  {C.ok(f'Ollama ready with {acount} models')}")

    # Initialize agent system
    agents = {
        "scanner": {
            "role": "Scans news, trends, and opportunities",
            "model": "qwen2.5-coder:7b",
            "system": "Du bist ein Research Agent. Scanne nach AI & BMA Trends. Output als JSON.",
        },
        "producer": {
            "role": "Creates content for all platforms",
            "model": "qwen2.5-coder:7b",
            "system": "Du bist ein Content Creator Agent. Erstelle viralen Content. Output als JSON.",
        },
        "architect": {
            "role": "Plans and reviews code architecture",
            "model": "qwen2.5-coder:7b",
            "system": "Du bist ein Software Architect Agent. Plane und reviewe Code-Architektur.",
        },
        "fixer": {
            "role": "Finds and fixes bugs automatically",
            "model": "qwen2.5-coder:7b",
            "system": "Du bist ein Bug Fixer Agent. Finde und fixe Bugs. Minimal-invasiv.",
        },
    }

    print(f"\n  {C.BOLD}Available Agents:{C.RESET}")
    for name, info in agents.items():
        print(f"    {C.CYAN}• {name}{C.RESET}: {info['role']}")

    print(f"\n  {C.info('Agents ready. Use empire_engine.py for full autonomous cycle.')}")
    print(f"  {C.DIM}python3 empire_engine.py auto{C.RESET}")


# ═══════════════════════════════════════════════════════════════════
# ASK AI (Interactive)
# ═══════════════════════════════════════════════════════════════════

async def ask_ai(question: str, prefer: str = "auto"):
    """Ask a question to the AI chain."""
    print(f"\n  {C.CYAN}Question:{C.RESET} {question}")
    print(f"  {C.DIM}Routing...{C.RESET}")

    result = await smart_query(
        prompt=question,
        system="Du bist ein hilfreicher AI-Assistent im Empire System von Maurice Pfeifer. Antworte praezise und strukturiert.",
        prefer=prefer,
    )

    if result["success"]:
        print(f"\n  {C.GREEN}Provider:{C.RESET} {result['provider']} ({result['model']})")
        print(f"  {C.GREEN}Tokens:{C.RESET} {result['tokens']}")
        print(f"\n{result['content']}\n")
    else:
        print(f"\n  {C.fail(result['content'])}")


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_status()
        return

    cmd = sys.argv[1].lower()

    if cmd == "start":
        start_services()
    elif cmd == "stop":
        stop_services()
    elif cmd == "health":
        asyncio.run(deep_health_check())
    elif cmd == "repair":
        auto_repair()
    elif cmd == "agents":
        asyncio.run(launch_agents())
    elif cmd == "status":
        show_status()
    elif cmd == "ask":
        question = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Was ist der aktuelle Status?"
        prefer = "auto"
        asyncio.run(ask_ai(question, prefer))
    elif cmd == "auto":
        print(C.head("AUTONOMOUS CYCLE"))
        print(f"  {C.info('Redirecting to empire_engine.py auto...')}")
        os.execvp(sys.executable, [sys.executable, str(ROOT / "empire_engine.py"), "auto"])
    elif cmd == "revenue":
        print(C.head("REVENUE DASHBOARD"))
        print(f"  {C.info('Redirecting to empire_engine.py revenue...')}")
        os.execvp(sys.executable, [sys.executable, str(ROOT / "empire_engine.py"), "revenue"])
    else:
        print(f"  {C.fail(f'Unknown command: {cmd}')}")
        print(f"  {C.info('Available: start, stop, health, repair, agents, status, ask, auto, revenue')}")


if __name__ == "__main__":
    main()
