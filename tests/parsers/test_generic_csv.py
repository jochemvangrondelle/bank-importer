"""Tests for generic CSV parser."""

from decimal import Decimal
from pathlib import Path

import pytest

from bank_importer_th.banks.generic_csv import GenericCsvParser
from tests.parsers.test_base import BaseParserTest


class TestGenericCsvParser(BaseParserTest):
    """Test generic CSV parser functionality."""

    @pytest.fixture
    def parser_class(self):
        """Return the parser class."""
        return GenericCsvParser

    @pytest.fixture
    def valid_file_content(self) -> str:
        """Valid CSV file content."""
        return """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,ATM Withdrawal,-5000.00,THB,45000.00,debit,ATM,ATM001
2024-01-02,Transfer Credit,10000.00,THB,55000.00,credit,IB,TRF001"""

    @pytest.fixture
    def valid_filename(self) -> str:
        """Valid filename for CSV file."""
        return "generic_valid.csv"

    @pytest.fixture
    def invalid_file_content(self) -> str:
        """Invalid file content."""
        return """Some random text
That doesn't match CSV format
At all"""

    @pytest.fixture
    def invalid_filename(self) -> str:
        """Invalid filename."""
        return "invalid_file.txt"

    def test_parse_valid_csv_file(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing a valid CSV file."""
        # Use the sample file from test data
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, sample_file, sample_account_config
        )

        assert len(transactions) == 10  # Should have 10 transactions

        # Validate first transaction
        first_transaction = transactions[0]
        self.validate_transaction(first_transaction, sample_account_config)
        assert first_transaction.date.year == 2024
        assert first_transaction.date.month == 1
        assert first_transaction.date.day == 1
        assert float(first_transaction.amount) == -5000.00
        assert first_transaction.balance == Decimal("45000.00")
        assert first_transaction.channel == "ATM"
        assert first_transaction.description == "ATM Withdrawal"
        assert first_transaction.transaction_type == "debit"
        assert first_transaction.reference == "ATM001"

    def test_parse_csv_with_different_date_formats(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing CSV with different date formats."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,Test Transaction,-1000.00,THB,10000.00,debit,ATM,TEST001
2024/01/02,Another Transaction,2000.00,THB,12000.00,credit,IB,TEST002
01/03/2024,Third Transaction,-500.00,THB,11500.00,debit,POS,TEST003"""

        file_path = self.create_test_file(
            content, "generic_csv_different_dates.csv", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, file_path, sample_account_config
        )

        assert len(transactions) == 3

        # Check different date formats were parsed correctly
        assert (
            transactions[0].date.year == 2024
            and transactions[0].date.month == 1
            and transactions[0].date.day == 1
        )
        assert (
            transactions[1].date.year == 2024
            and transactions[1].date.month == 1
            and transactions[1].date.day == 2
        )
        assert (
            transactions[2].date.year == 2024
            and transactions[2].date.month == 3
            and transactions[2].date.day == 1
        )

    def test_parse_csv_with_missing_optional_fields(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing CSV with missing optional fields."""
        content = """date,description,amount,currency
2024-01-01,Simple Transaction,-1000.00,THB
2024-01-02,Another Transaction,2000.00,THB"""

        file_path = self.create_test_file(
            content, "generic_csv_minimal.csv", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, file_path, sample_account_config
        )

        assert len(transactions) == 2

        # Check that optional fields are handled gracefully
        for transaction in transactions:
            assert transaction.description is not None
            assert transaction.amount is not None
            assert transaction.currency == "THB"

    def test_parse_csv_with_extra_fields(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing CSV with extra fields."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference,extra_field,another_field
2024-01-01,Test Transaction,-1000.00,THB,10000.00,debit,ATM,TEST001,extra_value,another_value
2024-01-02,Another Transaction,2000.00,THB,12000.00,credit,IB,TEST002,extra_value2,another_value2"""

        file_path = self.create_test_file(
            content, "generic_csv_extra_fields.csv", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, file_path, sample_account_config
        )

        assert len(transactions) == 2

        # Check that extra fields don't interfere with parsing
        for transaction in transactions:
            self.validate_transaction(transaction, sample_account_config)

    def test_parse_csv_with_quoted_fields(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing CSV with quoted fields."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,"ATM Withdrawal, Central Branch",-1000.00,THB,10000.00,debit,ATM,TEST001
2024-01-02,"Transfer Credit, From Account 123-456",2000.00,THB,12000.00,credit,IB,TEST002"""

        file_path = self.create_test_file(
            content, "generic_csv_quoted.csv", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, file_path, sample_account_config
        )

        assert len(transactions) == 2

        # Check that quoted descriptions are parsed correctly
        assert "ATM Withdrawal, Central Branch" in transactions[0].description
        assert "Transfer Credit, From Account 123-456" in transactions[1].description

    def test_parse_csv_with_different_amount_formats(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing CSV with different amount formats."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,Test Transaction,-1000.50,THB,10000.00,debit,ATM,TEST001
2024-01-02,Another Transaction,2000,THB,12000.00,credit,IB,TEST002
2024-01-03,Third Transaction,-500.75,THB,11500.00,debit,POS,TEST003"""

        file_path = self.create_test_file(
            content, "generic_csv_amount_formats.csv", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, file_path, sample_account_config
        )

        assert len(transactions) == 3

        # Check different amount formats
        assert float(transactions[0].amount) == -1000.50
        assert float(transactions[1].amount) == 2000.0
        assert float(transactions[2].amount) == -500.75

    def test_parse_csv_with_empty_lines(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing CSV with empty lines."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference

2024-01-01,Test Transaction,-1000.00,THB,10000.00,debit,ATM,TEST001

2024-01-02,Another Transaction,2000.00,THB,12000.00,credit,IB,TEST002

"""

        file_path = self.create_test_file(
            content, "generic_csv_empty_lines.csv", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, file_path, sample_account_config
        )

        assert len(transactions) == 2  # Should ignore empty lines

    def test_parse_csv_with_malformed_lines(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing CSV with some malformed lines."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,Test Transaction,-1000.00,THB,10000.00,debit,ATM,TEST001
Invalid line that should be skipped
2024-01-02,Another Transaction,2000.00,THB,12000.00,credit,IB,TEST002
Another invalid line
2024-01-03,Third Transaction,-500.00,THB,11500.00,debit,POS,TEST003"""

        file_path = self.create_test_file(
            content, "generic_csv_malformed.csv", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, file_path, sample_account_config
        )

        assert len(transactions) == 3  # Should parse valid lines and skip invalid ones

    def test_parse_csv_with_different_currencies(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing CSV with different currencies."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,USD Transaction,-100.00,USD,1000.00,debit,ATM,TEST001
2024-01-02,EUR Transaction,200.00,EUR,1200.00,credit,IB,TEST002
2024-01-03,THB Transaction,-500.00,THB,11500.00,debit,POS,TEST003"""

        file_path = self.create_test_file(
            content, "generic_csv_currencies.csv", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, file_path, sample_account_config
        )

        assert len(transactions) == 3

        # Check different currencies
        assert transactions[0].currency == "USD"
        assert transactions[1].currency == "EUR"
        assert transactions[2].currency == "THB"

    def test_parse_csv_with_balance_calculation(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test that balance calculations are consistent."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, sample_file, sample_account_config
        )

        # Check that balances are properly formatted as Decimal
        for transaction in transactions:
            assert isinstance(transaction.balance, Decimal)
            assert transaction.balance > 0

    def test_source_file_tracking(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test that source file is properly tracked."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, sample_file, sample_account_config
        )

        for transaction in transactions:
            assert transaction.source_file == str(sample_file)

    def test_parser_name_tracking(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test that parser name is properly set."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, sample_file, sample_account_config
        )

        for transaction in transactions:
            assert transaction.parser_name == "generic_csv"

    def test_transaction_type_detection(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test that transaction types are correctly detected."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, sample_file, sample_account_config
        )

        # Check transaction types
        debit_transactions = [t for t in transactions if t.transaction_type == "debit"]
        credit_transactions = [
            t for t in transactions if t.transaction_type == "credit"
        ]

        assert len(debit_transactions) > 0
        assert len(credit_transactions) > 0

    def test_channel_detection(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test that channels are correctly detected."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, sample_file, sample_account_config
        )

        # Check that channels are set
        channels = {t.channel for t in transactions if t.channel}
        expected_channels = {"ATM", "IB", "POS", "INT", "CDM", "FEE"}

        assert len(channels) > 0
        assert all(channel in expected_channels for channel in channels)

    def test_reference_tracking(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test that references are correctly tracked."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser, sample_file, sample_account_config
        )

        # Check that references are set
        references = [t.reference for t in transactions if t.reference]
        assert len(references) > 0

        # Check that references are unique
        unique_references = set(references)
        assert len(unique_references) == len(references)
