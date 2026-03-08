#!/usr/bin/env python3
"""
AIEmpire Telegram Worker
========================
Verarbeitet Aufgaben aus der Redis-Queue die vom Bot gesendet werden.
Läuft parallel zum Bot als separater Prozess.

Start: python3 telegram_bot/worker.py
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

log = logging.getLogger("AIEmpire-Worker")
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

def get_redis():
    """Redis-Verbindung."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        log.warning(f"Redis nicht verfügbar: {e}")
        return None


def process_task(task: dict) -> str:
    """Verarbeitet eine Aufgabe und gibt Ergebnis zurück."""
    task_type = task.get("type", "text")
    content = task.get("content", "")
    filepath = task.get("filepath", "")

    if task_type == "pdf":
        from bot import process_pdf
        return process_pdf(Path(filepath))

    elif task_type == "zip":
        from bot import process_zip
        return process_zip(Path(filepath))

    elif task_type == "text":
        from bot import process_text_content
        return process_text_content(content)

    elif task_type == "empire_command":
        import subprocess
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "empire_engine.py"), content],
            capture_output=True, text=True, timeout=120,
            cwd=str(REPO_ROOT)
        )
        return result.stdout or result.stderr or "Fertig"

    return f"Unbekannter Task-Typ: {task_type}"


def run_worker():
    """Worker-Loop."""
    log.info("AIEmpire Worker gestartet")
    r = get_redis()

    if not r:
        log.info("Redis nicht verfügbar - Worker wartet auf Redis...")
        while True:
            time.sleep(30)
            r = get_redis()
            if r:
                log.info("Redis verbunden!")
                break

    queue_key = "aiempire:telegram:tasks"
    result_key_prefix = "aiempire:telegram:results:"

    log.info(f"Warte auf Tasks in Queue: {queue_key}")

    while True:
        try:
            # Blocking pop - wartet auf neue Aufgaben
            item = r.blpop(queue_key, timeout=30)
            if not item:
                continue

            _, raw = item
            task = json.loads(raw)
            task_id = task.get("id", "unknown")

            log.info(f"Task {task_id}: {task.get('type')} - {str(task.get('content', ''))[:50]}")

            # Verarbeiten
            result = process_task(task)

            # Ergebnis speichern (Bot holt es ab)
            r.setex(
                f"{result_key_prefix}{task_id}",
                300,  # 5 Minuten TTL
                json.dumps({"result": result, "task_id": task_id})
            )

            log.info(f"Task {task_id} abgeschlossen")

        except KeyboardInterrupt:
            log.info("Worker gestoppt")
            break
        except Exception as e:
            log.error(f"Worker-Fehler: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_worker()
