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

"""Status endpoints."""

import contextlib
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from bank_importer.api.dependencies import get_config_manager, get_db_manager
from bank_importer.api.schemas.import_ import ImportSessionResponse
from bank_importer.api.schemas.status import (
    AccountStatus,
    AccountStatusSummary,
    StatusResponse,
)
from bank_importer.api.security import require_auth
from bank_importer.config import ConfigManager
from bank_importer.models.database import DatabaseManager

router = APIRouter()


def _get_last_import_date(import_sessions: list[dict[str, Any]]) -> datetime | None:
    """Get the last import date from import sessions."""
    if not import_sessions:
        return None

    sorted_sessions = sorted(
        import_sessions,
        key=lambda x: x.get("started_at", ""),
        reverse=True,
    )
    if sorted_sessions[0].get("started_at"):
        last_import_str = sorted_sessions[0]["started_at"]
        with contextlib.suppress(ValueError):
            return datetime.fromisoformat(last_import_str)
    return None


def _calculate_date_range(
    transactions: list[dict[str, Any]],
) -> dict[str, datetime | None]:
    """Calculate date range from transactions."""
    date_range: dict[str, datetime | None] = {"min_date": None, "max_date": None}
    if not transactions:
        return date_range

    dates = []
    for t in transactions:
        date_val = t.get("date")
        if date_val and isinstance(date_val, (datetime, str)):
            dates.append(date_val)

    if not dates:
        return date_range

    try:
        date_objs = []
        for d in dates:
            if isinstance(d, datetime):
                date_objs.append(d)
            elif isinstance(d, str):
                date_objs.append(datetime.fromisoformat(d))
        if date_objs:
            date_range["min_date"] = min(date_objs)
            date_range["max_date"] = max(date_objs)
    except (ValueError, TypeError):
        pass

    return date_range


def _build_account_status(
    account: dict[str, Any],
    db: DatabaseManager,
) -> AccountStatus:
    """Build AccountStatus for a single account."""
    account_name = account["name"]
    transactions = db.get_transactions_by_account(account.get("account_number", ""))
    import_sessions = db.get_import_sessions_by_account(account_name)
    last_import = _get_last_import_date(import_sessions)
    date_range = _calculate_date_range(transactions)

    return AccountStatus(
        account_name=account_name,
        bank_name=account.get("bank_name", ""),
        account_number=account.get("account_number", ""),
        parser=account.get("parser"),
        transaction_count=len(transactions),
        last_import=last_import,
        date_range=date_range,
    )


def _calculate_summary(
    accounts_config: list[dict[str, Any]],
    all_sessions: list[dict[str, Any]],
    db: DatabaseManager,
) -> AccountStatusSummary:
    """Calculate account status summary."""
    total_accounts = len(accounts_config)
    total_transactions = sum(
        len(db.get_transactions_by_account(acc.get("account_number", "")))
        for acc in accounts_config
    )
    total_import_sessions = len(all_sessions)
    completed_sessions = sum(1 for s in all_sessions if s.get("status") == "completed")
    failed_sessions = sum(1 for s in all_sessions if s.get("status") == "failed")

    return AccountStatusSummary(
        total_accounts=total_accounts,
        total_transactions=total_transactions,
        total_import_sessions=total_import_sessions,
        completed_sessions=completed_sessions,
        failed_sessions=failed_sessions,
    )


@router.get("", tags=["Status"])
async def get_status(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> StatusResponse:
    """Get system status."""
    accounts_config = config.get_all_accounts()
    account_statuses = [
        _build_account_status(account, db) for account in accounts_config
    ]

    # Get all import sessions
    all_sessions = []
    for account in accounts_config:
        sessions = db.get_import_sessions_by_account(account["name"])
        all_sessions.extend(sessions)

    summary = _calculate_summary(accounts_config, all_sessions, db)

    return StatusResponse(
        accounts=account_statuses,
        summary=summary,
        import_sessions=[ImportSessionResponse.from_dict(s) for s in all_sessions],
    )


@router.get("/accounts", tags=["Status"])
async def get_account_status(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> dict[str, Any]:
    """Get account status."""
    accounts_config = config.get_all_accounts()
    account_statuses = [
        _build_account_status(account, db) for account in accounts_config
    ]

    # Get all import sessions
    all_sessions = []
    for account in accounts_config:
        sessions = db.get_import_sessions_by_account(account["name"])
        all_sessions.extend(sessions)

    summary = _calculate_summary(accounts_config, all_sessions, db)

    return {
        "accounts": account_statuses,
        "summary": summary,
    }


@router.get(
    "/accounts/{account_name}",
    tags=["Status"],
)
async def get_account_status_by_name(
    account_name: str,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict[str, Any], Depends(require_auth)],
) -> AccountStatus:
    """Get account status by name."""
    account = config.get_account_config(account_name)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_name}' not found",
        )

    return _build_account_status(account, db)
