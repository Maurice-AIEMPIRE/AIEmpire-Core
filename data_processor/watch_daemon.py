"""
Watch Daemon - Monitort Input-Ordner und starte Verarbeitung
"""

import asyncio
import os
import shutil
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataWatchHandler(FileSystemEventHandler):
    """Reagiert auf neue Dateien im Input-Ordner"""

    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            # Warte kurz bis Datei vollständig geschrieben ist
            asyncio.get_event_loop().call_later(2, self._process_file, event.src_path)

    def _process_file(self, file_path):
        """Triggere Verarbeitung"""
        logger.info(f"📥 Neue Datei erkannt: {file_path}")
        asyncio.create_task(self.callback(file_path))


class WatchDaemon:
    """Überwacht Input-Ordner und starte Analyse"""

    def __init__(self, input_dir="/data/input", processor_callback=None):
        self.input_dir = Path(input_dir)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.processor_callback = processor_callback
        self.observer = None

    async def start(self):
        """Starte Watch Daemon"""
        logger.info(f"🔍 Watch Daemon gestartet: {self.input_dir}")

        handler = DataWatchHandler(self.processor_callback or self._default_callback)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.input_dir), recursive=False)
        self.observer.start()

    async def stop(self):
        """Stoppe Watch Daemon"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("🛑 Watch Daemon gestoppt")

    async def _default_callback(self, file_path):
        """Default: Nur logging"""
        logger.info(f"⏳ Warte auf Processor für: {file_path}")


if __name__ == "__main__":
    async def main():
        daemon = WatchDaemon()
        await daemon.start()
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await daemon.stop()

    asyncio.run(main())
