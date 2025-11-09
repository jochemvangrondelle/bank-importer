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

"""Transaction endpoints."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from bank_importer.api.dependencies import get_db_manager
from bank_importer.api.schemas.transaction import TransactionResponse, TransactionUpdate
from bank_importer.api.security import require_auth
from bank_importer.models.database import DatabaseManager

router = APIRouter()


@router.get("", tags=["Import"])
async def list_transactions(
    account_number: Annotated[
        str | None,
        Query(description="Filter by account number"),
    ] = None,
    account_name: Annotated[
        str | None,
        Query(description="Filter by account name"),
    ] = None,
    date_from: Annotated[
        datetime | None,
        Query(description="Filter transactions from this date"),
    ] = None,
    date_to: Annotated[
        datetime | None,
        Query(description="Filter transactions to this date"),
    ] = None,
    transaction_type: Annotated[
        str | None,
        Query(description="Filter by transaction type"),
    ] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum number of results"),
    ] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of results to skip")] = 0,
    db: DatabaseManager = Depends(get_db_manager),
    _: dict = Depends(require_auth),
) -> dict[str, Any]:
    """List transactions with optional filtering."""
    transactions, total = db.get_transactions_filtered(
        account_number=account_number,
        date_from=date_from,
        date_to=date_to,
        transaction_type=transaction_type,
        category=category,
        limit=limit,
        offset=offset,
    )

    return {
        "transactions": [TransactionResponse.from_transaction(t) for t in transactions],
        "total": total,
    }


@router.get(
    "/{transaction_id}",
    tags=["Import"],
)
async def get_transaction(
    transaction_id: int,
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> TransactionResponse:
    """Get transaction by ID."""
    transaction = db.get_transaction_by_id(transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    return TransactionResponse.from_transaction(transaction)


@router.patch(
    "/{transaction_id}",
    tags=["Import"],
)
async def update_transaction(
    transaction_id: int,
    update: TransactionUpdate,
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> TransactionResponse:
    """Update transaction."""
    transaction = db.update_transaction(
        transaction_id=transaction_id,
        category=update.category,
        subcategory=update.subcategory,
        memo=update.memo,
        translated_description=update.translated_description,
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    return TransactionResponse.from_transaction(transaction)
