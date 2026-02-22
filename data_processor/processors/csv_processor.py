"""
CSV Processor - Liest und analysiert CSV-Dateien
"""

import csv
from typing import Dict, Any, List
from .base import BaseProcessor
import logging

logger = logging.getLogger(__name__)


class CSVProcessor(BaseProcessor):
    """Verarbeitet CSV-Dateien"""

    async def extract(self) -> Dict[str, Any]:
        """Lese CSV und erkenne Struktur"""
        try:
            rows = []
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                for row in reader:
                    rows.append(row)

            return {
                "content_type": "csv",
                "headers": headers,
                "record_count": len(rows),
                "sample_rows": rows[:5],  # Nur erste 5 zeigen
                "all_rows": rows,
            }
        except Exception as e:
            logger.error(f"CSV Parse-Fehler: {str(e)}")
            return {
                "content_type": "csv",
                "processing_status": "error",
                "error": str(e),
            }
