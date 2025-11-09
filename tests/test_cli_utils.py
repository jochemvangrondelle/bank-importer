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

"""Tests for CLI utilities."""

from pathlib import Path
from unittest.mock import patch

from bank_importer.cli.utils import CLIContext, cli_error_handler, load_cli_config


class TestCLIErrorHandler:
    """Test CLI error handler decorator."""

    def test_cli_error_handler_success(self) -> None:
        """Test error handler with successful function."""

        @cli_error_handler
        def test_func() -> str:
            return "success"

        result = test_func()
        assert result == "success"

    def test_cli_error_handler_exception(self) -> None:
        """Test error handler with exception."""

        @cli_error_handler
        def test_func() -> None:
            msg = "Test error"
            raise ValueError(msg)

        with patch("bank_importer.cli.utils.log_error") as mock_log:
            with patch("bank_importer.cli.utils.sys.exit") as mock_exit:
                test_func()
                mock_log.assert_called_once_with("Test error")
                mock_exit.assert_called_once_with(1)


class TestLoadCLIConfig:
    """Test loading CLI configuration."""

    def test_load_cli_config(self, tmp_path: Path) -> None:
        """Test loading CLI configuration."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[app]
timezone = "Asia/Bangkok"

[database]
url = "sqlite:///test.db"
""",
        )

        config_manager, db_manager = load_cli_config(str(config_file))
        assert config_manager is not None
        assert db_manager is not None
        assert config_manager.config_path == config_file


class TestCLIContext:
    """Test CLI context manager."""

    def test_clic_context_init(self) -> None:
        """Test CLI context initialization."""
        context = CLIContext("test_config.toml")
        assert context.config_file == "test_config.toml"

    def test_clic_context_repr(self) -> None:
        """Test CLI context string representation."""
        context = CLIContext("test_config.toml")
        assert "CLIContext" in repr(context)
        assert "test_config.toml" in repr(context)

    def test_clic_context_enter_exit(self, tmp_path: Path) -> None:
        """Test CLI context enter and exit."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[database]
url = "sqlite:///test.db"
""",
        )

        with CLIContext(str(config_file)) as context:
            assert context._config_manager is not None
            assert context._db_manager is not None

    def test_get_config_manager(self, tmp_path: Path) -> None:
        """Test getting config manager."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[database]
url = "sqlite:///test.db"
""",
        )

        context = CLIContext(str(config_file))
        config_manager = context.get_config_manager()
        assert config_manager is not None

    def test_get_db_manager(self, tmp_path: Path) -> None:
        """Test getting database manager."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[database]
url = "sqlite:///test.db"
""",
        )

        context = CLIContext(str(config_file))
        db_manager = context.get_db_manager()
        assert db_manager is not None

    def test_get_config_manager_lazy_load(self, tmp_path: Path) -> None:
        """Test that config manager is lazily loaded."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[database]
url = "sqlite:///test.db"
""",
        )

        context = CLIContext(str(config_file))
        # Should not be loaded yet
        assert context._config_manager is None

        # First call should load it
        config_manager1 = context.get_config_manager()
        assert config_manager1 is not None

        # Second call should return same instance
        config_manager2 = context.get_config_manager()
        assert config_manager1 is config_manager2
