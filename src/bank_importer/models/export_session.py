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

"""Export session model for tracking transaction exports."""

from datetime import datetime

from pydantic import BaseModel, Field

from bank_importer.models.enums import ExportedTransactionStatus, ExportStatus


class ExportSession(BaseModel):
    """Export session model."""

    id: int | None = Field(default=None, description="Primary key")
    session_name: str = Field(description="Session name")
    target_name: str = Field(description="Target name")
    account_reference: str = Field(description="Account reference")
    status: str = Field(
        default="processing",
        description="Status (stored as string, use status_enum property)",
    )
    total_transactions: int = Field(default=0)
    exported_transactions: int = Field(default=0)
    skipped_transactions: int = Field(default=0)
    error_transactions: int = Field(default=0)
    output_file: str | None = Field(default=None)
    session_metadata: str | None = Field(default=None, description="JSON string")
    error_message: str | None = Field(default=None)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = Field(default=None)

    @property
    def status_enum(self) -> ExportStatus:
        """Get status as enum."""
        try:
            return ExportStatus(self.status)
        except ValueError:
            # Fallback for legacy values
            return ExportStatus.PROCESSING

    @status_enum.setter
    def status_enum(self, value: ExportStatus) -> None:
        """Set status from enum."""
        self.status = value.value


class ExportedTransaction(BaseModel):
    """Model to track which transactions have been exported to which targets."""

    id: int | None = Field(default=None, description="Primary key")
    transaction_id: int = Field(description="Transaction ID")
    target_name: str = Field(description="Target name")
    export_session_id: int = Field(description="Export session ID")
    exported_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(
        default="exported",
        description="Status (stored as string, use status_enum property)",
    )
    error_message: str | None = Field(default=None)

    @property
    def status_enum(self) -> ExportedTransactionStatus:
        """Get status as enum."""
        try:
            return ExportedTransactionStatus(self.status)
        except ValueError:
            # Fallback for legacy values
            return ExportedTransactionStatus.EXPORTED

    @status_enum.setter
    def status_enum(self, value: ExportedTransactionStatus) -> None:
        """Set status from enum."""
        self.status = value.value
