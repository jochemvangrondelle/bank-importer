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

"""Transaction model for bank statements."""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """Represents a bank transaction."""

    # Primary key
    id: int | None = Field(default=None, description="Primary key")

    # Core transaction data
    date: datetime = Field(description="Transaction date")
    description: str = Field(max_length=500, description="Transaction description")
    translated_description: str | None = Field(default=None, max_length=500)
    amount: Decimal = Field(description="Transaction amount")
    balance: Decimal = Field(description="Account balance after transaction")
    transaction_type: str = Field(max_length=100, description="Transaction type")
    account_number: str = Field(max_length=50, description="Account number")

    # Enhanced balance tracking
    old_balance: Decimal | None = Field(default=None)
    new_balance: Decimal | None = Field(default=None)

    # Additional date fields
    transaction_date: datetime | None = Field(default=None)
    value_date: datetime | None = Field(default=None)
    posting_date: datetime | None = Field(default=None)
    effective_date: datetime | None = Field(default=None)

    # Account and location info
    currency: str = Field(max_length=3, description="Currency code")
    country_code: str = Field(max_length=2, description="Country code")

    # Optional transaction details
    channel: str | None = Field(default=None, max_length=100)
    reference: str | None = Field(default=None, max_length=200)
    check_number: str | None = Field(default=None, max_length=50)
    memo: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)
    subcategory: str | None = Field(default=None, max_length=100)

    # Additional transaction metadata
    exchange_rate: Decimal | None = Field(default=None)
    foreign_currency: str | None = Field(default=None, max_length=10)
    foreign_amount: Decimal | None = Field(default=None)
    fees: Decimal | None = Field(default=None)
    interest: Decimal | None = Field(default=None)
    tax: Decimal | None = Field(default=None)

    # Raw data preservation - store as JSON string
    raw_text: str | None = Field(default=None)
    raw_json: str | None = Field(default=None)

    # Processing metadata
    source_file: str | None = Field(default=None, max_length=500)
    parser_name: str | None = Field(default=None, max_length=100)
    unique_id: str | None = Field(default=None, max_length=100)

    def get_raw_json_dict(self) -> dict[str, Any] | None:
        """Get raw JSON data as dictionary."""
        if self.raw_json is None:
            return None
        try:
            result = json.loads(self.raw_json)
            if isinstance(result, dict):
                return result
            return None
        except (json.JSONDecodeError, TypeError):
            return None

    def set_raw_json_dict(self, value: dict[str, Any] | None) -> None:
        """Set raw JSON data from dictionary."""
        if value is None:
            self.raw_json = None
        else:
            self.raw_json = json.dumps(value, ensure_ascii=False)

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
            "raw_json": self.get_raw_json_dict(),
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
            msg = "Missing required fields: date, description, amount, balance"
            raise ValueError(
                msg,
            )

        # Parse timezone-aware dates
        def parse_datetime(date_str: str | None) -> datetime | None:
            if not date_str:
                return None
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                # Fallback for non-ISO format dates
                return datetime.fromisoformat(date_str)

        # Ensure date is not None since it's required
        parsed_date = parse_datetime(data["date"])
        if parsed_date is None:
            msg = "Invalid date format"
            raise ValueError(msg)

        # Create transaction instance
        transaction = cls(
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
            raw_json=None,  # Will be set below
            source_file=data.get("source_file"),
            parser_name=data.get("parser_name"),
        )

        # Set raw JSON data if provided
        if data.get("raw_json"):
            transaction.set_raw_json_dict(data["raw_json"])

        return transaction
