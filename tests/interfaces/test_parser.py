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

"""Tests for parser interface."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from bank_importer.config import ConfigManager
from bank_importer.interfaces.parser import Parser, ReconciliationTotals
from bank_importer.models.transaction import Transaction


class ConcreteParser(Parser):
    """Concrete parser implementation for testing."""

    def parse_file(
        self,
        file_path: Path,
        account_config: dict[str, Any],
        config_manager: "ConfigManager | None" = None,
    ) -> Iterator[Transaction]:
        """Parse file."""
        return iter([])

    def can_parse(self, file_path: Path) -> bool:
        """Check if can parse."""
        return True


class TestReconciliationTotals:
    """Test ReconciliationTotals dataclass."""

    def test_valid_totals(self) -> None:
        """Test creating valid reconciliation totals."""
        totals = ReconciliationTotals(
            debit_count=10,
            debit_total=Decimal("1000.00"),
            credit_count=5,
            credit_total=Decimal("500.00"),
        )
        assert totals.debit_count == 10
        assert totals.debit_total == Decimal("1000.00")
        assert totals.credit_count == 5
        assert totals.credit_total == Decimal("500.00")

    def test_negative_debit_count_raises_error(self) -> None:
        """Test that negative debit count raises ValueError."""
        with pytest.raises(ValueError, match="Counts cannot be negative"):
            ReconciliationTotals(
                debit_count=-1,
                debit_total=Decimal("1000.00"),
                credit_count=5,
                credit_total=Decimal("500.00"),
            )

    def test_negative_credit_count_raises_error(self) -> None:
        """Test that negative credit count raises ValueError."""
        with pytest.raises(ValueError, match="Counts cannot be negative"):
            ReconciliationTotals(
                debit_count=10,
                debit_total=Decimal("1000.00"),
                credit_count=-1,
                credit_total=Decimal("500.00"),
            )

    def test_negative_debit_total_raises_error(self) -> None:
        """Test that negative debit total raises ValueError."""
        with pytest.raises(ValueError, match="Totals cannot be negative"):
            ReconciliationTotals(
                debit_count=10,
                debit_total=Decimal("-1000.00"),
                credit_count=5,
                credit_total=Decimal("500.00"),
            )

    def test_negative_credit_total_raises_error(self) -> None:
        """Test that negative credit total raises ValueError."""
        with pytest.raises(ValueError, match="Totals cannot be negative"):
            ReconciliationTotals(
                debit_count=10,
                debit_total=Decimal("1000.00"),
                credit_count=5,
                credit_total=Decimal("-500.00"),
            )


class TestParserAbstractMethods:
    """Test parser abstract methods raise NotImplementedError."""

    def test_get_bank_type_raises_not_implemented(self) -> None:
        """Test get_bank_type raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_bank_type",
        ):
            parser.get_bank_type()

    def test_get_export_config_raises_not_implemented(self) -> None:
        """Test get_export_config raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_export_config",
        ):
            parser.get_export_config()

    def test_get_parser_name_raises_not_implemented(self) -> None:
        """Test get_parser_name raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_parser_name",
        ):
            parser.get_parser_name()

    def test_get_default_account_name_raises_not_implemented(self) -> None:
        """Test get_default_account_name raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_default_account_name",
        ):
            parser.get_default_account_name()

    def test_get_default_account_number_raises_not_implemented(self) -> None:
        """Test get_default_account_number raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_default_account_number",
        ):
            parser.get_default_account_number()

    def test_get_default_currency_raises_not_implemented(self) -> None:
        """Test get_default_currency raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_default_currency",
        ):
            parser.get_default_currency()

    def test_get_default_country_code_raises_not_implemented(self) -> None:
        """Test get_default_country_code raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_default_country_code",
        ):
            parser.get_default_country_code()

    def test_get_supported_file_patterns_raises_not_implemented(self) -> None:
        """Test get_supported_file_patterns raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_supported_file_patterns",
        ):
            parser.get_supported_file_patterns()

    def test_get_supported_extensions_raises_not_implemented(self) -> None:
        """Test get_supported_extensions raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_supported_extensions",
        ):
            parser.get_supported_extensions()

    def test_get_parser_description_raises_not_implemented(self) -> None:
        """Test get_parser_description raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_parser_description",
        ):
            parser.get_parser_description()

    def test_get_parser_version_raises_not_implemented(self) -> None:
        """Test get_parser_version raises NotImplementedError."""
        parser = ConcreteParser()
        with pytest.raises(
            NotImplementedError,
            match="Subclasses must implement get_parser_version",
        ):
            parser.get_parser_version()


class TestParserReconciliation:
    """Test parser reconciliation methods."""

    def test_supports_reconciliation_default_false(self) -> None:
        """Test supports_reconciliation defaults to False."""
        parser = ConcreteParser()
        assert parser.supports_reconciliation() is False

    def test_extract_reconciliation_totals_returns_none_when_not_supported(
        self,
    ) -> None:
        """Test extract_reconciliation_totals returns None when reconciliation not supported."""
        parser = ConcreteParser()
        result = parser.extract_reconciliation_totals(Path("test.pdf"), {})
        assert result is None

    def test_extract_reconciliation_totals_raises_when_supported_but_not_implemented(
        self,
    ) -> None:
        """Test extract_reconciliation_totals raises when supported but not implemented."""
        parser = ConcreteParser()
        # Mock supports_reconciliation to return True
        parser.supports_reconciliation = Mock(return_value=True)  # type: ignore[method-assign]
        with pytest.raises(
            NotImplementedError,
            match="Parser supports reconciliation but extract_reconciliation_totals",
        ):
            parser.extract_reconciliation_totals(Path("test.pdf"), {})

    def test_verify_reconciliation_success(self) -> None:
        """Test verify_reconciliation succeeds when totals match."""
        parser = ConcreteParser()
        transactions = [
            Transaction(
                date=datetime(2025, 1, 1, tzinfo=UTC),
                amount=Decimal("-100.00"),
                description="Debit 1",
                balance=Decimal("1000.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                parser_name="test",
            ),
            Transaction(
                date=datetime(2025, 1, 2, tzinfo=UTC),
                amount=Decimal("-200.00"),
                description="Debit 2",
                balance=Decimal("800.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                parser_name="test",
            ),
            Transaction(
                date=datetime(2025, 1, 3, tzinfo=UTC),
                amount=Decimal("300.00"),
                description="Credit 1",
                balance=Decimal("1100.00"),
                transaction_type="credit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                parser_name="test",
            ),
        ]
        expected_totals = ReconciliationTotals(
            debit_count=2,
            debit_total=Decimal("300.00"),
            credit_count=1,
            credit_total=Decimal("300.00"),
        )
        # Should not raise
        parser.verify_reconciliation(transactions, expected_totals, Path("test.pdf"))

    def test_verify_reconciliation_debit_total_mismatch(self) -> None:
        """Test verify_reconciliation raises on debit total mismatch."""
        parser = ConcreteParser()
        transactions = [
            Transaction(
                date=datetime(2025, 1, 1, tzinfo=UTC),
                amount=Decimal("-100.00"),
                description="Debit 1",
                balance=Decimal("1000.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                parser_name="test",
            ),
        ]
        expected_totals = ReconciliationTotals(
            debit_count=1,
            debit_total=Decimal("200.00"),  # Expected 200, actual 100
            credit_count=0,
            credit_total=Decimal("0.00"),
        )
        with pytest.raises(ValueError, match="Debit total mismatch"):
            parser.verify_reconciliation(
                transactions,
                expected_totals,
                Path("test.pdf"),
            )

    def test_verify_reconciliation_credit_total_mismatch(self) -> None:
        """Test verify_reconciliation raises on credit total mismatch."""
        parser = ConcreteParser()
        transactions = [
            Transaction(
                date=datetime(2025, 1, 1, tzinfo=UTC),
                amount=Decimal("100.00"),
                description="Credit 1",
                balance=Decimal("1100.00"),
                transaction_type="credit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                parser_name="test",
            ),
        ]
        expected_totals = ReconciliationTotals(
            debit_count=0,
            debit_total=Decimal("0.00"),
            credit_count=1,
            credit_total=Decimal("200.00"),  # Expected 200, actual 100
        )
        with pytest.raises(ValueError, match="Credit total mismatch"):
            parser.verify_reconciliation(
                transactions,
                expected_totals,
                Path("test.pdf"),
            )

    def test_verify_reconciliation_debit_count_mismatch(self) -> None:
        """Test verify_reconciliation raises on debit count mismatch."""
        from datetime import UTC, datetime

        parser = ConcreteParser()
        transactions = [
            Transaction(
                date=datetime(2025, 1, 1, tzinfo=UTC),
                amount=Decimal("-100.00"),
                description="Debit 1",
                balance=Decimal("1000.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                parser_name="test",
            ),
        ]
        expected_totals = ReconciliationTotals(
            debit_count=2,  # Expected 2, actual 1
            debit_total=Decimal("100.00"),
            credit_count=0,
            credit_total=Decimal("0.00"),
        )
        with pytest.raises(ValueError, match="Debit count mismatch"):
            parser.verify_reconciliation(
                transactions,
                expected_totals,
                Path("test.pdf"),
            )

    def test_verify_reconciliation_credit_count_mismatch(self) -> None:
        """Test verify_reconciliation raises on credit count mismatch."""
        parser = ConcreteParser()
        transactions = [
            Transaction(
                date=datetime(2025, 1, 1, tzinfo=UTC),
                amount=Decimal("100.00"),
                description="Credit 1",
                balance=Decimal("1100.00"),
                transaction_type="credit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                parser_name="test",
            ),
        ]
        expected_totals = ReconciliationTotals(
            debit_count=0,
            debit_total=Decimal("0.00"),
            credit_count=2,  # Expected 2, actual 1
            credit_total=Decimal("100.00"),
        )
        with pytest.raises(ValueError, match="Credit count mismatch"):
            parser.verify_reconciliation(
                transactions,
                expected_totals,
                Path("test.pdf"),
            )

    def test_verify_reconciliation_with_tolerance(self) -> None:
        """Test verify_reconciliation respects tolerance."""
        parser = ConcreteParser()
        transactions = [
            Transaction(
                date=datetime(2025, 1, 1, tzinfo=UTC),
                amount=Decimal("-100.00"),
                description="Debit 1",
                balance=Decimal("1000.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                parser_name="test",
            ),
        ]
        expected_totals = ReconciliationTotals(
            debit_count=1,
            debit_total=Decimal("100.01"),  # Within tolerance of 0.01
            credit_count=0,
            credit_total=Decimal("0.00"),
        )
        # Should not raise with tolerance
        parser.verify_reconciliation(
            transactions,
            expected_totals,
            Path("test.pdf"),
            tolerance=Decimal("0.02"),
        )

    def test_verify_reconciliation_multiple_errors(self) -> None:
        """Test verify_reconciliation reports all errors."""
        parser = ConcreteParser()
        transactions = [
            Transaction(
                date=datetime(2025, 1, 1, tzinfo=UTC),
                amount=Decimal("-100.00"),
                description="Debit 1",
                balance=Decimal("1000.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                parser_name="test",
            ),
        ]
        expected_totals = ReconciliationTotals(
            debit_count=2,  # Wrong count
            debit_total=Decimal("200.00"),  # Wrong total
            credit_count=1,  # Wrong count
            credit_total=Decimal("50.00"),  # Wrong total
        )
        with pytest.raises(ValueError) as exc_info:
            parser.verify_reconciliation(
                transactions,
                expected_totals,
                Path("test.pdf"),
            )
        error_msg = str(exc_info.value)
        assert "Debit total mismatch" in error_msg
        assert "Debit count mismatch" in error_msg
        assert "Credit total mismatch" in error_msg
        assert "Credit count mismatch" in error_msg
