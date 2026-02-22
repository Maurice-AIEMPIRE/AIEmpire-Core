"""
File Type Processors - Verarbeitung verschiedener Dateitypen
"""

from .pdf_processor import PDFProcessor
from .image_processor import ImageProcessor
from .audio_processor import AudioProcessor
from .json_processor import JSONProcessor
from .csv_processor import CSVProcessor
from .office_processor import OfficeProcessor

__all__ = [
    "PDFProcessor",
    "ImageProcessor",
    "AudioProcessor",
    "JSONProcessor",
    "CSVProcessor",
    "OfficeProcessor",
]
