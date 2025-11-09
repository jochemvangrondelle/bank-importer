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

"""Import API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from bank_importer.models.enums import (
    DryRunMode,
    ParserName,
    ReprocessBehavior,
    TranslationBehavior,
)
from bank_importer.models.import_session import ImportSession


class ImportRequest(BaseModel):
    """Import request schema."""

    file_paths: list[str] = Field(
        ...,
        description="List of file paths or directories to import",
    )
    account_name: str | None = Field(
        None,
        description="Specific account to process (if not provided, processes all accounts)",
    )
    reprocess_behavior: ReprocessBehavior = Field(
        default=ReprocessBehavior.SKIP_EXISTING,
        description="File reprocessing behavior: skip_existing (skip already imported files) or reprocess_existing (reprocess even if already imported)",
    )
    dry_run_mode: DryRunMode = Field(
        default=DryRunMode.DISABLED,
        description="Dry run mode: enabled (simulate without making changes) or disabled (execute normally)",
    )


class ImportJobResponse(BaseModel):
    """Import job response schema."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(
        ...,
        description="Job status",
        examples=["pending", "processing", "completed", "failed"],
    )
    message: str | None = Field(None, description="Status message")


class ImportFileSyncRequest(BaseModel):
    """Import file sync request schema."""

    file_path: str = Field(..., description="Path to file on server to import")
    account_name: str = Field(..., description="Account name (must exist in config)")
    parser_name: ParserName | None = Field(
        None,
        description="Parser name to use (auto-detect if not provided)",
    )
    reprocess_behavior: ReprocessBehavior = Field(
        default=ReprocessBehavior.SKIP_EXISTING,
        description="File reprocessing behavior: skip_existing (skip already imported files) or reprocess_existing (reprocess even if already imported)",
    )
    translation_behavior: TranslationBehavior = Field(
        default=TranslationBehavior.ENABLED,
        description="Translation behavior: enabled (translate transaction descriptions) or disabled (do not translate)",
    )


class ImportFileSyncResponse(BaseModel):
    """Import file sync response schema."""

    transactions: list[dict[str, Any]] = Field(
        ...,
        description="List of newly imported transactions",
    )
    skipped: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of skipped (duplicate) transactions",
    )
    session_id: int | None = Field(None, description="Import session ID")
    total_processed: int = Field(
        ...,
        description="Total number of transactions processed",
    )
    error_count: int = Field(default=0, description="Number of errors encountered")


class ImportSessionResponse(BaseModel):
    """Import session response schema."""

    id: int | None = None
    account_name: str
    bank_name: str
    session_name: str
    file_path: str
    file_hash: str
    status: str
    total_transactions: int = 0
    processed_transactions: int = 0
    error_count: int = 0
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None

    @classmethod
    def from_import_session(cls, session: ImportSession) -> "ImportSessionResponse":
        """Create from ImportSession model."""
        return cls(**session.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImportSessionResponse":
        """Create from dictionary."""
        return cls(**data)
