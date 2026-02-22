"""
Antigravity Configuration
==========================
Central config for all 4 Godmode Programmer agents + Ollama routing.
Auto-loads .env file for reliable config after system restarts/crashes.
"""

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# ─── Auto-Load .env ─────────────────────────────────────────────────
# This ensures env vars survive crashes, reboots, and terminal resets.
def _load_dotenv():
    """Load .env file from project root without requiring python-dotenv."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Only set if not already in environment (env vars take priority)
            if key and key not in os.environ:
                os.environ[key] = value
    except (FileNotFoundError, UnicodeDecodeError) as e:
        # Log but don't crash - .env issues are non-fatal
        import warnings
        warnings.warn(f"Failed to load .env file: {e}", stacklevel=2)

_load_dotenv()

# ─── Ollama Connection ──────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_V1 = f"{OLLAMA_BASE_URL}/v1"  # OpenAI-compatible endpoint

# ─── Google Gemini Connection ───────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ─── Anthropic / Claude Connection ──────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─── Kimi / Moonshot Connection ──────────────────────────────────────
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
KIMI_API_KEY = MOONSHOT_API_KEY  # alias

def _gcloud_project():
    try:
        out = subprocess.check_output(
            ["gcloud", "config", "get-value", "project"],
            stderr=subprocess.DEVNULL, text=True, timeout=5
        ).strip()
        return out if out and out != "(unset)" else ""
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        # gcloud not installed or timed out - this is expected in offline mode
        return ""
    except Exception as e:
        # Log unexpected errors but still return empty (graceful degradation)
        import warnings
        warnings.warn(f"Unexpected error querying gcloud project: {e}", stacklevel=2)
        return ""

GOOGLE_CLOUD_PROJECT = (
    os.getenv("GOOGLE_CLOUD_PROJECT")
    or os.getenv("GCLOUD_PROJECT")
    or os.getenv("PROJECT_ID")
    or _gcloud_project()
)
if not GOOGLE_CLOUD_PROJECT:
    # Soft fallback instead of hard crash - allows offline mode to work
    import warnings
    warnings.warn(
        "Missing GCP project id. Set GOOGLE_CLOUD_PROJECT in .env or run: "
        "gcloud config set project <id>. Gemini/Vertex AI will be disabled."
    )
    GOOGLE_CLOUD_PROJECT = ""

GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION", "europe-west4")
VERTEX_AI_ENABLED = os.getenv("VERTEX_AI_ENABLED", "false").lower() == "true"
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "false").lower() in ("1", "true", "yes")

# ─── Model Selection (optimized for 16GB RAM) ──────────────────────
# Local models (Ollama)
DEFAULT_MODEL_14B = "qwen2.5-coder:14b"
DEFAULT_MODEL_7B = "qwen2.5-coder:7b"
REASONING_MODEL = "deepseek-r1:7b"
CODE_MODEL = "codellama:7b"

# Cloud models (Gemini)
GEMINI_FLASH = "gemini-2.0-flash"
GEMINI_PRO = "gemini-2.0-pro"
GEMINI_FLASH_THINKING = "gemini-2.0-flash-thinking"

# ─── HTTP Timeout Constants (seconds) ─────────────────────────────
# Standardized across all HTTP clients to prevent timeout chaos
TIMEOUT_HEALTH_CHECK = 3       # Quick alive/dead checks
TIMEOUT_QUICK_OP = 10          # Model listing, status queries
TIMEOUT_STANDARD = 60          # Normal API requests
TIMEOUT_GENERATION = 120       # LLM text generation (Gemini, Kimi)
TIMEOUT_OLLAMA_GENERATE = 300  # Ollama local generation (slow on CPU)
TIMEOUT_STREAMING = 300        # Streaming responses (long-running)

# ─── Project Paths ──────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANTIGRAVITY_DIR = os.path.join(PROJECT_ROOT, "antigravity")
REPORTS_DIR = os.path.join(ANTIGRAVITY_DIR, "_reports")
SCRIPTS_DIR = os.path.join(ANTIGRAVITY_DIR, "scripts")
ISSUES_FILE = os.path.join(ANTIGRAVITY_DIR, "ISSUES.json")
KANBAN_FILE = os.path.join(ANTIGRAVITY_DIR, "ISSUES_KANBAN.md")
STRUCTURE_MAP_JSON = os.path.join(ANTIGRAVITY_DIR, "STRUCTURE_MAP.json")
STRUCTURE_MAP_HTML = os.path.join(ANTIGRAVITY_DIR, "STRUCTURE_MAP.html")

# ─── Branch Naming ──────────────────────────────────────────────────
BRANCH_PREFIX = {
    "architect": "agent/architect",
    "fixer": "agent/fixer",
    "coder": "agent/coder",
    "qa": "agent/qa",
}

# ─── Merge Gate Rules ───────────────────────────────────────────────
MERGE_CHECKS = [
    "python3 -m compileall . -q",
    "ruff check . --select E,F,I --quiet",
    "pytest -q --tb=short --no-header 2>/dev/null || true",
]


@dataclass
class AgentConfig:
    """Configuration for a single Godmode Programmer agent."""

    name: str
    role: str
    model: str
    system_prompt: str
    temperature: float = 0.2
    max_tokens: int = 4096
    branch_prefix: str = ""
    focus_files: list = field(default_factory=list)

    def __post_init__(self):
        if not self.branch_prefix:
            self.branch_prefix = BRANCH_PREFIX.get(self.name.lower(), f"agent/{self.name.lower()}")


# ─── The 4 Godmode Programmer Agents ────────────────────────────────

ARCHITECT = AgentConfig(
    name="Architect",
    role="architect",
    model=DEFAULT_MODEL_14B,
    system_prompt="""Du bist der ARCHITECT Agent im Godmode Programmer System.
