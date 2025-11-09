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

"""Tests for CLI run command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from bank_importer.cli.commands import run


class TestRunCommand:
    """Tests for run command."""

    @patch("bank_importer.cli.commands.run.setup_logging")
    @patch("bank_importer.cli.commands.run.get_logger")
    @patch("bank_importer.cli.commands.status.status")
    @patch("bank_importer.cli.commands.import_files.import_files")
    @patch("bank_importer.cli.commands.export_multi.export_multi")
    def test_run_full_pipeline(
        self,
        mock_export_multi,
        mock_import_files,
        mock_status,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test run command executes full pipeline."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        run.run()

        # Should setup logging
        mock_setup_logging.assert_called_once()

        # Should call all steps
        assert mock_status.call_count == 2  # Initial and final status
        mock_import_files.assert_called_once()
        mock_export_multi.assert_called_once()

        # Should log steps
        assert mock_logger.info.call_count >= 4

    @patch("bank_importer.cli.commands.run.setup_logging")
    @patch("bank_importer.cli.commands.run.get_logger")
    @patch("bank_importer.cli.commands.status.status")
    @patch("bank_importer.cli.commands.import_files.import_files")
    @patch("bank_importer.cli.commands.export_multi.export_multi")
    def test_run_with_verbose(
        self,
        mock_export_multi,
        mock_import_files,
        mock_status,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test run command with verbose flag."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        run.run(verbose=True)

        # Should setup logging with DEBUG level
        call_kwargs = mock_setup_logging.call_args[1]
        assert call_kwargs["console_level"] == "DEBUG"

    @patch("bank_importer.cli.commands.run.setup_logging")
    @patch("bank_importer.cli.commands.run.get_logger")
    @patch("bank_importer.cli.commands.status.status")
    @patch("bank_importer.cli.commands.import_files.import_files")
    @patch("bank_importer.cli.commands.export_multi.export_multi")
    def test_run_with_dry_run(
        self,
        mock_export_multi,
        mock_import_files,
        mock_status,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test run command with dry-run flag."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        run.run(dry_run=True)

        # Should log dry run mode
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("DRY RUN" in str(call) for call in calls)

        # Should pass dry_run to import and export
        mock_import_files.assert_called_once()
        # import_files is called with positional args: [Path("data/")], config_file, account, verbose=verbose, dry_run=dry_run
        call_kwargs = (
            mock_import_files.call_args[1] if mock_import_files.call_args[1] else {}
        )
        assert call_kwargs.get("dry_run") is True

        mock_export_multi.assert_called_once()
        # export_multi is called with positional args: config_file, "", verbose=verbose, dry_run=dry_run
        call_kwargs = (
            mock_export_multi.call_args[1] if mock_export_multi.call_args[1] else {}
        )
        assert call_kwargs.get("dry_run") is True

    @patch("bank_importer.cli.commands.run.setup_logging")
    @patch("bank_importer.cli.commands.run.get_logger")
    @patch("bank_importer.cli.commands.status.status")
    @patch("bank_importer.cli.commands.import_files.import_files")
    @patch("bank_importer.cli.commands.export_multi.export_multi")
    def test_run_with_account(
        self,
        mock_export_multi,
        mock_import_files,
        mock_status,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test run command with specific account."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        run.run(account="test_account")

        # Should pass account to import_files
        mock_import_files.assert_called_once()
        # import_files is called with: [Path("data/")], config_file, account, ...
        call_args = mock_import_files.call_args[0]
        assert len(call_args) >= 3
        assert call_args[2] == "test_account"

    @patch("bank_importer.cli.commands.run.setup_logging")
    @patch("bank_importer.cli.commands.run.get_logger")
    @patch("bank_importer.cli.commands.status.status")
    @patch("bank_importer.cli.commands.import_files.import_files")
    @patch("bank_importer.cli.commands.export_multi.export_multi")
    def test_run_with_config_file(
        self,
        mock_export_multi,
        mock_import_files,
        mock_status,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test run command with config file."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        run.run(config_file="custom_config.toml")

        # Should pass config_file to all commands
        assert mock_status.call_count == 2
        # status is called with config_file as positional arg
        assert mock_status.call_args[0][0] == "custom_config.toml"

        mock_import_files.assert_called_once()
        # import_files is called with: [Path("data/")], config_file, account, ...
        call_args = mock_import_files.call_args[0]
        assert call_args[1] == "custom_config.toml"

        mock_export_multi.assert_called_once()
        # export_multi is called with: config_file, "", ...
        call_args = mock_export_multi.call_args[0]
        assert call_args[0] == "custom_config.toml"
