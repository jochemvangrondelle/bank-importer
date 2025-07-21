"""Target completion model for tracking processing status."""

from datetime import datetime

from sqlalchemy import DateTime, Text
from sqlmodel import Column, Field, Index, SQLModel


class TargetCompletion(SQLModel, table=True):
    """Track completion status for targets."""

    __tablename__ = "target_completions"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Foreign key to transaction
    transaction_id: int = Field(foreign_key="transactions.id", nullable=False, index=True)
    target_name: str = Field(max_length=100, nullable=False, index=True)

    # Completion tracking
    status: str = Field(max_length=50, nullable=False, index=True)  # pending, completed, failed
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime, index=True))
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    retry_count: int = Field(default=0, nullable=False)

    # Database indexes
    __table_args__ = (
        Index("idx_target_completion_unique", "transaction_id", "target_name", unique=True),
        Index("idx_target_completion_status", "status"),
        Index("idx_target_completion_target", "target_name"),
    )

    def to_dict(self) -> dict:
        """Convert target completion to dictionary."""
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "target_name": self.target_name,
            "status": self.status,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }
