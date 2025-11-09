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

"""Tests for import_files CLI command."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from bank_importer.cli.commands.import_files import import_files

# Constants for tests
EXPECTED_TWO_ACCOUNTS = 2


class TestImportFiles:
    """Tests for import_files command."""

    @pytest.fixture
    def mock_processor(self) -> Mock:
        """Create a mock processor."""
        processor = Mock()
        processor.config_manager.get_all_accounts.return_value = [
            {"name": "test_account"},
        ]
        processor.process_account.return_value = [
            {"file": "test.pdf", "transactions": 10},
        ]
        return processor

    @pytest.fixture
    def mock_parser_detector(self) -> Mock:
        """Create a mock parser detector."""
        detector = Mock()
        detector.detect_parser.return_value = "krungsri_pdf"
        return detector

    def test_import_files_with_account(
        self,
        tmp_path: Path,
        mock_processor: Mock,
    ) -> None:
        """Test importing files for a specific account."""
        with (
            patch(
                "bank_importer.cli.commands.import_files.get_processor",
                return_value=mock_processor,
            ),
            patch("bank_importer.cli.commands.import_files.setup_logging"),
            patch("bank_importer.cli.commands.import_files.get_logger"),
        ):
            import_files(
                paths=[tmp_path],
                account="test_account",
                verbose=False,
                dry_run=False,
                reprocess_existing=False,
            )
            mock_processor.process_account.assert_called_once_with(
                "test_account",
                reprocess_existing=False,
            )

    def test_import_files_all_accounts(
        self,
        tmp_path: Path,
        mock_processor: Mock,
    ) -> None:
        """Test importing files for all accounts."""
        mock_processor.config_manager.get_all_accounts.return_value = [
            {"name": "account1"},
            {"name": "account2"},
        ]
        with (
            patch(
                "bank_importer.cli.commands.import_files.get_processor",
                return_value=mock_processor,
            ),
            patch("bank_importer.cli.commands.import_files.setup_logging"),
            patch(
                "bank_importer.cli.commands.import_files.get_logger",
            ) as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            import_files(
                paths=[tmp_path],
                account=None,  # type: ignore[arg-type]
                verbose=False,
                dry_run=False,
                reprocess_existing=False,
            )
            assert mock_processor.process_account.call_count == EXPECTED_TWO_ACCOUNTS

    def test_import_files_dry_run(
        self,
        tmp_path: Path,
        mock_processor: Mock,
    ) -> None:
        """Test import files in dry run mode."""
        with (
            patch(
                "bank_importer.cli.commands.import_files.get_processor",
                return_value=mock_processor,
            ),
            patch("bank_importer.cli.commands.import_files.setup_logging"),
            patch(
                "bank_importer.cli.commands.import_files.get_logger",
            ) as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            import_files(
                paths=[tmp_path],
                account="test_account",
                verbose=False,
                dry_run=True,
                reprocess_existing=False,
            )
            # Check that dry run message was logged
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("DRY RUN" in str(call) for call in log_calls)

    def test_import_files_no_accounts_auto_detect_file(
        self,
        tmp_path: Path,
        mock_processor: Mock,
        mock_parser_detector: Mock,
    ) -> None:
        """Test auto-detection when no accounts configured."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")
        mock_processor.config_manager.get_all_accounts.return_value = []

        with (
            patch(
                "bank_importer.cli.commands.import_files.get_processor",
                return_value=mock_processor,
            ),
            patch(
                "bank_importer.cli.commands.import_files.ParserDetector",
                return_value=mock_parser_detector,
            ),
            patch("bank_importer.cli.commands.import_files.setup_logging"),
            patch(
                "bank_importer.cli.commands.import_files.get_logger",
            ) as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            import_files(
                paths=[test_file],
                account=None,  # type: ignore[arg-type]
                verbose=False,
                dry_run=False,
                reprocess_existing=False,
            )
            mock_parser_detector.detect_parser.assert_called_once()

    def test_import_files_no_accounts_auto_detect_directory(
        self,
        tmp_path: Path,
        mock_processor: Mock,
        mock_parser_detector: Mock,
    ) -> None:
        """Test auto-detection in directory when no accounts configured."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")
        mock_processor.config_manager.get_all_accounts.return_value = []

        with (
            patch(
                "bank_importer.cli.commands.import_files.get_processor",
                return_value=mock_processor,
            ),
            patch(
                "bank_importer.cli.commands.import_files.ParserDetector",
                return_value=mock_parser_detector,
            ),
            patch("bank_importer.cli.commands.import_files.setup_logging"),
            patch(
                "bank_importer.cli.commands.import_files.get_logger",
            ) as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            import_files(
                paths=[tmp_path],
                account=None,  # type: ignore[arg-type]
                verbose=False,
                dry_run=False,
                reprocess_existing=False,
            )
            # Should detect parser for files in directory
            assert mock_parser_detector.detect_parser.called

    def test_import_files_default_path(
        self,
        mock_processor: Mock,
    ) -> None:
        """Test that default path is used when no paths provided."""
        with (
            patch(
                "bank_importer.cli.commands.import_files.get_processor",
                return_value=mock_processor,
            ),
            patch("bank_importer.cli.commands.import_files.setup_logging"),
            patch(
                "bank_importer.cli.commands.import_files.get_logger",
            ) as mock_get_logger,
            patch("bank_importer.cli.commands.import_files.Path") as mock_path,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            import_files(
                paths=None,  # type: ignore[arg-type]
                account="test_account",
                verbose=False,
                dry_run=False,
                reprocess_existing=False,
            )
            # Should use default path
            mock_path.assert_called()

    def test_import_files_reprocess_existing(
        self,
        tmp_path: Path,
        mock_processor: Mock,
    ) -> None:
        """Test importing with reprocess_existing flag."""
        with (
            patch(
                "bank_importer.cli.commands.import_files.get_processor",
                return_value=mock_processor,
            ),
            patch("bank_importer.cli.commands.import_files.setup_logging"),
            patch(
                "bank_importer.cli.commands.import_files.get_logger",
            ) as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            import_files(
                paths=[tmp_path],
                account="test_account",
                verbose=False,
                dry_run=False,
                reprocess_existing=True,
            )
            mock_processor.process_account.assert_called_once_with(
                "test_account",
                reprocess_existing=True,
            )
