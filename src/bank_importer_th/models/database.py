"""Database models and management using SQLModel."""

from datetime import datetime

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine, select

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

    def add_transaction(self, transaction: Transaction) -> int:
        """Add transaction to database."""
        with Session(self.engine) as session:
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction.id or 0

    def get_transactions_by_account(self, account_number: str) -> list[dict]:
        """Get transactions for an account."""
        with Session(self.engine) as session:
            statement = (
                select(Transaction)
                .where(Transaction.account_number == account_number)
                .order_by(Transaction.date.desc())
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
            result = session.exec(statement, {"target_name": target_name})
            return [dict(row._mapping) for row in result]

    def mark_target_completed(self, transaction_id: int, target_name: str, error_message: str | None = None) -> None:
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
            session.add(import_session)
            session.commit()
            session.refresh(import_session)
            return import_session.id or 0

    def update_import_session(self, session_id: int, **kwargs) -> None:
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
                .order_by(ImportSession.started_at.desc())
            )
            sessions = session.exec(statement).all()
            return [session.to_dict() for session in sessions]

    def get_import_session_by_file_hash(self, file_hash: str) -> dict | None:
        """Get import session by file hash for deduplication."""
        with Session(self.engine) as session:
            statement = select(ImportSession).where(ImportSession.file_hash == file_hash)
            import_session = session.exec(statement).first()
            return import_session.to_dict() if import_session else None

    def get_pending_import_sessions(self) -> list[dict]:
        """Get all pending import sessions."""
        with Session(self.engine) as session:
            statement = (
                select(ImportSession).where(ImportSession.status == "pending").order_by(ImportSession.started_at.asc())
            )
            sessions = session.exec(statement).all()
            return [session.to_dict() for session in sessions]
