"""Tests for SCB PDF parser."""

from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from bank_importer_th.banks.scb_pdf import ScbPdfParser
from tests.parsers.test_base import BaseParserTest


class TestScbPdfParser(BaseParserTest):
    """Test SCB PDF parser functionality."""

    @pytest.fixture
    def parser_class(self):
        """Return the parser class."""
        return ScbPdfParser

    @pytest.fixture
    def valid_file_content(self) -> str:
        """Valid SCB PDF content (mocked)."""
        return "Mocked PDF content"

    @pytest.fixture
    def valid_filename(self) -> str:
        """Valid filename for SCB PDF file."""
        return "scb_valid.pdf"

    @pytest.fixture
    def invalid_file_content(self) -> str:
        """Invalid file content."""
        return "Invalid content"

    @pytest.fixture
    def invalid_filename(self) -> str:
        """Invalid filename."""
        return "invalid_file.txt"

    def test_can_parse_pdf_file(self, test_data_dir: Path) -> None:
        """Test that parser can identify PDF files."""
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()  # Create empty PDF file

        parser = ScbPdfParser()
        assert parser.can_parse(pdf_file) is True

    def test_cannot_parse_non_pdf_file(self, test_data_dir: Path) -> None:
        """Test that parser rejects non-PDF files."""
        txt_file = test_data_dir / "test.txt"
        txt_file.touch()

        parser = ScbPdfParser()
        assert parser.can_parse(txt_file) is False

    @patch("bank_importer_th.banks.scb_pdf.pdfplumber")
    def test_parse_file_with_valid_password(
        self, mock_pdfplumber, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing PDF file with valid password."""
        # Mock PDF content
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = """
        ACCOUNT STATEMENT WITH NOTES
        SCB Siam Commercial Bank
        Account: 042-289064-1

        01/01/2024 ATM Withdrawal 5,000.00 45,000.00
        01/02/2024 Transfer Credit 10,000.00 55,000.00
        """
        mock_pdf.pages = [mock_page]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        # Add password to account config
        sample_account_config["password"] = "test_password"

        parser = ScbPdfParser()
        transactions = list(parser.parse_file(pdf_file, sample_account_config))

        assert len(transactions) > 0
        mock_pdfplumber.open.assert_called_once_with(pdf_file, password="test_password")

    @patch("bank_importer_th.banks.scb_pdf.pdfplumber")
    def test_parse_file_without_password(
        self, mock_pdfplumber, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing PDF file without password raises error."""
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        parser = ScbPdfParser()

        with pytest.raises(ValueError, match="Password is required"):
            list(parser.parse_file(pdf_file, sample_account_config))

    @patch("bank_importer_th.banks.scb_pdf.pdfplumber")
    def test_parse_file_with_incorrect_password(
        self, mock_pdfplumber, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing PDF file with incorrect password."""
        mock_pdfplumber.open.side_effect = Exception("PDFPasswordIncorrect")

        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()
        sample_account_config["password"] = "wrong_password"

        parser = ScbPdfParser()

        with pytest.raises(ValueError, match="Incorrect password"):
            list(parser.parse_file(pdf_file, sample_account_config))

    @patch("bank_importer_th.banks.scb_pdf.pdfplumber")
    def test_parse_file_not_scb_statement(
        self, mock_pdfplumber, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing non-SCB PDF file."""
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = (
            "Some random PDF content without SCB indicators"
        )
        mock_pdf.pages = [mock_page]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()
        sample_account_config["password"] = "test_password"

        parser = ScbPdfParser()

        with pytest.raises(
            ValueError, match="does not appear to be an SCB bank statement"
        ):
            list(parser.parse_file(pdf_file, sample_account_config))

    def test_parse_transaction_details_valid(self, sample_account_config: dict) -> None:
        """Test parsing valid transaction details."""
        parser = ScbPdfParser()

        line = "01/01/2024 ATM Withdrawal 5,000.00 45,000.00"
        details = parser._parse_transaction_details(line)

        assert details is not None
        assert details["date"] == "01/01/2024"
        assert details["description"] == "ATM Withdrawal"
        assert details["amount"] == "5,000.00"
        assert details["balance"] == "45,000.00"

    def test_parse_transaction_details_invalid(self) -> None:
        """Test parsing invalid transaction details."""
        parser = ScbPdfParser()

        line = "Invalid line format"
        details = parser._parse_transaction_details(line)

        assert details is None

    def test_create_transaction_valid(
        self, sample_account_config: dict, test_data_dir: Path
    ) -> None:
        """Test creating transaction from valid data."""
        parser = ScbPdfParser()

        transaction_data = {
            "date": "01/01/2024",
            "description": "ATM Withdrawal",
            "amount": "5,000.00",
            "balance": "45,000.00",
        }

        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        transaction = parser._create_transaction(
            transaction_data, sample_account_config, pdf_file
        )

        assert transaction is not None
        assert transaction.date.year == 2024
        assert transaction.date.month == 1
        assert transaction.date.day == 1
        assert float(transaction.amount) == 5000.00
        assert transaction.balance == Decimal("45000.00")
        assert transaction.description == "ATM Withdrawal"
        assert transaction.source_file == str(pdf_file)
        assert transaction.parser_name == "scb_pdf"

    def test_parse_transaction_line_valid(
        self, sample_account_config: dict, test_data_dir: Path
    ) -> None:
        """Test parsing valid transaction line."""
        parser = ScbPdfParser()

        line = "01/01/2024 ATM Withdrawal 5,000.00 45,000.00"
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        transaction = parser._parse_transaction_line(
            line, sample_account_config, pdf_file
        )

        assert transaction is not None
        self.validate_transaction(transaction, sample_account_config)

    def test_parse_transaction_line_invalid(
        self, sample_account_config: dict, test_data_dir: Path
    ) -> None:
        """Test parsing invalid transaction line."""
        parser = ScbPdfParser()

        line = "Invalid line format"
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        transaction = parser._parse_transaction_line(
            line, sample_account_config, pdf_file
        )

        assert transaction is None

    @patch("bank_importer_th.banks.scb_pdf.pdfplumber")
    def test_parse_file_with_multiple_pages(
        self, mock_pdfplumber, test_data_dir: Path, sample_account_config: dict
    ) -> None:
        """Test parsing PDF file with multiple pages."""
        # Mock multiple pages
        mock_pdf = Mock()
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = """
        ACCOUNT STATEMENT WITH NOTES
        SCB Siam Commercial Bank
        Account: 042-289064-1
        
        01/01/2024 ATM Withdrawal 5,000.00 45,000.00
        """
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = """
        01/02/2024 Transfer Credit 10,000.00 55,000.00
        01/03/2024 Payment Debit 2,500.00 52,500.00
        """
        mock_pdf.pages = [mock_page1, mock_page2]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()
        sample_account_config["password"] = "test_password"

        parser = ScbPdfParser()
        transactions = list(parser.parse_file(pdf_file, sample_account_config))

        assert len(transactions) == 3  # Should parse transactions from both pages

    def test_amount_parsing_with_commas(
        self, sample_account_config: dict, test_data_dir: Path
    ) -> None:
        """Test parsing amounts with comma separators."""
        parser = ScbPdfParser()

        line = "01/06/2024 Deposit Credit 15,000.00 59,650.00"
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        transaction = parser._parse_transaction_line(
            line, sample_account_config, pdf_file
        )

        assert transaction is not None
        assert float(transaction.amount) == 15000.00
        assert transaction.balance == Decimal("59650.00")

    def test_date_parsing_various_formats(
        self, sample_account_config: dict, test_data_dir: Path
    ) -> None:
        """Test parsing various date formats."""
        parser = ScbPdfParser()
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        # Test different date formats
        test_cases = [
            ("01/01/2024", 2024, 1, 1),
            ("15/12/2023", 2023, 12, 15),
            ("31/03/2024", 2024, 3, 31),
        ]

        for date_str, year, month, day in test_cases:
            line = f"{date_str} ATM Withdrawal 5,000.00 45,000.00"
            transaction = parser._parse_transaction_line(
                line, sample_account_config, pdf_file
            )

            assert transaction is not None
            assert transaction.date.year == year
            assert transaction.date.month == month
            assert transaction.date.day == day

    def test_transaction_type_detection(
        self, sample_account_config: dict, test_data_dir: Path
    ) -> None:
        """Test that transaction types are correctly detected."""
        parser = ScbPdfParser()
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        # Test withdrawal
        withdrawal_line = "01/01/2024 ATM Withdrawal 5,000.00 45,000.00"
        withdrawal_transaction = parser._parse_transaction_line(
            withdrawal_line, sample_account_config, pdf_file
        )
        assert "Withdrawal" in withdrawal_transaction.transaction_type

        # Test credit
        credit_line = "01/02/2024 Transfer Credit 10,000.00 55,000.00"
        credit_transaction = parser._parse_transaction_line(
            credit_line, sample_account_config, pdf_file
        )
        assert "Credit" in credit_transaction.transaction_type

        # Test debit
        debit_line = "01/03/2024 Payment Debit 2,500.00 52,500.00"
        debit_transaction = parser._parse_transaction_line(
            debit_line, sample_account_config, pdf_file
        )
        assert "Debit" in debit_transaction.transaction_type

    def test_balance_calculation_consistency(
        self, sample_account_config: dict, test_data_dir: Path
    ) -> None:
        """Test that balance calculations are consistent."""
        parser = ScbPdfParser()
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        test_lines = [
            "01/01/2024 ATM Withdrawal 5,000.00 45,000.00",
            "01/02/2024 Transfer Credit 10,000.00 55,000.00",
            "01/03/2024 Payment Debit 2,500.00 52,500.00",
        ]

        for line in test_lines:
            transaction = parser._parse_transaction_line(
                line, sample_account_config, pdf_file
            )
            assert isinstance(transaction.balance, Decimal)
            assert transaction.balance > 0

    def test_source_file_tracking(
        self, sample_account_config: dict, test_data_dir: Path
    ) -> None:
        """Test that source file is properly tracked."""
        parser = ScbPdfParser()
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        line = "01/01/2024 ATM Withdrawal 5,000.00 45,000.00"
        transaction = parser._parse_transaction_line(
            line, sample_account_config, pdf_file
        )

        assert transaction.source_file == str(pdf_file)

    def test_parser_name_tracking(
        self, sample_account_config: dict, test_data_dir: Path
    ) -> None:
        """Test that parser name is properly set."""
        parser = ScbPdfParser()
        pdf_file = test_data_dir / "test.pdf"
        pdf_file.touch()

        line = "01/01/2024 ATM Withdrawal 5,000.00 45,000.00"
        transaction = parser._parse_transaction_line(
            line, sample_account_config, pdf_file
        )

        assert transaction.parser_name == "scb_pdf"
