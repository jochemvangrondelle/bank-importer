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

"""Target completion model for tracking processing status."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from bank_importer.models.enums import TargetCompletionStatus


class TargetCompletion(BaseModel):
    """Track completion status for targets."""

    # Primary key
    id: int | None = Field(default=None, description="Primary key")

    # Foreign key to transaction
    transaction_id: int = Field(description="Transaction ID")
    target_name: str = Field(max_length=100, description="Target name")

    # Completion tracking
    status: str = Field(
        max_length=50,
        description="Status (stored as string, use status_enum property)",
    )
    completed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None)
    retry_count: int = Field(default=0)

    @property
    def status_enum(self) -> TargetCompletionStatus:
        """Get status as enum."""
        try:
            return TargetCompletionStatus(self.status)
        except ValueError:
            # Fallback for legacy values
            return TargetCompletionStatus.PENDING

    @status_enum.setter
    def status_enum(self, value: TargetCompletionStatus) -> None:
        """Set status from enum."""
        self.status = value.value

    def to_dict(self) -> dict[str, Any]:
        """Convert target completion to dictionary."""
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "target_name": self.target_name,
            "status": self.status,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }
