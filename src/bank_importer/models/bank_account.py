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

"""Bank account model."""

from pydantic import BaseModel, Field


class BankAccount(BaseModel):
    """Represents a bank account configuration."""

    # Primary key
    id: int | None = Field(default=None, description="Primary key")

    # Account identification
    account_number: str = Field(max_length=50, description="Account number")
    account_name: str = Field(max_length=200, description="Account name")
    bank_name: str = Field(max_length=100, description="Bank name")

    # Account details
    currency: str = Field(max_length=3, description="Currency code")
    country_code: str = Field(max_length=2, description="Country code")

    # Optional details
    branch_name: str | None = Field(default=None, max_length=100)
    reference: str | None = Field(default=None, max_length=200)

    def validate_account(self) -> None:
        """Validate account configuration."""
        if not self.account_number:
            msg = "Account number is required"
            raise ValueError(msg)
        if not self.account_name:
            msg = "Account name is required"
            raise ValueError(msg)
        if not self.bank_name:
            msg = "Bank name is required"
            raise ValueError(msg)
        if not self.currency:
            msg = "Currency is required"
            raise ValueError(msg)
        if not self.country_code:
            msg = "Country code is required"
            raise ValueError(msg)
