"""
Base Processor - Abstrakte Klasse für alle Prozessoren
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Base class für alle Datei-Prozessoren"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_name = self.file_path.name
        self.file_type = self.file_path.suffix.lower()

    @abstractmethod
    async def extract(self) -> Dict[str, Any]:
        """Extrahiere Rohdaten aus Datei"""
        pass

    async def process(self) -> Dict[str, Any]:
        """Kompletter Prozess: Extract → Analyse → Return"""
        logger.info(f"📄 Verarbeite {self.file_name}...")
        try:
            data = await self.extract()
            data["file_name"] = self.file_name
            data["file_type"] = self.file_type
            data["processing_status"] = "success"
            return data
        except Exception as e:
            logger.error(f"❌ Fehler bei {self.file_name}: {str(e)}")
            return {
                "file_name": self.file_name,
                "file_type": self.file_type,
                "processing_status": "error",
                "error": str(e),
            }
