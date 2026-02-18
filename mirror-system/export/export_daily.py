#!/usr/bin/env python3
"""
EXPORT DAILY - Mac → Cloud Export-Paket Generator

Sammelt System-Status, Logs, Tasks und Metriken.
Redacted alle Secrets und Private Daten.
Erzeugt ein ZIP-Paket für die Cloud (Mirror Lab).

Usage:
  python export_daily.py                # Erstelle tägliches Export-Paket
  python export_daily.py --dry-run      # Zeige was exportiert würde
  python export_daily.py --push git     # Exportiere + push als Git Tag
  python export_daily.py --push gcs     # Exportiere + upload zu GCS
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

# Paths
MIRROR_DIR = Path(__file__).parent.parent
PROJECT_ROOT = MIRROR_DIR.parent
EXPORT_DIR = MIRROR_DIR / "export" / "exports"
CONFIG_DIR = MIRROR_DIR / "config"

EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_privacy_rules() -> dict:
    """Load privacy and redaction rules."""
    rules_file = CONFIG_DIR / "privacy_rules.json"
    if rules_file.exists():
        return json.loads(rules_file.read_text())
    return {"redaction_rules": {"always_remove": [], "patterns_to_redact": [], "paths_never_export": []}}


def redact_text(text: str, rules: dict) -> str:
    """Remove secrets and sensitive patterns from text."""
    redacted = text

    # Remove known env var values
    for key in rules.get("redaction_rules", {}).get("always_remove", []):
        val = os.getenv(key, "")
        if val and len(val) > 4:
            redacted = redacted.replace(val, f"[REDACTED:{key}]")

    # Remove regex patterns (API keys, emails, credit cards)
    for pattern in rules.get("redaction_rules", {}).get("patterns_to_redact", []):
        try:
            redacted = re.sub(pattern, "[REDACTED]", redacted)
        except re.error:
            pass

    return redacted


def is_path_allowed(path: Path, rules: dict) -> bool:
    """Check if a path is allowed for export based on privacy rules."""
    path_str = str(path)
    for blocked in rules.get("redaction_rules", {}).get("paths_never_export", []):
        if blocked.startswith("*"):
            if path_str.endswith(blocked[1:]):
                return False
        elif blocked in path_str:
            return False
    return True


def collect_system_status() -> dict:
    """Collect current system status."""
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "disk": {},
        "models": [],
    }

    # Check Ollama
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "http://127.0.0.1:11434/api/tags"],
            capture_output=True, text=True, timeout=5
        )
        status["services"]["ollama"] = {"status": "UP" if result.stdout.strip() == "200" else "DOWN"}

        if status["services"]["ollama"]["status"] == "UP":
            model_result = subprocess.run(
                ["curl", "-s", "http://127.0.0.1:11434/api/tags"],
                capture_output=True, text=True, timeout=5
            )
            try:
                models_data = json.loads(model_result.stdout)
                status["models"] = [m.get("name", "") for m in models_data.get("models", [])]
            except (json.JSONDecodeError, KeyError):
                pass
    except (subprocess.TimeoutExpired, FileNotFoundError):
        status["services"]["ollama"] = {"status": "DOWN"}

    # Check Redis
    try:
        result = subprocess.run(
            ["redis-cli", "ping"], capture_output=True, text=True, timeout=3
        )
        status["services"]["redis"] = {"status": "UP" if "PONG" in result.stdout else "DOWN"}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        status["services"]["redis"] = {"status": "UNKNOWN"}

    # Check PostgreSQL
    try:
        result = subprocess.run(
            ["pg_isready"], capture_output=True, text=True, timeout=3
        )
        status["services"]["postgresql"] = {"status": "UP" if result.returncode == 0 else "DOWN"}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        status["services"]["postgresql"] = {"status": "UNKNOWN"}

    # Disk usage
    try:
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=3)
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:
            parts = lines[1].split()
            status["disk"] = {
                "total": parts[1] if len(parts) > 1 else "?",
                "used": parts[2] if len(parts) > 2 else "?",
                "available": parts[3] if len(parts) > 3 else "?",
                "usage_pct": parts[4] if len(parts) > 4 else "?",
            }
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return status


def collect_task_log() -> list:
    """Collect recent task activities from workflow state."""
    tasks = []

    # Workflow state
    state_file = PROJECT_ROOT / "workflow_system" / "state" / "current_state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            for step in state.get("steps_completed", []):
                tasks.append({
                    "source": "workflow",
                    "step": step.get("step", ""),
                    "timestamp": step.get("timestamp", ""),
                    "summary": step.get("summary", "")[:200],
                })
        except json.JSONDecodeError:
            pass

    # Cowork state
    cowork_file = PROJECT_ROOT / "workflow_system" / "state" / "cowork_state.json"
    if cowork_file.exists():
        try:
            cowork = json.loads(cowork_file.read_text())
            for action in cowork.get("actions_taken", [])[-20:]:
                tasks.append({
                    "source": "cowork",
                    "action": str(action)[:200],
                })
        except json.JSONDecodeError:
            pass

    return tasks


def collect_index_summary() -> dict:
    """Collect file structure summary (no content, just structure)."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "directories": {},
        "total_files": 0,
        "recent_changes": [],
    }

    # Count files per top-level directory
    for item in PROJECT_ROOT.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            try:
                count = sum(1 for _ in item.rglob("*") if _.is_file())
                summary["directories"][item.name] = count
                summary["total_files"] += count
            except PermissionError:
                pass

    # Recent git changes
    try:
        result = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "log", "--oneline", "-20",
             "--format=%H|%s|%ai"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|", 2)
                summary["recent_changes"].append({
                    "hash": parts[0][:8],
                    "message": parts[1][:100] if len(parts) > 1 else "",
                    "date": parts[2] if len(parts) > 2 else "",
                })
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return summary


