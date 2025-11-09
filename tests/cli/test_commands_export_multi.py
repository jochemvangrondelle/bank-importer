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

"""Tests for export_multi CLI command."""

from unittest.mock import Mock, patch

import pytest

from bank_importer.cli.commands.export_multi import export_multi
from bank_importer.interfaces.target import TargetResult


class TestExportMulti:
    """Tests for export_multi command."""

    @pytest.fixture
    def mock_processor(self) -> Mock:
        """Create a mock processor."""
        processor = Mock()
        processor.config_manager.config = {
            "targets": [
                {"name": "csv", "enabled": True},
                {"name": "yaml", "enabled": False},
            ],
        }
        return processor

    @pytest.fixture
    def mock_target_manager(self) -> Mock:
        """Create a mock target manager."""
        target_manager = Mock()
        target_manager.targets = {"csv": Mock(), "yaml": Mock()}
        target_manager.export_all_files_and_consolidated.return_value = {
            "export1": TargetResult(
                target_name="csv",
                success=True,
                exported_count=10,
                skipped_count=0,
                error_count=0,
                output_file="output.csv",
                error_message=None,
            ),
        }
        return target_manager

    def test_export_multi_specific_target(
        self,
        mock_processor: Mock,
        mock_target_manager: Mock,
    ) -> None:
        """Test exporting to a specific target."""
        mock_processor.target_manager = mock_target_manager
        with (
            patch(
                "bank_importer.cli.commands.export_multi.get_processor",
                return_value=mock_processor,
            ),
            patch("bank_importer.cli.commands.export_multi.setup_logging"),
            patch(
                "bank_importer.cli.commands.export_multi.get_logger",
            ) as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            export_multi(
                target="csv",
                verbose=False,
                dry_run=False,
            )
            mock_target_manager.export_all_files_and_consolidated.assert_called_once_with(
                "csv",
            )

    def test_export_multi_all_targets(
        self,
        mock_processor: Mock,
        mock_target_manager: Mock,
    ) -> None:
        """Test exporting to all enabled targets."""
        mock_processor.target_manager = mock_target_manager
        with (
            patch(
                "bank_importer.cli.commands.export_multi.get_processor",
                return_value=mock_processor,
            ),
            patch("bank_importer.cli.commands.export_multi.setup_logging"),
            patch(
                "bank_importer.cli.commands.export_multi.get_logger",
            ) as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            export_multi(
                target="",
                verbose=False,
                dry_run=False,
            )
            # Should call export for enabled targets
            assert mock_target_manager.export_all_files_and_consolidated.called

    def test_export_multi_dry_run(
        self,
        mock_processor: Mock,
        mock_target_manager: Mock,
    ) -> None:
        """Test export in dry run mode."""
        mock_processor.target_manager = mock_target_manager
        with (
            patch(
                "bank_importer.cli.commands.export_multi.get_processor",
                return_value=mock_processor,
            ),
            patch("bank_importer.cli.commands.export_multi.setup_logging"),
            patch(
                "bank_importer.cli.commands.export_multi.get_logger",
            ) as mock_get_logger,
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            export_multi(
                target="csv",
                verbose=False,
                dry_run=True,
            )
            # Check that dry run message was logged
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("DRY RUN" in str(call) for call in log_calls)

    def test_export_multi_with_errors(
        self,
        mock_processor: Mock,
        mock_target_manager: Mock,
    ) -> None:
        """Test export with errors."""
        error_result = TargetResult(
            target_name="csv",
            success=False,
            exported_count=0,
            skipped_count=0,
            error_count=5,
            output_file=None,
            error_message="Export failed",
        )
        mock_target_manager.export_all_files_and_consolidated.return_value = {
            "export1": error_result,
        }
        mock_processor.target_manager = mock_target_manager
        with (
            patch(
                "bank_importer.cli.commands.export_multi.get_processor",
                return_value=mock_processor,
            ),
            patch("bank_importer.cli.commands.export_multi.setup_logging"),
            patch(
                "bank_importer.cli.commands.export_multi.get_logger",
            ) as mock_get_logger,
            patch("bank_importer.cli.commands.export_multi.log_error"),
        ):
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            export_multi(
                target="csv",
                verbose=False,
                dry_run=False,
            )
            # Should handle error result
            mock_target_manager.export_all_files_and_consolidated.assert_called_once()
