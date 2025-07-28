"""Export session model for tracking transaction exports."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class ExportSession(SQLModel, table=True):
    """Export session model."""

    id: int | None = Field(default=None, primary_key=True)
    session_name: str = Field(index=True)
    target_name: str = Field(index=True)
    account_reference: str = Field(index=True)
    status: str = Field(default="processing")  # processing, completed, failed, skipped
    total_transactions: int = Field(default=0)
    exported_transactions: int = Field(default=0)
    skipped_transactions: int = Field(default=0)
    error_transactions: int = Field(default=0)
    output_file: str | None = Field(default=None)
    session_metadata: str | None = Field(default=None)  # JSON string
    error_message: str | None = Field(default=None)
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = Field(default=None)


class ExportedTransaction(SQLModel, table=True):
    """Model to track which transactions have been exported to which targets."""

    id: int | None = Field(default=None, primary_key=True)
    transaction_id: int = Field(foreign_key="transactions.id", index=True)
    target_name: str = Field(index=True)
    export_session_id: int = Field(foreign_key="exportsession.id", index=True)
    exported_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="exported")  # exported, failed, skipped
    error_message: str | None = Field(default=None)
