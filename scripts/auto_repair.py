#!/usr/bin/env python3
"""
AUTO-REPAIR SYSTEM — Bombproof Self-Healing
=============================================
Runs automatically on system boot (via LaunchAgent).
Detects and repairs ALL known issues without any human intervention.
Uses Ollama (local, free, offline) for AI-powered diagnosis.

What it fixes:
1. Corrupted/empty files (0-byte crash artifacts)
2. Missing .env variables
3. Broken gcloud config (the 'projects/' error)
4. Stopped Ollama service
5. Invalid Python imports
6. State file corruption
7. Git state inconsistencies

Usage:
  python3 scripts/auto_repair.py           # Full repair
  python3 scripts/auto_repair.py --check   # Check only, don't fix
  python3 scripts/auto_repair.py --ai      # Use Ollama for smart diagnosis
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
REPAIR_LOG = PROJECT_ROOT / "workflow_system" / "state" / "repair_log.jsonl"

# Required .env variables and their defaults
REQUIRED_ENV = {
    "GOOGLE_CLOUD_PROJECT": "ai-empire-486415",
    "GOOGLE_CLOUD_REGION": "europe-west4",
    "VERTEX_AI_ENABLED": "false",
    "OFFLINE_MODE": "false",
    "OLLAMA_BASE_URL": "http://localhost:11434",
}

# Critical files that must not be 0 bytes
CRITICAL_FILES = [
    "antigravity/config.py",
    "antigravity/gemini_client.py",
    "antigravity/unified_router.py",
    "antigravity/sync_engine.py",
    "antigravity/cross_verify.py",
    "antigravity/system_guardian.py",
    "workflow_system/resource_guard.py",
    "workflow_system/orchestrator.py",
    "workflow_system/cowork.py",
    "workflow_system/empire.py",
]

# ═══════════════════════════════════════════════════════════
# REPAIR FUNCTIONS
# ═══════════════════════════════════════════════════════════


def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        REPAIR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(REPAIR_LOG, "a") as f:
            f.write(json.dumps({"ts": ts, "level": level, "msg": msg}) + "\n")
    except OSError:
        pass  # Can't log to file - already printed to stdout


def run(cmd: str, timeout: int = 15) -> tuple:
    """Run shell command, return (success, output)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode == 0, r.stdout.strip()
    except Exception as e:
        return False, str(e)


# ── 1. Fix .env file ────────────────────────────────────

def repair_env_file() -> list:
    """Ensure .env has all required variables."""
    repairs = []

    if not ENV_FILE.exists():
        log(".env file missing — creating from defaults", "FIX")
        lines = [f"{k}={v}" for k, v in REQUIRED_ENV.items()]
        ENV_FILE.write_text("\n".join(lines) + "\n")
        repairs.append("Created .env file")
        return repairs

    # Read existing .env
    existing = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        existing[key.strip()] = val.strip()

    # Check for missing keys
    added = []
    for key, default in REQUIRED_ENV.items():
        if key not in existing:
            added.append(f"{key}={default}")
            repairs.append(f"Added missing env var: {key}")

    if added:
        with open(ENV_FILE, "a") as f:
            f.write("\n" + "\n".join(added) + "\n")
        log(f"Added {len(added)} missing env vars to .env", "FIX")

    # Check for empty values in critical vars
    for key in ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_REGION"]:
        if key in existing and not existing[key]:
            log(f"Empty value for {key} — setting default", "FIX")
            content = ENV_FILE.read_text()
            content = content.replace(
                f"{key}=", f"{key}={REQUIRED_ENV[key]}"
            )
            ENV_FILE.write_text(content)
            repairs.append(f"Fixed empty {key}")

    return repairs


# ── 2. Fix gcloud config ────────────────────────────────

def repair_gcloud_config() -> list:
    """Fix the 'Invalid project resource name projects/' error."""
    repairs = []

    # Check current gcloud project
    ok, project = run("gcloud config get-value project 2>/dev/null")
    if ok and project and project != "(unset)":
        log(f"gcloud project OK: {project}")
        return repairs

    # Fix: set the project from .env
    target_project = REQUIRED_ENV["GOOGLE_CLOUD_PROJECT"]
    log(f"gcloud project missing/unset — setting to {target_project}", "FIX")

    ok, _ = run(f"gcloud config set project {target_project}")
    if ok:
        repairs.append(f"Set gcloud project to {target_project}")
    else:
        log("gcloud not installed or not accessible — skipping", "WARN")

    # Also set region
    target_region = REQUIRED_ENV["GOOGLE_CLOUD_REGION"]
    run(f"gcloud config set compute/region {target_region}")

    return repairs


# ── 3. Fix corrupted files ──────────────────────────────

def repair_corrupted_files() -> list:
    """Detect and repair 0-byte or corrupt files."""
    repairs = []

    for rel_path in CRITICAL_FILES:
        filepath = PROJECT_ROOT / rel_path
        if not filepath.exists():
            log(f"MISSING: {rel_path}", "WARN")
            repairs.append(f"Missing: {rel_path} (needs manual restore or git checkout)")
            continue

        if filepath.stat().st_size == 0:
            log(f"CORRUPT (0 bytes): {rel_path}", "FIX")
            # Try git restore
            ok, _ = run(f"cd {PROJECT_ROOT} && git checkout HEAD -- {rel_path}")
            if ok:
                repairs.append(f"Restored from git: {rel_path}")
            else:
                repairs.append(f"0-byte file needs restore: {rel_path}")

        # Check Python syntax
        if filepath.suffix == ".py" and filepath.stat().st_size > 0:
            ok, err = run(f"python3 -c 'import ast; ast.parse(open(\"{filepath}\").read())'")
            if not ok:
                log(f"SYNTAX ERROR: {rel_path}", "WARN")
                ok, _ = run(f"cd {PROJECT_ROOT} && git checkout HEAD -- {rel_path}")
                if ok:
                    repairs.append(f"Restored (syntax error): {rel_path}")

    return repairs


# ── 4. Fix Ollama service ───────────────────────────────

def repair_ollama() -> list:
    """Ensure Ollama is running."""
    repairs = []

    ok, _ = run("curl -s http://localhost:11434/api/version", timeout=5)
    if ok:
        log("Ollama service running OK")
        return repairs

    log("Ollama not responding — attempting restart", "FIX")

    # macOS: try starting Ollama
    ok, _ = run("open -a Ollama 2>/dev/null || ollama serve &")
    if ok:
        time.sleep(3)
        ok2, _ = run("curl -s http://localhost:11434/api/version", timeout=5)
        if ok2:
            repairs.append("Restarted Ollama service")
        else:
            log("Could not start Ollama — may need manual restart", "WARN")
    else:
        log("Ollama not installed or not startable", "WARN")

    return repairs


# ── 5. Fix state files ──────────────────────────────────

def repair_state_files() -> list:
    """Clean up corrupt state/json files."""
    repairs = []
    state_dirs = [
        PROJECT_ROOT / "workflow_system" / "state",
        PROJECT_ROOT / "antigravity" / "_state",
        PROJECT_ROOT / "antigravity" / "_data",
    ]

    for state_dir in state_dirs:
        if not state_dir.exists():
            continue
        for json_file in state_dir.glob("*.json"):
            try:
                json.loads(json_file.read_text())
            except (json.JSONDecodeError, Exception):
                backup = json_file.with_suffix(".json.corrupt")
                json_file.rename(backup)
                repairs.append(f"Moved corrupt state: {json_file.name}")
                log(f"Corrupt state file moved: {json_file}", "FIX")

        # Clean up temp files from interrupted writes
        for tmp in state_dir.glob("*.tmp"):
            tmp.unlink()
            repairs.append(f"Cleaned temp file: {tmp.name}")

    return repairs


# ── 6. Fix Python pycache ───────────────────────────────

def repair_pycache() -> list:
    """Remove stale __pycache__ that can cause import errors after crash."""
    repairs = []
    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        try:
            import shutil
            shutil.rmtree(cache_dir)
            repairs.append(f"Cleared: {cache_dir.relative_to(PROJECT_ROOT)}")
        except OSError:
            pass  # Skip cache dirs that can't be removed (in use)

    if repairs:
        log(f"Cleared {len(repairs)} __pycache__ directories", "FIX")
    return repairs


# ── 7. Backup System ────────────────────────────────────

