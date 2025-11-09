# Copyright (C) 2025 Jochem van Grondelle <jochem@vangrondelle.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the PolyForm Noncommercial License 1.0.0.
# You may not use this program except in compliance with the License.
# A copy of the License is available at https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# PolyForm Noncommercial License 1.0.0 for more details.

"""Bank Importer - Multi-language financial data processing."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode

from bank_importer.banks import KrungsriTextParser
from bank_importer.config import ConfigManager
from bank_importer.library import (
    detect_parser,
    export_transactions,
    get_parser,
    get_translation_service_from_config,
    import_file,
    list_parsers,
    list_targets,
    parse_file,
    translate_text,
)
from bank_importer.models import (
    BankAccount,
    DatabaseManager,
    TargetCompletion,
    Transaction,
)
from bank_importer.processor import Processor

__all__ = [
    "BankAccount",
    "ConfigManager",
    "DatabaseManager",
    "KrungsriTextParser",
    "Processor",
    "TargetCompletion",
    "Transaction",
    # Library API
    "detect_parser",
    "export_transactions",
    "get_parser",
    "get_translation_service_from_config",
    "import_file",
    "list_parsers",
    "list_targets",
    "parse_file",
    "translate_text",
]
