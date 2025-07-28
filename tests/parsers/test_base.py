"""Base test class for parser testing."""

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from bank_importer_th.models.transaction import Transaction


class BaseParserTest:
    """Base class for parser tests with common utilities."""

    @pytest.fixture
    def sample_account_config(self) -> dict[str, Any]:
        """Sample account configuration for testing."""
        return {
            "name": "test_account",
            "bank_name": "Test Bank",
            "account_number": "123-456-789",
            "account_name": "Test User",
            "currency": "THB",
            "country_code": "TH",
            "reference": "test_ref",
        }

    @pytest.fixture
    def test_data_dir(self) -> Path:
        """Get the test data directory."""
        return Path(__file__).parent.parent / "data"

    def create_test_file(
        self, content: str, filename: str, test_data_dir: Path
    ) -> Path:
        """Create a test file with given content."""
        test_data_dir.mkdir(exist_ok=True)
        file_path = test_data_dir / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def assert_transaction_basic_fields(
        self, transaction: Transaction, account_config: dict[str, Any]
    ) -> None:
        """Assert basic transaction fields are correctly set."""
        assert transaction is not None
        assert transaction.account_number == account_config["account_number"]
        assert transaction.currency == account_config["currency"]
        assert transaction.source_file is not None
        assert transaction.parser_name is not None

    def assert_transaction_amount_valid(self, transaction: Transaction) -> None:
        """Assert transaction amount is valid."""
        assert transaction.amount is not None
        assert isinstance(transaction.amount, int | float | str | Decimal)
        # Convert to float for comparison if it's a string or Decimal
        if isinstance(transaction.amount, str):
            amount = float(transaction.amount)
        elif isinstance(transaction.amount, Decimal):
            amount = float(transaction.amount)
        else:
            amount = transaction.amount
        assert amount != 0  # Amount should not be zero

    def assert_transaction_date_valid(self, transaction: Transaction) -> None:
        """Assert transaction date is valid."""
        assert transaction.date is not None
        assert hasattr(transaction.date, "year")
        assert hasattr(transaction.date, "month")
        assert hasattr(transaction.date, "day")

    def assert_transaction_description_valid(self, transaction: Transaction) -> None:
        """Assert transaction description is valid."""
        assert transaction.description is not None
        assert isinstance(transaction.description, str)
        assert len(transaction.description.strip()) > 0

    def validate_transaction(
        self, transaction: Transaction, account_config: dict[str, Any]
    ) -> None:
        """Validate a transaction has all required fields."""
        self.assert_transaction_basic_fields(transaction, account_config)
        self.assert_transaction_amount_valid(transaction)
        self.assert_transaction_date_valid(transaction)
        self.assert_transaction_description_valid(transaction)

    def get_transactions_from_parser(
        self, parser_class, file_path: Path, account_config: dict[str, Any]
    ) -> list[Transaction]:
        """Get all transactions from a parser."""
        parser = parser_class()
        transactions = list(parser.parse_file(file_path, account_config))
        return transactions

    def test_parser_can_parse_valid_file(
        self,
        parser_class,
        valid_file_content: str,
        valid_filename: str,
        test_data_dir: Path,
    ) -> None:
        """Test that parser can identify valid files."""
        file_path = self.create_test_file(
            valid_file_content, valid_filename, test_data_dir
        )
        parser = parser_class()

        assert parser.can_parse(file_path) is True

    def test_parser_cannot_parse_invalid_file(
        self,
        parser_class,
        invalid_file_content: str,
        invalid_filename: str,
        test_data_dir: Path,
    ) -> None:
        """Test that parser correctly rejects invalid files."""
        file_path = self.create_test_file(
            invalid_file_content, invalid_filename, test_data_dir
        )
        parser = parser_class()

        assert parser.can_parse(file_path) is False

    def test_parser_raises_error_for_nonexistent_file(self, parser_class) -> None:
        """Test that parser raises error for nonexistent files."""
        parser = parser_class()
        nonexistent_file = Path("/nonexistent/file.txt")

        with pytest.raises(ValueError, match="File does not exist"):
            parser.can_parse(nonexistent_file)

    def test_parser_raises_error_for_directory(
        self, parser_class, test_data_dir: Path
    ) -> None:
        """Test that parser raises error for directories."""
        parser = parser_class()

        with pytest.raises(ValueError, match="Path is not a file"):
            parser.can_parse(test_data_dir)
