"""Bank Importer - Multi-language financial data processing."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode

from .banks import KrungsriTextParser
from .config import ConfigManager
from .models import BankAccount, DatabaseManager, TargetCompletion, Transaction
from .processor import Processor

__all__ = [
    "BankAccount",
    "ConfigManager",
    "DatabaseManager",
    "KrungsriTextParser",
    "Processor",
    "TargetCompletion",
    "Transaction",
]