def collect_open_tasks() -> list:
    """Collect open tasks from various sources."""
    tasks = []

    # Check docs/CHATGPT_TASKS.md
    tasks_file = PROJECT_ROOT / "docs" / "CHATGPT_TASKS.md"
    if tasks_file.exists():
        content = tasks_file.read_text()
        for line in content.split("\n"):
            if line.strip().startswith("- [ ]"):
                tasks.append({"source": "chatgpt_tasks", "task": line.strip()[6:100]})

    # Cowork pending recommendations
    cowork_file = PROJECT_ROOT / "workflow_system" / "state" / "cowork_state.json"
    if cowork_file.exists():
        try:
            cowork = json.loads(cowork_file.read_text())
            for rec in cowork.get("pending_recommendations", []):
                tasks.append({"source": "cowork", "task": str(rec)[:200]})
        except json.JSONDecodeError:
            pass

    return tasks


def collect_error_patterns() -> list:
    """Collect recent error patterns from logs."""
    errors = []

    # Check workflow output for errors
    output_dir = PROJECT_ROOT / "workflow_system" / "output"
    if output_dir.exists():
        for f in sorted(output_dir.glob("*.json"), key=lambda x: x.stat().st_mtime)[-5:]:
            try:
                data = json.loads(f.read_text())
                if "error" in str(data).lower():
                    errors.append({
                        "file": f.name,
                        "type": "workflow_error",
                        "summary": str(data)[:300],
                    })
            except (json.JSONDecodeError, OSError):
                pass

    return errors


def collect_vision_state() -> dict:
    """Collect current vision state if it exists."""
    vision_file = MIRROR_DIR / "dip" / "vision_state.json"
    if vision_file.exists():
        try:
            return json.loads(vision_file.read_text())
        except json.JSONDecodeError:
            pass
    return {"status": "not_initialized", "message": "Run DIP first"}


def create_export_package(dry_run: bool = False) -> Path:
    """Create the daily export package."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    export_name = f"{date_str}_export"
    export_path = EXPORT_DIR / export_name
    zip_path = EXPORT_DIR / f"{export_name}.zip"

    rules = load_privacy_rules()

    print(f"[EXPORT] Creating daily export: {export_name}")

    # Collect all data
    data = {
        "system_status": collect_system_status(),
        "task_log": collect_task_log(),
        "index_summary": collect_index_summary(),
        "open_tasks": collect_open_tasks(),
        "error_patterns": collect_error_patterns(),
        "vision_state": collect_vision_state(),
    }

    if dry_run:
        print("\n[DRY RUN] Would export:")
        for key, value in data.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} items")
            elif isinstance(value, dict):
                print(f"  {key}: {len(value)} keys")
        return Path("/dev/null")

    # Create export directory
    export_path.mkdir(parents=True, exist_ok=True)

    # Write each component (redacted)
    for key, value in data.items():
        content = json.dumps(value, indent=2, default=str, ensure_ascii=False)
        content = redact_text(content, rules)
        (export_path / f"{key}.json").write_text(content)

    # Create manifest
    manifest = {
        "created": datetime.now().isoformat(),
        "source": "main_brain_mac",
        "version": "1.0",
        "components": list(data.keys()),
        "redacted": True,
        "privacy_level": "P1_INTERNAL",
    }
    (export_path / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # Create ZIP
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in export_path.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(export_path))

    # Cleanup unzipped directory
    shutil.rmtree(export_path)

    size_kb = zip_path.stat().st_size / 1024
    print(f"[EXPORT] Created: {zip_path} ({size_kb:.1f} KB)")
    return zip_path


def push_git(zip_path: Path):
    """Push export as Git tag."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    tag_name = f"export/{date_str}"

    subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "add", str(zip_path)],
        check=True
    )
    subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "commit", "-m",
         f"[mirror-export] Daily export {date_str}"],
        check=True
    )
    subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "tag", tag_name],
        check=True
    )
    print(f"[EXPORT] Tagged as: {tag_name}")


def push_gcs(zip_path: Path):
    """Upload export to Google Cloud Storage."""
    bucket = "gs://ai-empire-mirror/exports/"
    try:
        subprocess.run(
            ["gsutil", "cp", str(zip_path), bucket],
            check=True, timeout=60
        )
        print(f"[EXPORT] Uploaded to: {bucket}{zip_path.name}")
    except FileNotFoundError:
        print("[EXPORT] gsutil not found. Install Google Cloud SDK first.")
    except subprocess.CalledProcessError as e:
        print(f"[EXPORT] Upload failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Daily Export Paket Generator")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be exported")
    parser.add_argument("--push", choices=["git", "gcs"], help="Push method after export")
    args = parser.parse_args()

    zip_path = create_export_package(dry_run=args.dry_run)

    if args.push and not args.dry_run:
        if args.push == "git":
            push_git(zip_path)
        elif args.push == "gcs":
            push_gcs(zip_path)

    print("[EXPORT] Done.")


if __name__ == "__main__":
    main()
