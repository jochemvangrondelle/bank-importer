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

"""Tests for processor module."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from bank_importer.models.transaction import Transaction
from bank_importer.processor import Processor


class TestProcessor:
    """Test processor functionality."""

    @pytest.fixture
    def mock_config_manager(self) -> Mock:
        """Create a mock config manager."""
        config_manager = Mock()
        config_manager.config = {
            "output_dir": "data/out",
            "accounts": [
                {
                    "name": "test_account",
                    "bank_name": "Test Bank",
                    "account_number": "123-456-789",
                    "parser": "krungsri_text",
                    "file_path": "test/path",
                },
            ],
        }
        config_manager.get_all_accounts.return_value = config_manager.config["accounts"]
        config_manager.get_account_config.return_value = config_manager.config[
            "accounts"
        ][0]
        return config_manager

    @pytest.fixture
    def mock_db_manager(self) -> Mock:
        """Create a mock database manager."""
        db_manager = Mock()
        db_manager.get_pending_import_sessions.return_value = []
        db_manager.get_import_session_by_file_hash.return_value = None
        return db_manager

    @pytest.fixture
    def processor(self, mock_config_manager: Mock, mock_db_manager: Mock) -> Processor:
        """Create a processor instance with mocked dependencies."""
        with (
            patch(
                "bank_importer.processor.ConfigManager",
                return_value=mock_config_manager,
            ),
            patch(
                "bank_importer.processor.DatabaseManager",
                return_value=mock_db_manager,
            ),
        ):
            return Processor()

    @pytest.mark.processor
    def test_processor_initialization(self, processor: Processor) -> None:
        """Test processor initialization."""
        assert processor.config_manager is not None
        assert processor.db_manager is not None
        assert processor.logger is not None

    @pytest.mark.processor
    def test_processor_initialization_with_config_file(self, tmp_path: Path) -> None:
        """Test processor initialization with config file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[[accounts]]
