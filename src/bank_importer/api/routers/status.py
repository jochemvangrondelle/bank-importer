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


@router.get("", tags=["Status"])
async def get_status(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> StatusResponse:
    """Get system status."""
    accounts_config = config.get_all_accounts()
    account_statuses = []

    for account in accounts_config:
        account_name = account["name"]
        transactions = db.get_transactions_by_account(account.get("account_number", ""))

        # Get last import session
        import_sessions = db.get_import_sessions_by_account(account_name)
        last_import = None
        if import_sessions:
            sorted_sessions = sorted(
                import_sessions,
                key=lambda x: x.get("started_at", ""),
                reverse=True,
            )
            if sorted_sessions[0].get("started_at"):
                last_import_str = sorted_sessions[0]["started_at"]
                with contextlib.suppress(ValueError):
                    last_import = datetime.fromisoformat(
                        last_import_str,
                    )

        # Calculate date range
        date_range = {"min_date": None, "max_date": None}
        if transactions:
            dates = []
            for t in transactions:
                date_val = t.get("date")
                if date_val:
                    # Handle both datetime objects and strings
                    if isinstance(date_val, (datetime, str)):
                        dates.append(date_val)
            if dates:
                try:
                    # Convert to datetime objects if needed
                    date_objs = []
                    for d in dates:
                        if isinstance(d, datetime):
                            date_objs.append(d)
                        elif isinstance(d, str):
                            date_objs.append(
                                datetime.fromisoformat(d),
                            )
                    if date_objs:
                        date_range["min_date"] = min(date_objs)
                        date_range["max_date"] = max(date_objs)
                except (ValueError, TypeError):
                    pass

        account_statuses.append(
            AccountStatus(
                account_name=account_name,
                bank_name=account.get("bank_name", ""),
                account_number=account.get("account_number", ""),
                parser=account.get("parser"),
                transaction_count=len(transactions),
                last_import=last_import,
                date_range=date_range,
            ),
        )

    # Get all import sessions
    all_sessions = []
    for account in accounts_config:
        sessions = db.get_import_sessions_by_account(account["name"])
        all_sessions.extend(sessions)

    # Calculate summary
    total_accounts = len(accounts_config)
    total_transactions = sum(
        len(db.get_transactions_by_account(acc.get("account_number", "")))
        for acc in accounts_config
    )
    total_import_sessions = len(all_sessions)
    completed_sessions = sum(1 for s in all_sessions if s.get("status") == "completed")
    failed_sessions = sum(1 for s in all_sessions if s.get("status") == "failed")

    summary = AccountStatusSummary(
        total_accounts=total_accounts,
        total_transactions=total_transactions,
        total_import_sessions=total_import_sessions,
        completed_sessions=completed_sessions,
        failed_sessions=failed_sessions,
    )

    return StatusResponse(
        accounts=account_statuses,
        summary=summary,
        import_sessions=[ImportSessionResponse.from_dict(s) for s in all_sessions],
    )


@router.get("/accounts", tags=["Status"])
async def get_account_status(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> dict[str, Any]:
    """Get account status."""
    # Reuse get_status logic
    status_response = await get_status(config, db)
    return {
        "accounts": status_response.accounts,
        "summary": status_response.summary,
    }


@router.get(
    "/accounts/{account_name}",
    tags=["Status"],
)
async def get_account_status_by_name(
    account_name: str,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> AccountStatus:
    """Get account status by name."""
    account = config.get_account_config(account_name)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account '{account_name}' not found",
        )

    transactions = db.get_transactions_by_account(account.get("account_number", ""))

    # Get last import session
    import_sessions = db.get_import_sessions_by_account(account_name)
    last_import = None
    if import_sessions:
        sorted_sessions = sorted(
            import_sessions,
            key=lambda x: x.get("started_at", ""),
            reverse=True,
        )
        if sorted_sessions[0].get("started_at"):
            last_import_str = sorted_sessions[0]["started_at"]
            with contextlib.suppress(ValueError):
                last_import = datetime.fromisoformat(
                    last_import_str,
                )

    # Calculate date range
    date_range = {"min_date": None, "max_date": None}
    if transactions:
        dates = []
        for t in transactions:
            date_val = t.get("date")
            if date_val:
                # Handle both datetime objects and strings
                if isinstance(date_val, (datetime, str)):
                    dates.append(date_val)
        if dates:
            try:
                # Convert to datetime objects if needed
                date_objs = []
                for d in dates:
                    if isinstance(d, datetime):
                        date_objs.append(d)
                    elif isinstance(d, str):
                        date_objs.append(
                            datetime.fromisoformat(d),
                        )
                if date_objs:
                    date_range["min_date"] = min(date_objs)
                    date_range["max_date"] = max(date_objs)
            except (ValueError, TypeError):
                pass

    return AccountStatus(
        account_name=account_name,
        bank_name=account.get("bank_name", ""),
        account_number=account.get("account_number", ""),
        parser=account.get("parser"),
        transaction_count=len(transactions),
        last_import=last_import,
        date_range=date_range,
    )
