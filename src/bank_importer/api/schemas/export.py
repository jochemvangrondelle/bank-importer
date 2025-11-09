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

"""Export API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from bank_importer.models.export_session import ExportSession


class ExportRequest(BaseModel):
    """Export request schema."""

    target_name: str | None = Field(
        None,
        description="Specific target to export to (if not provided, exports to all enabled targets)",
    )
    account_name: str | None = Field(
        None,
        description="Specific account to export (if not provided, exports all accounts)",
    )
    date_from: datetime | None = Field(
        None,
        description="Export transactions from this date",
    )
    date_to: datetime | None = Field(
        None,
        description="Export transactions to this date",
    )
    dry_run: bool = Field(default=False, description="Whether to perform a dry run")


class ExportJobResponse(BaseModel):
    """Export job response schema."""

    job_id: str = Field(..., description="Job identifier")
    status: str = Field(
        ...,
        description="Job status",
        examples=["pending", "processing", "completed", "failed"],
    )
    message: str | None = Field(None, description="Status message")


class ExportSessionResponse(BaseModel):
    """Export session response schema."""

    id: int | None = None
    session_name: str
    target_name: str
    account_reference: str
    status: str
    total_transactions: int = 0
    exported_transactions: int = 0
    skipped_transactions: int = 0
    error_transactions: int = 0
    output_file: str | None = None
    session_metadata: str | None = None
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def from_export_session(cls, session: ExportSession) -> "ExportSessionResponse":
        """Create from ExportSession model."""
        return cls(
            id=session.id,
            session_name=session.session_name,
            target_name=session.target_name,
            account_reference=session.account_reference,
            status=session.status,
            total_transactions=session.total_transactions,
            exported_transactions=session.exported_transactions,
            skipped_transactions=session.skipped_transactions,
            error_transactions=session.error_transactions,
            output_file=session.output_file,
            session_metadata=session.session_metadata,
            error_message=session.error_message,
            started_at=session.started_at,
            completed_at=session.completed_at,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExportSessionResponse":
        """Create from dictionary."""
        return cls(**data)
