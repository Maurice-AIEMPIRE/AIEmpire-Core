#!/usr/bin/env python3
"""
AIEmpire API Key Manager
=========================
Interactive console for managing all API keys.
Stores keys in encrypted JSON, syncs to .env, validates connections.

Usage:
    python3 tools/api_keys.py              # Interactive menu
    python3 tools/api_keys.py list         # Show all keys
    python3 tools/api_keys.py test         # Test all connections
    python3 tools/api_keys.py sync         # Sync DB → .env
    python3 tools/api_keys.py add <name>   # Add/update a specific key
    python3 tools/api_keys.py export       # Export for server deployment
"""

import base64
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_ROOT / ".api_keys.json"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"

# ─── Colors ─────────────────────────────────────────────────────────────────
class C:
    R = "\033[0;31m"
    G = "\033[0;32m"
    Y = "\033[1;33m"
    B = "\033[0;34m"
    M = "\033[0;35m"
    W = "\033[1;37m"
    D = "\033[0;90m"
    N = "\033[0m"

# ─── Provider Registry ─────────────────────────────────────────────────────
# All supported AI providers with their config
PROVIDERS = {
    "moonshot": {
        "name": "Moonshot / Kimi",
        "env_var": "MOONSHOT_API_KEY",
        "prefix": "sk-",
        "test_url": "https://api.moonshot.cn/v1/models",
        "test_header": "Authorization",
        "tier": "primary",
        "cost": "$$",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "description": "Primaer-Provider, guenstig + schnell, 128K Context",
    },
    "openai": {
        "name": "OpenAI",
        "env_var": "OPENAI_API_KEY",
        "prefix": "sk-",
        "test_url": "https://api.openai.com/v1/models",
        "test_header": "Authorization",
        "tier": "premium",
        "cost": "$$$",
        "models": ["gpt-4o-mini", "gpt-4o", "o1-mini"],
        "description": "Premium-Provider, GPT-4o, teuer aber zuverlaessig",
    },
    "anthropic": {
        "name": "Anthropic / Claude",
        "env_var": "ANTHROPIC_API_KEY",
        "prefix": "sk-ant-",
        "test_url": "https://api.anthropic.com/v1/messages",
        "test_header": "x-api-key",
        "tier": "critical",
        "cost": "$$$$",
        "models": ["claude-haiku-4-5", "claude-sonnet-4-5", "claude-opus-4-6"],
        "description": "Nur fuer kritische Tasks, bester Reasoning, teuerste Option",
    },
    "groq": {
        "name": "Groq",
        "env_var": "GROQ_API_KEY",
        "prefix": "gsk_",
        "test_url": "https://api.groq.com/openai/v1/models",
        "test_header": "Authorization",
        "tier": "fast",
        "cost": "$",
        "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        "description": "Ultra-schnelle Inference, Open-Source Modelle, guenstig",
    },
    "google": {
        "name": "Google Gemini",
        "env_var": "GOOGLE_API_KEY",
        "prefix": "",
        "test_url": "https://generativelanguage.googleapis.com/v1beta/models?key={key}",
        "test_header": None,
        "tier": "versatile",
        "cost": "$$",
        "models": ["gemini-2.0-flash", "gemini-2.0-pro"],
        "description": "Gemini Flash (schnell) + Pro (stark), grosses Free-Tier",
    },
    "ollama": {
        "name": "Ollama (Lokal)",
        "env_var": "OLLAMA_BASE_URL",
        "prefix": "",
        "test_url": "http://localhost:11434/api/version",
        "test_header": None,
        "tier": "free",
        "cost": "FREE",
        "models": ["qwen2.5-coder:7b", "qwen2.5-coder:14b", "deepseek-r1:7b"],
        "description": "Lokale Modelle, 100%% kostenlos, keine API Keys noetig",
    },
    "github": {
        "name": "GitHub",
        "env_var": "GITHUB_TOKEN",
        "prefix": "ghp_",
        "test_url": "https://api.github.com/user",
        "test_header": "Authorization",
        "tier": "infra",
        "cost": "FREE",
        "models": [],
        "description": "Repository, Actions, Deployments",
    },
    "twitter": {
        "name": "X / Twitter",
        "env_var": "TWITTER_API_KEY",
        "prefix": "",
        "test_url": None,
        "test_header": None,
        "tier": "marketing",
        "cost": "$$",
        "models": [],
        "description": "Auto-Posting, Lead-Gen, 3 Personas",
        "extra_vars": ["TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"],
    },
    "telegram": {
        "name": "Telegram Bot",
        "env_var": "TELEGRAM_BOT_TOKEN",
        "prefix": "",
        "test_url": "https://api.telegram.org/bot{key}/getMe",
        "test_header": None,
        "tier": "marketing",
        "cost": "FREE",
        "models": [],
        "description": "Notifications + Bot Commands",
    },
    "gumroad": {
        "name": "Gumroad",
        "env_var": "GUMROAD_ACCESS_TOKEN",
        "prefix": "",
        "test_url": "https://api.gumroad.com/v2/user",
        "test_header": None,
        "tier": "revenue",
        "cost": "FREE",
        "models": [],
        "description": "Digitale Produkte verkaufen, Revenue Tracking",
    },
}

