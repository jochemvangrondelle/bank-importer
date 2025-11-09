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

"""API dependencies for dependency injection."""

from pathlib import Path

from fastapi import Depends

from bank_importer.config import ConfigManager
from bank_importer.models.database import DatabaseManager
from bank_importer.parser_detector import ParserDetector
from bank_importer.processor import Processor


def get_config_manager(config_file: str = "config.toml") -> ConfigManager:
    """Get ConfigManager instance.

    Thread-safe: ConfigManager is read-only after initialization.
    Each request gets its own instance.
    """
    return ConfigManager(Path(config_file))


def get_db_manager(
    config: ConfigManager = Depends(get_config_manager),
) -> DatabaseManager:
    """Get DatabaseManager instance.

    Thread-safe: Each request gets its own DatabaseManager instance
    with its own DuckDB connection. DuckDB supports multiple concurrent
    connections to the same database file, making this safe for use
    with multiple workers.

    The connection is automatically cleaned up when the request completes.
    """
    db_url = config.get_database_url()
    return DatabaseManager(db_url)


def get_processor(
    config: ConfigManager = Depends(get_config_manager),
    _db: DatabaseManager = Depends(get_db_manager),
) -> Processor:
    """Get Processor instance."""
    # Processor takes config_path, but we can create it with the config path
    # Note: Processor will create its own ConfigManager and DatabaseManager internally
    # For API usage, we could refactor Processor to accept config/db directly, but for now
    # we'll use the config_path approach
    return Processor(config.config_path)


def get_parser_detector() -> ParserDetector:
    """Get ParserDetector instance."""
    return ParserDetector()
