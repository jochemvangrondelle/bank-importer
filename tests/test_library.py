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

"""Tests for library functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bank_importer.library import (
    detect_parser,
    export_transactions,
    get_parser,
    get_translation_service_from_config,
    list_targets,
    parse_file,
    translate_text,
)


class TestLibraryFunctions:
    """Tests for library functions."""

    def test_detect_parser(self, tmp_path: Path) -> None:
        """Test parser detection."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        # Should return a parser name or None
        result = detect_parser(test_file)
        # Result can be None or a parser name
        assert result is None or isinstance(result, str)

    def test_detect_parser_with_hint(self, tmp_path: Path) -> None:
        """Test parser detection with parent folder hint."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        result = detect_parser(test_file, parent_folder_hint="SCB")
        # Result can be None or a parser name
        assert result is None or isinstance(result, str)

    def test_get_parser(self) -> None:
        """Test getting parser by name."""
        parser = get_parser("krungsri_text")
        assert parser is not None
        assert hasattr(parser, "parse_file")

    def test_get_parser_invalid(self) -> None:
        """Test getting invalid parser."""
        parser = get_parser("nonexistent_parser")
        assert parser is None

    @patch("bank_importer.library.get_parser")
    @patch("bank_importer.library.detect_parser")
    def test_parse_file_with_parser_name(
        self,
        mock_detect: MagicMock,
        mock_get_parser: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test parsing file with explicit parser name."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        mock_parser = MagicMock()
        mock_parser.parse_file.return_value = []
        mock_get_parser.return_value = mock_parser

        account_config = {
            "account_number": "123-456-789",
            "account_name": "Test Account",
            "bank_name": "Test Bank",
        }

        result = list(
            parse_file(
                test_file,
                parser_name="krungsri_text",
                account_config=account_config,
            ),
        )
        assert isinstance(result, list)
        mock_get_parser.assert_called_once_with("krungsri_text")

    @patch("bank_importer.library.get_parser")
    @patch("bank_importer.library.detect_parser")
    def test_parse_file_auto_detect(
        self,
        mock_detect: MagicMock,
        mock_get_parser: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test parsing file with auto-detection."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        mock_detect.return_value = "krungsri_text"
        mock_parser = MagicMock()
        mock_parser.parse_file.return_value = []
        mock_get_parser.return_value = mock_parser

        account_config = {
            "account_number": "123-456-789",
            "account_name": "Test Account",
            "bank_name": "Test Bank",
        }

        result = list(
            parse_file(
                test_file,
                parser_name=None,
                account_config=account_config,
                auto_detect=True,
            ),
        )
        assert isinstance(result, list)
        mock_detect.assert_called_once()

    def test_export_transactions(
        self,
        tmp_path: Path,
    ) -> None:
        """Test exporting transactions."""
        from datetime import UTC, datetime
        from decimal import Decimal

        from bank_importer.models.transaction import Transaction

        transaction = Transaction(
            date=datetime(2024, 1, 1, tzinfo=UTC),
            description="Test transaction",
            amount=Decimal("100.00"),
            balance=Decimal("1000.00"),
            transaction_type="debit",
            account_number="123-456-789",
            currency="THB",
            country_code="TH",
            source_file="test.txt",
        )

        result = export_transactions(
            [transaction],
            target_name="csv",
            output_dir=str(tmp_path / "output"),
        )

        assert result is not None
        assert result.success is True
        assert result.exported_count >= 0

    @patch("bank_importer.library._translation_service_func")
    def test_translate_text(
        self,
        mock_service_func: MagicMock,
    ) -> None:
        """Test translating text."""
        # Skip if translation is not available
        try:
            from bank_importer.library import TRANSLATION_AVAILABLE

            if not TRANSLATION_AVAILABLE:
                pytest.skip("Translation service not available")
        except ImportError:
            pytest.skip("Translation service not available")

        mock_service = MagicMock()
        mock_service.translate_description.return_value = "Hello"
        mock_service_func.return_value = mock_service

        result = translate_text("สวัสดี", api_key="test_key")
        assert result == "Hello"

    @patch("bank_importer.library._translation_service_func")
    def test_translate_text_with_languages(
        self,
        mock_get_service: MagicMock,
    ) -> None:
        """Test translating text with specific languages."""
        from bank_importer.models.enums import (
            Language,
            get_language_en,
        )

        mock_service = MagicMock()
        mock_service.translate_description.return_value = "Bonjour"
        mock_get_service.return_value = mock_service

        result = translate_text(
            "Hello",
            api_key="test_key",
            source_language=get_language_en(),
            target_language=Language.FR,
        )
        assert result == "Bonjour"

    def test_get_translation_service_from_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test getting translation service from config."""
        from bank_importer.config import ConfigManager

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """
[translation]
enable_translation = true
""",
        )
        config = ConfigManager(config_path)

        result = get_translation_service_from_config(config)
        # Result might be None if translation is not available
        # Just verify the function can be called without error
        assert result is None or hasattr(result, "translate_description")

    def test_list_targets(self) -> None:
        """Test listing available targets."""
        targets = list_targets()
        assert isinstance(targets, list)
        assert len(targets) > 0
        assert "csv" in targets or "yaml" in targets

    def test_list_parsers(self) -> None:
        """Test listing available parsers."""
        from bank_importer.library import list_parsers

        parsers = list_parsers()
        assert isinstance(parsers, list)
        assert len(parsers) > 0
