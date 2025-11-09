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

"""Database endpoints."""

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from bank_importer.api.dependencies import get_config_manager, get_db_manager
from bank_importer.api.security import require_auth
from bank_importer.config import ConfigManager
from bank_importer.models.database import DatabaseManager

router = APIRouter()


@router.post("/init", tags=["Database"])
async def init_database(
    *,
    reset: bool = False,
    config: ConfigManager = Depends(get_config_manager),
    _: dict = Depends(require_auth),
) -> dict[str, str]:
    """Initialize database."""
    db_url = config.get_database_url()

    if reset:
        # Delete existing database file if DuckDB
        if db_url.startswith("duckdb:///"):
            db_path = db_url.replace("duckdb:///", "")
            db_file = Path(db_path)
            if db_file.exists():
                db_file.unlink()
        elif db_url.startswith("duckdb:"):
            db_path = db_url.replace("duckdb:", "")
            db_file = Path(db_path)
            if db_file.exists():
                db_file.unlink()

    # Initialize database (tables are created automatically)
    DatabaseManager(db_url)

    return {
        "message": "Database initialized successfully",
        "database_url": db_url,
    }


@router.get("/stats", tags=["Database"])
async def get_database_stats(
    db: Annotated[DatabaseManager, Depends(get_db_manager)],
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> dict[str, Any]:
    """Get database statistics."""
    # Count transactions
    result = db.conn.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = result.fetchone()[0] if result else 0

    # Count import sessions
    result = db.conn.execute("SELECT COUNT(*) FROM import_sessions")
    total_import_sessions = result.fetchone()[0] if result else 0

    # Count export sessions
    result = db.conn.execute("SELECT COUNT(*) FROM export_sessions")
    total_export_sessions = result.fetchone()[0] if result else 0

    # Get database size
    db_url = config.get_database_url()
    database_size = 0
    database_path = ""

    if db_url.startswith("duckdb:///"):
        db_path = db_url.replace("duckdb:///", "")
        db_file = Path(db_path)
        if db_file.exists():
            database_size = db_file.stat().st_size
            database_path = str(db_file.absolute())
    elif db_url.startswith("duckdb:"):
        db_path = db_url.replace("duckdb:", "")
        db_file = Path(db_path)
        if db_file.exists():
            database_size = db_file.stat().st_size
            database_path = str(db_file.absolute())

    return {
        "total_transactions": total_transactions or 0,
        "total_import_sessions": total_import_sessions or 0,
        "total_export_sessions": total_export_sessions or 0,
        "database_size": database_size,
        "database_path": database_path,
    }
