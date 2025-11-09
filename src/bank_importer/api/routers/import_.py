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

"""Import endpoints."""

import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from bank_importer.api.dependencies import get_db_manager, get_processor
from bank_importer.api.schemas.import_ import (
    ImportFileSyncRequest,
    ImportFileSyncResponse,
    ImportJobResponse,
    ImportRequest,
    ImportSessionResponse,
)
from bank_importer.api.schemas.transaction import TransactionResponse
from bank_importer.api.security import require_auth
from bank_importer.models.database import DatabaseManager
from bank_importer.models.enums import (
    ParserName,
    ReprocessBehavior,
    TranslationBehavior,
)

router = APIRouter()


def _process_import_sync(
    processor: Any,
    account_name: str | None,
    *,
    reprocess_existing: bool,
) -> list[dict[str, Any]]:
    """Synchronous import processing (runs in background thread).

    Uses the library API for consistency across CLI, API, and library usage.
    """
    from bank_importer.library import import_file

    results = []
    try:
        if account_name:
            # Process specific account using library function
            account_config = processor.config_manager.get_account_config(account_name)
            if account_config:
                file_path = Path(account_config.get("file_path", "data/in"))
                file_pattern = account_config.get("file_pattern", "*")
                files = list(file_path.glob(file_pattern))

                for file_path in files:
                    result = import_file(
                        file_path=file_path,
                        parser_name=account_config.get("parser"),
                        account_config=account_config,
                        config_manager=processor.config_manager,
                        db_manager=processor.db_manager,
                        auto_detect=True,
                        reprocess_existing=reprocess_existing,
                        translate=True,
                    )
                    results.append(
                        {
                            "account_name": account_name,
                            "file_path": str(file_path),
                            "transactions": len(result.get("transactions", [])),
                            "skipped": len(result.get("skipped", [])),
                        },
                    )
        else:
            # Process all accounts
            all_accounts = processor.config_manager.get_all_accounts()
            for acc in all_accounts:
                account_results = list(
                    processor.process_account(
                        acc["name"],
                        reprocess_existing=reprocess_existing,
                    ),
                )
                results.extend(account_results)
    except Exception:
        # Log error - in production, you'd want to track this in the job
        pass
    return results


@router.post(
    "/files",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Import"],
)
async def import_files(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    processor: Annotated[Any, Depends(get_processor)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> ImportJobResponse:
    """Import files (async job).

    Uses FastAPI BackgroundTasks to run blocking operations asynchronously.
    The actual processing happens in a background thread, allowing the API
    to return immediately with a job ID.
    """
    job_id = str(uuid.uuid4())

    # Add background task for processing
    # In production, you'd want to use a proper job queue (Celery, RQ, etc.)
    # Convert enum to boolean for internal function
    reprocess_existing = (
        request.reprocess_behavior == ReprocessBehavior.REPROCESS_EXISTING
    )
    background_tasks.add_task(
        _process_import_sync,
        processor,
        request.account_name,
        reprocess_existing=reprocess_existing,
    )

    return ImportJobResponse(
        job_id=job_id,
        status="processing",
        message="Import job started. Check import sessions for progress.",
    )


@router.get(
    "/sessions",
    tags=["Import"],
)
async def list_import_sessions(
    account_name: Annotated[
        str | None,
        Query(description="Filter by account name"),
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
    """List import sessions."""
    if account_name:
        sessions = db.get_import_sessions_by_account(account_name)
    else:
        # Get all sessions from all accounts
        # This is a simplified version - in production, you'd want a proper query
        sessions = []
        # TODO: Implement proper query for all sessions

    # Filter by status if provided
    if status_filter:
        sessions = [s for s in sessions if s.get("status") == status_filter]

    # Apply pagination
    total = len(sessions)
    sessions = sessions[offset : offset + limit]

    return {
        "sessions": [ImportSessionResponse.from_dict(s) for s in sessions],
        "total": total,
    }


@router.get(
    "/sessions/{session_id}",
    tags=["Import"],
)
async def get_import_session(
    session_id: int,
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> ImportSessionResponse:
    """Get import session."""
    session = db.get_import_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import session {session_id} not found",
        )
    return ImportSessionResponse.from_dict(session)


@router.get(
    "/sessions/{session_id}/transactions",
    tags=["Import"],
)
async def get_import_session_transactions(
    session_id: int,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum number of results"),
    ] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip")] = 0,
    *,
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> dict[str, Any]:
    """Get transactions for import session."""
    # Verify session exists
    session = db.get_import_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import session {session_id} not found",
        )

    transactions = db.get_transactions_by_session(session_id)
    total = len(transactions)

    # Apply pagination
    transactions = transactions[offset : offset + limit]

    return {
        "transactions": [TransactionResponse.from_dict(t) for t in transactions],
        "total": total,
    }


@router.post(
    "/file",
    status_code=status.HTTP_200_OK,
    tags=["Import"],
)
async def import_file_sync(
    request: ImportFileSyncRequest,
    processor: Annotated[Any, Depends(get_processor)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> ImportFileSyncResponse:
    """Import a single file synchronously (with database).

    This endpoint provides a synchronous import operation that stores transactions
    in the database. Use this when you want immediate results and database storage.

    **Use Case**: Import a single file and store in database, get results immediately.

    **Example**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/import/file" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "file_path": "/data/in/statement.pdf",
        "account_name": "my-account",
        "parser_name": "krungsri_pdf",
        "reprocess_behavior": "skip_existing",
        "translation_behavior": "enabled"
      }'
    ```

    **Response**: Returns import results with transactions, skipped count, and session ID.
    """
    from bank_importer.library import import_file

    path = Path(request.file_path)

    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {request.file_path}",
        )

    # Get account config
    account_config = processor.config_manager.get_account_config(request.account_name)
    if not account_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found: {request.account_name}",
        )

    try:
        # Import file using library function
        # Convert enums to values/booleans for library function
        parser_name_str = (
            request.parser_name.value
            if isinstance(request.parser_name, ParserName)
            else request.parser_name
        )
        reprocess_existing = (
            request.reprocess_behavior == ReprocessBehavior.REPROCESS_EXISTING
        )
        translate = request.translation_behavior == TranslationBehavior.ENABLED
        result = import_file(
            file_path=path,
            parser_name=parser_name_str,
            account_config=account_config,
            config_manager=processor.config_manager,
            db_manager=processor.db_manager,
            auto_detect=parser_name_str is None,
            reprocess_existing=reprocess_existing,
            translate=translate,
        )

        return ImportFileSyncResponse(
            transactions=[
                TransactionResponse.from_transaction(t).model_dump()
                for t in result.get("transactions", [])
            ],
            skipped=[
                TransactionResponse.from_transaction(t).model_dump()
                for t in result.get("skipped", [])
            ],
            session_id=result.get("session_id"),
            total_processed=result.get("total_processed", 0),
            error_count=result.get("error_count", 0),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing file: {e!s}",
        ) from e
