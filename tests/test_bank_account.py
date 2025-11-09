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

"""Tests for BankAccount model."""

import pytest

from bank_importer.models.bank_account import BankAccount


class TestBankAccount:
    """Tests for BankAccount model."""

    @pytest.mark.parametrize(
        ("account_name", "account_number", "bank_name", "currency", "country_code"),
        [
            ("Test Account", "123-456-789", "Test Bank", "THB", "TH"),
            ("Account 1", "111-222-333", "Bank A", "THB", "TH"),
            ("Account 2", "999-888-777", "Bank B", "USD", "US"),
        ],
    )
    def test_init(
        self,
        account_name: str,
        account_number: str,
        bank_name: str,
        currency: str,
        country_code: str,
    ) -> None:
        """Test basic initialization."""
        account = BankAccount(
            account_name=account_name,
            account_number=account_number,
            bank_name=bank_name,
            currency=currency,
            country_code=country_code,
        )
        assert account.account_name == account_name
        assert account.account_number == account_number
        assert account.bank_name == bank_name
        assert account.currency == currency
        assert account.country_code == country_code

    @pytest.mark.parametrize(
        ("currency", "country_code", "expected_currency", "expected_country"),
        [
            ("THB", "TH", "THB", "TH"),
            ("USD", "US", "USD", "US"),
            ("EUR", "DE", "EUR", "DE"),
        ],
    )
    def test_init_with_currency(
        self,
        currency: str,
        country_code: str,
        expected_currency: str,
        expected_country: str,
    ) -> None:
        """Test initialization with different currencies."""
        account = BankAccount(
            account_name="test",
            account_number="123",
            bank_name="Bank",
            currency=currency,
            country_code=country_code,
        )
        assert account.currency == expected_currency
        assert account.country_code == expected_country

    def test_init_with_all_fields(self) -> None:
        """Test initialization with all fields."""
        account = BankAccount(
            account_name="Test Account",
            account_number="123-456-789",
            bank_name="Test Bank",
            currency="THB",
            country_code="TH",
            branch_name="Main Branch",
            reference="test_ref",
        )
        assert account.currency == "THB"
        assert account.country_code == "TH"
        assert account.branch_name == "Main Branch"
        assert account.reference == "test_ref"

    @pytest.mark.parametrize(
        ("account_name", "account_number", "bank_name", "expected_in_str"),
        [
            ("Test Account", "123-456-789", "Test Bank", "Test Account"),
            ("Account 1", "111-222-333", "Bank A", "Account 1"),
        ],
    )
    def test_str_representation(
        self,
        account_name: str,
        account_number: str,
        bank_name: str,
        expected_in_str: str,
    ) -> None:
        """Test string representation."""
        account = BankAccount(
            account_name=account_name,
            account_number=account_number,
            bank_name=bank_name,
            currency="THB",
            country_code="TH",
        )
        str_repr = str(account)
        assert expected_in_str in str_repr
        assert account_number in str_repr

    @pytest.mark.parametrize(
        ("field_name", "field_value", "should_raise"),
        [
            ("account_number", "", True),
            ("account_name", "", True),
            ("bank_name", "", True),
            ("currency", "", True),
            ("country_code", "", True),
            ("account_number", "123", False),
            ("account_name", "Test", False),
        ],
    )
    def test_validate_account(
        self,
        field_name: str,
        field_value: str,
        should_raise: bool,
    ) -> None:
        """Test account validation."""
        account_data = {
            "account_number": "123-456-789",
            "account_name": "Test Account",
            "bank_name": "Test Bank",
            "currency": "THB",
            "country_code": "TH",
        }
        account_data[field_name] = field_value
        account = BankAccount(**account_data)

        if should_raise:
            with pytest.raises(ValueError):
                account.validate_account()
        else:
            account.validate_account()  # Should not raise
