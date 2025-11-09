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

"""Status API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from bank_importer.api.schemas.import_ import ImportSessionResponse


class AccountStatusSummary(BaseModel):
    """Account status summary schema."""

    total_accounts: int = Field(..., description="Total number of accounts")
    total_transactions: int = Field(..., description="Total number of transactions")
    total_import_sessions: int = Field(
        ...,
        description="Total number of import sessions",
    )
    completed_sessions: int = Field(..., description="Number of completed sessions")
    failed_sessions: int = Field(..., description="Number of failed sessions")


class AccountStatus(BaseModel):
    """Account status schema."""

    account_name: str = Field(..., description="Account name")
    bank_name: str = Field(..., description="Bank name")
    account_number: str = Field(..., description="Account number")
    parser: str | None = Field(None, description="Parser name")
    transaction_count: int = Field(..., description="Number of transactions")
    last_import: datetime | None = Field(None, description="Last import timestamp")
    date_range: dict[str, datetime | None] = Field(
        ...,
        description="Date range of transactions",
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AccountStatus":
        """Create from dictionary."""
        return cls(**data)


class StatusResponse(BaseModel):
    """Status response schema."""

    accounts: list[AccountStatus] = Field(..., description="Account statuses")
    summary: AccountStatusSummary = Field(..., description="Summary statistics")
    import_sessions: list[ImportSessionResponse] = Field(
        ...,
        description="Import sessions",
    )
