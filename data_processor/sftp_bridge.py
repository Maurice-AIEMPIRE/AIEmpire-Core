"""
SFTP Bridge — Mac ↔ Server ↔ iCloud Daten-Übertragung
=======================================================
Mac Upload:   rsync/sftp → /data/input/ auf Server
Server Output: /data/results/ → rsync → iCloud Drive Ordner auf Mac

Nutzung (Mac-Seite):
  ./scripts/mac_upload.sh /path/to/meine/datei.pdf
  ./scripts/mac_upload.sh /path/to/ordner/

Nutzung (Server-Seite):
  python3 data_processor/sftp_bridge.py push-results
  python3 data_processor/sftp_bridge.py status

Konfiguration via .env:
  MAC_USER=maurice
  MAC_HOST=192.168.x.x  (oder deine Hetzner IP wenn Mac ins VPN)
  MAC_ICLOUD_PATH=/Users/maurice/Library/Mobile Documents/com~apple~CloudDocs
  MAC_RESULTS_FOLDER=AIEmpire-Results
  SERVER_INPUT_DIR=/data/input
  SERVER_OUTPUT_DIR=/data/results
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from antigravity.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

# ─── Config aus .env ─────────────────────────────────────────────────────────
def _env(key: str, default: str = "") -> str:
    """Lese Env-Variable (config.py lädt .env automatisch)."""
    return os.environ.get(key, default)

MAC_USER = _env("MAC_USER", "maurice")
MAC_HOST = _env("MAC_HOST", "")           # Nur gesetzt wenn Mac erreichbar
MAC_ICLOUD_PATH = _env(
    "MAC_ICLOUD_PATH",
    f"/Users/{MAC_USER}/Library/Mobile Documents/com~apple~CloudDocs"
)
MAC_RESULTS_FOLDER = _env("MAC_RESULTS_FOLDER", "AIEmpire-Results")
SERVER_INPUT_DIR = Path(_env("SERVER_INPUT_DIR", "/data/input"))
SERVER_OUTPUT_DIR = Path(_env("SERVER_OUTPUT_DIR", "/data/results"))
SERVER_PROCESSED_DIR = Path(_env("SERVER_PROCESSED_DIR", "/data/processed"))

# SSH Optionen (keine Passwortabfrage, kein Hostkey-Problem)
SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=10",
]


# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Führe Shell-Kommando aus und logge Ergebnis."""
    logger.debug(f"RUN: {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def mac_reachable() -> bool:
    """Prüfe ob Mac per SSH erreichbar ist."""
    if not MAC_HOST:
        return False
    try:
        result = _run(
            ["ssh"] + SSH_OPTS + [f"{MAC_USER}@{MAC_HOST}", "echo ok"],
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


# ─── Upload: Mac → Server ─────────────────────────────────────────────────────

def upload_from_mac(local_path: str, remote_input_dir: str | None = None) -> bool:
    """
    Wird vom Mac-Script aufgerufen via:
      rsync -av <local_path> <user>@<server>:<input_dir>/

    Diese Funktion ist die Server-Seite: Sie registriert den Upload im Log.
    Das eigentliche rsync läuft im Mac-Script mac_upload.sh.
    """
    dest = Path(remote_input_dir or SERVER_INPUT_DIR)
    dest.mkdir(parents=True, exist_ok=True)
    logger.info(f"📥 Upload-Ziel bereit: {dest}")
    return True


# ─── Download: Server → Mac/iCloud ───────────────────────────────────────────

async def push_results_to_mac(results_dir: Path | None = None) -> dict:
    """
    Sync Analyse-Ergebnisse vom Server zurück auf den Mac in den iCloud-Ordner.

    Ziel-Struktur auf Mac/iCloud:
      ~/Library/Mobile Documents/com~apple~CloudDocs/
        AIEmpire-Results/
          Vertraege/      ← aus icloud_folder-Zuweisung
          Rechnungen/
          Berichte/
          Notizen/
          Daten/
          Bilder/
          Sonstiges/
          _Uebersicht.md  ← Auto-generierter Index
    """
    results_dir = results_dir or SERVER_OUTPUT_DIR

    if not results_dir.exists():
        return {"status": "error", "message": f"Results dir nicht gefunden: {results_dir}"}

    if not MAC_HOST:
        logger.warning("MAC_HOST nicht gesetzt — kein Auto-Push möglich")
        logger.info(f"Ergebnisse liegen in: {results_dir}")
        return {"status": "skipped", "message": "MAC_HOST nicht konfiguriert"}

    if not mac_reachable():
        logger.warning(f"Mac {MAC_HOST} nicht erreichbar")
        return {"status": "error", "message": f"Mac nicht erreichbar: {MAC_HOST}"}

    remote_path = f"{MAC_USER}@{MAC_HOST}:{MAC_ICLOUD_PATH}/{MAC_RESULTS_FOLDER}/"

    # Erstelle Remote-Ordner
    _run(
        ["ssh"] + SSH_OPTS + [
            f"{MAC_USER}@{MAC_HOST}",
            f'mkdir -p "{MAC_ICLOUD_PATH}/{MAC_RESULTS_FOLDER}"'
        ],
        check=False
    )

    # rsync: Server results → Mac iCloud
    cmd = [
        "rsync", "-avz", "--progress",
        "--exclude", "*.tmp",
        "--exclude", ".DS_Store",
        str(results_dir) + "/",
        remote_path,
    ]

    try:
        result = _run(cmd)
        logger.info(f"✅ Push erfolgreich nach {remote_path}")
        return {
            "status": "success",
            "destination": remote_path,
            "output": result.stdout[-500:] if result.stdout else "",
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"rsync Fehler: {e.stderr}")
        return {"status": "error", "message": e.stderr}


# ─── Index-Übersicht generieren ───────────────────────────────────────────────

def generate_index(results_dir: Path | None = None) -> str:
    """
    Erstelle _Uebersicht.md mit allen verarbeiteten Dateien.
    Wird in results_dir abgelegt und mit nach iCloud gepusht.
    """
    results_dir = results_dir or SERVER_OUTPUT_DIR
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    lines = [
        f"# AIEmpire Daten-Übersicht\n",
        f"**Erstellt:** {now}\n",
        f"**Server:** {os.uname().nodename}\n",
        "",
        "---",
        "",
    ]

    total_files = 0
    folder_stats: dict[str, int] = {}

    # Scanne alle Kategorien-Ordner
    for category_dir in sorted(results_dir.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        json_files = list(category_dir.glob("*_analysis.json"))
        md_files = list(category_dir.glob("*_report.md"))
        count = len(json_files)
        folder_stats[category] = count
        total_files += count

        if count > 0:
            lines.append(f"## {category} ({count} Dateien)\n")
            for jf in sorted(json_files):
                stem = jf.stem.replace("_analysis", "")
                try:
                    with open(jf) as f:
                        data = json.load(f)
                    final = data.get("analysis", {}).get("final", {})
                    summary = final.get("summary", "")[:100]
                    importance = final.get("importance", "")
                    lines.append(f"- **{stem}** `[{importance}]` — {summary}")
                except Exception:
                    lines.append(f"- {stem}")
            lines.append("")

    lines.extend([
        "---",
        f"\n**Gesamt:** {total_files} Dateien analysiert",
        "",
        "| Ordner | Dateien |",
        "|--------|---------|",
    ])
    for folder, count in sorted(folder_stats.items(), key=lambda x: -x[1]):
        lines.append(f"| {folder} | {count} |")

    content = "\n".join(lines)
    index_file = results_dir / "_Uebersicht.md"
    index_file.write_text(content, encoding="utf-8")
    logger.info(f"📊 Index erstellt: {index_file} ({total_files} Dateien)")
    return str(index_file)


# ─── Status ──────────────────────────────────────────────────────────────────

def pipeline_status() -> dict:
    """Zeige Status der Pipeline-Ordner."""
    def count_files(d: Path) -> int:
        if not d.exists():
            return 0
        return sum(1 for f in d.rglob("*") if f.is_file())

    return {
        "input_dir": str(SERVER_INPUT_DIR),
        "input_pending": count_files(SERVER_INPUT_DIR),
        "output_dir": str(SERVER_OUTPUT_DIR),
        "output_ready": count_files(SERVER_OUTPUT_DIR),
        "processed_dir": str(SERVER_PROCESSED_DIR),
        "processed_total": count_files(SERVER_PROCESSED_DIR),
        "mac_host": MAC_HOST or "nicht konfiguriert",
        "mac_reachable": mac_reachable() if MAC_HOST else False,
        "icloud_path": f"{MAC_ICLOUD_PATH}/{MAC_RESULTS_FOLDER}",
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        status = pipeline_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif cmd == "push-results":
        index = generate_index()
        print(f"Index: {index}")
        result = asyncio.run(push_results_to_mac())
        print(json.dumps(result, indent=2))

    elif cmd == "index":
        index = generate_index()
        print(f"Index erstellt: {index}")

    else:
        print(f"Unbekannter Befehl: {cmd}")
        print("Verfügbar: status, push-results, index")
        sys.exit(1)
