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

"""System endpoints."""

import contextlib
import os
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from bank_importer.api.dependencies import get_db_manager
from bank_importer.api.schemas.common import HealthResponse, VersionResponse
from bank_importer.models.database import DatabaseManager
from bank_importer.version import get_version, get_version_info

router = APIRouter()


@router.get("/health", tags=["System"])
async def get_health(
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
) -> HealthResponse:
    """Health check endpoint that verifies database connectivity and dependencies."""
    # Check database connectivity
    try:
        # Execute a simple query to verify database is accessible
        db.conn.execute("SELECT 1").fetchone()
    except Exception as e:
        # Database is not accessible - return 503 Service Unavailable
        raise HTTPException(
            status_code=503,
            detail=f"Database connectivity check failed: {e!s}",
        )

    # All checks passed
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=get_version(),
    )


@router.get("/version", tags=["System"])
async def get_version_endpoint() -> VersionResponse:
    """Get version information."""
    version_info = get_version_info()
    build_date = None
    git_commit = None

    # Get build date from environment
    build_date_str = os.environ.get("BUILD_DATE")
    if build_date_str:
        with contextlib.suppress(ValueError):
            build_date = datetime.fromisoformat(build_date_str)

    # Get git commit from environment
    git_commit = os.environ.get("GIT_COMMIT")

    return VersionResponse(
        version=version_info["version"],
        build_date=build_date,
        git_commit=git_commit,
    )
