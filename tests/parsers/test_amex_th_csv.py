"""Tests for American Express Thailand CSV parser."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from bank_importer_th.banks.amex_th_csv import AmexThCsvParser


class TestAmexThCsvParser:
    """Test AMEX Thailand CSV parser functionality."""

    @pytest.fixture
    def parser(self) -> AmexThCsvParser:
        """Create a parser instance for testing."""
        return AmexThCsvParser()

    @pytest.fixture
    def sample_account_config(self) -> dict[str, Any]:
        """Sample account configuration for testing."""
        return {
            "name": "amex_th_csv",
            "bank_name": "American Express Thailand",
            "account_number": "XXXX-XXXXXX-43002",
            "account_name": "TH - CC AMEX (Billed / Uncharged)",
            "currency": "THB",
            "country_code": "TH",
            "reference": "amex_th_csv",
            "translation": {
                "enabled": False,
                "source_language": "en",
                "target_language": "en",
                "use_term_mapping": False,
                "use_api_translation": False,
                "preserve_original": True,
            },
        }

    @pytest.fixture
    def sample_csv_file(self, test_data_dir: Path) -> Path:
        """Get the sample AMEX CSV file."""
        return test_data_dir / "amex_sample.csv"

    def test_can_parse_csv_file(
        self, parser: AmexThCsvParser, sample_csv_file: Path
    ) -> None:
        """Test that the parser can identify AMEX CSV files."""
        assert parser.can_parse(sample_csv_file) is True

    def test_cannot_parse_non_csv_file(
        self, parser: AmexThCsvParser, test_data_dir: Path
    ) -> None:
        """Test that the parser rejects non-CSV files."""
        pdf_file = test_data_dir / "test.pdf"
        assert parser.can_parse(pdf_file) is False

    def test_parse_file_success(
        self,
        parser: AmexThCsvParser,
        sample_csv_file: Path,
        sample_account_config: dict[str, Any],
    ) -> None:
        """Test successful parsing of AMEX CSV file."""
        transactions = list(parser.parse_file(sample_csv_file, sample_account_config))

        # Check that we have the expected number of transactions
        assert len(transactions) == 9

        # Check first transaction (SHOPEE TH)
        first_txn = transactions[0]
        assert (
            first_txn.description
            == "SHOPEE TH (89 AIA CAPITAL CENTER 24FL.RATCHADAPISEK RD. DINDAENGDINDAENG BANGKOKBANGKOK, THAILAND)"
        )
        assert first_txn.amount == -3397.00  # Negated for Firefly-III format
        assert first_txn.currency == "THB"
        assert first_txn.account_number == "XXXX-XXXXXX-43002"
        assert first_txn.parser_name == "amex_th_csv"

        # Check payment transaction (should be positive after negation)
        payment_txn = [t for t in transactions if "NET PAYMENT" in t.description][0]
        assert payment_txn.amount == 50000.00  # Payment is now positive after negation

        # Check foreign currency transaction
        grab_txn = next(t for t in transactions if "GRAB" in t.description)
        assert (
            grab_txn.amount == -504.00
        )  # Should be negative (expense in Firefly-III format)
        assert grab_txn.foreign_currency == "THB"
        assert grab_txn.foreign_amount == Decimal("504.00")
        assert "SINGAPORE" in grab_txn.description

    def test_country_code_detection(self, parser: AmexThCsvParser) -> None:
        """Test that country codes are properly detected and spaced."""
        # Test TH detection
        assert parser._fix_country_codes_in_description("SHOPEETH") == "SHOPEE TH"
        assert parser._fix_country_codes_in_description("SHOPEETH") == "SHOPEE TH"

        # Test no detection for other text
        assert parser._fix_country_codes_in_description("GRAB") == "GRAB"
        assert (
            parser._fix_country_codes_in_description("LOTUS'S 5022 SUKHUMVIT")
            == "LOTUS'S 5022 SUKHUMVIT"
        )

    def test_amount_normalization(
        self,
        parser: AmexThCsvParser,
        sample_csv_file: Path,
        sample_account_config: dict[str, Any],
    ) -> None:
        """Test that amounts are properly normalized (expenses negative, credits positive)."""
        transactions = list(parser.parse_file(sample_csv_file, sample_account_config))

        # Expenses should be negative (after negation)
        expenses = [t for t in transactions if "NET PAYMENT" not in t.description]
        for txn in expenses:
            assert txn.amount < 0, (
                f"Expense {txn.description} should be negative: {txn.amount}"
            )

        # Credits (repayments) should be positive (after negation)
        credits = [t for t in transactions if "NET PAYMENT" in t.description]
        for txn in credits:
            assert txn.amount > 0, (
                f"Credit {txn.description} should be positive: {txn.amount}"
            )

    def test_foreign_currency_parsing(
        self,
        parser: AmexThCsvParser,
        sample_csv_file: Path,
        sample_account_config: dict[str, Any],
    ) -> None:
        """Test parsing of foreign currency transactions."""
        transactions = list(parser.parse_file(sample_csv_file, sample_account_config))

        # Find GRAB transaction with foreign currency
        grab_txn = next(t for t in transactions if "GRAB" in t.description)

        assert grab_txn.amount < 0  # Should be negative (expense in Firefly-III format)
        assert grab_txn.foreign_currency == "THB"
        assert grab_txn.foreign_amount == Decimal("504.00")
        assert "SINGAPORE" in grab_txn.description

    def test_parser_metadata(self, parser: AmexThCsvParser) -> None:
        """Test parser metadata methods."""
        assert parser.get_bank_type() == "amex_th"
        assert parser.get_parser_name() == "amex_th_csv"
        assert parser.get_default_account_name() == "TH - CC AMEX (Billed / Uncharged)"
        assert parser.get_default_account_number() == "XXXX-XXXXXX-43002"
        assert parser.get_default_currency() == "THB"
        assert parser.get_default_country_code() == "TH"
        assert parser.get_supported_file_patterns() == ["*.csv"]
        assert parser.get_supported_extensions() == [".csv"]
        assert (
            parser.get_parser_description()
            == "American Express Thailand CSV Statement Parser"
        )
        assert parser.get_parser_version() == "1.0.0"

    def test_export_config(self, parser: AmexThCsvParser) -> None:
        """Test export configuration."""
        config = parser.get_export_config()
        assert config["bank_name"] == "American Express Thailand"
        assert config["default_account_name"] == "TH - CC AMEX (Billed / Uncharged)"
        assert config["default_account_number"] == "XXXX-XXXXXX-43002"
        assert config["default_currency"] == "THB"
        assert config["default_country_code"] == "TH"
        assert config["supports_foreign_currency"] is True
        assert config["supports_translation"] is True

    def test_transaction_type_detection(self, parser: AmexThCsvParser) -> None:
        """Test transaction type detection."""
        # Test purchase detection (negative amounts - expenses)
        assert (
            parser._determine_transaction_type("SHOPEETH", Decimal("-100"))
            == "purchase"
        )
        assert parser._determine_transaction_type("GRAB", Decimal("-50")) == "transport"

        # Test payment detection (positive amounts - credits)
        assert (
            parser._determine_transaction_type(
                "NET PAYMENT - THANK YOU", Decimal("100")
            )
            == "payment"
        )

        # Test specific merchant types (negative amounts for expenses)
        assert parser._determine_transaction_type("GRAB", Decimal("-50")) == "transport"
        assert (
            parser._determine_transaction_type("SPOTIFY", Decimal("-139"))
            == "entertainment"
        )
        assert (
            parser._determine_transaction_type("VILLA MARKET", Decimal("-1000"))
            == "groceries"
        )

        # Test withdrawal detection (negative amounts for expenses)
        assert (
            parser._determine_transaction_type("ATM WITHDRAWAL", Decimal("-100"))
            == "purchase"
        )

    def test_unique_id_generation(self, parser: AmexThCsvParser) -> None:
        """Test unique ID generation."""
        # Test with reference
        unique_id = parser._generate_unique_id(
            reference="'011818359108323'",
            account_number="-43002",
            date=datetime(2025, 5, 2),
            amount=Decimal("-3397.00"),
            description="SHOPEETH",
        )
        assert unique_id == "-43002_20250502_4895f691"

        # Test without reference (should use description hash)
        unique_id_no_ref = parser._generate_unique_id(
            reference="",
            account_number="-43002",
            date=datetime(2025, 5, 2),
            amount=Decimal("-3397.00"),
            description="SHOPEETH",
        )
        assert unique_id_no_ref.startswith("-43002_20250502_")

    def test_foreign_currency_parsing_method(self, parser: AmexThCsvParser) -> None:
        """Test the foreign currency parsing method."""
        # Test with foreign currency details
        currency, amount, rate = parser._parse_foreign_currency(
            "504.00 BAHT CONVERTED TO504.00 BAHT CONVERTED TO"
        )
        assert currency == "THB"  # Should detect THB from BAHT
        assert amount == Decimal("504.00")
        assert rate is None

        # Test with empty details
        currency, amount, rate = parser._parse_foreign_currency("")
        assert currency is None
        assert amount is None
        assert rate is None

    def test_description_creation(self, parser: AmexThCsvParser) -> None:
        """Test full description creation."""
        description = parser._create_full_description(
            description="SHOPEETH",
            appears_on_statement="SHOPEETH",
            address="89 AIA CAPITAL CENTER 24FL.RATCHADAPISEK RD. DINDAENGDINDAENG BANGKOKBANGKOK",
            city_state="",
            country="THAILAND",
        )

        # Should include fixed country code and location
        assert "SHOPEE TH" in description
        assert "THAILAND" in description
        assert "89 AIA CAPITAL CENTER" in description