Deine Aufgaben:
- Repo-Struktur analysieren und optimieren
- API-Design und Interface-Definitionen
- Refactoring-Entscheidungen treffen
- Dependency-Management
- Architektur-Dokumentation

REGELN:
- Du änderst NIE Implementierungsdetails, nur Struktur/Interfaces
- Du arbeitest IMMER in deiner eigenen Branch
- Jede Änderung muss begründet und dokumentiert sein
- Output IMMER als strukturiertes JSON mit: {action, files, reason, tests_needed}
""",
    temperature=0.1,
    max_tokens=8192,
)

FIXER = AgentConfig(
    name="Fixer",
    role="fixer",
    model=DEFAULT_MODEL_14B,
    system_prompt="""Du bist der FIXER Agent im Godmode Programmer System.
Deine Aufgaben:
- Bugs fixen basierend auf Tracebacks
- Import-Fehler beheben
- NoneType/Init-Order Probleme lösen
- Edge-Cases abfangen
- Fehlende Dependencies identifizieren

REGELN:
- Du bekommst IMMER einen konkreten Fehler + Traceback
- Fix muss minimal-invasiv sein (kleinster möglicher Patch)
- NIEMALS Features hinzufügen, NUR Bugs fixen
- Output als: {file, original_code, fixed_code, explanation, test_command}
""",
    temperature=0.1,
    max_tokens=4096,
)

CODER = AgentConfig(
    name="Coder",
    role="coder",
    model=DEFAULT_MODEL_7B,  # 7B for speed on feature work
    system_prompt="""Du bist der CODER Agent im Godmode Programmer System.
Deine Aufgaben:
- Feature-Implementierung nach Spezifikation
- Schnelle Iteration und Prototyping
- Code nach vorgegebenen Interfaces schreiben
- Utility-Funktionen und Helpers

REGELN:
- Du bekommst IMMER eine klare Aufgabe + Scope (Dateien)
- Halte dich EXAKT an vorgegebene Interfaces/APIs
- Schreibe docstrings für jede Funktion
- Output als: {files_created, files_modified, code_blocks, dependencies_needed}
""",
    temperature=0.3,
    max_tokens=8192,
)

QA_REVIEWER = AgentConfig(
    name="QA",
    role="qa",
    model=REASONING_MODEL,  # DeepSeek R1 for thorough review
    system_prompt="""Du bist der QA/REVIEWER Agent im Godmode Programmer System.
Deine Aufgaben:
- Code-Review aller Änderungen
- Test-Erstellung und Ausführung
- Lint-Checks (ruff) durchführen
- Sicherheits-Review
- Regressions-Check

REGELN:
- Du bekommst IMMER einen Diff + aktuelle Testausgabe
- JEDE Änderung braucht mindestens einen Test
- Merge-Block wenn: compile fails, lint errors, test regressions
- Output als: {approved: bool, issues: [], tests_added: [], lint_clean: bool}
""",
    temperature=0.1,
    max_tokens=4096,
)

ALL_AGENTS = [ARCHITECT, FIXER, CODER, QA_REVIEWER]

# Dict for lookup by role name (used by godmode_router)
AGENTS: dict[str, AgentConfig] = {
    "architect": ARCHITECT,
    "fixer": FIXER,
    "coder": CODER,
    "qa": QA_REVIEWER,
}

# ─── Mode Configurations ────────────────────────────────────────────

MODES = {
    "fix-first": {
        "description": "Fix all bugs before adding features",
        "order": ["fixer", "qa", "architect", "coder"],
        "parallel": False,
    },
    "feature-sprint": {
        "description": "Rapid feature development with QA gate",
        "order": ["architect", "coder", "qa", "fixer"],
        "parallel": False,
    },
    "review-all": {
        "description": "Review everything, fix nothing automatically",
        "order": ["qa"],
        "parallel": False,
    },
    "full-parallel": {
        "description": "All agents work simultaneously (needs >=32GB RAM)",
        "order": ["architect", "fixer", "coder", "qa"],
        "parallel": True,
    },
}
