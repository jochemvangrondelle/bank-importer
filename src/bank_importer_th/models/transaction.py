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
    translated_description: str | None = Field(default=None, max_length=500)
    amount: Decimal = Field(sa_column=Column(Numeric(15, 2), nullable=False))
    balance: Decimal = Field(sa_column=Column(Numeric(15, 2), nullable=False))
    transaction_type: str = Field(max_length=100, nullable=False, index=True)
    account_number: str = Field(max_length=50, nullable=False, index=True)

    # Enhanced balance tracking
    old_balance: Decimal | None = Field(default=None, sa_column=Column(Numeric(15, 2)))
    new_balance: Decimal | None = Field(default=None, sa_column=Column(Numeric(15, 2)))

    # Additional date fields
    transaction_date: datetime | None = Field(default=None, sa_column=Column(DateTime))
    value_date: datetime | None = Field(default=None, sa_column=Column(DateTime))
    posting_date: datetime | None = Field(default=None, sa_column=Column(DateTime))
    effective_date: datetime | None = Field(default=None, sa_column=Column(DateTime))

    # Account and location info
    currency: str = Field(max_length=3, nullable=False)
    country_code: str = Field(max_length=2, nullable=False)

    # Optional transaction details
    channel: str | None = Field(default=None, max_length=100, index=True)
    reference: str | None = Field(default=None, max_length=200)
    check_number: str | None = Field(default=None, max_length=50)
    memo: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100, index=True)
    subcategory: str | None = Field(default=None, max_length=100)

    # Additional transaction metadata
    exchange_rate: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(10, 6))
    )
    foreign_currency: str | None = Field(default=None, max_length=3)
    foreign_amount: Decimal | None = Field(
        default=None, sa_column=Column(Numeric(15, 2))
    )
    fees: Decimal | None = Field(default=None, sa_column=Column(Numeric(15, 2)))
    interest: Decimal | None = Field(default=None, sa_column=Column(Numeric(15, 2)))
    tax: Decimal | None = Field(default=None, sa_column=Column(Numeric(15, 2)))

    # Raw data preservation
    raw_text: str | None = Field(default=None, sa_column=Column(Text))
    raw_json: dict[str, Any] | None = Field(default=None, sa_column=Column(Text))

    # Processing metadata
    source_file: str | None = Field(default=None, max_length=500, index=True)
    parser_name: str | None = Field(default=None, max_length=100, index=True)
    unique_id: str | None = Field(default=None, max_length=100, index=True)

    # Database indexes
    __table_args__ = (
        Index(
            "idx_transaction_unique",
            "date",
            "amount",
            "description",
            "account_number",
            "source_file",
            "unique_id",
            unique=True,
        ),
        Index("idx_transaction_date", "date"),
        Index("idx_transaction_account", "account_number"),
        Index("idx_transaction_type", "transaction_type"),
        Index("idx_transaction_category", "category"),
        Index("idx_transaction_channel", "channel"),
        Index("idx_transaction_value_date", "value_date"),
    )

    @property
    def is_withdrawal(self) -> bool:
        """Check if transaction is a withdrawal (negative amount)."""
        return self.amount < 0

    @property
    def is_deposit(self) -> bool:
        """Check if transaction is a deposit (positive amount)."""
        return self.amount > 0

    @property
    def balance_change(self) -> Decimal | None:
        """Calculate the balance change (new_balance - old_balance)."""
        if self.new_balance is not None and self.old_balance is not None:
            return self.new_balance - self.old_balance
        return None

    @property
    def primary_date(self) -> datetime:
        """Get the primary date for the transaction (prefers value_date over date)."""
        return self.value_date or self.transaction_date or self.date

    def to_dict(self) -> dict[str, Any]:
        """Convert transaction to dictionary for storage."""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description,
            "amount": float(self.amount) if self.amount else None,
            "balance": float(self.balance) if self.balance else None,
            "old_balance": float(self.old_balance) if self.old_balance else None,
            "new_balance": float(self.new_balance) if self.new_balance else None,
            "transaction_type": self.transaction_type,
            "account_number": self.account_number,
            "transaction_date": self.transaction_date.isoformat()
            if self.transaction_date
            else None,
            "value_date": self.value_date.isoformat() if self.value_date else None,
            "posting_date": self.posting_date.isoformat()
            if self.posting_date
            else None,
            "effective_date": self.effective_date.isoformat()
            if self.effective_date
            else None,
            "currency": self.currency,
            "country_code": self.country_code,
            "channel": self.channel,
            "reference": self.reference,
            "check_number": self.check_number,
            "memo": self.memo,
            "category": self.category,
            "subcategory": self.subcategory,
            "exchange_rate": float(self.exchange_rate) if self.exchange_rate else None,
            "foreign_currency": self.foreign_currency,
            "foreign_amount": float(self.foreign_amount)
            if self.foreign_amount
            else None,
            "fees": float(self.fees) if self.fees else None,
            "interest": float(self.interest) if self.interest else None,
            "tax": float(self.tax) if self.tax else None,
            "raw_text": self.raw_text,
            "raw_json": self.raw_json,
            "source_file": self.source_file,
            "parser_name": self.parser_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        """Create transaction from dictionary."""
        # Ensure required fields are present
        if (
            not data.get("date")
            or not data.get("description")
            or not data.get("amount")
            or not data.get("balance")
        ):
            raise ValueError(
                "Missing required fields: date, description, amount, balance"
            )

        # Parse timezone-aware dates
        def parse_datetime(date_str: str | None) -> datetime | None:
            if not date_str:
                return None
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                # Fallback for non-ISO format dates
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        # Ensure date is not None since it's required
        parsed_date = parse_datetime(data["date"])
        if parsed_date is None:
            raise ValueError("Invalid date format")

        return cls(
            id=data.get("id"),
            date=parsed_date,
            description=data["description"],
            amount=Decimal(str(data["amount"])),
            balance=Decimal(str(data["balance"])),
            old_balance=Decimal(str(data["old_balance"]))
            if data.get("old_balance")
            else None,
            new_balance=Decimal(str(data["new_balance"]))
            if data.get("new_balance")
            else None,
            transaction_type=data["transaction_type"],
            account_number=data["account_number"],
            transaction_date=parse_datetime(data.get("transaction_date")),
            value_date=parse_datetime(data.get("value_date")),
            posting_date=parse_datetime(data.get("posting_date")),
            effective_date=parse_datetime(data.get("effective_date")),
            currency=data["currency"],
            country_code=data["country_code"],
            channel=data.get("channel"),
            reference=data.get("reference"),
            check_number=data.get("check_number"),
            memo=data.get("memo"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            exchange_rate=Decimal(str(data["exchange_rate"]))
            if data.get("exchange_rate")
            else None,
            foreign_currency=data.get("foreign_currency"),
            foreign_amount=Decimal(str(data["foreign_amount"]))
            if data.get("foreign_amount")
            else None,
            fees=Decimal(str(data["fees"])) if data.get("fees") else None,
            interest=Decimal(str(data["interest"])) if data.get("interest") else None,
            tax=Decimal(str(data["tax"])) if data.get("tax") else None,
            raw_text=data.get("raw_text"),
            raw_json=data.get("raw_json"),
            source_file=data.get("source_file"),
            parser_name=data.get("parser_name"),
        )