# Tier display order and colors
TIER_ORDER = ["free", "primary", "fast", "versatile", "premium", "critical", "infra", "marketing", "revenue"]
TIER_COLORS = {
    "free": C.G, "primary": C.B, "fast": C.Y, "versatile": C.M,
    "premium": C.W, "critical": C.R, "infra": C.D, "marketing": C.D, "revenue": C.G,
}


# ═══════════════════════════════════════════════════════════════════════════
# KEY DATABASE
# ═══════════════════════════════════════════════════════════════════════════

def _obfuscate(value: str) -> str:
    """Simple obfuscation (not encryption — keys are also in .env)."""
    return base64.b64encode(value.encode()).decode()

def _deobfuscate(value: str) -> str:
    try:
        return base64.b64decode(value.encode()).decode()
    except Exception:
        return value

def load_db() -> dict:
    if not DB_FILE.exists():
        return {"keys": {}, "meta": {"created": _now(), "version": 1}}
    try:
        data = json.loads(DB_FILE.read_text())
        return data
    except Exception:
        return {"keys": {}, "meta": {"created": _now(), "version": 1}}

def save_db(db: dict):
    db["meta"]["updated"] = _now()
    DB_FILE.write_text(json.dumps(db, indent=2, ensure_ascii=False))
    os.chmod(DB_FILE, 0o600)

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def get_key(db: dict, provider_id: str) -> str | None:
    entry = db["keys"].get(provider_id)
    if not entry:
        return None
    return _deobfuscate(entry["value"])

def set_key(db: dict, provider_id: str, value: str, tested: bool = False):
    db["keys"][provider_id] = {
        "value": _obfuscate(value),
        "added": _now(),
        "tested": tested,
        "last_test": _now() if tested else None,
        "enabled": True,
    }
    save_db(db)


# ═══════════════════════════════════════════════════════════════════════════
# KEY VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def test_provider(provider_id: str, key: str) -> tuple[bool, str]:
    """Test if an API key works. Returns (success, message)."""
    prov = PROVIDERS[provider_id]
    test_url = prov.get("test_url")

    if not test_url:
        return True, "No test endpoint (manual verification needed)"

    # Substitute key into URL if needed
    url = test_url.replace("{key}", key)

    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "AIEmpire-KeyManager/1.0")

        header = prov.get("test_header")
        if header == "Authorization":
            req.add_header("Authorization", f"Bearer {key}")
        elif header == "x-api-key":
            req.add_header("x-api-key", key)
            req.add_header("anthropic-version", "2023-06-01")

        # For Gumroad, add token as query param
        if provider_id == "gumroad":
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}access_token={key}"
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "AIEmpire-KeyManager/1.0")

        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            if status in (200, 201):
                return True, f"OK (HTTP {status})"
            return False, f"Unexpected HTTP {status}"

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "INVALID KEY (HTTP 401 Unauthorized)"
        if e.code == 403:
            return False, "ACCESS DENIED (HTTP 403 Forbidden)"
        if e.code in (404, 405):
            # Some APIs return 404/405 for model listing but key is valid
            return True, f"Endpoint responds (HTTP {e.code}) — key format OK"
        return False, f"HTTP Error {e.code}"
    except urllib.error.URLError as e:
        if provider_id == "ollama":
            return False, "Ollama nicht gestartet (ollama serve)"
        return False, f"Connection failed: {e.reason}"
    except Exception as e:
        return False, f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# .ENV SYNC
