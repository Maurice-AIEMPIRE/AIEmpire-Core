#!/usr/bin/env python3
"""
SYNC MANAGER - Koordiniert alle Sync-Operationen zwischen Mac und Cloud.

Orchestriert:
1. Täglicher Export (Mac → Cloud)
2. Cloud-PR Check (Cloud → Mac)
3. Telemetrie sammeln
4. Vision State synchronisieren

Usage:
  python sync_manager.py daily           # Voller täglicher Sync-Zyklus
  python sync_manager.py export          # Nur Export
  python sync_manager.py import          # Nur Import/Merge Gate
  python sync_manager.py telemetry       # Nur Telemetrie sammeln
  python sync_manager.py status          # Sync Status
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MIRROR_DIR = Path(__file__).parent.parent
PROJECT_ROOT = MIRROR_DIR.parent
SYNC_LOG = MIRROR_DIR / "sync" / "logs" / "sync.jsonl"

SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(MIRROR_DIR / "export"))
sys.path.insert(0, str(MIRROR_DIR / "import"))


def log_sync(action: str, result: str, detail: str = ""):
    """Log sync activity."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "result": result,
        "detail": detail,
    }
    with open(SYNC_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_export():
    """Run daily export."""
    print("\n  [1/4] EXPORT: Erstelle tägliches Export-Paket...")
    try:
        result = subprocess.run(
            [sys.executable, str(MIRROR_DIR / "export" / "export_daily.py")],
            capture_output=True, text=True, timeout=120
        )
        print(result.stdout)
        log_sync("export", "success" if result.returncode == 0 else "error",
                result.stderr[:200] if result.returncode != 0 else "")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log_sync("export", "timeout")
        print("  [TIMEOUT] Export dauerte zu lange.")
        return False


def run_import():
    """Run merge gate check."""
    print("\n  [2/4] IMPORT: Prüfe Cloud-Branches...")
    try:
        result = subprocess.run(
            [sys.executable, str(MIRROR_DIR / "import" / "merge_gate.py"), "check"],
            capture_output=True, text=True, timeout=60
        )
        print(result.stdout)
        log_sync("import_check", "success", result.stdout[:200])
        return True
    except subprocess.TimeoutExpired:
        log_sync("import_check", "timeout")
        return False


def run_telemetry():
    """Collect and save telemetry."""
    print("\n  [3/4] TELEMETRIE: Sammle Metriken...")

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "tasks_completed_today": 0,
        "errors_today": 0,
        "exports_created": 0,
        "prs_reviewed": 0,
        "products_in_pipeline": 0,
        "vision_sessions": 0,
    }

    # Count exports
    export_dir = MIRROR_DIR / "export" / "exports"
    if export_dir.exists():
        metrics["exports_created"] = len(list(export_dir.glob("*.zip")))

    # Count product ideas
    inbox = MIRROR_DIR / "product-factory" / "data" / "ideas" / "inbox.jsonl"
    if inbox.exists():
        metrics["products_in_pipeline"] = sum(1 for line in inbox.read_text().split("\n") if line.strip())

    # Count vision sessions
    vision_file = MIRROR_DIR / "dip" / "vision_state.json"
    if vision_file.exists():
        try:
            vs = json.loads(vision_file.read_text())
            metrics["vision_sessions"] = vs.get("sessions_completed", 0)
        except json.JSONDecodeError:
            pass

    # Count sync logs for today
    today = datetime.now().strftime("%Y-%m-%d")
    if SYNC_LOG.exists():
        for line in SYNC_LOG.read_text().split("\n"):
            if today in line:
                try:
                    entry = json.loads(line)
                    if entry.get("result") == "error":
                        metrics["errors_today"] += 1
                except json.JSONDecodeError:
                    pass

    telemetry_file = MIRROR_DIR / "sync" / "logs" / f"telemetry_{today}.json"
    telemetry_file.write_text(json.dumps(metrics, indent=2))

    print(f"  Exports: {metrics['exports_created']}")
    print(f"  Produkte: {metrics['products_in_pipeline']}")
    print(f"  Vision Sessions: {metrics['vision_sessions']}")
    print(f"  Fehler heute: {metrics['errors_today']}")

    log_sync("telemetry", "success")
    return True


def sync_vision():
    """Ensure vision state is available for both systems."""
    print("\n  [4/4] VISION: Synchronisiere Vision State...")

    vision_file = MIRROR_DIR / "dip" / "vision_state.json"
    if vision_file.exists():
        print("  Vision State: vorhanden")
        try:
            vs = json.loads(vision_file.read_text())
            print(f"  Sessions: {vs.get('sessions_completed', 0)}")
            print(f"  Streak: {vs.get('meta', {}).get('streak_days', 0)} Tage")
            print(f"  Updated: {vs.get('updated', 'nie')}")
        except json.JSONDecodeError:
            pass
    else:
        print("  Vision State: NICHT INITIALISIERT")
        print("  → Führe 'python dip/daily_interrogation.py morning' aus!")

    log_sync("vision_sync", "success")
    return True


def run_daily():
    """Full daily sync cycle."""
    print(f"\n{'='*60}")
    print(f"  DAILY SYNC - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    results = []
    results.append(("Export", run_export()))
    results.append(("Import", run_import()))
    results.append(("Telemetrie", run_telemetry()))
    results.append(("Vision", sync_vision()))

    print(f"\n{'='*60}")
    print("  ERGEBNIS:")
    for name, ok in results:
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")
    print(f"{'='*60}\n")

    all_ok = all(r[1] for r in results)
    log_sync("daily_full", "success" if all_ok else "partial_failure")


def show_status():
    """Show sync status."""
    print(f"\n{'='*60}")
    print("  SYNC STATUS")
    print(f"{'='*60}")

    # Last sync
    if SYNC_LOG.exists():
        lines = SYNC_LOG.read_text().strip().split("\n")
        if lines:
            last = json.loads(lines[-1])
            print(f"  Letzter Sync: {last.get('timestamp', '?')[:16]}")
            print(f"  Aktion: {last.get('action', '?')}")
            print(f"  Ergebnis: {last.get('result', '?')}")
    else:
        print("  Noch kein Sync durchgeführt.")

    # Export count
    export_dir = MIRROR_DIR / "export" / "exports"
    if export_dir.exists():
        exports = list(export_dir.glob("*.zip"))
        print(f"  Export-Pakete: {len(exports)}")
    else:
        print("  Export-Pakete: 0")

    # Import count
    import_dir = MIRROR_DIR / "import" / "imports"
    if import_dir.exists():
        imports = list(import_dir.glob("*.json"))
        print(f"  Import-Reviews: {len(imports)}")
    else:
        print("  Import-Reviews: 0")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Sync Manager")
    parser.add_argument("command", choices=["daily", "export", "import", "telemetry", "status"],
                       help="Sync command")
    args = parser.parse_args()

    if args.command == "daily":
        run_daily()
    elif args.command == "export":
        run_export()
    elif args.command == "import":
        run_import()
    elif args.command == "telemetry":
        run_telemetry()
    elif args.command == "status":
        show_status()


if __name__ == "__main__":
    main()
