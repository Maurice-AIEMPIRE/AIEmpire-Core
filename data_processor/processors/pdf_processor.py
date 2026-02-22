"""
PDF Processor - Extrahiert Text + Tabellen aus PDFs
"""

import asyncio
from typing import Dict, Any
from .base import BaseProcessor
import logging

logger = logging.getLogger(__name__)


class PDFProcessor(BaseProcessor):
    """Verarbeitet PDF-Dateien"""

    async def extract(self) -> Dict[str, Any]:
        """Extrahiere Text und Metadaten aus PDF"""
        try:
            import PyPDF2
        except ImportError:
            logger.warning("PyPDF2 nicht installiert, installiere: pip install PyPDF2")
            return {"error": "PyPDF2 nicht installiert"}

        with open(self.file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)

            text_content = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                text_content.append(
                    {"page": page_num + 1, "content": text or "[kein Text]"}
                )

            return {
                "content_type": "pdf",
                "num_pages": num_pages,
                "text": text_content,
                "metadata": dict(reader.metadata or {}),
            }