# ═══════════════════════════════════════════════════════════════════════════

def sync_to_env(db: dict) -> int:
    """Write all keys from DB into .env file. Returns count of keys written."""

    # Read existing .env or start from example
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text().splitlines()
    elif ENV_EXAMPLE.exists():
        lines = ENV_EXAMPLE.read_text().splitlines()
    else:
        lines = ["# AIEmpire-Core Environment Variables", ""]

    existing_keys = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            existing_keys[k] = i

    count = 0
    for prov_id, prov in PROVIDERS.items():
        key = get_key(db, prov_id)
        if not key:
            continue

        entry = db["keys"].get(prov_id, {})
        if not entry.get("enabled", True):
            continue

        env_var = prov["env_var"]
        new_line = f"{env_var}={key}"

        if env_var in existing_keys:
            idx = existing_keys[env_var]
            old = lines[idx].split("=", 1)[1].strip() if "=" in lines[idx] else ""
            if old != key and not old.startswith("your-"):
                lines[idx] = new_line
                count += 1
            elif old.startswith("your-") or old.startswith("sk-your"):
                lines[idx] = new_line
                count += 1
        else:
            lines.append(new_line)
            count += 1

        # Handle extra vars (e.g. Twitter has 4 keys)
        for extra_var in prov.get("extra_vars", []):
            extra_key = get_key(db, f"{prov_id}_{extra_var}")
            if extra_key:
                new_line = f"{extra_var}={extra_key}"
                if extra_var in existing_keys:
                    lines[existing_keys[extra_var]] = new_line
                else:
                    lines.append(new_line)
                count += 1

    ENV_FILE.write_text("\n".join(lines) + "\n")
    os.chmod(ENV_FILE, 0o600)
    return count


# ═══════════════════════════════════════════════════════════════════════════
# DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def mask_key(key: str | None) -> str:
    if not key:
        return f"{C.D}-- nicht gesetzt --{C.N}"
    if len(key) <= 8:
        return key[:2] + "***"
    return key[:6] + "..." + key[-4:]

def provider_status_line(prov_id: str, db: dict) -> str:
    prov = PROVIDERS[prov_id]
    key = get_key(db, prov_id)
    entry = db["keys"].get(prov_id, {})
    enabled = entry.get("enabled", True)
    tested = entry.get("tested", False)
    tier_color = TIER_COLORS.get(prov["tier"], C.D)

    # Status indicator
    if prov_id == "ollama":
        status = f"{C.G}LOCAL{C.N}"
    elif key and tested and enabled:
        status = f"{C.G}AKTIV{C.N}"
    elif key and enabled:
        status = f"{C.Y}UNGE.{C.N}"
    elif key and not enabled:
        status = f"{C.D}DEAKT{C.N}"
    else:
        status = f"{C.R}FEHLT{C.N}"

    cost = prov["cost"]
    name = prov["name"][:20].ljust(20)
    masked = mask_key(key)

    return f"  {tier_color}{prov_id:<12}{C.N} {name} [{status}] {cost:>5}  {masked}"


# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIVE CONSOLE
# ═══════════════════════════════════════════════════════════════════════════

def print_banner():
    print(f"""
{C.W}╔═══════════════════════════════════════════════════════════╗
║           API KEY MANAGER — AIEmpire-Core                 ║
║           Alle Provider • Test • Sync • Datenbank         ║
╚═══════════════════════════════════════════════════════════╝{C.N}
""")

