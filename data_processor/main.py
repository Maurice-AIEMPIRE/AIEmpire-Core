"""
Empire Data Processor — Hauptprozess
=====================================
Orchestriert den kompletten Pipeline-Flow:
  Watch → Extract → Analyze (3-Layer AI) → Format → Output → iCloud Push

Starten:
  python3 data_processor/main.py               # Daemon-Modus (Watch + Auto-Prozess)
  python3 data_processor/main.py process <file> # Einzelne Datei verarbeiten
  python3 data_processor/main.py batch          # Alle Dateien in /data/input/ verarbeiten
  python3 data_processor/main.py status         # Pipeline-Status anzeigen
  python3 data_processor/main.py push           # Ergebnisse nach iCloud pushen
"""

import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path

# ─── Projekt-Root im Pfad ────────────────────────────────────────────────────
_HERE = Path(__file__).parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from data_processor.watch_daemon import WatchDaemon
from data_processor.processors import (
    PDFProcessor,
    ImageProcessor,
    AudioProcessor,
    JSONProcessor,
    CSVProcessor,
    OfficeProcessor,
)
from data_processor.analyzer import EmpireAnalyzer
from data_processor.output_formatter import OutputFormatter
from data_processor.sftp_bridge import (
    pipeline_status,
    push_results_to_mac,
    generate_index,
    SERVER_INPUT_DIR,
    SERVER_OUTPUT_DIR,
    SERVER_PROCESSED_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("empire.pipeline")

# ─── Dateityp → Prozessor-Mapping ────────────────────────────────────────────
PROCESSOR_MAP: dict[str, type] = {
    ".pdf":  PDFProcessor,
    ".jpg":  ImageProcessor,
    ".jpeg": ImageProcessor,
    ".png":  ImageProcessor,
    ".gif":  ImageProcessor,
    ".bmp":  ImageProcessor,
    ".mp3":  AudioProcessor,
    ".wav":  AudioProcessor,
    ".m4a":  AudioProcessor,
    ".ogg":  AudioProcessor,
    ".flac": AudioProcessor,
    ".json": JSONProcessor,
    ".csv":  CSVProcessor,
    ".tsv":  CSVProcessor,
    ".docx": OfficeProcessor,
    ".xlsx": OfficeProcessor,
    ".pptx": OfficeProcessor,
    ".doc":  OfficeProcessor,
    ".xls":  OfficeProcessor,
    ".txt":  JSONProcessor,   # txt als einfacher Text
}


def get_processor(file_path: Path):
    """Wähle richtigen Prozessor basierend auf Dateiendung."""
    suffix = file_path.suffix.lower()
    cls = PROCESSOR_MAP.get(suffix, JSONProcessor)
    return cls(str(file_path))


# ─── Haupt-Prozess-Funktion ───────────────────────────────────────────────────

class EmpireDataProcessor:
    """Pipeline-Orchestrator: Watch → Extract → Analyze → Output → iCloud"""

    def __init__(
        self,
        input_dir: str | None = None,
        output_dir: str | None = None,
        processed_dir: str | None = None,
        auto_push: bool = False,
    ):
        self.input_dir = Path(input_dir or SERVER_INPUT_DIR)
        self.output_dir = Path(output_dir or SERVER_OUTPUT_DIR)
        self.processed_dir = Path(processed_dir or SERVER_PROCESSED_DIR)

        # Verzeichnisse anlegen
        for d in [self.input_dir, self.output_dir, self.processed_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.analyzer = EmpireAnalyzer()
        self.formatter = OutputFormatter(str(self.output_dir))
        self.daemon = WatchDaemon(str(self.input_dir), self.process_file)
        self.auto_push = auto_push
        self._processed_count = 0

    async def start(self):
        """Starte als Daemon (Watch-Modus)."""
        logger.info("=" * 60)
        logger.info("  Empire Data Pipeline — Daemon gestartet")
        logger.info(f"  Input:     {self.input_dir}")
        logger.info(f"  Output:    {self.output_dir}")
        logger.info(f"  Processed: {self.processed_dir}")
        logger.info(f"  Auto-Push: {self.auto_push}")
        logger.info("=" * 60)
        await self.daemon.start()

    async def stop(self):
        """Stoppe Daemon."""
        await self.daemon.stop()
        logger.info(f"Pipeline gestoppt — {self._processed_count} Dateien verarbeitet")

    async def process_file(self, file_path: str) -> dict | None:
        """
        Kompletter Flow für eine Datei:
          1. Extract  — Rohinhalt lesen
          2. Analyze  — 3-Layer AI (Qwen → DeepSeek → Verify)
          3. Format   — Markdown + JSON in iCloud-Ordner
          4. Archive  — Originaldatei → /data/processed/
          5. Push     — Optional: Ergebnisse → Mac/iCloud
        """
        fp = Path(file_path)
        if not fp.exists():
            logger.error(f"Datei nicht gefunden: {fp}")
            return None

        logger.info(f"\n{'─'*50}")
        logger.info(f"📥 Verarbeite: {fp.name}")

        try:
            # Phase 1: Extract
            processor = get_processor(fp)
            extracted = await processor.process()
            logger.info(f"  ✓ Extrahiert: {extracted.get('content_type', '?')}")

            # Phase 2: Analyze (3 Layers)
            analysis = await self.analyzer.analyze(extracted)
            icloud_folder = analysis.get("final", {}).get("icloud_folder", "Sonstiges")
            importance = analysis.get("final", {}).get("importance", "?")
            logger.info(f"  ✓ Analysiert: [{importance}] → {icloud_folder}/")

            # Phase 3: Format & Save
            outputs = await self.formatter.format_and_save(extracted, analysis)
            logger.info(f"  ✓ Gespeichert: {outputs['markdown']}")

            # Phase 4: Archive Original
            archive_path = self.processed_dir / fp.name
            shutil.move(str(fp), str(archive_path))
            logger.info(f"  ✓ Archiviert: {archive_path}")

            self._processed_count += 1

            # Phase 5: Auto-Push nach iCloud (optional)
            if self.auto_push:
                generate_index(self.output_dir)
                await push_results_to_mac(self.output_dir)

            logger.info(f"  ✅ FERTIG: {fp.name} ({analysis.get('total_analysis_time_s', '?')}s)")
            return {
                "file": fp.name,
                "icloud_folder": icloud_folder,
                "importance": importance,
                "outputs": outputs,
            }

        except Exception as e:
            logger.error(f"  ❌ FEHLER bei {fp.name}: {e}", exc_info=True)
            return {"file": fp.name, "error": str(e)}

    async def process_batch(self) -> list[dict]:
        """Verarbeite alle Dateien die gerade in input_dir liegen."""
        files = [
            f for f in self.input_dir.iterdir()
            if f.is_file() and not f.name.startswith(".")
        ]
        if not files:
            logger.info("Keine Dateien in input_dir gefunden")
            return []

        logger.info(f"Batch: {len(files)} Dateien")
        results = []
        for f in files:
            result = await self.process_file(str(f))
            if result:
                results.append(result)

        # Index + Push nach Batch
        generate_index(self.output_dir)
        if self.auto_push:
            await push_results_to_mac(self.output_dir)

        logger.info(f"\nBatch fertig: {len(results)}/{len(files)} erfolgreich")
        return results


# ─── CLI ─────────────────────────────────────────────────────────────────────

async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "daemon"

    if cmd == "status":
        import json
        print(json.dumps(pipeline_status(), indent=2, ensure_ascii=False))

    elif cmd == "push":
        generate_index()
        result = await push_results_to_mac()
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "index":
        path = generate_index()
        print(f"Index erstellt: {path}")

    elif cmd == "process" and len(sys.argv) > 2:
        file_arg = sys.argv[2]
        processor = EmpireDataProcessor()
        result = await processor.process_file(file_arg)
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    elif cmd == "batch":
        auto_push = "--push" in sys.argv
        processor = EmpireDataProcessor(auto_push=auto_push)
        results = await processor.process_batch()
        import json
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))

    elif cmd in ("daemon", "watch", "start"):
        auto_push = "--push" in sys.argv
        processor = EmpireDataProcessor(auto_push=auto_push)
        try:
            await processor.start()
            while True:
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            logger.info("\nStoppe...")
            await processor.stop()

    else:
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
