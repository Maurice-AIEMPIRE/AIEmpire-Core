"""
Centralized Environment Configuration & Validation.

Provides a single source of truth for all API keys, endpoints, and settings.
Import this module instead of calling os.getenv() directly.

Usage:
    from config.env_config import get_api_key, get_config, validate_env

    # Get a specific API key (returns "" if not set)
    key = get_api_key("MOONSHOT_API_KEY")

    # Get full config dict
    cfg = get_config()

    # Validate required vars (raises ValueError if missing)
    validate_env(require=["MOONSHOT_API_KEY"])
"""

import os
from typing import Optional

# ── API Endpoints (canonical, single source of truth) ──────────────────────
MOONSHOT_API_URL = "https://api.moonshot.ai/v1/chat/completions"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ── All Known Environment Variables ────────────────────────────────────────
_ENV_REGISTRY = {
    # API Keys
    "MOONSHOT_API_KEY": {
        "description": "Kimi/Moonshot API key for cloud inference",
        "required": False,  # Not required if running fully local
    },
    "ANTHROPIC_API_KEY": {
        "description": "Anthropic/Claude API key (fallback for critical tasks)",
        "required": False,
    },
    "GITHUB_TOKEN": {
        "description": "GitHub API token for issue/PR management",
        "required": False,
    },
    # Connection URLs
    "OLLAMA_BASE_URL": {
        "description": "Ollama server URL (default: http://localhost:11434)",
        "required": False,
        "default": "http://localhost:11434",
    },
    "IPAD_LLM_URL": {
        "description": "iPad compute node URL",
        "required": False,
        "default": "http://192.168.178.45:3000/v1",
    },
    # Repository
    "GITHUB_REPO": {
        "description": "GitHub repository (owner/name)",
        "required": False,
        "default": "mauricepfeifer-ctrl/AIEmpire-Core",
    },
    # X/Twitter
    "TWITTER_API_KEY": {"description": "Twitter/X API key", "required": False},
    "TWITTER_API_SECRET": {"description": "Twitter/X API secret", "required": False},
    "TWITTER_ACCESS_TOKEN": {"description": "Twitter/X access token", "required": False},
    "TWITTER_ACCESS_SECRET": {"description": "Twitter/X access secret", "required": False},
    # Telegram
    "TELEGRAM_BOT_TOKEN": {"description": "Telegram bot token", "required": False},
}


def get_api_key(name: str) -> str:
    """Get an API key from environment, returns empty string if not set."""
    return os.getenv(name, "")


def get_config() -> dict:
    """Get full configuration dict with all known variables and their values."""
    config = {}
    for var_name, var_info in _ENV_REGISTRY.items():
        default = var_info.get("default", "")
        config[var_name] = {
            "value": os.getenv(var_name, default),
            "is_set": bool(os.getenv(var_name)),
            "description": var_info["description"],
        }
    # Add canonical endpoints
    config["_endpoints"] = {
        "moonshot": MOONSHOT_API_URL,
        "anthropic": ANTHROPIC_API_URL,
        "ollama": OLLAMA_BASE_URL,
    }
    return config


def validate_env(require: Optional[list] = None, warn: bool = True) -> bool:
    """
    Validate environment variables.

    Args:
        require: List of variable names that MUST be set. Raises ValueError if missing.
        warn: If True, print warnings for unset optional variables.

    Returns:
        True if all required variables are set.

    Raises:
        ValueError: If any required variable is missing.
    """
    missing = []
    if require:
        for var in require:
            if not os.getenv(var):
                desc = _ENV_REGISTRY.get(var, {}).get("description", "unknown")
                missing.append(f"  {var}: {desc}")

    if missing:
        raise ValueError(
            "Missing required environment variables:\n"
            + "\n".join(missing)
            + "\n\nSee .env.example for setup instructions."
        )

    if warn:
        for var_name, var_info in _ENV_REGISTRY.items():
            if not os.getenv(var_name) and var_info.get("required"):
                print(f"⚠️  {var_name} not set: {var_info['description']}")

    return True


def print_config_status():
    """Print a formatted status of all configuration variables."""
    print("═" * 60)
    print("  AIEmpire-Core Configuration Status")
    print("═" * 60)
    for var_name, var_info in _ENV_REGISTRY.items():
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            if "KEY" in var_name or "TOKEN" in var_name or "SECRET" in var_name:
                display = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "****"
            else:
                display = value
            print(f"  ✅ {var_name}: {display}")
        else:
            default = var_info.get("default", "")
            if default:
                print(f"  ⚡ {var_name}: using default ({default})")
            else:
                print(f"  ❌ {var_name}: not set")
    print("═" * 60)
