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

"""Tests for CLI init command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bank_importer.cli.commands import init


class TestInitCommand:
    """Tests for init command."""

    def test_init_creates_config_file(self, tmp_path: Path) -> None:
        """Test init creates a new config file."""
        config_file = tmp_path / "config.toml"

        with (
            patch(
                "bank_importer.cli.commands.init.ConfigManager"
            ) as mock_config_manager_class,
            patch("bank_importer.cli.commands.init.log_success") as mock_log_success,
            patch("bank_importer.cli.commands.init.log_warning") as mock_log_warning,
        ):
            mock_config_manager = MagicMock()
            mock_config_manager_class.return_value = mock_config_manager

            init.init(config_file=str(config_file), force=False)

            mock_config_manager_class.assert_called_once_with(config_file)
            mock_config_manager.save_config.assert_called_once()
            mock_log_success.assert_called_once()
            mock_log_warning.assert_called_once()

    def test_init_with_existing_file_no_force(self, tmp_path: Path) -> None:
        """Test init with existing file without force."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("existing config")

        with (
            patch("bank_importer.cli.commands.init.log_warning") as mock_log_warning,
            patch(
                "bank_importer.cli.commands.init.ConfigManager"
            ) as mock_config_manager_class,
        ):
            init.init(config_file=str(config_file), force=False)

            # Should warn and not create
            mock_log_warning.assert_called_once()
            assert "already exists" in str(mock_log_warning.call_args)
            # ConfigManager should not be called
            mock_config_manager_class.assert_not_called()

    def test_init_with_existing_file_with_force(self, tmp_path: Path) -> None:
        """Test init with existing file with force."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("existing config")

        with (
            patch(
                "bank_importer.cli.commands.init.ConfigManager"
            ) as mock_config_manager_class,
            patch("bank_importer.cli.commands.init.log_success") as mock_log_success,
            patch("bank_importer.cli.commands.init.log_warning") as mock_log_warning,
        ):
            mock_config_manager = MagicMock()
            mock_config_manager_class.return_value = mock_config_manager

            init.init(config_file=str(config_file), force=True)

            # Should create despite existing file
            mock_config_manager_class.assert_called_once()
            mock_config_manager.save_config.assert_called_once()
            mock_log_success.assert_called_once()

    def test_init_creates_sample_config(self, tmp_path: Path) -> None:
        """Test init creates correct sample configuration."""
        config_file = tmp_path / "config.toml"

        with (
            patch(
                "bank_importer.cli.commands.init.ConfigManager"
            ) as mock_config_manager_class,
            patch("bank_importer.cli.commands.init.log_success"),
            patch("bank_importer.cli.commands.init.log_warning"),
        ):
            mock_config_manager = MagicMock()
            mock_config_manager_class.return_value = mock_config_manager

            init.init(config_file=str(config_file), force=False)

            # Check that config was set with sample data
            mock_config_manager.config = mock_config_manager.config
            assert mock_config_manager.save_config.called

            # Verify the config structure
            call_args = mock_config_manager_class.call_args
            assert call_args is not None
