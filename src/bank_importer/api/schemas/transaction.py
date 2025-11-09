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

"""Transaction API schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from bank_importer.models.transaction import Transaction


class TransactionResponse(BaseModel):
    """Transaction response schema."""

    id: int | None = None
    date: datetime
    description: str = Field(..., max_length=500)
    translated_description: str | None = Field(None, max_length=500)
    amount: Decimal
    balance: Decimal
    transaction_type: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=50)
    old_balance: Decimal | None = None
    new_balance: Decimal | None = None
    transaction_date: datetime | None = None
    value_date: datetime | None = None
    posting_date: datetime | None = None
    effective_date: datetime | None = None
    currency: str = Field(..., max_length=3)
    country_code: str = Field(..., max_length=2)
    channel: str | None = Field(None, max_length=100)
    reference: str | None = Field(None, max_length=200)
    check_number: str | None = Field(None, max_length=50)
    memo: str | None = Field(None, max_length=500)
    category: str | None = Field(None, max_length=100)
    subcategory: str | None = Field(None, max_length=100)
    exchange_rate: Decimal | None = None
    foreign_currency: str | None = Field(None, max_length=3)
    foreign_amount: Decimal | None = None
    fees: Decimal | None = None
    interest: Decimal | None = None
    tax: Decimal | None = None
    raw_text: str | None = None
    raw_json: str | None = None
    source_file: str | None = Field(None, max_length=500)
    parser_name: str | None = Field(None, max_length=100)
    unique_id: str | None = Field(None, max_length=100)

    @classmethod
    def from_transaction(cls, transaction: Transaction) -> "TransactionResponse":
        """Create from Transaction model."""
        data = transaction.to_dict()
        # Ensure raw_json is a string, not a dict
        if "raw_json" in data and isinstance(data["raw_json"], dict):
            import json

            data["raw_json"] = json.dumps(data["raw_json"], ensure_ascii=False)
        return cls(**data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TransactionResponse":
        """Create from dictionary."""
        return cls(**data)


class TransactionUpdate(BaseModel):
    """Transaction update schema (only updatable fields)."""

    category: str | None = Field(
        None,
        max_length=100,
        description="Transaction category",
    )
    subcategory: str | None = Field(
        None,
        max_length=100,
        description="Transaction subcategory",
    )
    memo: str | None = Field(None, max_length=500, description="Transaction memo")
    translated_description: str | None = Field(
        None,
        max_length=500,
        description="Translated description",
    )
