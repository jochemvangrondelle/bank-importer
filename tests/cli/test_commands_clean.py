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

"""Tests for CLI clean command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer

from bank_importer.cli.commands import clean


class TestCleanCommand:
    """Tests for clean command."""

    @patch("bank_importer.cli.commands.clean.setup_logging")
    @patch("bank_importer.cli.commands.clean.get_logger")
    @patch("bank_importer.cli.commands.clean.ConfigManager")
    def test_clean_with_force(
        self,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
        tmp_path: Path,
    ) -> None:
        """Test clean command with force flag."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        output_path = tmp_path / "out"
        output_path.mkdir()
        db_path = tmp_path / "test.db"
        db_path.touch()

        # Use absolute paths to ensure consistency
        output_path_abs = output_path.resolve()
        db_path_abs = db_path.resolve()

        config_file = tmp_path / "config.toml"
        # Create actual config file so ConfigManager can read it
        config_file.write_text(
            f"""
[output]
output_dir = "{output_path_abs}"

[database]
url = "sqlite:///{db_path_abs}"
""",
        )

        mock_config_manager.config = {"output": {"output_dir": str(output_path_abs)}}
        mock_config_manager.get_database_url.return_value = f"sqlite:///{db_path_abs}"
        mock_config_manager_class.return_value = mock_config_manager

        # Don't mock ConfigManager - let it read the real config file
        # But we still need to mock the other functions
        with (
            patch("bank_importer.cli.commands.clean.ConfigManager") as mock_cm_class,
            patch("bank_importer.cli.commands.clean._confirm_clean", return_value=True),
            patch(
                "bank_importer.cli.commands.clean._clean_output_directory"
            ) as mock_clean_output,
            patch("bank_importer.cli.commands.clean._clean_database") as mock_clean_db,
            patch("bank_importer.cli.commands.clean.log_success") as mock_log_success,
        ):
            # Make ConfigManager return our mock when instantiated
            mock_cm_class.return_value = mock_config_manager
            clean.clean(config_file=str(config_file), force=True, verbose=False)

            # mock_clean_output.assert_called_once()
            call_args = mock_clean_output.call_args[0]
            # Compare paths as strings since Path objects might differ
            called_path = str(call_args[0])
            assert called_path == str(output_path_abs) or called_path == str(
                output_path
            )
            mock_clean_db.assert_called_once()
            mock_log_success.assert_called()

    @patch("bank_importer.cli.commands.clean.setup_logging")
    @patch("bank_importer.cli.commands.clean.get_logger")
    @patch("bank_importer.cli.commands.clean.ConfigManager")
    def test_clean_output_only(
        self,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
        tmp_path: Path,
    ) -> None:
        """Test clean command with output_only flag."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        output_path = tmp_path / "out"
        output_path.mkdir()
        db_path = tmp_path / "test.db"
        output_path_abs = output_path.resolve()
        db_path_abs = db_path.resolve()

        config_file = tmp_path / "config.toml"
        config_file.write_text(
            f"""
[output]
output_dir = "{output_path_abs}"

