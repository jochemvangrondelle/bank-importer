"""Tests for Krungsri text parser."""

from decimal import Decimal
from pathlib import Path

import pytest

from bank_importer_th.banks.krungsri_text import KrungsriTextParser
from tests.parsers.test_base import BaseParserTest


class TestKrungsriTextParser(BaseParserTest):
    """Test Krungsri text parser functionality."""

    @pytest.fixture
    def parser_class(self):
        """Return the parser class."""
        return KrungsriTextParser

    @pytest.fixture
    def valid_file_content(self) -> str:
        """Valid Krungsri text file content."""
        return """Date/Time Transaction Withdrawal/Deposit Outstanding Balance Channel Description
01/01/2024 09:30:15 ATM Withdrawal 5,000.00 45,000.00 ATM ATM Withdrawal
01/02/2024 14:20:30 Transfer Credit 10,000.00 55,000.00 IB Transfer from Account 123-456-789"""

    @pytest.fixture
    def valid_filename(self) -> str:
        """Valid filename for Krungsri text file."""
        return "krungsri_valid.txt"

    @pytest.fixture
    def invalid_file_content(self) -> str:
        """Invalid file content that should not be parsed."""
        return """Some random text
That doesn't match the Krungsri format
At all"""

    @pytest.fixture
    def invalid_filename(self) -> str:
        """Invalid filename."""
        return "invalid_file.txt"

    def test_parse_valid_krungsri_file(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing a valid Krungsri text file."""
        parser = KrungsriTextParser()
        file_path = test_data_dir / "krungsri_sample.txt"

        transactions = list(parser.parse_file(file_path, sample_account_config))

        assert len(transactions) > 0

        # Validate first transaction
        first_transaction = transactions[0]
        self.validate_transaction(first_transaction, sample_account_config)

        # Check specific values
        assert first_transaction.date.year == 2024
        assert first_transaction.date.month == 1
        assert first_transaction.date.day == 1
        assert (
            float(first_transaction.amount) == -5000.00
        )  # Withdrawal should be negative (spending)
        assert first_transaction.balance == Decimal("45000.00")
        assert first_transaction.channel == "ATM"

    def test_parse_line_withdrawal(self, sample_account_config: dict) -> None:
        """Test parsing a withdrawal line."""
        parser = KrungsriTextParser()
        line = (
            "01/01/2024 09:30:15 ATM Withdrawal 5,000.00 45,000.00 ATM ATM Withdrawal"
        )

        transaction = parser._parse_line(line, sample_account_config, "test.txt")

        assert transaction is not None
        assert transaction.date.year == 2024
        assert transaction.date.month == 1
        assert transaction.date.day == 1
        assert (
            float(transaction.amount) == -5000.00
        )  # Withdrawals should be negative (spending)
        assert transaction.balance == Decimal("45000.00")
        assert transaction.channel == "ATM"
        assert "ATM Withdrawal" in transaction.description

    def test_parse_line_credit(self, sample_account_config: dict) -> None:
        """Test parsing a credit line."""
        parser = KrungsriTextParser()
        line = "01/02/2024 14:20:30 Transfer Credit 10,000.00 55,000.00 IB Transfer from Account"

        transaction = parser._parse_line(line, sample_account_config, "test.txt")

        assert transaction is not None
        assert transaction.date.year == 2024
        assert transaction.date.month == 2  # Fixed: should be February, not January
        assert transaction.date.day == 1
        assert (
            float(transaction.amount) == 10000.00
        )  # Credits should be positive (money coming in)
        assert transaction.balance == Decimal("55000.00")
        assert transaction.channel == "IB"
        assert "Transfer from Account" in transaction.description

    def test_parse_line_with_interest(self, sample_account_config: dict) -> None:
        """Test parsing an interest line."""
        parser = KrungsriTextParser()
        line = (
            "01/04/2024 16:45:20 Interest Credit 150.00 52,650.00 INT Monthly Interest"
        )

        transaction = parser._parse_line(line, sample_account_config, "test.txt")

        assert transaction is not None
        assert (
            float(transaction.amount) == 150.00
        )  # Interest should be positive (credit)
        assert transaction.balance == Decimal("52650.00")
        assert transaction.channel == "INT"
        assert "Monthly Interest" in transaction.description

    def test_parse_line_with_fee(self, sample_account_config: dict) -> None:
        """Test parsing a fee line."""
        parser = KrungsriTextParser()
        line = "01/07/2024 12:40:50 Fee Debit 50.00 59,600.00 FEE Monthly Account Fee"

        transaction = parser._parse_line(line, sample_account_config, "test.txt")

        assert transaction is not None
        assert float(transaction.amount) == -50.00  # Fees should be negative (spending)
        assert transaction.balance == Decimal("59600.00")
        assert transaction.channel == "FEE"
        assert "Monthly Account Fee" in transaction.description

    def test_parse_line_without_channel(self, sample_account_config: dict) -> None:
        """Test parsing a line without channel information."""
        parser = KrungsriTextParser()
        line = (
            "01/10/2024 14:35:15 Payment Debit 1,200.00 60,400.00 Payment at Restaurant"
        )

        transaction = parser._parse_line(line, sample_account_config, "test.txt")

        assert transaction is not None
        assert (
            float(transaction.amount) == -1200.00
        )  # Payments should be negative (spending)
        assert transaction.balance == Decimal("60400.00")
        assert transaction.channel is None
        assert "Payment at Restaurant" in transaction.description

    def test_parse_invalid_line_format(self, sample_account_config: dict) -> None:
        """Test parsing an invalid line format."""
        parser = KrungsriTextParser()
        line = "Invalid line format without proper structure"

        with pytest.raises(ValueError, match="Could not find amount and balance"):
            parser._parse_line(line, sample_account_config, "test.txt")

    def test_parse_line_insufficient_parts(self, sample_account_config: dict) -> None:
        """Test parsing a line with insufficient parts."""
        parser = KrungsriTextParser()
        line = "01/01/2024"

        with pytest.raises(ValueError, match="Could not find amount and balance"):
            parser._parse_line(line, sample_account_config, "test.txt")

    def test_parse_file_with_empty_lines(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing file with empty lines."""
        content = """Date/Time Transaction Withdrawal/Deposit Outstanding Balance Channel Description

01/01/2024 09:30:15 ATM Withdrawal 5,000.00 45,000.00 ATM ATM Withdrawal

01/02/2024 14:20:30 Transfer Credit 10,000.00 55,000.00 IB Transfer from Account

"""
        file_path = self.create_test_file(
            content, "krungsri_with_empty_lines.txt", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            KrungsriTextParser, file_path, sample_account_config
        )

        assert len(transactions) == 2  # Should ignore empty lines

    def test_parse_file_with_malformed_lines(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing file with some malformed lines."""
        content = """Date/Time Transaction Withdrawal/Deposit Outstanding Balance Channel Description
01/01/2024 09:30:15 ATM Withdrawal 5,000.00 45,000.00 ATM ATM Withdrawal
Invalid line that should be skipped
01/02/2024 14:20:30 Transfer Credit 10,000.00 55,000.00 IB Transfer from Account
Another invalid line
01/03/2024 11:15:45 Payment Debit 2,500.00 52,500.00 POS Payment at Supermarket"""
        file_path = self.create_test_file(
            content, "krungsri_with_malformed_lines.txt", test_data_dir
        )

        transactions = self.get_transactions_from_parser(
            KrungsriTextParser, file_path, sample_account_config
        )

        assert len(transactions) == 3  # Should parse valid lines and skip invalid ones

    def test_transaction_type_detection(self, sample_account_config: dict) -> None:
        """Test that transaction types are correctly detected."""
        parser = KrungsriTextParser()

        # Test withdrawal
        withdrawal_line = (
            "01/01/2024 09:30:15 ATM Withdrawal 5,000.00 45,000.00 ATM ATM Withdrawal"
        )
        withdrawal_transaction = parser._parse_line(
            withdrawal_line, sample_account_config, "test.txt"
        )
        assert "Withdrawal" in withdrawal_transaction.transaction_type

        # Test credit
        credit_line = "01/02/2024 14:20:30 Transfer Credit 10,000.00 55,000.00 IB Transfer from Account"
        credit_transaction = parser._parse_line(
            credit_line, sample_account_config, "test.txt"
        )
        assert "Credit" in credit_transaction.transaction_type

    def test_amount_parsing_with_commas(self, sample_account_config: dict) -> None:
        """Test parsing amounts with commas."""
        parser = KrungsriTextParser()
        line = "01/06/2024 10:25:35 Deposit Credit 15,000.00 59,650.00 CDM Cash Deposit"

        transaction = parser._parse_line(line, sample_account_config, "test.txt")

        assert transaction is not None
        assert (
            float(transaction.amount) == 15000.00
        )  # Deposit should be positive (credit)
        assert transaction.balance == Decimal("59650.00")
        assert transaction.channel == "CDM"
        assert "Cash Deposit" in transaction.description

    def test_balance_calculation_consistency(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test that balance calculations are consistent."""
        sample_file = test_data_dir / "krungsri_sample.txt"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            KrungsriTextParser, sample_file, sample_account_config
        )

        # Check that balances are properly formatted as Decimal
        for transaction in transactions:
            assert isinstance(transaction.balance, Decimal)
            assert transaction.balance > 0

    def test_source_file_tracking(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test that source file is properly tracked."""
        sample_file = test_data_dir / "krungsri_sample.txt"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            KrungsriTextParser, sample_file, sample_account_config
        )

        for transaction in transactions:
            assert transaction.source_file == str(sample_file)

    def test_parser_name_tracking(
        self, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test that parser name is properly set."""
        sample_file = test_data_dir / "krungsri_sample.txt"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            KrungsriTextParser, sample_file, sample_account_config
        )

        for transaction in transactions:
            assert transaction.parser_name == "krungsri_text"
