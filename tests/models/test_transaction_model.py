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

"""Tests for transaction model."""

import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from bank_importer.models.transaction import Transaction


class TestTransaction:
    """Test transaction model functionality."""

    @pytest.fixture
    def transaction(self, transaction_factory) -> Transaction:
        """Create a transaction for testing."""
        return transaction_factory()

    def test_get_raw_json_dict_valid(self, transaction: Transaction) -> None:
        """Test getting raw JSON dict with valid JSON."""
        test_dict = {"key1": "value1", "key2": 123}
        transaction.raw_json = json.dumps(test_dict)
        result = transaction.get_raw_json_dict()
        assert result == test_dict

    def test_get_raw_json_dict_invalid(self, transaction: Transaction) -> None:
        """Test getting raw JSON dict with invalid JSON."""
        transaction.raw_json = "invalid json{"
        result = transaction.get_raw_json_dict()
        assert result is None

    def test_get_raw_json_dict_none(self, transaction: Transaction) -> None:
        """Test getting raw JSON dict when None."""
        transaction.raw_json = None
        result = transaction.get_raw_json_dict()
        assert result is None

    def test_set_raw_json_dict(self, transaction: Transaction) -> None:
        """Test setting raw JSON dict."""
        test_dict = {"key1": "value1", "key2": 123}
        transaction.set_raw_json_dict(test_dict)
        assert transaction.raw_json is not None
        parsed = json.loads(transaction.raw_json)
        assert parsed == test_dict

    def test_set_raw_json_dict_none(self, transaction: Transaction) -> None:
        """Test setting raw JSON dict to None."""
        transaction.raw_json = "some json"
        transaction.set_raw_json_dict(None)
        assert transaction.raw_json is None

    @pytest.mark.parametrize(
        ("amount", "expected_withdrawal", "expected_deposit"),
        [
            (Decimal("-100.00"), True, False),
            (Decimal("100.00"), False, True),
            (Decimal("0.00"), False, False),
        ],
    )
    def test_is_withdrawal_is_deposit(
        self,
        transaction_factory,
        amount: Decimal,
        expected_withdrawal: bool,
        expected_deposit: bool,
    ) -> None:
        """Test withdrawal and deposit properties."""
        transaction = transaction_factory(amount=amount)
        assert transaction.is_withdrawal == expected_withdrawal
        assert transaction.is_deposit == expected_deposit

    def test_balance_change(self, transaction_factory) -> None:
        """Test balance change calculation."""
        transaction = transaction_factory(
            old_balance=Decimal("1000.00"),
            new_balance=Decimal("1200.00"),
        )
        assert transaction.balance_change == Decimal("200.00")

    def test_balance_change_none(self, transaction: Transaction) -> None:
        """Test balance change when balances are None."""
        transaction.old_balance = None
        transaction.new_balance = None
        assert transaction.balance_change is None

    def test_primary_date(self, transaction_factory) -> None:
        """Test primary date property."""
        value_date = datetime(2024, 1, 2, tzinfo=UTC)
        transaction_date = datetime(2024, 1, 3, tzinfo=UTC)
        date = datetime(2024, 1, 1, tzinfo=UTC)

        # Prefers value_date
        transaction = transaction_factory(
            date=date,
            value_date=value_date,
            transaction_date=transaction_date,
        )
        assert transaction.primary_date == value_date

        # Falls back to transaction_date
        transaction = transaction_factory(
            date=date,
            value_date=None,
            transaction_date=transaction_date,
        )
        assert transaction.primary_date == transaction_date

        # Falls back to date
        transaction = transaction_factory(
            date=date,
            value_date=None,
            transaction_date=None,
        )
        assert transaction.primary_date == date

    def test_to_dict(self, transaction: Transaction) -> None:
        """Test converting transaction to dictionary."""
        result = transaction.to_dict()
        assert isinstance(result, dict)
        assert "id" in result
        assert "date" in result
        assert "description" in result
        assert "amount" in result
        assert "balance" in result
        assert "transaction_type" in result
        assert "account_number" in result

    def test_to_dict_with_all_fields(self, transaction_factory) -> None:
        """Test converting transaction with all fields to dictionary."""
        transaction = transaction_factory(
            old_balance=Decimal("1000.00"),
            new_balance=Decimal("1200.00"),
            transaction_date=datetime(2024, 1, 2, tzinfo=UTC),
            value_date=datetime(2024, 1, 3, tzinfo=UTC),
        )
        result = transaction.to_dict()
        assert result["old_balance"] == 1000.00
        assert result["new_balance"] == 1200.00
        assert "transaction_date" in result
        assert "value_date" in result
        assert isinstance(result, dict)