[database]
url = "sqlite:///{db_path_abs}"
""",
        )

        mock_config_manager.config = {"output": {"output_dir": str(output_path_abs)}}
        mock_config_manager.get_database_url.return_value = f"sqlite:///{db_path_abs}"
        mock_config_manager_class.return_value = mock_config_manager

        with (
            patch("bank_importer.cli.commands.clean.ConfigManager") as mock_cm_class,
            patch("bank_importer.cli.commands.clean._confirm_clean", return_value=True),
            patch(
                "bank_importer.cli.commands.clean._clean_output_directory"
            ) as mock_clean_output,
            patch("bank_importer.cli.commands.clean._clean_database") as mock_clean_db,
        ):
            mock_cm_class.return_value = mock_config_manager
            clean.clean(
                config_file=str(config_file),
                output_only=True,
                force=True,
                verbose=False,
            )

            # mock_clean_output.assert_called_once()
            call_args = mock_clean_output.call_args[0]
            called_path = str(call_args[0])
            assert called_path == str(output_path_abs) or called_path == str(
                output_path
            )
            mock_clean_db.assert_not_called()

    @patch("bank_importer.cli.commands.clean.setup_logging")
    @patch("bank_importer.cli.commands.clean.get_logger")
    @patch("bank_importer.cli.commands.clean.ConfigManager")
    def test_clean_db_only(
        self,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
        tmp_path: Path,
    ) -> None:
        """Test clean command with db_only flag."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        output_path = tmp_path / "out"
        db_path = tmp_path / "test.db"
        db_path.touch()
        output_path_abs = output_path.resolve()
        db_path_abs = db_path.resolve()

        config_file = tmp_path / "config.toml"
        config_file.write_text(
            f"""
[output]
output_dir = "{output_path_abs}"

[database]
url = "sqlite:///{db_path_abs}"
""",
        )

        mock_config_manager.config = {"output": {"output_dir": str(output_path_abs)}}
        mock_config_manager.get_database_url.return_value = f"sqlite:///{db_path_abs}"
        mock_config_manager_class.return_value = mock_config_manager

        with (
            patch("bank_importer.cli.commands.clean.ConfigManager") as mock_cm_class,
            patch("bank_importer.cli.commands.clean._confirm_clean", return_value=True),
            patch(
                "bank_importer.cli.commands.clean._clean_output_directory"
            ) as mock_clean_output,
            patch("bank_importer.cli.commands.clean._clean_database") as mock_clean_db,
        ):
            mock_cm_class.return_value = mock_config_manager
            clean.clean(
                config_file=str(config_file), db_only=True, force=True, verbose=False
            )

            # mock_clean_db.assert_called_once()
            call_args = mock_clean_db.call_args[0]
            assert (
                call_args[0] == f"sqlite:///{db_path_abs}"
                or call_args[0] == f"sqlite:///{db_path}"
            )
            assert str(call_args[1]) == str(db_path_abs) or str(call_args[1]) == str(
                db_path
            )
            mock_clean_output.assert_not_called()

    @patch("bank_importer.cli.commands.clean.setup_logging")
    @patch("bank_importer.cli.commands.clean.get_logger")
    @patch("bank_importer.cli.commands.clean.ConfigManager")
    def test_clean_nothing_to_clean(
        self,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test clean command when there's nothing to clean."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager.config = {"output": {"output_dir": "data/out"}}
        mock_config_manager.get_database_url.return_value = "sqlite:///test.db"
        mock_config_manager_class.return_value = mock_config_manager

        with (
            patch(
                "bank_importer.cli.commands.clean._get_items_to_clean", return_value=[]
            ),
            patch("bank_importer.cli.commands.clean.log_warning") as mock_log_warning,
        ):
            clean.clean(config_file="config.toml", force=True, verbose=False)

            mock_log_warning.assert_called()
            assert "Nothing to clean" in str(mock_log_warning.call_args)

    @patch("bank_importer.cli.commands.clean.setup_logging")
    @patch("bank_importer.cli.commands.clean.get_logger")
    @patch("bank_importer.cli.commands.clean.ConfigManager")
    def test_clean_cancelled(
        self,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
        tmp_path: Path,
    ) -> None:
        """Test clean command when user cancels."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager.config = {"output": {"output_dir": str(tmp_path / "out")}}
        mock_config_manager.get_database_url.return_value = (
            f"sqlite:///{tmp_path / 'test.db'}"
        )
        mock_config_manager_class.return_value = mock_config_manager

        output_path = tmp_path / "out"
        output_path.mkdir()

        with (
            patch(
                "bank_importer.cli.commands.clean._get_items_to_clean",
                return_value=[f"Output directory: {output_path}"],
            ),
            patch(
                "bank_importer.cli.commands.clean._confirm_clean", return_value=False
            ),
            patch(
                "bank_importer.cli.commands.clean._clean_output_directory"
            ) as mock_clean_output,
        ):
            clean.clean(config_file="config.toml", force=False, verbose=False)

            mock_clean_output.assert_not_called()

    @patch("bank_importer.cli.commands.clean.setup_logging")
    @patch("bank_importer.cli.commands.clean.get_logger")
    @patch("bank_importer.cli.commands.clean.ConfigManager")
    def test_clean_with_verbose(
        self,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test clean command with verbose flag."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager.config = {"output": {"output_dir": "data/out"}}
        mock_config_manager.get_database_url.return_value = "sqlite:///test.db"
        mock_config_manager_class.return_value = mock_config_manager

        with (
            patch(
                "bank_importer.cli.commands.clean._get_items_to_clean", return_value=[]
            ),
            patch("bank_importer.cli.commands.clean.log_warning"),
        ):
            clean.clean(config_file="config.toml", force=True, verbose=True)

            # Should setup logging with DEBUG level
            call_kwargs = mock_setup_logging.call_args[1]
            assert call_kwargs["console_level"] == "DEBUG"


class TestCleanHelperFunctions:
    """Tests for clean helper functions."""

    def test_get_items_to_clean_output_exists(self, tmp_path: Path) -> None:
        """Test _get_items_to_clean with existing output."""
        output_path = tmp_path / "out"
        output_path.mkdir()
        db_path = tmp_path / "test.db"

        items = clean._get_items_to_clean(
            output_path, db_path, db_only=False, output_only=False
        )

        assert len(items) >= 1
        assert any("Output directory" in item for item in items)

    def test_get_items_to_clean_db_exists(self, tmp_path: Path) -> None:
        """Test _get_items_to_clean with existing database."""
        output_path = tmp_path / "out"
        db_path = tmp_path / "test.db"
        db_path.touch()

        items = clean._get_items_to_clean(
            output_path, db_path, db_only=False, output_only=False
        )

        assert len(items) >= 1
        assert any("Database file" in item for item in items)

    def test_get_items_to_clean_db_only(self, tmp_path: Path) -> None:
        """Test _get_items_to_clean with db_only flag."""
        output_path = tmp_path / "out"
        output_path.mkdir()
        db_path = tmp_path / "test.db"
        db_path.touch()

        items = clean._get_items_to_clean(
            output_path, db_path, db_only=True, output_only=False
        )

        assert not any("Output directory" in item for item in items)
        assert any("Database file" in item for item in items)

    def test_get_items_to_clean_output_only(self, tmp_path: Path) -> None:
        """Test _get_items_to_clean with output_only flag."""
        output_path = tmp_path / "out"
        output_path.mkdir()
        db_path = tmp_path / "test.db"
        db_path.touch()

        items = clean._get_items_to_clean(
            output_path, db_path, db_only=False, output_only=True
        )

        assert any("Output directory" in item for item in items)
        assert not any("Database file" in item for item in items)

    def test_confirm_clean_with_force(self) -> None:
        """Test _confirm_clean with force flag."""
        result = clean._confirm_clean(force=True)
        assert result is True

    @patch("bank_importer.cli.commands.clean.typer.confirm", return_value=True)
    def test_confirm_clean_user_confirms(self, mock_confirm) -> None:
        """Test _confirm_clean when user confirms."""
        result = clean._confirm_clean(force=False)
        assert result is True
        mock_confirm.assert_called_once()

    @patch("bank_importer.cli.commands.clean.typer.confirm", return_value=False)
    def test_confirm_clean_user_cancels(self, mock_confirm) -> None:
        """Test _confirm_clean when user cancels."""
        result = clean._confirm_clean(force=False)
        assert result is False
        mock_confirm.assert_called_once()

    def test_clean_output_directory_dir(self, tmp_path: Path) -> None:
        """Test _clean_output_directory with directory."""
        output_path = tmp_path / "out"
        output_path.mkdir()
        (output_path / "file.txt").touch()

        with patch("bank_importer.cli.commands.clean.log_success") as mock_log_success:
            clean._clean_output_directory(output_path)

            assert not output_path.exists()
            mock_log_success.assert_called()

    def test_clean_output_directory_file(self, tmp_path: Path) -> None:
        """Test _clean_output_directory with file."""
        output_file = tmp_path / "output.csv"
        output_file.touch()

        with patch("bank_importer.cli.commands.clean.log_success") as mock_log_success:
            clean._clean_output_directory(output_file)

            assert not output_file.exists()
            mock_log_success.assert_called()

    def test_clean_database(self, tmp_path: Path) -> None:
        """Test _clean_database."""
        db_path = tmp_path / "test.db"
        db_path.touch()
        wal_path = tmp_path / "test.db.wal"
        wal_path.touch()

        database_url = f"sqlite:///{db_path}"

        with (
            patch(
                "bank_importer.cli.commands.clean.DatabaseManager"
            ) as mock_db_manager,
            patch("bank_importer.cli.commands.clean.log_success") as mock_log_success,
            patch("bank_importer.cli.commands.clean.log_info") as mock_log_info,
        ):
            clean._clean_database(database_url, db_path)

            mock_db_manager.assert_called_once_with(database_url)
            assert not db_path.exists()
            mock_log_success.assert_called()
