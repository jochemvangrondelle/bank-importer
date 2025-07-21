"""Transaction model for bank statements."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Numeric, Text
from sqlmodel import Column, Field, Index, SQLModel


class Transaction(SQLModel, table=True):
    """Represents a bank transaction."""

    __tablename__ = "transactions"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Core transaction data
    date: datetime = Field(sa_column=Column(DateTime, nullable=False, index=True))
    description: str = Field(max_length=500, nullable=False)
    amount: Decimal = Field(sa_column=Column(Numeric(15, 2), nullable=False))
    balance: Decimal = Field(sa_column=Column(Numeric(15, 2), nullable=False))
    transaction_type: str = Field(max_length=100, nullable=False, index=True)
    account_number: str = Field(max_length=50, nullable=False, index=True)

    # Account and location info
    currency: str = Field(max_length=3, nullable=False)
    country_code: str = Field(max_length=2, nullable=False)

    # Optional transaction details
    channel: str | None = Field(default=None, max_length=100, index=True)
    reference: str | None = Field(default=None, max_length=200)

    # Raw data preservation
    raw_text: str | None = Field(default=None, sa_column=Column(Text))
    raw_json: dict[str, Any] | None = Field(default=None, sa_column=Column(Text))

    # Processing metadata
    source_file: str | None = Field(default=None, max_length=500, index=True)
    parser_name: str | None = Field(default=None, max_length=100, index=True)

    # Database indexes
    __table_args__ = (
        Index("idx_transaction_unique", "date", "amount", "description", "account_number", unique=True),
        Index("idx_transaction_date", "date"),
        Index("idx_transaction_account", "account_number"),
        Index("idx_transaction_type", "transaction_type"),
    )

    @property
    def is_withdrawal(self) -> bool:
        """Check if transaction is a withdrawal (negative amount)."""
        return self.amount < 0

    @property
    def is_deposit(self) -> bool:
        """Check if transaction is a deposit (positive amount)."""
        return self.amount > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert transaction to dictionary for storage."""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description,
            "amount": float(self.amount) if self.amount else None,
            "balance": float(self.balance) if self.balance else None,
            "transaction_type": self.transaction_type,
            "account_number": self.account_number,
            "currency": self.currency,
            "country_code": self.country_code,
            "channel": self.channel,
            "reference": self.reference,
            "raw_text": self.raw_text,
            "raw_json": self.raw_json,
            "source_file": self.source_file,
            "parser_name": self.parser_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        """Create transaction from dictionary."""
        return cls(
            id=data.get("id"),
            date=datetime.fromisoformat(data["date"]) if data.get("date") else None,
            description=data["description"],
            amount=Decimal(str(data["amount"])) if data.get("amount") else None,
            balance=Decimal(str(data["balance"])) if data.get("balance") else None,
            transaction_type=data["transaction_type"],
            account_number=data["account_number"],
            currency=data["currency"],
            country_code=data["country_code"],
            channel=data.get("channel"),
            reference=data.get("reference"),
            raw_text=data.get("raw_text"),
            raw_json=data.get("raw_json"),
            source_file=data.get("source_file"),
            parser_name=data.get("parser_name"),
        )
