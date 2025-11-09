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

"""Tests for generic CSV parser."""

from decimal import Decimal
from pathlib import Path

import pytest

from bank_importer.banks.generic_csv import GenericCsvParser
from tests.banks.test_base import BaseParserTest


class TestGenericCsvParser(BaseParserTest):
    """Test generic CSV parser functionality."""

    @pytest.fixture
    def parser_class(self):
        """Return the parser class."""
        return GenericCsvParser

    @pytest.fixture
    def parser(self) -> GenericCsvParser:
        """Return a parser instance."""
        return GenericCsvParser()

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
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parsing a valid CSV file."""
        # Use the sample file from test data
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            sample_file,
            sample_account_config,
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
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parsing CSV with different date formats."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,Test Transaction,-1000.00,THB,10000.00,debit,ATM,TEST001
2024/01/02,Another Transaction,2000.00,THB,12000.00,credit,IB,TEST002
01/03/2024,Third Transaction,-500.00,THB,11500.00,debit,POS,TEST003"""

        file_path = self.create_test_file(
            content,
            "generic_csv_different_dates.csv",
            test_data_dir,
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            file_path,
            sample_account_config,
        )

        assert len(transactions) == 3

        # Check different date formats were parsed correctly
        assert transactions[0].date.year == 2024
        assert transactions[0].date.month == 1
        assert transactions[0].date.day == 1
        assert transactions[1].date.year == 2024
        assert transactions[1].date.month == 1
        assert transactions[1].date.day == 2
        assert transactions[2].date.year == 2024
        assert transactions[2].date.month == 3
        assert transactions[2].date.day == 1

    def test_parse_csv_with_missing_optional_fields(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parsing CSV with missing optional fields."""
        content = """date,description,amount,currency
2024-01-01,Simple Transaction,-1000.00,THB
2024-01-02,Another Transaction,2000.00,THB"""

        file_path = self.create_test_file(
            content,
            "generic_csv_minimal.csv",
            test_data_dir,
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            file_path,
            sample_account_config,
        )

        assert len(transactions) == 2

        # Check that optional fields are handled gracefully
        for transaction in transactions:
            assert transaction.description is not None
            assert transaction.amount is not None
            assert transaction.currency == "THB"

    def test_parse_csv_with_extra_fields(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parsing CSV with extra fields."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference,extra_field,another_field
2024-01-01,Test Transaction,-1000.00,THB,10000.00,debit,ATM,TEST001,extra_value,another_value
2024-01-02,Another Transaction,2000.00,THB,12000.00,credit,IB,TEST002,extra_value2,another_value2"""

        file_path = self.create_test_file(
            content,
            "generic_csv_extra_fields.csv",
            test_data_dir,
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            file_path,
            sample_account_config,
        )

        assert len(transactions) == 2

        # Check that extra fields don't interfere with parsing
        for transaction in transactions:
            self.validate_transaction(transaction, sample_account_config)

    def test_parse_csv_with_quoted_fields(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parsing CSV with quoted fields."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,"ATM Withdrawal, Central Branch",-1000.00,THB,10000.00,debit,ATM,TEST001
2024-01-02,"Transfer Credit, From Account 123-456",2000.00,THB,12000.00,credit,IB,TEST002"""

        file_path = self.create_test_file(
            content,
            "generic_csv_quoted.csv",
            test_data_dir,
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            file_path,
            sample_account_config,
        )

        assert len(transactions) == 2

        # Check that quoted descriptions are parsed correctly
        assert "ATM Withdrawal, Central Branch" in transactions[0].description
        assert "Transfer Credit, From Account 123-456" in transactions[1].description

    def test_parse_csv_with_different_amount_formats(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parsing CSV with different amount formats."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,Test Transaction,-1000.50,THB,10000.00,debit,ATM,TEST001
2024-01-02,Another Transaction,2000,THB,12000.00,credit,IB,TEST002
2024-01-03,Third Transaction,-500.75,THB,11500.00,debit,POS,TEST003"""

        file_path = self.create_test_file(
            content,
            "generic_csv_amount_formats.csv",
            test_data_dir,
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            file_path,
            sample_account_config,
        )

        assert len(transactions) == 3

        # Check different amount formats
        assert float(transactions[0].amount) == -1000.50
        assert float(transactions[1].amount) == 2000.0
        assert float(transactions[2].amount) == -500.75

    def test_parse_csv_with_empty_lines(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parsing CSV with empty lines."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference

2024-01-01,Test Transaction,-1000.00,THB,10000.00,debit,ATM,TEST001

2024-01-02,Another Transaction,2000.00,THB,12000.00,credit,IB,TEST002

"""

        file_path = self.create_test_file(
            content,
            "generic_csv_empty_lines.csv",
            test_data_dir,
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            file_path,
            sample_account_config,
        )

        assert len(transactions) == 2  # Should ignore empty lines

    def test_parse_csv_with_malformed_lines(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parsing CSV with some malformed lines."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,Test Transaction,-1000.00,THB,10000.00,debit,ATM,TEST001
Invalid line that should be skipped
2024-01-02,Another Transaction,2000.00,THB,12000.00,credit,IB,TEST002
Another invalid line
2024-01-03,Third Transaction,-500.00,THB,11500.00,debit,POS,TEST003"""

        file_path = self.create_test_file(
            content,
            "generic_csv_malformed.csv",
            test_data_dir,
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            file_path,
            sample_account_config,
        )

        assert len(transactions) == 3  # Should parse valid lines and skip invalid ones

    def test_parse_csv_with_different_currencies(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parsing CSV with different currencies."""
        content = """date,description,amount,currency,balance,transaction_type,channel,reference
2024-01-01,USD Transaction,-100.00,USD,1000.00,debit,ATM,TEST001
2024-01-02,EUR Transaction,200.00,EUR,1200.00,credit,IB,TEST002
2024-01-03,THB Transaction,-500.00,THB,11500.00,debit,POS,TEST003"""

        file_path = self.create_test_file(
            content,
            "generic_csv_currencies.csv",
            test_data_dir,
        )

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            file_path,
            sample_account_config,
        )

        assert len(transactions) == 3

        # Check different currencies
        assert transactions[0].currency == "USD"
        assert transactions[1].currency == "EUR"
        assert transactions[2].currency == "THB"

    def test_parser_metadata(self, parser: GenericCsvParser) -> None:
        """Test parser metadata methods."""
        assert parser.get_bank_type() == "generic"
        assert parser.get_parser_name() == "generic_csv"
        assert parser.get_default_account_name() == "Generic Account"
        assert parser.get_default_account_number() == "0000000000"
        assert parser.get_default_currency() == "THB"
        assert parser.get_default_country_code() == "TH"
        assert parser.get_supported_file_patterns() == ["*.csv", "*.tsv", "*.txt"]
        assert parser.get_supported_extensions() == [".csv", ".tsv", ".txt"]
        assert (
            parser.get_parser_description()
            == "Generic CSV/TSV parser with auto-detection of delimiters and formats"
        )
        assert parser.get_parser_version() == "1.0.0"

    def test_export_config(self, parser: GenericCsvParser) -> None:
        """Test export configuration."""
        config = parser.get_export_config()
        assert config["bank_name"] == "Generic Bank"
        assert config["default_account_name"] == "Generic Account"
        assert config["default_account_number"] == "0000000000"
        assert config["default_currency"] == "THB"
        assert config["default_country_code"] == "TH"

    def test_can_parse_with_latin1_encoding(
        self,
        test_data_dir: Path,
    ) -> None:
        """Test can_parse with latin-1 encoded file."""
        # Create a file with latin-1 encoding
        content = "date,description,amount\n2024-01-01,Test,100.00"
        file_path = test_data_dir / "test_latin1.csv"
        file_path.write_bytes(content.encode("latin-1"))

        parser = GenericCsvParser()
        # Should handle latin-1 encoding
        result = parser.can_parse(file_path)
        assert result is True

    def test_can_parse_with_invalid_encoding(
        self,
        test_data_dir: Path,
    ) -> None:
        """Test can_parse with file that can't be decoded."""
        # Create a file with binary data that can't be decoded
        file_path = test_data_dir / "test_binary.csv"
        file_path.write_bytes(b"\xff\xfe\x00\x01")

        parser = GenericCsvParser()
        result = parser.can_parse(file_path)
        assert result is False

    def test_parse_file_with_no_headers(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parse_file with CSV file that has no headers."""
        # Empty file should trigger "File appears to be empty"
        content = ""
        file_path = self.create_test_file(
            content,
            "no_headers.csv",
            test_data_dir,
        )

        parser = GenericCsvParser()
        with pytest.raises(
            ValueError,
            match="File appears to be empty|No headers found",
        ):
            list(parser.parse_file(file_path, sample_account_config))

    def test_parse_file_with_empty_file(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parse_file with empty file."""
        file_path = test_data_dir / "empty.csv"
        file_path.write_text("")

        parser = GenericCsvParser()
        with pytest.raises(ValueError, match="File appears to be empty"):
            list(parser.parse_file(file_path, sample_account_config))

    def test_parse_file_with_latin1_encoding(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parse_file with latin-1 encoded file."""
        content = "date,description,amount\n2024-01-01,Test Transaction,-1000.00"
        file_path = test_data_dir / "test_latin1_parse.csv"
        file_path.write_bytes(content.encode("latin-1"))

        parser = GenericCsvParser()
        transactions = list(parser.parse_file(file_path, sample_account_config))
        assert len(transactions) == 1

    def test_parse_file_with_row_parsing_errors(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test parse_file continues when individual rows fail."""
        content = """date,description,amount
2024-01-01,Valid Transaction,-1000.00
invalid_row_data
2024-01-02,Another Valid Transaction,2000.00"""
        file_path = self.create_test_file(
            content,
            "row_errors.csv",
            test_data_dir,
        )

        parser = GenericCsvParser()
        transactions = list(parser.parse_file(file_path, sample_account_config))
        # Should parse valid rows and skip invalid ones
        assert len(transactions) >= 1

    def test_detect_format_with_empty_file(
        self,
        test_data_dir: Path,
    ) -> None:
        """Test _detect_format with empty file."""
        file_path = test_data_dir / "empty_detect.csv"
        file_path.write_text("")

        parser = GenericCsvParser()
        with pytest.raises(ValueError, match="File appears to be empty"):
            parser._detect_format(file_path)

    def test_detect_format_with_latin1_encoding(
        self,
        test_data_dir: Path,
    ) -> None:
        """Test _detect_format with latin-1 encoded file."""
        content = "date,description,amount\n2024-01-01,Test,100.00"
        file_path = test_data_dir / "test_latin1_detect.csv"
        file_path.write_bytes(content.encode("latin-1"))

        parser = GenericCsvParser()
        delimiter, quotechar = parser._detect_format(file_path)
        assert delimiter == ","
        assert quotechar == '"'

    def test_detect_format_with_no_delimiter(
        self,
        test_data_dir: Path,
    ) -> None:
        """Test _detect_format with file that has no delimiter."""
        content = "This is just text with no delimiters"
        file_path = self.create_test_file(
            content,
            "no_delimiter.csv",
            test_data_dir,
        )

        parser = GenericCsvParser()
        delimiter, _quotechar = parser._detect_format(file_path)
        # Should default to comma when no delimiter found
        assert delimiter == ","

    def test_detect_format_with_single_quote(
        self,
        test_data_dir: Path,
    ) -> None:
        """Test _detect_format with single quote character."""
        content = "date,description,amount\n2024-01-01,'Test Transaction',100.00"
        file_path = self.create_test_file(
            content,
            "single_quote.csv",
            test_data_dir,
        )

        parser = GenericCsvParser()
        delimiter, quotechar = parser._detect_format(file_path)
        assert delimiter == ","
        # CSV parser defaults to double quotes (standard CSV quote character)
        assert quotechar == '"'

    def test_parse_date_with_various_formats(
        self,
        parser: GenericCsvParser,
    ) -> None:
        """Test _parse_date with various date formats."""
        # Test YYYY-MM-DD format
        date = parser._parse_date("2024-01-01")
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 1

        # Test DD/MM/YYYY format
        date = parser._parse_date("01/01/2024")
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 1

        # Test YYYY-MM-DD HH:MM:SS format
        date = parser._parse_date("2024-01-01 12:30:45")
        assert date is not None
        assert date.hour == 12

        # Test invalid format
        date = parser._parse_date("invalid")
        assert date is None

        # Test None
        date = parser._parse_date(None)
        assert date is None

    def test_parse_amount_with_various_formats(
        self,
        parser: GenericCsvParser,
    ) -> None:
        """Test _parse_amount with various amount formats."""
        # Test standard format
        amount = parser._parse_amount("1000.50")
        assert amount == Decimal("1000.50")

        # Test with currency symbol
        amount = parser._parse_amount("$1,000.50")
        assert amount == Decimal("1000.50")

        # Test negative amount
        amount = parser._parse_amount("-500.00")
        assert amount == Decimal("-500.00")

        # Test invalid format
        amount = parser._parse_amount("invalid")
        assert amount is None

        # Test None
        amount = parser._parse_amount(None)
        assert amount is None

        # Test empty string
        amount = parser._parse_amount("")
        assert amount is None

    def test_parse_csv_with_balance_calculation(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test that balance calculations are consistent."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            sample_file,
            sample_account_config,
        )

        # Check that balances are properly formatted as Decimal
        for transaction in transactions:
            assert isinstance(transaction.balance, Decimal)
            assert transaction.balance > 0

    def test_source_file_tracking(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test that source file is properly tracked."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            sample_file,
            sample_account_config,
        )

        for transaction in transactions:
            assert transaction.source_file == str(sample_file)

    def test_parser_name_tracking(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test that parser name is properly set."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            sample_file,
            sample_account_config,
        )

        for transaction in transactions:
            assert transaction.parser_name == "generic_csv"

    def test_transaction_type_detection(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test that transaction types are correctly detected."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            sample_file,
            sample_account_config,
        )

        # Check transaction types
        debit_transactions = [t for t in transactions if t.transaction_type == "debit"]
        credit_transactions = [
            t for t in transactions if t.transaction_type == "credit"
        ]

        assert len(debit_transactions) > 0
        assert len(credit_transactions) > 0

    def test_channel_detection(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test that channels are correctly detected."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            sample_file,
            sample_account_config,
        )

        # Check that channels are set
        channels = {t.channel for t in transactions if t.channel}
        expected_channels = {"ATM", "IB", "POS", "INT", "CDM", "FEE"}

        assert len(channels) > 0
        assert all(channel in expected_channels for channel in channels)

    def test_reference_tracking(
        self,
        test_data_dir: Path,
        sample_account_config: dict,
    ) -> None:
        """Test that references are correctly tracked."""
        sample_file = test_data_dir / "generic_csv_sample.csv"
        if not sample_file.exists():
            pytest.skip("Sample file not found")

        transactions = self.get_transactions_from_parser(
            GenericCsvParser,
            sample_file,
            sample_account_config,
        )

        # Check that references are set
        references = [t.reference for t in transactions if t.reference]
        assert len(references) > 0

        # Check that references are unique
        unique_references = set(references)
        assert len(unique_references) == len(references)
