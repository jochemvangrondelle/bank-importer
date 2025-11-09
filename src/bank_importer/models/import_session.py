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

"""Import session model for tracking file processing batches."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from bank_importer.models.enums import ImportStatus


class ImportSession(BaseModel):
    """Track import sessions for file processing."""

    # Primary key
    id: int | None = Field(default=None, description="Primary key")

    # Core session data
    account_name: str = Field(max_length=200, description="Account name")
    bank_name: str = Field(max_length=100, description="Bank name")
    session_name: str = Field(
        max_length=100,
        description="Session name (e.g., '2024-11', '2024-12', 'manual_import')",
    )
    file_path: str = Field(max_length=500, description="File path")
    file_hash: str = Field(
        max_length=64,
        description="File hash for deduplication",
    )
    status: str = Field(
        max_length=20,
        description="Status (stored as string, use status_enum property)",
    )

    # Processing statistics
    total_transactions: int = Field(default=0)
    processed_transactions: int = Field(default=0)
    error_count: int = Field(default=0)

    # Timestamps
    started_at: datetime = Field(description="Session start time")
    completed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)

    @property
    def status_enum(self) -> ImportStatus:
        """Get status as enum."""
        try:
            return ImportStatus(self.status)
        except ValueError:
            # Fallback for legacy values
            return ImportStatus.PENDING

    @status_enum.setter
    def status_enum(self, value: ImportStatus) -> None:
        """Set status from enum."""
        self.status = value.value

    @property
    def is_completed(self) -> bool:
        """Check if import session is completed."""
        return self.status_enum == ImportStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if import session failed."""
        return self.status_enum == ImportStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        """Convert import session to dictionary."""
        return {
            "id": self.id,
            "account_name": self.account_name,
            "bank_name": self.bank_name,
            "session_name": self.session_name,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "status": self.status,
            "total_transactions": self.total_transactions,
            "processed_transactions": self.processed_transactions,
            "error_count": self.error_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "error_message": self.error_message,
        }