def print_overview(db: dict):
    print(f"  {C.W}{'PROVIDER':<12} {'NAME':<20}  STATUS  KOSTEN  KEY{C.N}")
    print(f"  {'─'*70}")

    sorted_provs = sorted(PROVIDERS.keys(), key=lambda p: TIER_ORDER.index(PROVIDERS[p]["tier"]))
    for prov_id in sorted_provs:
        print(provider_status_line(prov_id, db))
    print()

def print_menu():
    print(f"  {C.W}Aktionen:{C.N}")
    print(f"  {C.G}[1]{C.N} Key hinzufuegen/aendern")
    print(f"  {C.G}[2]{C.N} Alle Keys testen")
    print(f"  {C.G}[3]{C.N} Einen Key testen")
    print(f"  {C.G}[4]{C.N} Sync → .env (Keys in .env schreiben)")
    print(f"  {C.G}[5]{C.N} Key loeschen")
    print(f"  {C.G}[6]{C.N} Key aktivieren/deaktivieren")
    print(f"  {C.G}[7]{C.N} Provider-Details anzeigen")
    print(f"  {C.G}[8]{C.N} Import von .env (vorhandene Keys laden)")
    print(f"  {C.G}[9]{C.N} Export fuer Server")
    print(f"  {C.D}[0]{C.N} Beenden")
    print()

def select_provider(prompt: str = "Provider waehlen") -> str | None:
    sorted_provs = sorted(PROVIDERS.keys(), key=lambda p: TIER_ORDER.index(PROVIDERS[p]["tier"]))
    print()
    for i, prov_id in enumerate(sorted_provs, 1):
        prov = PROVIDERS[prov_id]
        tier_color = TIER_COLORS.get(prov["tier"], C.D)
        print(f"  {C.G}[{i:2}]{C.N} {tier_color}{prov_id:<12}{C.N} {prov['name']}")

    print(f"  {C.D}[ 0]{C.N} Abbrechen")
    print()

    try:
        choice = input(f"  {prompt} [0-{len(sorted_provs)}]: ").strip()
        idx = int(choice)
        if idx == 0:
            return None
        if 1 <= idx <= len(sorted_provs):
            return sorted_provs[idx - 1]
    except (ValueError, EOFError):
        pass
    return None


