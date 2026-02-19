"""
SkyBot Configuration
====================
Central config for the AI agent. Loads from .env.
"""

import os
from pathlib import Path

# ─── Load .env ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent


def _load_env():
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()

# ─── API Keys ──────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_OWNER_ID = os.getenv("TELEGRAM_OWNER_ID", "")
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# ─── Model Config ─────────────────────────────────────────────
CLAUDE_MODEL = os.getenv("SKYBOT_MODEL", "claude-sonnet-4-5-20250929")
MAX_TOKENS = int(os.getenv("SKYBOT_MAX_TOKENS", "4096"))
MAX_TOOL_ROUNDS = int(os.getenv("SKYBOT_MAX_TOOL_ROUNDS", "15"))

# ─── Ollama (local fallback) ──────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

# ─── Workspace ────────────────────────────────────────────────
WORKSPACE_DIR = Path(os.getenv("SKYBOT_WORKSPACE", str(PROJECT_ROOT / "skybot_workspace")))
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# ─── Security ─────────────────────────────────────────────────
# Commands that are NEVER allowed in code execution
BLOCKED_COMMANDS = [
    "rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb",
    "shutdown", "reboot", "halt", "init 0", "init 6",
    "chmod -R 777 /", "chown -R", "> /dev/sda",
]

# Max output length per tool call (chars)
MAX_OUTPUT_LENGTH = 8000

# Max code execution time (seconds)
CODE_EXEC_TIMEOUT = 30

# Max web request time (seconds)
WEB_TIMEOUT = 15