name = "test_account"
parser = "test_parser"
file_path = "test/path"
""")

        with (
            patch("bank_importer.processor.ConfigManager") as mock_config_class,
            patch("bank_importer.processor.DatabaseManager") as mock_db_class,
        ):
            mock_config = Mock()
            mock_config.config = {"output_dir": "data/out", "accounts": []}
            mock_db = Mock()
            mock_config_class.return_value = mock_config
            mock_db_class.return_value = mock_db

            Processor(config_file)
            mock_config_class.assert_called_once_with(config_file)

    @pytest.mark.processor
    def test_identify_pending_import_jobs(
        self,
        processor: Processor,
        mock_db_manager: Mock,
    ) -> None:
        """Test identifying pending import jobs."""
        mock_sessions = [
            {
                "id": 1,
                "account_name": "test_account",
                "session_name": "2024-01",
                "status": "pending",
                "file_path": "/path/to/file.txt",
            },
        ]
        mock_db_manager.get_pending_import_sessions.return_value = mock_sessions

        jobs = processor.identify_pending_import_jobs()
        assert len(jobs) == 1
        assert jobs[0]["account_name"] == "test_account"
        assert jobs[0]["status"] == "pending"

    @pytest.mark.processor
    def test_identify_pending_import_jobs_empty(
        self,
        processor: Processor,
        mock_db_manager: Mock,
    ) -> None:
        """Test identifying pending import jobs when none exist."""
        mock_db_manager.get_pending_import_sessions.return_value = []

        jobs = processor.identify_pending_import_jobs()
        assert len(jobs) == 0

    @pytest.mark.processor
    def test_process_accounts(
        self,
        processor: Processor,
        mock_config_manager: Mock,
    ) -> None:
        """Test processing all accounts."""
        mock_config_manager.get_all_accounts.return_value = [
            {"name": "account1", "bank_name": "Bank 1", "parser": "parser1"},
            {"name": "account2", "bank_name": "Bank 2", "parser": "parser2"},
        ]

        with patch.object(processor, "process_account") as mock_process:
            mock_process.return_value = [
                {"account_name": "account1", "processed_transactions": 5},
                {"account_name": "account2", "processed_transactions": 3},
            ]
            results = list(processor.process_accounts())

            assert mock_process.call_count == 2
            assert len(results) == 4  # 2 results from each account

    @pytest.mark.processor
    def test_process_account_success(
        self,
        processor: Processor,
        mock_config_manager: Mock,
    ) -> None:
        """Test successful account processing."""
        account_config = {
            "name": "test_account",
            "bank_name": "Test Bank",
            "parser": "krungsri_text",
            "file_path": "test/path",
        }
        mock_config_manager.get_account_config.return_value = account_config

        with (
            patch.object(processor, "_get_parser") as mock_get_parser,
            patch.object(processor, "_process_file") as mock_process_file,
            patch("pathlib.Path.glob") as mock_glob,
        ):
            mock_parser = Mock()
            mock_get_parser.return_value = mock_parser
            mock_glob.return_value = [Path("test/file1.txt"), Path("test/file2.txt")]
            mock_process_file.return_value = [
                {"transaction_id": 1, "processed": True},
                {"transaction_id": 2, "processed": True},
            ]

            results = list(processor.process_account("test_account"))

            assert len(results) == 1
            assert results[0]["account_name"] == "test_account"
            assert (
                results[0]["processed_transactions"] == 0
            )  # Files are skipped in test

    @pytest.mark.processor
    def test_process_account_not_found(
        self,
        processor: Processor,
        mock_config_manager: Mock,
    ) -> None:
        """Test processing non-existent account."""
        mock_config_manager.get_account_config.return_value = None

        with pytest.raises(ValueError, match="Account not found"):
            list(processor.process_account("nonexistent"))

    @pytest.mark.processor
    def test_process_account_no_file(
        self,
        processor: Processor,
        mock_config_manager: Mock,
    ) -> None:
        """Test processing account with non-existent file."""
        account_config = {
            "name": "test_account",
            "bank_name": "Test Bank",
            "parser": "krungsri_text",
            "file_path": "nonexistent/path",
        }
        mock_config_manager.get_account_config.return_value = account_config

        with patch.object(processor, "_get_parser") as mock_get_parser:
            mock_parser = Mock()
            mock_get_parser.return_value = mock_parser

            results = list(processor.process_account("test_account"))

            assert len(results) == 1
            assert results[0]["error_count"] > 0

    @pytest.mark.processor
    def test_get_parser_krungsri_text(self, processor: Processor) -> None:
        """Test getting Krungsri text parser."""
        parser = processor._get_parser("krungsri_text")
        assert parser is not None
        # Check that it's the correct parser type by checking the class name
        assert parser.__class__.__name__ == "KrungsriTextParser"

    @pytest.mark.processor
    def test_get_parser_unknown(self, processor: Processor) -> None:
        """Test getting unknown parser."""
        with pytest.raises(ValueError, match="Unknown parser type: unknown_parser"):
            processor._get_parser("unknown_parser")

    @pytest.mark.processor
    def test_process_file_success(self, processor: Processor, tmp_path: Path) -> None:
        """Test successful file processing."""
        test_file = tmp_path / "test.txt"
        test_file.write_text(
            "Date/Time Transaction Withdrawal/Deposit Outstanding Balance Channel Description\n23/11/2024 16:34:41 Transfer Deposit 5,000.00 5,000.00 MOBILE SCB From Acc No. : X890641",
        )

        account_config = {
            "name": "test_account",
            "bank_name": "Test Bank",
            "account_number": "123-456-789",
        }

        with patch("bank_importer.library.import_file") as mock_import_file:
            mock_import_file.return_value = {
                "transactions": [
                    Transaction(
                        date=datetime.now(),
                        description="Test transaction",
                        amount=5000.00,
                        balance=5000.00,
                        transaction_type="Transfer Deposit",
                        account_number="123-456-789",
                        currency="THB",
                        country_code="TH",
                    ),
                ],
                "new_count": 1,
                "skipped_count": 0,
                "error_count": 0,
            }

            transactions = processor._process_file(
                test_file,
                account_config,
                "krungsri_text",
            )

            assert len(transactions) == 1
            assert transactions[0].description == "Test transaction"
            assert transactions[0].amount == 5000.00

    @pytest.mark.processor
    def test_process_file_parser_error(
        self,
        processor: Processor,
        tmp_path: Path,
    ) -> None:
        """Test file processing with parser error."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Invalid format")

        account_config = {
            "name": "test_account",
            "bank_name": "Test Bank",
            "account_number": "123-456-789",
        }

        with patch("bank_importer.library.import_file") as mock_import_file:
            mock_import_file.side_effect = ValueError("Parse error")

            with pytest.raises(ValueError, match="Parse error"):
                processor._process_file(test_file, account_config, "krungsri_text")

    @pytest.mark.processor
    def test_calculate_file_hash(self, processor: Processor, tmp_path: Path) -> None:
        """Test file hash calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        file_hash = processor._calculate_file_hash(test_file)
        assert isinstance(file_hash, str)
        assert len(file_hash) > 0

    @pytest.mark.processor
    def test_create_import_session(self, processor: Processor) -> None:
        """Test creating import session."""
        account_config = {
            "name": "test_account",
            "bank_name": "Test Bank",
            "account_number": "123-456-789",
        }
        file_path = Path("/path/to/file.txt")

        with (
            patch.object(processor, "_calculate_file_hash") as mock_hash,
            patch.object(processor.db_manager, "create_import_session") as mock_create,
        ):
            mock_hash.return_value = "test_hash"
            mock_create.return_value = 1

            session_id = processor._create_import_session(
                account_config,
                file_path,
                "test_session",
            )

            assert session_id == 1
            mock_create.assert_called_once()

    @pytest.mark.processor
    def test_update_import_session(self, processor: Processor) -> None:
        """Test updating import session."""
        with patch.object(processor.db_manager, "update_import_session") as mock_update:
            processor._update_import_session(
                1,
                status="completed",
                processed_transactions=10,
            )

            mock_update.assert_called_once_with(
                1,
                status="completed",
                processed_transactions=10,
            )

    @pytest.mark.processor
    def test_get_parser_none(self, processor: Processor) -> None:
        """Test getting parser with None name."""
        with pytest.raises(ValueError, match="Parser name is required"):
            processor._get_parser(None)

    @pytest.mark.processor
    def test_get_parser_empty_string(self, processor: Processor) -> None:
        """Test getting parser with empty string."""
        with pytest.raises(ValueError, match="Parser name is required"):
            processor._get_parser("")

    @pytest.mark.processor
    def test_get_parser_valid(self, processor: Processor) -> None:
        """Test getting a valid parser."""
        parser = processor.get_parser("krungsri_text")
        assert parser is not None

    @pytest.mark.processor
    def test_get_parser_invalid(self, processor: Processor) -> None:
        """Test getting an invalid parser."""
        parser = processor.get_parser("nonexistent_parser")
        assert parser is None

    @pytest.mark.processor
    @pytest.mark.parametrize(
        ("target_name", "expected_type"),
        [
            ("csv", list),
            ("yaml", list),
        ],
    )
    def test_get_unprocessed_transactions(
        self,
        processor: Processor,
        target_name: str,
        expected_type: type,
    ) -> None:
        """Test getting unprocessed transactions."""
        with patch.object(
            processor.db_manager,
            "get_unprocessed_transactions",
        ) as mock_get:
            mock_get.return_value = []
            result = processor.get_unprocessed_transactions(target_name)
            assert isinstance(result, expected_type)
            mock_get.assert_called_once_with(target_name)

    @pytest.mark.processor
    def test_mark_target_completed(self, processor: Processor) -> None:
        """Test marking target as completed."""
        with patch.object(processor.db_manager, "mark_target_completed") as mock_mark:
            processor.mark_target_completed(1, "csv")
            mock_mark.assert_called_once_with(1, "csv", None)

    @pytest.mark.processor
    def test_mark_target_completed_with_error(self, processor: Processor) -> None:
        """Test marking target as completed with error."""
        with patch.object(processor.db_manager, "mark_target_completed") as mock_mark:
            processor.mark_target_completed(1, "csv", error_message="Test error")
            mock_mark.assert_called_once_with(1, "csv", "Test error")

    @pytest.mark.processor
    def test_sync_to_target(self, processor: Processor) -> None:
        """Test syncing to a target."""
        with patch.object(processor.target_manager, "sync_to_target") as mock_sync:
            mock_result = Mock()
            mock_sync.return_value = mock_result
            result = processor.sync_to_target("csv")
            assert result == mock_result
            mock_sync.assert_called_once_with("csv", None)

    @pytest.mark.processor
    def test_sync_to_target_with_account(self, processor: Processor) -> None:
        """Test syncing to a target with account reference."""
        with patch.object(processor.target_manager, "sync_to_target") as mock_sync:
            mock_result = Mock()
            mock_sync.return_value = mock_result
            result = processor.sync_to_target("csv", account_reference="test_account")
            assert result == mock_result
            mock_sync.assert_called_once_with("csv", "test_account")

    @pytest.mark.processor
    def test_sync_all_targets(self, processor: Processor) -> None:
        """Test syncing to all targets."""
        with patch.object(processor.target_manager, "sync_all_targets") as mock_sync:
            mock_result = {"csv": Mock(), "yaml": Mock()}
            mock_sync.return_value = mock_result
            result = processor.sync_all_targets()
            assert result == mock_result
            mock_sync.assert_called_once_with(None)

    @pytest.mark.processor
    def test_get_export_sessions(self, processor: Processor) -> None:
        """Test getting export sessions."""
        with patch.object(processor.db_manager, "get_export_sessions") as mock_get:
            mock_get.return_value = []
            result = processor.get_export_sessions()
            assert result == []
            mock_get.assert_called_once_with(None)

    @pytest.mark.processor
    def test_get_export_sessions_with_target(self, processor: Processor) -> None:
        """Test getting export sessions for specific target."""
        with patch.object(processor.db_manager, "get_export_sessions") as mock_get:
            mock_get.return_value = []
            result = processor.get_export_sessions("csv")
            assert result == []
            mock_get.assert_called_once_with("csv")

    @pytest.mark.processor
    def test_generate_session_name(self, processor: Processor, tmp_path: Path) -> None:
        """Test generating session name from file path."""
        test_file = tmp_path / "test_file.txt"
        session_name = processor._generate_session_name(test_file)
        assert isinstance(session_name, str)
        assert len(session_name) > 0

    @pytest.mark.processor
    def test_calculate_file_hash_consistency(
        self,
        processor: Processor,
        tmp_path: Path,
    ) -> None:
        """Test that file hash is consistent for same content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        hash1 = processor._calculate_file_hash(test_file)
        hash2 = processor._calculate_file_hash(test_file)
        assert hash1 == hash2

    @pytest.mark.processor
    def test_calculate_file_hash_different_content(
        self,
        processor: Processor,
        tmp_path: Path,
    ) -> None:
        """Test that file hash differs for different content."""
        test_file1 = tmp_path / "test1.txt"
        test_file2 = tmp_path / "test2.txt"
        test_file1.write_text("Content 1")
        test_file2.write_text("Content 2")

        hash1 = processor._calculate_file_hash(test_file1)
        hash2 = processor._calculate_file_hash(test_file2)
        assert hash1 != hash2
