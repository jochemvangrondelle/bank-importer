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

"""Database models and management using DuckDB."""

import hashlib
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any

import duckdb

from bank_importer.models.enums import ImportStatus, TargetCompletionStatus
from bank_importer.models.export_session import ExportSession
from bank_importer.models.function_models import ExportSessionUpdate
from bank_importer.models.import_session import ImportSession
from bank_importer.models.transaction import Transaction
from bank_importer.telemetry import trace_span


class DatabaseManager:
    """Manage database operations using DuckDB.

    Thread-safe: Each instance maintains its own connection, which is safe
    for use within a single thread. Multiple instances can safely access
    the same database file concurrently.
    """

    def _extract_db_path_from_url(self, database_url: str) -> str:
        """Extract database path from URL."""
        if database_url.startswith("duckdb:///"):
            return database_url.replace("duckdb:///", "")
        if database_url.startswith("duckdb:"):
            return database_url.replace("duckdb:", "")
        if database_url == "duckdb:///:memory:":
            return ":memory:"
        if database_url.startswith("sqlite:///"):
            return database_url.replace("sqlite:///", "")
        if database_url.startswith("sqlite:"):
            return database_url.replace("sqlite:", "")
        if database_url == "sqlite:///:memory:":
            return ":memory:"
        return database_url

    def _ensure_db_directory_exists(self, db_path: str) -> None:
        """Ensure parent directory exists for file-based databases."""
        if db_path == ":memory:":
            return

        db_file = Path(db_path)
        parent_dir = db_file.parent
        if parent_dir and not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                msg = (
                    f"Cannot create database directory '{parent_dir}': {e}. "
                    f"Please ensure the directory exists and is writable, or check file permissions."
                )
                raise RuntimeError(msg) from e

    def _connect_to_database(self, db_path: str) -> None:
        """Create database connection with error handling."""
        try:
            self.conn = duckdb.connect(db_path)
        except Exception as e:
            if "Permission denied" in str(e) or "PermissionError" in str(
                type(e).__name__,
            ):
                msg = (
                    f"Cannot open database file '{db_path}': Permission denied. "
                    f"Please ensure the file/directory is writable. "
                    f"In Docker, ensure the database path is within a mounted volume (e.g., /app/data/)."
                )
                raise RuntimeError(msg) from e
            raise

    def __init__(self, database_url: str) -> None:
        """Initialize database manager.

        Args:
            database_url: Database connection URL (duckdb:///path or duckdb:path)

        """
        self.database_url = database_url
        self._closed = False

        db_path = self._extract_db_path_from_url(database_url)
        self._ensure_db_directory_exists(db_path)
        self._connect_to_database(db_path)
        self._create_tables()

    def close(self) -> None:
        """Close the database connection.

        This should be called when the DatabaseManager is no longer needed
        to ensure proper cleanup of resources.
        """
        # Check if connection attribute exists (might not if __init__ failed)
        if not hasattr(self, "conn"):
            self._closed = True
            return

        if not self._closed and self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                # Ignore errors during cleanup
                pass
            finally:
                self._closed = True
                self.conn = None  # type: ignore[assignment]

    def __enter__(self) -> "DatabaseManager":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit - ensures connection is closed."""
        self.close()

    def __del__(self) -> None:
        """Destructor - ensures connection is closed on garbage collection."""
        try:
            self.close()
        except Exception:
            # Ignore all errors during destruction - object is being garbage collected
            # and we can't do anything about errors at this point
            pass

    @contextmanager
    def _transaction(self) -> Generator[Any, None, None]:
        """Context manager for transactions.

        Thread-safe: Each transaction uses the instance's connection,
        which is safe for single-threaded use within a request.
        """
        self._ensure_connection()
        # DuckDB uses autocommit by default, but we can use BEGIN/COMMIT
        self.conn.execute("BEGIN TRANSACTION")
        try:
            yield self.conn
            self.conn.execute("COMMIT")
        except Exception:
            try:
                self.conn.execute("ROLLBACK")
            except Exception:
                pass  # Ignore rollback errors if no transaction is active
            raise

    def _get_columns(self, result: Any) -> list[str]:
        """Get column names from DuckDB result."""
        # DuckDB returns column names via .description attribute (list of tuples)
        if hasattr(result, "description") and result.description:
            return [desc[0] for desc in result.description]
        # Fallback: try .columns if available
        if hasattr(result, "columns") and result.columns:
            return list(result.columns)
        return []

    def _ensure_connection(self) -> None:
        """Ensure the database connection is open.

        Raises:
            RuntimeError: If the connection is closed

        """
        if self._closed or self.conn is None:
            msg = "Database connection is closed"
            raise RuntimeError(msg)

    def _get_next_id(self, table_name: str) -> int:
        """Get next ID for a table by finding max ID + 1."""
        self._ensure_connection()
        result = self.conn.execute(
            f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table_name}",
        ).fetchone()
        return result[0] if result else 1

    def _create_tables(self) -> None:
        """Create all tables."""
        # Transactions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                date TIMESTAMP NOT NULL,
                description VARCHAR(500) NOT NULL,
                translated_description VARCHAR(500),
                amount DECIMAL(15, 2) NOT NULL,
                balance DECIMAL(15, 2) NOT NULL,
                transaction_type VARCHAR(100) NOT NULL,
                account_number VARCHAR(50) NOT NULL,
                old_balance DECIMAL(15, 2),
                new_balance DECIMAL(15, 2),
                transaction_date TIMESTAMP,
                value_date TIMESTAMP,
                posting_date TIMESTAMP,
                effective_date TIMESTAMP,
                currency VARCHAR(3) NOT NULL,
                country_code VARCHAR(2) NOT NULL,
                channel VARCHAR(100),
                reference VARCHAR(200),
                check_number VARCHAR(50),
                memo VARCHAR(500),
                category VARCHAR(100),
                subcategory VARCHAR(100),
                exchange_rate DECIMAL(10, 6),
                foreign_currency VARCHAR(3),
                foreign_amount DECIMAL(15, 2),
                fees DECIMAL(15, 2),
                interest DECIMAL(15, 2),
                tax DECIMAL(15, 2),
                raw_text TEXT,
                raw_json TEXT,
                source_file VARCHAR(500),
                parser_name VARCHAR(100),
                unique_id VARCHAR(100),
                UNIQUE(date, amount, description, account_number, source_file, unique_id)
            )
        """)

        # Create indexes
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transaction_date ON transactions(date)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transaction_account ON transactions(account_number)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transaction_type ON transactions(transaction_type)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transaction_category ON transactions(category)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transaction_channel ON transactions(channel)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transaction_value_date ON transactions(value_date)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_transaction_source_file ON transactions(source_file)",
        )

        # Import sessions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS import_sessions (
                id INTEGER PRIMARY KEY,
                account_name VARCHAR(200) NOT NULL,
                bank_name VARCHAR(100) NOT NULL,
                session_name VARCHAR(100) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_hash VARCHAR(64) NOT NULL,
                status VARCHAR(20) NOT NULL,
                total_transactions INTEGER NOT NULL DEFAULT 0,
                processed_transactions INTEGER NOT NULL DEFAULT 0,
                error_count INTEGER NOT NULL DEFAULT 0,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                error_message TEXT,
                UNIQUE(file_hash)
            )
        """)

        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_import_session_account ON import_sessions(account_name)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_import_session_status ON import_sessions(status)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_import_session_date ON import_sessions(started_at)",
        )

        # Export sessions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS export_sessions (
                id INTEGER PRIMARY KEY,
                session_name VARCHAR(200) NOT NULL,
                target_name VARCHAR(100) NOT NULL,
                account_reference VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'processing',
                total_transactions INTEGER NOT NULL DEFAULT 0,
                exported_transactions INTEGER NOT NULL DEFAULT 0,
                skipped_transactions INTEGER NOT NULL DEFAULT 0,
                error_transactions INTEGER NOT NULL DEFAULT 0,
                output_file VARCHAR(500),
                session_metadata TEXT,
                error_message TEXT,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP
            )
        """)

        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_export_session_target ON export_sessions(target_name)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_export_session_started ON export_sessions(started_at)",
        )

        # Exported transactions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS exported_transactions (
                id INTEGER PRIMARY KEY,
                transaction_id INTEGER NOT NULL,
                target_name VARCHAR(100) NOT NULL,
                export_session_id INTEGER NOT NULL,
                exported_at TIMESTAMP NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'exported',
                error_message TEXT
            )
        """)

        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_exported_transaction_id ON exported_transactions(transaction_id)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_exported_target ON exported_transactions(target_name)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_exported_session ON exported_transactions(export_session_id)",
        )

        # Target completions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS target_completions (
                id INTEGER PRIMARY KEY,
                transaction_id INTEGER NOT NULL,
                target_name VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL,
                completed_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER NOT NULL DEFAULT 0,
                UNIQUE(transaction_id, target_name)
            )
        """)

        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_target_completion_status ON target_completions(status)",
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_target_completion_target ON target_completions(target_name)",
        )

        # Bank accounts table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bank_accounts (
                id INTEGER PRIMARY KEY,
                account_number VARCHAR(50) NOT NULL UNIQUE,
                account_name VARCHAR(200) NOT NULL,
                bank_name VARCHAR(100) NOT NULL,
                currency VARCHAR(3) NOT NULL,
                country_code VARCHAR(2) NOT NULL,
                branch_name VARCHAR(100),
                reference VARCHAR(200)
            )
        """)

        self.conn.commit()

    def _transaction_to_dict(self, row: dict[str, Any]) -> dict[str, Any]:
        """Convert database row to transaction dictionary."""
        return {
            "id": row.get("id"),
            "date": row.get("date"),
            "description": row.get("description"),
            "translated_description": row.get("translated_description"),
            "amount": float(row["amount"]) if row.get("amount") is not None else None,
            "balance": float(row["balance"])
            if row.get("balance") is not None
            else None,
            "old_balance": float(row["old_balance"])
            if row.get("old_balance") is not None
            else None,
            "new_balance": float(row["new_balance"])
            if row.get("new_balance") is not None
            else None,
            "transaction_type": row.get("transaction_type"),
            "account_number": row.get("account_number"),
            "transaction_date": row.get("transaction_date"),
            "value_date": row.get("value_date"),
            "posting_date": row.get("posting_date"),
            "effective_date": row.get("effective_date"),
            "currency": row.get("currency"),
            "country_code": row.get("country_code"),
            "channel": row.get("channel"),
            "reference": row.get("reference"),
            "check_number": row.get("check_number"),
            "memo": row.get("memo"),
            "category": row.get("category"),
            "subcategory": row.get("subcategory"),
            "exchange_rate": float(row["exchange_rate"])
            if row.get("exchange_rate") is not None
            else None,
            "foreign_currency": row.get("foreign_currency"),
            "foreign_amount": float(row["foreign_amount"])
            if row.get("foreign_amount") is not None
            else None,
            "fees": float(row["fees"]) if row.get("fees") is not None else None,
            "interest": float(row["interest"])
            if row.get("interest") is not None
            else None,
            "tax": float(row["tax"]) if row.get("tax") is not None else None,
            "raw_text": row.get("raw_text"),
            "raw_json": row.get("raw_json"),
            "source_file": row.get("source_file"),
            "parser_name": row.get("parser_name"),
        }

    def _transaction_from_model(self, transaction: Transaction) -> dict[str, Any]:
        """Convert Transaction model to database row."""
        return {
            "id": transaction.id,
            "date": transaction.date,
            "description": transaction.description,
            "translated_description": transaction.translated_description,
            "amount": str(transaction.amount),
            "balance": str(transaction.balance),
            "old_balance": str(transaction.old_balance)
            if transaction.old_balance
            else None,
            "new_balance": str(transaction.new_balance)
            if transaction.new_balance
            else None,
            "transaction_type": transaction.transaction_type,
            "account_number": transaction.account_number,
            "transaction_date": transaction.transaction_date,
            "value_date": transaction.value_date,
            "posting_date": transaction.posting_date,
            "effective_date": transaction.effective_date,
            "currency": transaction.currency,
            "country_code": transaction.country_code,
            "channel": transaction.channel,
            "reference": transaction.reference,
            "check_number": transaction.check_number,
            "memo": transaction.memo,
            "category": transaction.category,
            "subcategory": transaction.subcategory,
            "exchange_rate": str(transaction.exchange_rate)
            if transaction.exchange_rate
            else None,
            "foreign_currency": transaction.foreign_currency,
            "foreign_amount": str(transaction.foreign_amount)
            if transaction.foreign_amount
            else None,
            "fees": str(transaction.fees) if transaction.fees else None,
            "interest": str(transaction.interest) if transaction.interest else None,
            "tax": str(transaction.tax) if transaction.tax else None,
            "raw_text": transaction.raw_text,
            "raw_json": transaction.raw_json,
            "source_file": transaction.source_file,
            "parser_name": transaction.parser_name,
            "unique_id": transaction.unique_id,
        }

    def add_transaction(self, transaction: Transaction) -> tuple[int, bool]:
        """Add transaction to database.

        Returns:
            tuple: (transaction_id, is_new) where is_new indicates if this was a new transaction

        """
        with trace_span(
            "db_add_transaction",
            {
                "account_number": transaction.account_number,
                "source_file": transaction.source_file,
            },
        ):
            # Generate unique ID for the transaction if not already set
            if not transaction.unique_id:
                transaction.unique_id = self._generate_unique_id(transaction)

            with self._transaction():
                try:
                    # Check if transaction already exists
                    existing = self.conn.execute(
                        """
                        SELECT id FROM transactions
                        WHERE date = ? AND amount = ? AND description = ?
                          AND account_number = ? AND source_file = ? AND unique_id = ?
                    """,
                        [
                            transaction.date,
                            str(transaction.amount),
                            transaction.description,
                            transaction.account_number,
                            transaction.source_file,
                            transaction.unique_id,
                        ],
                    ).fetchone()

                    if existing:
                        return existing[0], False

                    # Insert new transaction
                    data = self._transaction_from_model(transaction)
                    columns = [k for k in data if data[k] is not None]
                    values = [data[k] for k in columns]
                    placeholders = ", ".join(["?" for _ in columns])
                    col_names = ", ".join(columns)

                    # Insert and get ID using RETURNING
                    # Exclude id from insert if it's None, generate new ID
                    transaction_id: int
                    existing_id = data.get("id")
                    if "id" in columns and existing_id is None:
                        columns.remove("id")
                        transaction_id = self._get_next_id("transactions")
                        columns.insert(0, "id")
                        values.insert(0, transaction_id)
                        placeholders = ", ".join(["?" for _ in columns])
                        col_names = ", ".join(columns)
                    elif existing_id is not None:
                        transaction_id = existing_id
                    else:
                        transaction_id = self._get_next_id("transactions")
                        if "id" not in columns:
                            columns.insert(0, "id")
                            values.insert(0, transaction_id)
                            placeholders = ", ".join(["?" for _ in columns])
                            col_names = ", ".join(columns)

                    result = self.conn.execute(
                        f"INSERT INTO transactions ({col_names}) VALUES ({placeholders}) RETURNING id",
                        values,
                    ).fetchone()
                    transaction_id = result[0] if result else transaction_id
                    return transaction_id, True

                except Exception as e:
                    # Check if this is a duplicate transaction error
                    if "UNIQUE constraint" in str(e) or "duplicate" in str(e).lower():
                        # Find the existing transaction
                        existing = self.conn.execute(
                            """
                            SELECT id FROM transactions
                            WHERE date = ? AND amount = ? AND description = ?
                              AND account_number = ? AND source_file = ? AND unique_id = ?
                        """,
                            [
                                transaction.date,
                                str(transaction.amount),
                                transaction.description,
                                transaction.account_number,
                                transaction.source_file,
                                transaction.unique_id,
                            ],
                        ).fetchone()
                        return (existing[0] if existing else 0), False
                    raise

    def _generate_unique_id(self, transaction: Transaction) -> str:
        """Generate a unique ID for a transaction to distinguish identical transactions in the same file."""
        hash_input = f"{transaction.date}_{transaction.amount}_{transaction.description}_{transaction.account_number}_{transaction.source_file}_{time.time()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def get_transactions_by_account(self, account_number: str) -> list[dict[str, Any]]:
        """Get transactions for an account."""
        result = self.conn.execute(
            """
            SELECT * FROM transactions
            WHERE account_number = ?
            ORDER BY date DESC
        """,
            [account_number],
        )
        rows = result.fetchall()
        columns = self._get_columns(result)
        return [
            self._transaction_to_dict(dict(zip(columns, row, strict=False)))
            for row in rows
        ]

    def get_unprocessed_transactions(self, target_name: str) -> list[dict[str, Any]]:
        """Get transactions not yet processed by target."""
        result = self.conn.execute(
            """
            SELECT t.* FROM transactions t
            LEFT JOIN target_completions tc ON t.id = tc.transaction_id
                AND tc.target_name = ?
                AND tc.completed_at IS NOT NULL
                AND tc.error_message IS NULL
            WHERE tc.id IS NULL
            ORDER BY t.date DESC
        """,
            [target_name],
        )
        rows = result.fetchall()
        columns = self._get_columns(result)
        return [
            self._transaction_to_dict(dict(zip(columns, row, strict=False)))
            for row in rows
        ]

    def mark_target_completed(
        self,
        transaction_id: int,
        target_name: str,
        error_message: str | None = None,
    ) -> None:
        """Mark transaction as completed for target."""
        with self._transaction():
            status_enum = (
                TargetCompletionStatus.COMPLETED
                if not error_message
                else TargetCompletionStatus.FAILED
            )
            completed_at = datetime.now(UTC) if not error_message else None

            # Use INSERT ... ON CONFLICT for DuckDB compatibility
            # Check if record exists first
            existing = self.conn.execute(
                """
                SELECT id FROM target_completions
                WHERE transaction_id = ? AND target_name = ?
            """,
                [transaction_id, target_name],
            ).fetchone()

            if existing:
                # Update existing record
                self.conn.execute(
                    """
                    UPDATE target_completions
                    SET status = ?, completed_at = ?, error_message = ?, retry_count = 0
                    WHERE transaction_id = ? AND target_name = ?
                """,
                    [
                        status_enum.value,
                        completed_at,
                        error_message,
                        transaction_id,
                        target_name,
                    ],
                )
            else:
                # Insert new record
                completion_id = self._get_next_id("target_completions")
                self.conn.execute(
                    """
                    INSERT INTO target_completions
                    (id, transaction_id, target_name, status, completed_at, error_message, retry_count)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """,
                    [
                        completion_id,
                        transaction_id,
                        target_name,
                        status_enum.value,
                        completed_at,
                        error_message,
                    ],
                )

    def create_import_session(self, import_session: ImportSession) -> int:
        """Create a new import session."""
        with self._transaction():
            # Check if a session with this file hash already exists
            existing = self.conn.execute(
                """
                SELECT * FROM import_sessions WHERE file_hash = ?
            """,
                [import_session.file_hash],
            ).fetchone()

            if existing:
                # Get columns from the query result
                result = self.conn.execute(
                    "SELECT * FROM import_sessions WHERE file_hash = ? LIMIT 1",
                    [import_session.file_hash],
                )
                columns = self._get_columns(result)
                existing_dict = dict(zip(columns, existing, strict=False))
                existing_session = ImportSession(**existing_dict)

                # If session exists and is completed/skipped, skip this import
                if existing_session.status_enum in [
                    ImportStatus.COMPLETED,
                    ImportStatus.SKIPPED,
                ]:
                    msg = f"File already processed: {import_session.file_path}"
                    raise ValueError(msg)

                # If session exists but is failed, update it and retry
                if existing_session.status_enum == ImportStatus.FAILED:
                    self.conn.execute(
                        """
                        UPDATE import_sessions
                        SET status = ?, started_at = ?, completed_at = NULL,
                            error_message = NULL, error_count = 0
                        WHERE id = ?
                    """,
                        [
                            ImportStatus.PROCESSING.value,
                            import_session.started_at,
                            existing_session.id,
                        ],
                    )
                    return existing_session.id or 0

                # If session is processing, skip
                msg = f"File already being processed: {import_session.file_path}"
                raise ValueError(msg)

            # Create new session
            session_id = self._get_next_id("import_sessions")
            self.conn.execute(
                """
                INSERT INTO import_sessions
                (id, account_name, bank_name, session_name, file_path, file_hash, status,
                 total_transactions, processed_transactions, error_count, started_at,
                 completed_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    session_id,
                    import_session.account_name,
                    import_session.bank_name,
                    import_session.session_name,
                    import_session.file_path,
                    import_session.file_hash,
                    import_session.status,
                    import_session.total_transactions,
                    import_session.processed_transactions,
                    import_session.error_count,
                    import_session.started_at,
                    import_session.completed_at,
                    import_session.error_message,
                ],
            )
            return session_id

    def update_import_session(self, session_id: int, **kwargs: object) -> None:
        """Update import session fields."""
        with self._transaction():
            updates: list[str] = []
            values: list[object] = []
            for key, value in kwargs.items():
                updates.append(f"{key} = ?")
                values.append(value)
            values.append(session_id)

            if updates:
                self.conn.execute(
                    f"UPDATE import_sessions SET {', '.join(updates)} WHERE id = ?",
                    values,
                )

    def get_import_session(self, session_id: int) -> dict[str, Any] | None:
        """Get import session by ID."""
        result = self.conn.execute(
            """
            SELECT * FROM import_sessions WHERE id = ?
        """,
            [session_id],
        )
        row = result.fetchone()

        if not row:
            return None

        columns = self._get_columns(result)
        data = dict(zip(columns, row, strict=False))
        # Convert to ImportSession and back to dict for consistency
        session = ImportSession(**data)
        return session.to_dict()

    def get_import_sessions_by_account(self, account_name: str) -> list[dict[str, Any]]:
        """Get all import sessions for an account."""
        result = self.conn.execute(
            """
            SELECT * FROM import_sessions
            WHERE account_name = ?
            ORDER BY started_at DESC
        """,
            [account_name],
        )
        rows = result.fetchall()
        columns = self._get_columns(result)
        return [
            ImportSession(**dict(zip(columns, row, strict=False))).to_dict()
            for row in rows
        ]

    def get_transactions_by_session(self, session_id: int) -> list[dict[str, Any]]:
        """Get all transactions for a specific import session."""
        # First get the import session to get the file_path
        result = self.conn.execute(
            """
            SELECT * FROM import_sessions WHERE id = ?
        """,
            [session_id],
        )
        row = result.fetchone()

        if not row:
            return []

        columns = self._get_columns(result)
        session_data = dict(zip(columns, row, strict=False))
        file_path = session_data.get("file_path")

        # Then get transactions that match the source_file
        result = self.conn.execute(
            """
            SELECT * FROM transactions
            WHERE source_file = ?
            ORDER BY date DESC
        """,
            [file_path],
        )
        rows = result.fetchall()
        columns = self._get_columns(result)
        return [
            self._transaction_to_dict(dict(zip(columns, row, strict=False)))
            for row in rows
        ]

    def get_import_session_by_file_hash(self, file_hash: str) -> dict[str, Any] | None:
        """Get import session by file hash for deduplication."""
        result = self.conn.execute(
            """
            SELECT * FROM import_sessions WHERE file_hash = ?
        """,
            [file_hash],
        )
        row = result.fetchone()

        if not row:
            return None

        columns = self._get_columns(result)
        data = dict(zip(columns, row, strict=False))
        return ImportSession(**data).to_dict()

    def get_pending_import_sessions(self) -> list[dict[str, Any]]:
        """Get all pending import sessions."""
        result = self.conn.execute(
            """
            SELECT * FROM import_sessions
            WHERE status = ?
            ORDER BY started_at ASC
        """,
            [ImportStatus.PENDING.value],
        )
        rows = result.fetchall()
        columns = self._get_columns(result)
        return [
            ImportSession(**dict(zip(columns, row, strict=False))).to_dict()
            for row in rows
        ]

    def create_export_session(
        self,
        session_name: str,
        target_name: str,
        account_reference: str,
    ) -> int:
        """Create a new export session."""
        with self._transaction():
            session_id = self._get_next_id("export_sessions")
            self.conn.execute(
                """
                INSERT INTO export_sessions
                (id, session_name, target_name, account_reference, status, started_at)
                VALUES (?, ?, ?, ?, 'processing', ?)
            """,
                [
                    session_id,
                    session_name,
                    target_name,
                    account_reference,
                    datetime.now(UTC),
                ],
            )
            return session_id

    def update_export_session(
        self,
        session_id: int,
        status: str | None = None,
        total_transactions: int | None = None,
        exported_transactions: int | None = None,
        skipped_transactions: int | None = None,
        error_transactions: int | None = None,
        output_file: str | None = None,
        session_metadata: str | None = None,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        """Update export session."""
        update = ExportSessionUpdate(
            session_id=session_id,
            status=status,
            total_transactions=total_transactions,
            exported_transactions=exported_transactions,
            skipped_transactions=skipped_transactions,
            error_transactions=error_transactions,
            output_file=output_file,
            session_metadata=session_metadata,
            error_message=error_message,
            completed_at=completed_at,
        )
        self._update_export_session_impl(update)

    def _build_export_session_updates(
        self,
        update: ExportSessionUpdate,
    ) -> tuple[list[str], list[object]]:
        """Build SQL update clauses and values from ExportSessionUpdate."""
        updates: list[str] = []
        values: list[object] = []

        if update.status is not None:
            updates.append("status = ?")
            values.append(update.status)
        if update.total_transactions is not None:
            updates.append("total_transactions = ?")
            values.append(update.total_transactions)
        if update.exported_transactions is not None:
            updates.append("exported_transactions = ?")
            values.append(update.exported_transactions)
        if update.skipped_transactions is not None:
            updates.append("skipped_transactions = ?")
            values.append(update.skipped_transactions)
        if update.error_transactions is not None:
            updates.append("error_transactions = ?")
            values.append(update.error_transactions)
        if update.output_file is not None:
            updates.append("output_file = ?")
            values.append(update.output_file)
        if update.session_metadata is not None:
            updates.append("session_metadata = ?")
            values.append(update.session_metadata)
        if update.error_message is not None:
            updates.append("error_message = ?")
            values.append(update.error_message)
        if update.completed_at is not None:
            updates.append("completed_at = ?")
            values.append(update.completed_at)

        return updates, values

    def _update_export_session_impl(self, update: ExportSessionUpdate) -> None:
        """Internal implementation of export session update."""
        updates, values = self._build_export_session_updates(update)
        if not updates:
            return

        with self._transaction():
            values.append(update.session_id)
            self.conn.execute(
                f"UPDATE export_sessions SET {', '.join(updates)} WHERE id = ?",
                values,
            )

    def mark_transaction_exported(
        self,
        transaction_id: int,
        target_name: str,
        export_session_id: int,
        status: str = "exported",
        error_message: str | None = None,
    ) -> int:
        """Mark a transaction as exported to a target."""
        with self._transaction():
            exported_id = self._get_next_id("exported_transactions")
            self.conn.execute(
                """
                INSERT INTO exported_transactions
                (id, transaction_id, target_name, export_session_id, exported_at, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    exported_id,
                    transaction_id,
                    target_name,
                    export_session_id,
                    datetime.now(UTC),
                    status,
                    error_message,
                ],
            )
            return exported_id

    def get_unexported_transactions(
        self,
        target_name: str,
        account_reference: str | None = None,
    ) -> list[Transaction]:
        """Get transactions that haven't been exported to a specific target."""
        if account_reference:
            rows = self.conn.execute(
                """
                SELECT t.* FROM transactions t
                WHERE t.id NOT IN (
                    SELECT transaction_id FROM exported_transactions WHERE target_name = ?
                )
                AND t.account_number = ?
                ORDER BY t.date DESC
            """,
                [target_name, account_reference],
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT t.* FROM transactions t
                WHERE t.id NOT IN (
                    SELECT transaction_id FROM exported_transactions WHERE target_name = ?
                )
                ORDER BY t.date DESC
            """,
                [target_name],
            ).fetchall()

        columns = [desc[0] for desc in self.conn.description]
        transactions = []
        for row in rows:
            data = dict(zip(columns, row, strict=False))
            # Convert Decimal strings back to Decimal
            for key in [
                "amount",
                "balance",
                "old_balance",
                "new_balance",
                "exchange_rate",
                "foreign_amount",
                "fees",
                "interest",
                "tax",
            ]:
                if data.get(key) is not None:
                    from decimal import Decimal

                    data[key] = Decimal(str(data[key]))
            transactions.append(Transaction(**data))
        return transactions

    def get_transactions_by_source_file(self, source_file: str) -> list[Transaction]:
        """Get all transactions from a specific source file."""
        result = self.conn.execute(
            """
            SELECT * FROM transactions
            WHERE source_file = ?
            ORDER BY date DESC
        """,
            [source_file],
        )
        rows = result.fetchall()
        columns = self._get_columns(result)
        transactions = []
        for row in rows:
            data = dict(zip(columns, row, strict=False))
            # Convert Decimal strings back to Decimal
            from decimal import Decimal

            for key in [
                "amount",
                "balance",
                "old_balance",
                "new_balance",
                "exchange_rate",
                "foreign_amount",
                "fees",
                "interest",
                "tax",
            ]:
                if data.get(key) is not None:
                    data[key] = Decimal(str(data[key]))
            transactions.append(Transaction(**data))
        return transactions

    def get_all_transactions(self) -> list[Transaction]:
        """Get all transactions from all source files."""
        result = self.conn.execute("""
            SELECT * FROM transactions
            ORDER BY date DESC
        """)
        rows = result.fetchall()
        columns = self._get_columns(result)
        transactions = []
        for row in rows:
            data = dict(zip(columns, row, strict=False))
            # Convert Decimal strings back to Decimal
            from decimal import Decimal

            for key in [
                "amount",
                "balance",
                "old_balance",
                "new_balance",
                "exchange_rate",
                "foreign_amount",
                "fees",
                "interest",
                "tax",
            ]:
                if data.get(key) is not None:
                    data[key] = Decimal(str(data[key]))
            transactions.append(Transaction(**data))
        return transactions

    def get_unique_source_files(self) -> list[str]:
        """Get list of all unique source files."""
        rows = self.conn.execute("""
            SELECT DISTINCT source_file FROM transactions
            WHERE source_file IS NOT NULL
        """).fetchall()
        return [row[0] for row in rows if row[0]]

    def get_transaction_by_id(self, transaction_id: int) -> Transaction | None:
        """Get transaction by ID."""
        result = self.conn.execute(
            """
            SELECT * FROM transactions WHERE id = ?
        """,
            [transaction_id],
        )
        row = result.fetchone()

        if not row:
            return None

        columns = self._get_columns(result)
        data = dict(zip(columns, row, strict=False))
        # Convert Decimal strings back to Decimal
        from decimal import Decimal

        for key in [
            "amount",
            "balance",
            "old_balance",
            "new_balance",
            "exchange_rate",
            "foreign_amount",
            "fees",
            "interest",
            "tax",
        ]:
            if data.get(key) is not None:
                data[key] = Decimal(str(data[key]))
        return Transaction(**data)

    def get_transactions_filtered(
        self,
        account_number: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        """Get transactions with filters.

        Returns:
            tuple: (transactions, total_count)

        """
        conditions: list[str] = []
        params: list[object] = []

        if account_number:
            conditions.append("account_number = ?")
            params.append(account_number)
        if date_from:
            conditions.append("date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("date <= ?")
            params.append(date_to)
        if transaction_type:
            conditions.append("transaction_type = ?")
            params.append(transaction_type)
        if category:
            conditions.append("category = ?")
            params.append(category)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Get total count
        count_row = self.conn.execute(
            f"""
            SELECT COUNT(*) FROM transactions WHERE {where_clause}
        """,
            params,
        ).fetchone()
        total = count_row[0] if count_row else 0

        # Get paginated results
        result = self.conn.execute(
            f"""
            SELECT * FROM transactions
            WHERE {where_clause}
            ORDER BY date DESC
            LIMIT ? OFFSET ?
        """,
            [*params, limit, offset],
        )
        rows = result.fetchall()
        columns = self._get_columns(result)
        transactions = []
        for row in rows:
            data = dict(zip(columns, row, strict=False))
            # Convert Decimal strings back to Decimal
            from decimal import Decimal

            for key in [
                "amount",
                "balance",
                "old_balance",
                "new_balance",
                "exchange_rate",
                "foreign_amount",
                "fees",
                "interest",
                "tax",
            ]:
                if data.get(key) is not None:
                    data[key] = Decimal(str(data[key]))
            transactions.append(Transaction(**data))

        return transactions, total

    def update_transaction(
        self,
        transaction_id: int,
        category: str | None = None,
        subcategory: str | None = None,
        memo: str | None = None,
        translated_description: str | None = None,
    ) -> Transaction | None:
        """Update transaction fields."""
        updates: list[str] = []
        params: list[str | int] = []

        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if subcategory is not None:
            updates.append("subcategory = ?")
            params.append(subcategory)
        if memo is not None:
            updates.append("memo = ?")
            params.append(memo)
        if translated_description is not None:
            updates.append("translated_description = ?")
            params.append(translated_description)

        if not updates:
            return self.get_transaction_by_id(transaction_id)

        params.append(transaction_id)

        with self._transaction():
            self.conn.execute(
                f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?",
                params,
            )

        return self.get_transaction_by_id(transaction_id)

    def get_export_sessions(
        self,
        target_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get export sessions."""
        if target_name:
            result = self.conn.execute(
                """
                SELECT * FROM export_sessions
                WHERE target_name = ?
                ORDER BY started_at DESC
            """,
                [target_name],
            )
        else:
            result = self.conn.execute("""
                SELECT * FROM export_sessions
                ORDER BY started_at DESC
            """)
        rows = result.fetchall()
        columns = self._get_columns(result)
        return [
            ExportSession(**dict(zip(columns, row, strict=False))).model_dump()
            for row in rows
        ]

    def clear_export_sessions(self) -> None:
        """Clear all export sessions and exported transactions."""
        with self._transaction():
            self.conn.execute("DELETE FROM exported_transactions")
            self.conn.execute("DELETE FROM export_sessions")

    def has_source_file_been_exported(
        self,
        source_file: str,
        target_name: str | None = None,
    ) -> bool:
        """Check if a source file has been exported to any (or specific) target."""
        # Get transactions from this source file
        transactions = self.get_transactions_by_source_file(source_file)
        if not transactions:
            return False

        transaction_ids = [t.id for t in transactions if t.id]
        if not transaction_ids:
            return False

        # Check if any of these transactions have been exported
        placeholders = ",".join(["?" for _ in transaction_ids])
        if target_name:
            row = self.conn.execute(
                f"""
                SELECT COUNT(*) FROM exported_transactions
                WHERE transaction_id IN ({placeholders}) AND target_name = ?
            """,
                [*transaction_ids, target_name],
            ).fetchone()
            count = row[0] if row else 0
        else:
            row = self.conn.execute(
                f"""
                SELECT COUNT(*) FROM exported_transactions
                WHERE transaction_id IN ({placeholders})
            """,
                transaction_ids,
            ).fetchone()
            count = row[0] if row else 0

        return bool(count > 0)

    def has_source_file_been_imported(self, source_file: str) -> bool:
        """Check if a source file has been imported (has completed import session)."""
        row = self.conn.execute(
            """
            SELECT COUNT(*) FROM import_sessions
            WHERE file_path = ? AND status = ?
        """,
            [source_file, ImportStatus.COMPLETED.value],
        ).fetchone()
        return row[0] > 0 if row else False

    @property
    def engine(self) -> duckdb.DuckDBPyConnection:
        """Compatibility property for code that accesses .engine."""
        return self.conn
