"""Bank-specific parsers."""

from .generic_csv import GenericCsvParser
from .generic_fixed_width import GenericFixedWidthParser
from .generic_json import GenericJsonParser
from .krungsri_pdf import KrungsriPdfParser
from .krungsri_text import KrungsriTextParser
from .scb_pdf import ScbPdfParser

__all__ = [
    "GenericCsvParser",
    "GenericFixedWidthParser",
    "GenericJsonParser",
    "KrungsriPdfParser",
    "KrungsriTextParser",
    "ScbPdfParser",
]
