"""
Image Processor - OCR + Bilderkennung
"""

from typing import Dict, Any
from .base import BaseProcessor
import logging

logger = logging.getLogger(__name__)


class ImageProcessor(BaseProcessor):
    """Verarbeitet Bilder mit OCR"""

    async def extract(self) -> Dict[str, Any]:
        """OCR auf Bildern"""
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            logger.warning("Pillow/pytesseract nicht installiert")
            return {"error": "Dependencies nicht installiert"}

        try:
            img = Image.open(self.file_path)
            text = pytesseract.image_to_string(img)

            return {
                "content_type": "image",
                "ocr_text": text,
                "image_size": img.size,
                "image_format": img.format,
            }
        except Exception as e:
            logger.error(f"OCR-Fehler: {str(e)}")
            return {
                "content_type": "image",
                "ocr_text": "[OCR fehlgeschlagen]",
                "error": str(e),
            }
