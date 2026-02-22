"""
Watch Daemon — Überwacht Input-Ordner auf neue Dateien
=======================================================
Nutzt watchdog für zuverlässiges File-System-Monitoring.
Löst automatisch die Pipeline aus sobald eine neue Datei erscheint.
"""

import asyncio
import logging
import threading
from pathlib import Path
from typing import Callable, Coroutine

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

# Wartezeit nach Datei-Erkennung (sicherstellen dass Datei vollständig geschrieben)
SETTLE_TIME_S = 2.0


class _DataWatchHandler(FileSystemEventHandler):
    """watchdog Handler der neue Dateien an den asyncio Event-Loop weitergibt."""

    def __init__(self, loop: asyncio.AbstractEventLoop, callback: Callable):
        super().__init__()
        self._loop = loop
        self._callback = callback
        self._pending: set[str] = set()
        self._lock = threading.Lock()

    def on_created(self, event):
        if event.is_directory:
            return
        path = event.src_path
        # Versteckte Dateien und Temp-Dateien ignorieren
        name = Path(path).name
        if name.startswith(".") or name.endswith(".tmp") or name.endswith("~"):
            return
        with self._lock:
            if path in self._pending:
                return
            self._pending.add(path)
        logger.info(f"📥 Neue Datei erkannt: {name}")
        # Kurz warten (Settle), dann im asyncio-Loop verarbeiten
        self._loop.call_soon_threadsafe(
            lambda p=path: asyncio.ensure_future(self._delayed_callback(p))
        )

    async def _delayed_callback(self, path: str):
        """Warte bis Datei vollständig geschrieben, dann Callback."""
        await asyncio.sleep(SETTLE_TIME_S)
        with self._lock:
            self._pending.discard(path)
        if Path(path).exists():
            try:
                await self._callback(path)
            except Exception as e:
                logger.error(f"Pipeline-Fehler für {path}: {e}", exc_info=True)
        else:
            logger.warning(f"Datei verschwunden vor Verarbeitung: {path}")

    def on_moved(self, event):
        """Auch auf verschobene Dateien reagieren (z.B. rsync rename)."""
        if not event.is_directory and event.dest_path:
            # Simuliere on_created für Zieldatei
            class _FakeEvent:
                src_path = event.dest_path
                is_directory = False
            self.on_created(_FakeEvent())


class WatchDaemon:
    """
    Überwacht einen Ordner und triggert callback() für jede neue Datei.

    Beispiel:
        async def on_file(path: str):
            print(f"Verarbeite: {path}")

        daemon = WatchDaemon("/data/input", on_file)
        await daemon.start()
        # ... läuft bis daemon.stop()
    """

    def __init__(
        self,
        input_dir: str = "/data/input",
        processor_callback: Callable | None = None,
    ):
        self.input_dir = Path(input_dir)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.processor_callback = processor_callback or self._default_callback
        self._observer: Observer | None = None

    async def start(self):
        """Starte watchdog Observer im Hintergrund-Thread."""
        loop = asyncio.get_running_loop()
        handler = _DataWatchHandler(loop, self.processor_callback)

        self._observer = Observer()
        self._observer.schedule(handler, str(self.input_dir), recursive=False)
        self._observer.start()
        logger.info(f"👁  Watch Daemon aktiv: {self.input_dir}")

    async def stop(self):
        """Stoppe watchdog Observer."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5)
            logger.info("Watch Daemon gestoppt")

    async def _default_callback(self, file_path: str):
        """Fallback wenn kein Processor übergeben wird."""
        logger.info(f"[Default] Datei bereit: {file_path} — kein Processor konfiguriert")