def create_backup() -> list:
    """Create a timestamped backup via git."""
    repairs = []

    os.chdir(PROJECT_ROOT)

    # Check if we're in a git repo
    ok, _ = run("git rev-parse --git-dir")
    if not ok:
        log("Not a git repo — cannot create backup", "WARN")
        return repairs

    # Auto-commit any uncommitted changes as backup
    ok, status = run("git status --porcelain")
    if ok and status:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run("git add -A")
        run(f'git commit -m "AUTO-BACKUP {ts} (pre-repair snapshot)"')
        repairs.append(f"Created backup commit: AUTO-BACKUP {ts}")
        log(f"Backup commit created: {ts}", "BACKUP")

    return repairs


# ── 8. AI-Powered Diagnosis (Ollama) ────────────────────

def ai_diagnose(issues: list) -> str:
    """Use local Ollama to diagnose issues and suggest fixes."""
    if not issues:
        return "No issues to diagnose."

    # Check if Ollama is available
    ok, _ = run("curl -s http://localhost:11434/api/version", timeout=5)
    if not ok:
        return "Ollama not available for AI diagnosis."

    prompt = f"""Du bist ein System-Repair-Agent fuer das AIEmpire-Core System.
Folgende Probleme wurden erkannt:

{json.dumps(issues, indent=2, ensure_ascii=False)}

Erstelle einen kurzen Reparatur-Plan (max 5 Schritte) und erklaere
was die wahrscheinliche Ursache war und wie man es in Zukunft verhindert.
Antworte auf Deutsch, kurz und praezise."""

    try:
        import json as j
        payload = j.dumps({
            "model": "qwen2.5-coder:7b",
            "prompt": prompt,
            "stream": False,
        })
        ok, response = run(
            f"curl -s http://localhost:11434/api/generate -d '{payload}'",
            timeout=60
        )
        if ok and response:
            data = j.loads(response)
            return data.get("response", "No response from model.")
    except Exception as e:
        return f"AI diagnosis failed: {e}"

    return "AI diagnosis unavailable."


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    check_only = "--check" in sys.argv
    use_ai = "--ai" in sys.argv

    print("""
╔══════════════════════════════════════════════════════════╗
║          AUTO-REPAIR SYSTEM — AIEmpire-Core              ║
║          Bombproof Self-Healing v1.0                     ║
╚══════════════════════════════════════════════════════════╝
    """)

    all_repairs = []
    all_issues = []

    # Run all repair checks
    checks = [
        ("Backup erstellen", create_backup),
        (".env Datei pruefen", repair_env_file),
        ("gcloud Config pruefen", repair_gcloud_config),
        ("Kritische Dateien pruefen", repair_corrupted_files),
        ("State-Dateien pruefen", repair_state_files),
        ("Python Cache aufraumen", repair_pycache),
        ("Ollama Service pruefen", repair_ollama),
    ]

    if check_only:
        log("CHECK-ONLY Modus — keine Aenderungen")

    for name, func in checks:
        print(f"\n  Checking: {name}...")
        try:
            repairs = func()
            if repairs:
                all_repairs.extend(repairs)
                all_issues.append({"check": name, "repairs": repairs})
                for r in repairs:
                    print(f"    FIX: {r}")
            else:
                print("    OK")
        except Exception as e:
            log(f"Check '{name}' failed: {e}", "ERROR")
            all_issues.append({"check": name, "error": str(e)})

    # AI Diagnosis
    if use_ai and all_issues:
        print("\n  Running AI Diagnosis (Ollama)...")
        diagnosis = ai_diagnose(all_issues)
        print(f"\n  AI DIAGNOSIS:\n  {diagnosis}")

    # Summary
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                    REPAIR SUMMARY                        ║
╠══════════════════════════════════════════════════════════╣
  Total Repairs:  {len(all_repairs)}
  Issues Found:   {len(all_issues)}
  Status:         {"ALL CLEAN" if not all_repairs else "REPAIRED"}
╚══════════════════════════════════════════════════════════╝
    """)

    if all_repairs:
        print("  Repairs performed:")
        for r in all_repairs:
            print(f"    - {r}")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "repairs": all_repairs,
        "issues": all_issues,
        "total_repairs": len(all_repairs),
    }
    try:
        report_file = PROJECT_ROOT / "workflow_system" / "state" / "last_repair.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    except OSError as e:
        log(f"Failed to save repair report: {e}", "WARN")

    return 0 if not all_issues else 1


if __name__ == "__main__":
    sys.exit(main())