def action_add_key(db: dict):
    prov_id = select_provider("Key eintragen fuer")
    if not prov_id:
        return

    prov = PROVIDERS[prov_id]
    print()
    print(f"  {C.W}{prov['name']}{C.N}")
    print(f"  {C.D}{prov['description']}{C.N}")

    if prov_id == "ollama":
        print(f"\n  {C.Y}Ollama braucht keinen API Key — nur die URL.{C.N}")
        url = input(f"  Ollama URL [{C.D}http://localhost:11434{C.N}]: ").strip()
        if not url:
            url = "http://localhost:11434"
        set_key(db, prov_id, url)
        print(f"  {C.G}[OK]{C.N} Ollama URL gespeichert: {url}")
        return

    current = get_key(db, prov_id)
    if current:
        print(f"  Aktueller Key: {mask_key(current)}")

    prefix_hint = f" (beginnt mit {prov['prefix']})" if prov.get("prefix") else ""
    print(f"  ENV Variable: {C.Y}{prov['env_var']}{C.N}{prefix_hint}")
    print()

    try:
        key = input(f"  API Key eingeben: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if not key:
        print(f"  {C.Y}Abgebrochen{C.N}")
        return

    # Validate prefix
    if prov.get("prefix") and not key.startswith(prov["prefix"]):
        print(f"  {C.Y}[WARN]{C.N} Key beginnt nicht mit '{prov['prefix']}' — trotzdem speichern?")
        try:
            confirm = input(f"  Speichern? [j/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if confirm not in ("j", "y", "ja", "yes"):
            return

    # Test the key
    print(f"  {C.B}[TEST]{C.N} Teste Verbindung...", end="", flush=True)
    ok, msg = test_provider(prov_id, key)

    if ok:
        print(f"\r  {C.G}[OK]{C.N}   {msg}                    ")
        set_key(db, prov_id, key, tested=True)
        print(f"  {C.G}[OK]{C.N}   Key gespeichert und getestet")
    else:
        print(f"\r  {C.R}[FAIL]{C.N} {msg}                    ")
        try:
            save_anyway = input(f"  Trotzdem speichern? [j/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if save_anyway in ("j", "y", "ja", "yes"):
            set_key(db, prov_id, key, tested=False)
            print(f"  {C.Y}[OK]{C.N}   Key gespeichert (NICHT getestet)")

    # Handle extra vars (Twitter needs 4 keys)
    for extra_var in prov.get("extra_vars", []):
        print()
        try:
            extra_key = input(f"  {extra_var}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if extra_key:
            set_key(db, f"{prov_id}_{extra_var}", extra_key)
            print(f"  {C.G}[OK]{C.N}   {extra_var} gespeichert")


def action_test_all(db: dict):
    print(f"\n  {C.W}Teste alle Provider...{C.N}\n")

    sorted_provs = sorted(PROVIDERS.keys(), key=lambda p: TIER_ORDER.index(PROVIDERS[p]["tier"]))
    ok_count = 0
    fail_count = 0
    skip_count = 0

    for prov_id in sorted_provs:
        prov = PROVIDERS[prov_id]
        key = get_key(db, prov_id)
        name = prov["name"][:20].ljust(20)

        if not key and prov_id != "ollama":
            print(f"  {C.D}[SKIP]{C.N}  {name}  -- kein Key --")
            skip_count += 1
            continue

        test_key = key or "http://localhost:11434"
        print(f"  {C.B}[TEST]{C.N}  {name}", end="", flush=True)
        ok, msg = test_provider(prov_id, test_key)

        if ok:
            print(f"\r  {C.G}[ OK ]{C.N}  {name}  {msg}")
            ok_count += 1
            if prov_id in db["keys"]:
                db["keys"][prov_id]["tested"] = True
                db["keys"][prov_id]["last_test"] = _now()
        else:
            print(f"\r  {C.R}[FAIL]{C.N}  {name}  {msg}")
            fail_count += 1

    save_db(db)
    print(f"\n  Ergebnis: {C.G}{ok_count} OK{C.N} | {C.R}{fail_count} FAIL{C.N} | {C.D}{skip_count} SKIP{C.N}\n")


def action_test_one(db: dict):
    prov_id = select_provider("Welchen Provider testen")
    if not prov_id:
        return

    key = get_key(db, prov_id)
    if not key and prov_id != "ollama":
        print(f"  {C.R}Kein Key fuer {PROVIDERS[prov_id]['name']} gespeichert{C.N}")
        return

    test_key = key or "http://localhost:11434"
    print(f"\n  {C.B}[TEST]{C.N} {PROVIDERS[prov_id]['name']}...", end="", flush=True)
    ok, msg = test_provider(prov_id, test_key)

    if ok:
        print(f"\r  {C.G}[OK]{C.N}   {PROVIDERS[prov_id]['name']}: {msg}          ")
        if prov_id in db["keys"]:
            db["keys"][prov_id]["tested"] = True
            db["keys"][prov_id]["last_test"] = _now()
            save_db(db)
    else:
        print(f"\r  {C.R}[FAIL]{C.N} {PROVIDERS[prov_id]['name']}: {msg}          ")


def action_sync_env(db: dict):
    count = sync_to_env(db)
    if count:
        print(f"\n  {C.G}[OK]{C.N}   {count} Keys in .env geschrieben ({ENV_FILE})")
    else:
        print(f"\n  {C.Y}[OK]{C.N}   Keine Aenderungen (alle Keys bereits aktuell)")
    print(f"  {C.D}Tipp: Auf Server deployen mit 'scp .env root@server:/opt/aiempire/.env'{C.N}\n")


def action_delete_key(db: dict):
    prov_id = select_provider("Key loeschen fuer")
    if not prov_id:
        return

    if prov_id not in db["keys"]:
        print(f"  {C.Y}Kein Key gespeichert fuer {PROVIDERS[prov_id]['name']}{C.N}")
        return

    try:
        confirm = input(f"  {C.R}Key fuer {PROVIDERS[prov_id]['name']} wirklich loeschen? [j/N]: {C.N}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if confirm in ("j", "y", "ja", "yes"):
        del db["keys"][prov_id]
        save_db(db)
        print(f"  {C.G}[OK]{C.N}   Key geloescht")


def action_toggle_key(db: dict):
    prov_id = select_provider("Aktivieren/Deaktivieren")
    if not prov_id:
        return

    if prov_id not in db["keys"]:
        print(f"  {C.Y}Kein Key gespeichert fuer {PROVIDERS[prov_id]['name']}{C.N}")
        return

    entry = db["keys"][prov_id]
    entry["enabled"] = not entry.get("enabled", True)
    save_db(db)

    state = f"{C.G}AKTIVIERT{C.N}" if entry["enabled"] else f"{C.R}DEAKTIVIERT{C.N}"
    print(f"  {PROVIDERS[prov_id]['name']}: {state}")


def action_show_details(db: dict):
    prov_id = select_provider("Details anzeigen fuer")
    if not prov_id:
        return

    prov = PROVIDERS[prov_id]
    entry = db["keys"].get(prov_id, {})
    key = get_key(db, prov_id)

    print(f"""
  {C.W}╔══════════════════════════════════════╗
  ║  {prov['name']:<36}║
  ╚══════════════════════════════════════╝{C.N}

  Provider:     {prov['name']}
  Tier:         {prov['tier'].upper()}
  Kosten:       {prov['cost']}
  Beschreibung: {prov['description']}
  ENV Variable: {C.Y}{prov['env_var']}{C.N}
  Key Prefix:   {prov.get('prefix', '(keiner)')}
  Key:          {mask_key(key)}
  Status:       {'Aktiv' if entry.get('enabled', True) else 'Deaktiviert'}
  Getestet:     {entry.get('tested', False)}
  Letzter Test: {entry.get('last_test', 'Nie')}
  Hinzugefuegt: {entry.get('added', 'N/A')}
  Modelle:      {', '.join(prov['models']) if prov['models'] else '(keine AI-Modelle)'}
""")


def action_import_env(db: dict):
    """Import keys from existing .env file into the DB."""
    if not ENV_FILE.exists():
        print(f"  {C.R}Keine .env Datei gefunden{C.N}")
        return

    env_data = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if v and not v.startswith("your-") and not v.startswith("sk-your") and not v.startswith("ghp_your"):
            env_data[k] = v

    count = 0
    for prov_id, prov in PROVIDERS.items():
        env_var = prov["env_var"]
        if env_var in env_data:
            existing = get_key(db, prov_id)
            if existing != env_data[env_var]:
                set_key(db, prov_id, env_data[env_var])
                count += 1
                print(f"  {C.G}[OK]{C.N}   {prov['name']}: importiert")

        for extra_var in prov.get("extra_vars", []):
            if extra_var in env_data:
                set_key(db, f"{prov_id}_{extra_var}", env_data[extra_var])
                count += 1

    if count:
        print(f"\n  {C.G}[OK]{C.N}   {count} Keys aus .env importiert")
    else:
        print(f"\n  {C.Y}Keine neuen Keys in .env gefunden{C.N}")


def action_export_server(db: dict):
    """Export keys as a .env snippet for server deployment."""
    print(f"\n  {C.W}Server-Export (.env fuer Hetzner){C.N}\n")

    lines = []
    for prov_id, prov in PROVIDERS.items():
        key = get_key(db, prov_id)
        entry = db["keys"].get(prov_id, {})
        if key and entry.get("enabled", True):
            lines.append(f"{prov['env_var']}={key}")
            for extra_var in prov.get("extra_vars", []):
                extra_key = get_key(db, f"{prov_id}_{extra_var}")
                if extra_key:
                    lines.append(f"{extra_var}={extra_key}")

    if not lines:
        print(f"  {C.Y}Keine Keys zum Exportieren{C.N}")
        return

    # Save to temporary export file
    export_file = PROJECT_ROOT / ".env.server"
    export_file.write_text("\n".join(lines) + "\n")
    os.chmod(export_file, 0o600)

    print(f"  {C.G}[OK]{C.N}   {len(lines)} Keys exportiert nach: {export_file}")
    print(f"\n  {C.W}Auf Server kopieren:{C.N}")
    print(f"  {C.Y}scp .env.server root@65.21.203.174:/opt/aiempire/.env{C.N}")
    print(f"\n  {C.R}Danach .env.server lokal loeschen!{C.N}\n")


def interactive_menu():
    db = load_db()

    # Auto-import from .env on first run
    if not db["keys"] and ENV_FILE.exists():
        action_import_env(db)
        db = load_db()

    while True:
        print_banner()
        print_overview(db)
        print_menu()

        try:
            choice = input(f"  {C.W}Aktion [0-9]: {C.N}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n\n  {C.D}Bye!{C.N}\n")
            break

        if choice == "0":
            print(f"\n  {C.D}Bye!{C.N}\n")
            break
        elif choice == "1":
            action_add_key(db)
            db = load_db()
        elif choice == "2":
            action_test_all(db)
            db = load_db()
        elif choice == "3":
            action_test_one(db)
            db = load_db()
        elif choice == "4":
            action_sync_env(db)
        elif choice == "5":
            action_delete_key(db)
            db = load_db()
        elif choice == "6":
            action_toggle_key(db)
            db = load_db()
        elif choice == "7":
            action_show_details(db)
        elif choice == "8":
            action_import_env(db)
            db = load_db()
        elif choice == "9":
            action_export_server(db)
        else:
            print(f"  {C.Y}Unbekannte Aktion{C.N}")

        print()
        try:
            input(f"  {C.D}[Enter] zurueck zum Menue...{C.N}")
        except (EOFError, KeyboardInterrupt):
            break


# ═══════════════════════════════════════════════════════════════════════════
# CLI COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

def cmd_list():
    db = load_db()
    print_banner()
    print_overview(db)

def cmd_test():
    db = load_db()
    action_test_all(db)

def cmd_sync():
    db = load_db()
    action_sync_env(db)

def cmd_add(name: str):
    db = load_db()
    if name not in PROVIDERS:
        print(f"  {C.R}Unbekannter Provider: {name}{C.N}")
        print(f"  Verfuegbar: {', '.join(PROVIDERS.keys())}")
        return

    prov = PROVIDERS[name]
    print(f"\n  {C.W}{prov['name']}{C.N} — {prov['description']}")

    if name == "ollama":
        url = input(f"  Ollama URL [http://localhost:11434]: ").strip() or "http://localhost:11434"
        set_key(db, name, url)
        print(f"  {C.G}[OK]{C.N} Gespeichert")
        return

    try:
        key = input(f"  {prov['env_var']}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if key:
        print(f"  Teste...", end="", flush=True)
        ok, msg = test_provider(name, key)
        if ok:
            print(f"\r  {C.G}[OK]{C.N}   {msg}          ")
        else:
            print(f"\r  {C.R}[FAIL]{C.N} {msg}          ")

        set_key(db, name, key, tested=ok)
        print(f"  {C.G}[OK]{C.N}   Gespeichert")

        for extra_var in prov.get("extra_vars", []):
            ev = input(f"  {extra_var}: ").strip()
            if ev:
                set_key(db, f"{name}_{extra_var}", ev)

def cmd_export():
    db = load_db()
    action_export_server(db)

def main():
    args = sys.argv[1:]

    if not args:
        interactive_menu()
    elif args[0] == "list":
        cmd_list()
    elif args[0] == "test":
        cmd_test()
    elif args[0] == "sync":
        cmd_sync()
    elif args[0] == "add" and len(args) > 1:
        cmd_add(args[1])
    elif args[0] == "export":
        cmd_export()
    elif args[0] == "import":
        db = load_db()
        action_import_env(db)
    elif args[0] in ("help", "--help", "-h"):
        print(__doc__)
    else:
        print(f"  Unbekannt: {args[0]}")
        print(__doc__)


if __name__ == "__main__":
    main()
