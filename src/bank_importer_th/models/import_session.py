"""Import session model for tracking file processing batches."""

from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlmodel import Column, Field, Index, SQLModel


class ImportSession(SQLModel, table=True):
    """Track import sessions for file processing."""

    __tablename__ = "import_sessions"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Core session data
    account_name: str = Field(max_length=200, nullable=False, index=True)
    bank_name: str = Field(max_length=100, nullable=False, index=True)
    session_name: str = Field(max_length=100, nullable=False)  # e.g., "2024-11", "2024-12", "manual_import"
    file_path: str = Field(max_length=500, nullable=False)
    file_hash: str = Field(max_length=64, nullable=False, index=True)  # For deduplication
    status: str = Field(max_length=20, nullable=False, index=True)  # pending, processing, completed, failed

    # Processing statistics
    total_transactions: int = Field(default=0, nullable=False)
    processed_transactions: int = Field(default=0, nullable=False)
    error_count: int = Field(default=0, nullable=False)

    # Timestamps
    started_at: datetime = Field(sa_column=Column(DateTime, nullable=False, index=True))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime, index=True))
    error_message: str | None = Field(default=None, sa_column=Column(Text))

    # Database indexes
    __table_args__ = (
        Index("idx_import_session_unique", "file_hash", unique=True),
        Index("idx_import_session_account", "account_name"),
        Index("idx_import_session_status", "status"),
        Index("idx_import_session_date", "started_at"),
    )

    @property
    def is_completed(self) -> bool:
        """Check if import session is completed."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if import session failed."""
        return self.status == "failed"

    def to_dict(self) -> dict:
        """Convert import session to dictionary."""
        return {
            "id": self.id,
            "account_name": self.account_name,
            "bank_name": self.bank_name,
            "session_name": self.session_name,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "status": self.status,
            "total_transactions": self.total_transactions,
            "processed_transactions": self.processed_transactions,
            "error_count": self.error_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }
