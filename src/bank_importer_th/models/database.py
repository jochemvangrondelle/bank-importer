"""Database models and management using SQLModel."""

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

from .export_session import ExportedTransaction, ExportSession
from .import_session import ImportSession
from .target_completion import TargetCompletion
from .transaction import Transaction


class DatabaseManager:
    """Manage database operations using SQLModel."""

    def __init__(self, database_url: str):
        """Initialize database manager."""
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self._create_tables()

    def _create_tables(self) -> None:
        """Create all tables."""
        SQLModel.metadata.create_all(self.engine)

    def add_transaction(self, transaction: Transaction) -> tuple[int, bool]:
        """Add transaction to database.

        Returns:
            tuple: (transaction_id, is_new) where is_new indicates if this was a new transaction
        """
        # Generate unique ID for the transaction if not already set
        if not transaction.unique_id:
            transaction.unique_id = self._generate_unique_id(transaction)

        with Session(self.engine) as session:
            try:
                session.add(transaction)
                session.commit()
                session.refresh(transaction)
                return transaction.id or 0, True
            except IntegrityError as e:
                # Check if this is a duplicate transaction error
                if (
                    "UNIQUE constraint failed: transactions.date, transactions.amount, transactions.description, transactions.account_number, transactions.source_file, transactions.unique_id"
                    in str(e)
                ):
                    session.rollback()
                    # Find the existing transaction
                    statement = select(Transaction).where(
                        Transaction.date == transaction.date,
                        Transaction.amount == transaction.amount,
                        Transaction.description == transaction.description,
                        Transaction.account_number == transaction.account_number,
                        Transaction.source_file == transaction.source_file,
                        Transaction.unique_id == transaction.unique_id,
                    )
                    existing = session.exec(statement).first()
                    return (existing.id or 0) if existing else 0, False
                else:
                    # Re-raise if it's a different integrity error
                    raise

    def _generate_unique_id(self, transaction: Transaction) -> str:
        """Generate a unique ID for a transaction to distinguish identical transactions in the same file."""
        import hashlib
        import time

        # Create a hash based on transaction details and current timestamp
        hash_input = f"{transaction.date}_{transaction.amount}_{transaction.description}_{transaction.account_number}_{transaction.source_file}_{time.time()}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]

        return hash_value

    def get_transactions_by_account(self, account_number: str) -> list[dict]:
        """Get transactions for an account."""
        with Session(self.engine) as session:
            statement = (
                select(Transaction)
                .where(Transaction.account_number == account_number)
                .order_by(Transaction.date.desc())  # type: ignore[attr-defined]
            )
            transactions = session.exec(statement).all()
            return [transaction.to_dict() for transaction in transactions]

    def get_unprocessed_transactions(self, target_name: str) -> list[dict]:
        """Get transactions not yet processed by target."""
        with Session(self.engine) as session:
            # Complex query to find transactions not completed for target
            statement = text("""
                SELECT t.* FROM transactions t
                LEFT JOIN target_completions tc ON t.id = tc.transaction_id
                    AND tc.target_name = :target_name
                    AND tc.completed_at IS NOT NULL
                    AND tc.error_message IS NULL
                WHERE tc.id IS NULL
                ORDER BY t.date DESC
            """)
            result = session.execute(statement, {"target_name": target_name})
            return [dict(row._mapping) for row in result]

    def mark_target_completed(
        self, transaction_id: int, target_name: str, error_message: str | None = None
    ) -> None:
        """Mark transaction as completed for target."""
        with Session(self.engine) as session:
            completion = TargetCompletion(
                transaction_id=transaction_id,
                target_name=target_name,
                completed_at=datetime.now() if not error_message else None,
                error_message=error_message,
            )
            session.add(completion)
            session.commit()

    def create_import_session(self, import_session: ImportSession) -> int:
        """Create a new import session."""
        with Session(self.engine) as session:
            # Check if a session with this file hash already exists
            existing_session = session.exec(
                select(ImportSession).where(
                    ImportSession.file_hash == import_session.file_hash
                )
            ).first()

            if existing_session:
                # If session exists and is completed/skipped, skip this import
                if existing_session.status in ["completed", "skipped"]:
                    raise ValueError(
                        f"File already processed: {import_session.file_path}"
                    )
                # If session exists but is failed, update it and retry
                elif existing_session.status == "failed":
                    existing_session.status = "processing"
                    existing_session.started_at = import_session.started_at
                    existing_session.completed_at = None
                    existing_session.error_message = None
                    existing_session.error_count = 0
                    session.add(existing_session)
                    session.commit()
                    session.refresh(existing_session)
                    return existing_session.id or 0
                # If session is processing, skip
                else:
                    raise ValueError(
                        f"File already being processed: {import_session.file_path}"
                    )

            # Create new session
            session.add(import_session)
            session.commit()
            session.refresh(import_session)
            return import_session.id or 0

    def update_import_session(self, session_id: int, **kwargs: Any) -> None:
        """Update import session fields."""
        with Session(self.engine) as session:
            statement = select(ImportSession).where(ImportSession.id == session_id)
            import_session = session.exec(statement).first()
            if import_session:
                for key, value in kwargs.items():
                    if hasattr(import_session, key):
                        setattr(import_session, key, value)
                session.add(import_session)
                session.commit()

    def get_import_session(self, session_id: int) -> dict | None:
        """Get import session by ID."""
        with Session(self.engine) as session:
            statement = select(ImportSession).where(ImportSession.id == session_id)
            import_session = session.exec(statement).first()
            return import_session.to_dict() if import_session else None

    def get_import_sessions_by_account(self, account_name: str) -> list[dict]:
        """Get all import sessions for an account."""
        with Session(self.engine) as session:
            statement = (
                select(ImportSession)
                .where(ImportSession.account_name == account_name)
                .order_by(ImportSession.started_at.desc())  # type: ignore[attr-defined]
            )
            sessions = session.exec(statement).all()
            return [session.to_dict() for session in sessions]

    def get_transactions_by_session(self, session_id: int) -> list[dict]:
        """Get all transactions for a specific import session."""
        with Session(self.engine) as session:
            # First get the import session to get the file_path
            import_session = session.exec(
                select(ImportSession).where(ImportSession.id == session_id)
            ).first()

            if not import_session:
                return []

            # Then get transactions that match the source_file
            statement = (
                select(Transaction)
                .where(Transaction.source_file == import_session.file_path)
                .order_by(Transaction.date.desc())  # type: ignore[attr-defined]
            )
            transactions = session.exec(statement).all()
            return [transaction.to_dict() for transaction in transactions]

    def get_import_session_by_file_hash(self, file_hash: str) -> dict | None:
        """Get import session by file hash for deduplication."""
        with Session(self.engine) as session:
            statement = select(ImportSession).where(
                ImportSession.file_hash == file_hash
            )
            import_session = session.exec(statement).first()
            return import_session.to_dict() if import_session else None

    def get_pending_import_sessions(self) -> list[dict]:
        """Get all pending import sessions."""
        with Session(self.engine) as session:
            statement = (
                select(ImportSession)
                .where(ImportSession.status == "pending")
                .order_by(ImportSession.started_at.asc())  # type: ignore[attr-defined]
            )
            sessions = session.exec(statement).all()
            return [session.to_dict() for session in sessions]

    def create_export_session(
        self, session_name: str, target_name: str, account_reference: str
    ) -> int:
        """Create a new export session."""
        with Session(self.engine) as session:
            export_session = ExportSession(
                session_name=session_name,
                target_name=target_name,
                account_reference=account_reference,
            )
            session.add(export_session)
            session.commit()
            session.refresh(export_session)
            return export_session.id or 0

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
        with Session(self.engine) as session:
            statement = select(ExportSession).where(ExportSession.id == session_id)
            export_session = session.exec(statement).first()
            if export_session:
                if status is not None:
                    export_session.status = status
                if total_transactions is not None:
                    export_session.total_transactions = total_transactions
                if exported_transactions is not None:
                    export_session.exported_transactions = exported_transactions
                if skipped_transactions is not None:
                    export_session.skipped_transactions = skipped_transactions
                if error_transactions is not None:
                    export_session.error_transactions = error_transactions
                if output_file is not None:
                    export_session.output_file = output_file
                if session_metadata is not None:
                    export_session.session_metadata = session_metadata
                if error_message is not None:
                    export_session.error_message = error_message
                if completed_at is not None:
                    export_session.completed_at = completed_at
                session.commit()

    def mark_transaction_exported(
        self,
        transaction_id: int,
        target_name: str,
        export_session_id: int,
        status: str = "exported",
        error_message: str | None = None,
    ) -> int:
        """Mark a transaction as exported to a target."""
        with Session(self.engine) as session:
            exported_transaction = ExportedTransaction(
                transaction_id=transaction_id,
                target_name=target_name,
                export_session_id=export_session_id,
                status=status,
                error_message=error_message,
            )
            session.add(exported_transaction)
            session.commit()
            session.refresh(exported_transaction)
            return exported_transaction.id or 0

    def get_unexported_transactions(
        self, target_name: str, account_reference: str | None = None
    ) -> list[Transaction]:
        """Get transactions that haven't been exported to a specific target."""
        with Session(self.engine) as session:
            # Subquery to get exported transaction IDs
            exported_subquery = select(ExportedTransaction.transaction_id).where(
                ExportedTransaction.target_name == target_name
            )

            # Main query to get unexported transactions
            statement = select(Transaction).where(
                Transaction.id.not_in(exported_subquery)  # type: ignore[union-attr]
            )

            if account_reference:
                statement = statement.where(
                    Transaction.account_number == account_reference
                )

            return list(session.exec(statement).all())

    def get_transactions_by_source_file(self, source_file: str) -> list[Transaction]:
        """Get all transactions from a specific source file."""
        with Session(self.engine) as session:
            statement = (
                select(Transaction)
                .where(Transaction.source_file == source_file)
                .order_by(Transaction.date.desc())  # type: ignore[attr-defined]
            )
            return list(session.exec(statement).all())

    def get_all_transactions(self) -> list[Transaction]:
        """Get all transactions from all source files."""
        with Session(self.engine) as session:
            statement = select(Transaction).order_by(Transaction.date.desc())  # type: ignore[attr-defined]
            return list(session.exec(statement).all())

    def get_unique_source_files(self) -> list[str]:
        """Get list of all unique source files."""
        with Session(self.engine) as session:
            statement = (
                select(Transaction.source_file)
                .distinct()
                .where(Transaction.source_file.is_not(None))  # type: ignore[union-attr]
            )
            result = session.exec(statement).all()
            return [file for file in result if file]

    def get_export_sessions(
        self, target_name: str | None = None
    ) -> list[dict[str, Any]]:
        """Get export sessions."""
        with Session(self.engine) as session:
            statement = select(ExportSession)
            if target_name:
                statement = statement.where(ExportSession.target_name == target_name)
            statement = statement.order_by(ExportSession.started_at.desc())  # type: ignore[attr-defined]
            sessions = session.exec(statement).all()
            return [session.model_dump() for session in sessions]

    def clear_export_sessions(self) -> None:
        """Clear all export sessions and exported transactions."""
        with Session(self.engine) as session:
            # Delete exported transactions first (foreign key constraint)
            session.execute(text("DELETE FROM exportedtransaction"))
            # Delete export sessions
            session.execute(text("DELETE FROM exportsession"))
            session.commit()

    def has_source_file_been_exported(
        self, source_file: str, target_name: str | None = None
    ) -> bool:
        """Check if a source file has been exported to any (or specific) target."""
        with Session(self.engine) as session:
            # Get transactions from this source file
            transactions = self.get_transactions_by_source_file(source_file)
            if not transactions:
                return False

            # Check if any of these transactions have been exported
            transaction_ids = [t.id for t in transactions if t.id]
            if not transaction_ids:
                return False

            # Build query to check exported transactions
            statement = select(ExportedTransaction).where(
                ExportedTransaction.transaction_id.in_(transaction_ids)  # type: ignore[attr-defined]
            )

            if target_name:
                statement = statement.where(
                    ExportedTransaction.target_name == target_name
                )

            exported_count = len(session.exec(statement).all())
            return exported_count > 0

    def has_source_file_been_imported(self, source_file: str) -> bool:
        """Check if a source file has been imported (has completed import session)."""
        with Session(self.engine) as session:
            # Check if there's a completed import session for this file
            statement = select(ImportSession).where(
                ImportSession.file_path == source_file,
                ImportSession.status == "completed",
            )
            import_session = session.exec(statement).first()
            return import_session is not None
