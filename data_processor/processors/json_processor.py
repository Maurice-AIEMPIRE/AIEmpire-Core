"""
JSON Processor - Liest und strukturiert JSON-Dateien
"""

import json
from typing import Dict, Any
from .base import BaseProcessor
import logging

logger = logging.getLogger(__name__)


class JSONProcessor(BaseProcessor):
    """Verarbeitet JSON-Dateien"""

    async def extract(self) -> Dict[str, Any]:
        """Lese JSON und validiere Struktur"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {
                "content_type": "json",
                "data": data,
                "schema_keys": list(data.keys()) if isinstance(data, dict) else None,
                "record_count": len(data) if isinstance(data, list) else 1,
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse-Fehler: {str(e)}")
            return {
                "content_type": "json",
                "processing_status": "error",
                "error": f"Ungültige JSON: {str(e)}",
            }
