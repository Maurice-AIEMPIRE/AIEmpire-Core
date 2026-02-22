"""
Main Data Processor - Orchestriert den gesamten Prozess
"""

import asyncio
from pathlib import Path
from typing import Dict, Any
import logging

from watch_daemon import WatchDaemon
from processors import (
    PDFProcessor,
    ImageProcessor,
    AudioProcessor,
    JSONProcessor,
    CSVProcessor,
    OfficeProcessor,
)
from analyzer import HybridAnalyzer
from output_formatter import OutputFormatter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Hauptprozess: Watch → Extract → Analyze → Format → Output"""

    def __init__(
        self,
        input_dir="/data/input",
        output_dir="/data/results",
        processed_dir="/data/processed",
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self.analyzer = HybridAnalyzer()
        self.formatter = OutputFormatter(output_dir)
        self.daemon = WatchDaemon(input_dir, self.process_file)

    async def start(self):
        """Starte Data Processor"""
        logger.info("🚀 Data Processor gestartet")
        await self.daemon.start()

    async def stop(self):
        """Stoppe Data Processor"""
        await self.daemon.stop()

    async def process_file(self, file_path: str):
        """Kompletter Prozess: Extract → Analyze → Format"""
        try:
            file_path = Path(file_path)
            logger.info(f"⚙️  Verarbeite: {file_path.name}")

            # Phase 1: Extract
            processor = self._get_processor(file_path)
            extracted = await processor.process()
            logger.info(f"✅ Extrahiert: {file_path.name}")

            # Phase 2: Analyze
            analysis = await self.analyzer.analyze(extracted)
            logger.info(f"🧠 Analysiert: {file_path.name}")

            # Phase 3: Format & Save
            outputs = await self.formatter.format_and_save(extracted, analysis)
            logger.info(f"📁 Gespeichert: {file_path.name}")

            # Phase 4: Move to processed
            import shutil

            processed_file = self.processed_dir / file_path.name
            shutil.move(str(file_path), str(processed_file))
            logger.info(f"✨ Fertig: {file_path.name}")

        except Exception as e:
            logger.error(f"❌ Fehler bei {file_path.name}: {str(e)}")

    def _get_processor(self, file_path: Path):
        """Wähle richtigen Prozessor basierend auf Dateityp"""
        suffix = file_path.suffix.lower()

        processors = {
            ".pdf": PDFProcessor,
            ".jpg": ImageProcessor,
            ".jpeg": ImageProcessor,
            ".png": ImageProcessor,
            ".mp3": AudioProcessor,
            ".wav": AudioProcessor,
            ".m4a": AudioProcessor,
            ".json": JSONProcessor,
            ".csv": CSVProcessor,
            ".docx": OfficeProcessor,
            ".xlsx": OfficeProcessor,
            ".pptx": OfficeProcessor,
        }

        processor_class = processors.get(suffix, JSONProcessor)
        return processor_class(str(file_path))


async def main():
    """Hauptprogramm"""
    processor = DataProcessor()
    try:
        await processor.start()
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Stoppe Data Processor...")
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(main())
