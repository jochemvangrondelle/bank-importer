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

"""Common API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(
        ...,
        description="Health status",
        examples=["healthy", "unhealthy"],
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp",
    )
    version: str | None = Field(None, description="Application version")


class VersionResponse(BaseModel):
    """Version information response schema."""

    version: str = Field(..., description="Application version")
    build_date: datetime | None = Field(None, description="Build date")
    git_commit: str | None = Field(None, description="Git commit hash")
