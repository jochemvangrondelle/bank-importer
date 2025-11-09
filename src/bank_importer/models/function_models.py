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

"""Pydantic models for function parameters to reduce argument count."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from bank_importer.models.enums import (
    Language,
    LogLevel,
    get_language_en,
    get_language_th,
)


class LoggingConfig(BaseModel):
    """Configuration for logging setup."""

    log_level: LogLevel | str | None = Field(
        default=None,
        description="Overall logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_file: str | None = Field(
        default=None,
        description="Optional log file path",
    )
    log_dir: str = Field(
        default="./logs",
        description="Directory for log files",
    )
    enable_rich: bool = Field(
        default=True,
        description="Whether to use Rich formatting for console output",
    )
    console_level: LogLevel | str = Field(
        default=LogLevel.INFO,
        description="Console logging level",
    )
    file_level: LogLevel | str = Field(
        default=LogLevel.DEBUG,
        description="File logging level",
    )


class ExportSessionUpdate(BaseModel):
    """Update parameters for export session."""

    session_id: int = Field(description="Export session ID")
    status: str | None = Field(default=None, description="Session status")
    total_transactions: int | None = Field(
        default=None,
        description="Total number of transactions",
    )
    exported_transactions: int | None = Field(
        default=None,
        description="Number of exported transactions",
    )
    skipped_transactions: int | None = Field(
        default=None,
        description="Number of skipped transactions",
    )
    error_transactions: int | None = Field(
        default=None,
        description="Number of error transactions",
    )
    output_file: str | None = Field(default=None, description="Output file path")
    session_metadata: str | None = Field(
        default=None,
        description="Session metadata",
    )
    error_message: str | None = Field(default=None, description="Error message")
    completed_at: datetime | None = Field(
        default=None,
        description="Completion timestamp",
    )


class TranslationConfig(BaseModel):
    """Configuration for translation."""

    description: str = Field(description="Text to translate")
    use_cache: bool = Field(
        default=True,
        description="Whether to use translation cache",
    )
    api_key: str | None = Field(default=None, description="Google Translate API key")
    source_language: Language = Field(
        default_factory=get_language_th,
        description="Source language code (ISO 639-1)",
    )
    target_language: Language = Field(
        default_factory=get_language_en,
        description="Target language code (ISO 639-1)",
    )
    term_mappings: dict[str, str] | None = Field(
        default=None,
        description="Dictionary of term mappings",
    )
    use_term_mapping: bool = Field(
        default=True,
        description="Whether to apply term mappings",
    )
    use_api_translation: bool = Field(
        default=True,
        description="Whether to use API translation",
    )


class ImportFilesConfig(BaseModel):
    """Configuration for importing files."""

    paths: list[Path] | None = Field(
        default=None,
        description="Paths to files or directories to import",
    )
    config_file: str = Field(
        default="config.toml",
        description="Configuration file path",
    )
    account: str | None = Field(default=None, description="Account name to process")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    dry_run: bool = Field(default=False, description="Dry run mode")
    reprocess_existing: bool = Field(
        default=False,
        description="Reprocess existing files",
    )
