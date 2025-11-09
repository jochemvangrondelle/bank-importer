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

"""Export endpoints."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from bank_importer.api.dependencies import get_db_manager, get_processor
from bank_importer.api.schemas.export import (
    ExportJobResponse,
    ExportRequest,
    ExportSessionResponse,
)
from bank_importer.api.security import require_auth
from bank_importer.models.database import DatabaseManager

router = APIRouter()


def _process_export_sync(
    processor: Any,
    target_name: str | None,
) -> dict[str, Any]:
    """Synchronous export processing (runs in background thread)."""
    results = {}
    try:
        target_manager = processor.target_manager

        if target_name:
            results = target_manager.export_all_files_and_consolidated(target_name)
        else:
            # Export to all enabled targets
            targets_config = processor.config_manager.config.get("targets", [])
            for target_config in targets_config:
                tgt_name = target_config.get("name")
                enabled = target_config.get("enabled", False)
                if enabled and tgt_name in target_manager.targets:
                    target_results = target_manager.export_all_files_and_consolidated(
                        tgt_name,
                    )
                    results.update(target_results)
    except Exception:
        # Log error - in production, you'd want to track this in the job
        pass
    return results


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Export"],
)
async def export_transactions(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    processor: Annotated[Any, Depends(get_processor)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> ExportJobResponse:
    """Export transactions (async job).

    Uses FastAPI BackgroundTasks to run blocking operations asynchronously.
    The actual processing happens in a background thread, allowing the API
    to return immediately with a job ID.
    """
    job_id = str(uuid.uuid4())

    # Add background task for processing
    # In production, you'd want to use a proper job queue (Celery, RQ, etc.)
    background_tasks.add_task(
        _process_export_sync,
        processor,
        request.target_name,
    )

    return ExportJobResponse(
        job_id=job_id,
        status="processing",
        message="Export job started. Check export sessions for progress.",
    )


@router.get(
    "/sessions",
    tags=["Export"],
)
async def list_export_sessions(
    target_name: Annotated[
        str | None,
        Query(description="Filter by target name"),
    ] = None,
    status_filter: Annotated[str | None, Query(description="Filter by status")] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum number of results"),
    ] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip")] = 0,
    *,
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> dict[str, Any]:
    """List export sessions."""
    sessions = db.get_export_sessions(target_name=target_name)

    # Filter by status if provided
    if status_filter:
        sessions = [s for s in sessions if s.get("status") == status_filter]

    # Apply pagination
    total = len(sessions)
    sessions = sessions[offset : offset + limit]

    return {
        "sessions": [ExportSessionResponse.from_dict(s) for s in sessions],
        "total": total,
    }


@router.get(
    "/sessions/{session_id}",
    tags=["Export"],
)
async def get_export_session(
    session_id: int,
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> ExportSessionResponse:
    """Get export session."""
    sessions = db.get_export_sessions()
    export_session = next((s for s in sessions if s.get("id") == session_id), None)

    if not export_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export session {session_id} not found",
        )

    return ExportSessionResponse.from_dict(export_session)


@router.get(
    "/sessions/{session_id}/download",
    tags=["Export"],
)
async def download_export_file(
    session_id: int,
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> FileResponse:
    """Download export file."""
    sessions = db.get_export_sessions()
    export_session = next((s for s in sessions if s.get("id") == session_id), None)

    if not export_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export session {session_id} not found",
        )

    output_file = export_session.get("output_file")
    if not output_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not available",
        )

    from pathlib import Path

    file_path = Path(output_file)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found on disk",
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )
