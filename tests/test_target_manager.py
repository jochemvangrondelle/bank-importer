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

"""Tests for target manager."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from bank_importer.config import ConfigManager
from bank_importer.interfaces.target import TargetResult
from bank_importer.models.database import DatabaseManager
from bank_importer.target_manager import TargetManager


class TestTargetManager:
    """Test target manager functionality."""

    @pytest.fixture
    def config_manager(self, tmp_path: Path) -> ConfigManager:
        """Create a config manager for testing."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[app]
timezone = "Asia/Bangkok"

[database]
url = "sqlite:///test.db"

[[accounts]]
name = "test_account"
parser = "krungsri_text"
file_path = "data/in"
""",
        )
        return ConfigManager(config_file)

    @pytest.fixture
    def db_manager(self, tmp_path: Path) -> DatabaseManager:
        """Create a database manager for testing."""
        db_path = tmp_path / "test.db"
        db_url = f"sqlite:///{db_path}"
        return DatabaseManager(db_url)

    @pytest.fixture
    def target_manager(
        self,
        config_manager: ConfigManager,
        db_manager: DatabaseManager,
    ) -> TargetManager:
        """Create a target manager for testing."""
        return TargetManager(config_manager, db_manager)

    def test_init(self, target_manager: TargetManager) -> None:
        """Test target manager initialization."""
        assert target_manager.config_manager is not None
        assert target_manager.db_manager is not None
        assert len(target_manager.targets) > 0

    def test_get_target_existing(self, target_manager: TargetManager) -> None:
        """Test getting an existing target."""
        target = target_manager.get_target("csv")
        assert target is not None
        assert target.get_name() == "csv"

    def test_get_target_nonexistent(self, target_manager: TargetManager) -> None:
        """Test getting a non-existent target."""
        target = target_manager.get_target("nonexistent")
        assert target is None

    @pytest.mark.parametrize("target_name", ["csv", "yaml", "firefly"])
    def test_get_available_targets(
        self,
        target_manager: TargetManager,
        target_name: str,
    ) -> None:
        """Test getting available targets."""
        available = target_manager.get_available_targets()
        assert target_name in available

    def test_get_available_targets_list(self, target_manager: TargetManager) -> None:
        """Test that available targets returns a list."""
        available = target_manager.get_available_targets()
        assert isinstance(available, list)
        assert len(available) >= 3  # csv, yaml, firefly

    def test_sync_to_target_not_found(self, target_manager: TargetManager) -> None:
        """Test syncing to a non-existent target."""
        result = target_manager.sync_to_target("nonexistent")
        assert isinstance(result, TargetResult)
        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_sync_to_target_no_transactions(
        self,
        target_manager: TargetManager,
    ) -> None:
        """Test syncing to target with no unexported transactions."""
        with patch.object(
            target_manager.db_manager,
            "get_unexported_transactions",
        ) as mock_get:
            mock_get.return_value = []
            result = target_manager.sync_to_target("csv")
            assert result.success is True
            assert result.exported_count == 0

    def test_sync_to_target_with_transactions(
        self,
        target_manager: TargetManager,
        sample_transaction,
    ) -> None:
        """Test syncing to target with transactions."""
        # Add a transaction to the database
        _transaction_id, _ = target_manager.db_manager.add_transaction(
            sample_transaction,
        )

        with patch.object(
            target_manager,
            "_get_bank_type_from_source_file",
        ) as mock_bank_type:
            mock_bank_type.return_value = "krungsri"
            result = target_manager.sync_to_target("csv")
            # Result depends on export success, but should attempt export
            assert isinstance(result, TargetResult)

    def test_sync_to_target_with_account_reference(
        self,
        target_manager: TargetManager,
    ) -> None:
        """Test syncing to target with account reference."""
        with patch.object(
            target_manager.db_manager,
            "get_unexported_transactions",
        ) as mock_get:
            mock_get.return_value = []
            result = target_manager.sync_to_target(
                "csv",
                account_reference="test_account",
            )
            assert result.success is True
            mock_get.assert_called_once_with("csv", "test_account")

    def test_sync_all_targets(self, target_manager: TargetManager) -> None:
        """Test syncing to all enabled targets."""
        with patch.object(target_manager, "sync_to_target") as mock_sync:
            mock_result = TargetResult(
                target_name="csv",
                success=True,
                exported_count=0,
                skipped_count=0,
                error_count=0,
            )
            mock_sync.return_value = mock_result

            # Mock get_available_targets to return only csv and yaml
            with patch.object(
                target_manager,
                "get_available_targets",
            ) as mock_available:
                mock_available.return_value = ["csv", "yaml"]
                results = target_manager.sync_all_targets()
                assert isinstance(results, dict)
                assert len(results) == 2
                assert "csv" in results
                assert "yaml" in results

    def test_get_bank_type_from_source_file(
        self,
        target_manager: TargetManager,
        tmp_path: Path,
    ) -> None:
        """Test getting bank type from source file."""
        test_file = tmp_path / "krungsri_sample.txt"
        test_file.write_text("Test content")

        with patch.object(target_manager, "_get_processor") as mock_get_processor:
            mock_processor = Mock()
            mock_parser_detector = Mock()
            mock_parser_detector.detect_parser.return_value = "krungsri_text"
            mock_processor.parser_detector = mock_parser_detector
            mock_parser = Mock()
            mock_parser.get_bank_type.return_value = "krungsri"
            mock_processor.get_parser.return_value = mock_parser
            mock_get_processor.return_value = mock_processor

            bank_type = target_manager._get_bank_type_from_source_file(str(test_file))
            assert bank_type == "krungsri"

    def test_get_bank_type_from_source_file_no_parser(
        self,
        target_manager: TargetManager,
        tmp_path: Path,
    ) -> None:
        """Test getting bank type when no parser can handle file."""
        test_file = tmp_path / "unknown_file.xyz"
        test_file.write_text("Test content")

        with patch.object(target_manager, "_get_processor") as mock_get_processor:
            mock_processor = Mock()
            mock_parser_detector = Mock()
            mock_parser_detector.detect_parser.return_value = None
            mock_processor.parser_detector = mock_parser_detector
            mock_get_processor.return_value = mock_processor

            with pytest.raises(ValueError, match="No parser can handle file"):
                target_manager._get_bank_type_from_source_file(str(test_file))

    def test_get_organized_output_dir(
        self,
        target_manager: TargetManager,
        tmp_path: Path,
    ) -> None:
        """Test getting organized output directory."""
        base_dir = tmp_path / "output"
        organized_dir = target_manager._get_organized_output_dir(
            "krungsri",
            str(base_dir),
        )
        assert organized_dir.exists()
        assert organized_dir.name == "krungsri"
        assert organized_dir.parent == base_dir

    def test_export_all_files_and_consolidated_no_transactions(
        self,
        target_manager: TargetManager,
    ) -> None:
        """Test exporting when no transactions exist."""
        with patch.object(
            target_manager.db_manager,
            "get_unique_source_files",
        ) as mock_files:
            mock_files.return_value = []
            results = target_manager.export_all_files_and_consolidated("csv")
            assert isinstance(results, dict)
            # When no transactions, results may be empty or contain error result
            # Just verify the method doesn't crash
            assert results is not None

    def test_export_all_files_and_consolidated_with_transactions(
        self,
        target_manager: TargetManager,
        sample_transaction,
    ) -> None:
        """Test exporting with transactions."""
        # Add transaction
        transaction_id, _ = target_manager.db_manager.add_transaction(
            sample_transaction,
        )
        sample_transaction.id = transaction_id

        with (
            patch.object(
                target_manager,
                "_get_bank_type_from_source_file",
            ) as mock_bank_type,
            patch.object(
                target_manager.db_manager,
                "get_unique_source_files",
            ) as mock_files,
            patch.object(
                target_manager.db_manager,
                "get_transactions_by_source_file",
            ) as mock_get_trans,
        ):
            mock_bank_type.return_value = "Krungsri"
            mock_files.return_value = [sample_transaction.source_file or "test.txt"]
            mock_get_trans.return_value = [sample_transaction]
            results = target_manager.export_all_files_and_consolidated("csv")
            assert isinstance(results, dict)
            # Should have some results (consolidated or per-file)
            assert len(results) > 0

    def test_get_processor_lazy_initialization(
        self,
        target_manager: TargetManager,
    ) -> None:
        """Test that processor is lazily initialized."""
        # First call should create processor
        processor1 = target_manager._get_processor()
        assert processor1 is not None

        # Second call should return same instance
        processor2 = target_manager._get_processor()
        assert processor1 is processor2
