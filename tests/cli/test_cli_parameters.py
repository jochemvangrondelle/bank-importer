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

"""Tests for CLI parameters."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from bank_importer.cli.parameters import (
    LazyDependencies,
    _autocomplete_accounts,
    _validate_account,
    get_available_accounts,
    get_db_manager,
    get_processor,
    lazy_deps,
)


class TestGetAvailableAccounts:
    """Test getting available accounts."""

    def test_get_available_accounts_success(self, tmp_path: Path) -> None:
        """Test getting available accounts from config."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[[accounts]]
name = "account1"

[[accounts]]
name = "account2"
""",
        )

        with patch(
            "bank_importer.cli.parameters.ConfigManager",
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.get_all_accounts.return_value = [
                {"name": "account1"},
                {"name": "account2"},
            ]
            mock_config_class.return_value = mock_config

            accounts = get_available_accounts()
            assert "account1" in accounts
            assert "account2" in accounts

    def test_get_available_accounts_empty(self) -> None:
        """Test getting available accounts when none exist."""
        with patch(
            "bank_importer.cli.parameters.ConfigManager",
        ) as mock_config_class:
            mock_config = Mock()
            mock_config.get_all_accounts.return_value = []
            mock_config_class.return_value = mock_config

            accounts = get_available_accounts()
            assert accounts == []

    def test_get_available_accounts_exception(self) -> None:
        """Test getting available accounts when config fails."""
        with patch(
            "bank_importer.cli.parameters.ConfigManager",
        ) as mock_config_class:
            mock_config_class.side_effect = Exception("Config error")
            accounts = get_available_accounts()
            assert accounts == []


class TestValidateAccount:
    """Test account validation."""

    def test_validate_account_none(self) -> None:
        """Test validating None account."""
        ctx = Mock()
        param = Mock()
        result = _validate_account(ctx, param, None)
        assert result is None

    def test_validate_account_valid(self) -> None:
        """Test validating valid account."""
        ctx = Mock()
        param = Mock()
        with patch(
            "bank_importer.cli.parameters.get_available_accounts",
        ) as mock_get:
            mock_get.return_value = ["account1", "account2"]
            result = _validate_account(ctx, param, "account1")
            assert result == "account1"

    def test_validate_account_invalid(self) -> None:
        """Test validating invalid account."""
        ctx = Mock()
        ctx.command_path = "test-command"
        param = Mock()
        with (
            patch("bank_importer.cli.parameters.get_available_accounts") as mock_get,
            patch("bank_importer.cli.parameters.get_console") as mock_console,
        ):
            mock_get.return_value = ["account1", "account2"]
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance

            with pytest.raises(typer.BadParameter, match="Invalid account"):
                _validate_account(ctx, param, "invalid_account")

    def test_validate_account_flag(self) -> None:
        """Test validating account that starts with -- (flag)."""
        ctx = Mock()
        param = Mock()
        result = _validate_account(ctx, param, "--help")
        assert result == "--help"


class TestAutocompleteAccounts:
    """Test account autocomplete."""

    def test_autocomplete_accounts(self) -> None:
        """Test account autocomplete."""
        ctx = Mock()
        args = []
        with patch(
            "bank_importer.cli.parameters.get_available_accounts",
        ) as mock_get:
            mock_get.return_value = ["account1", "account2", "account3"]
            result = _autocomplete_accounts(ctx, args, "account")
            assert len(result) == 3
            assert "account1" in result

    def test_autocomplete_accounts_partial(self) -> None:
        """Test account autocomplete with partial match."""
        ctx = Mock()
        args = []
        with patch(
            "bank_importer.cli.parameters.get_available_accounts",
        ) as mock_get:
            mock_get.return_value = ["account1", "account2", "other"]
            result = _autocomplete_accounts(ctx, args, "account")
            assert len(result) == 2
            assert "account1" in result
            assert "account2" in result
            assert "other" not in result


class TestLazyDependencies:
    """Test lazy dependencies."""

    def test_lazy_dependencies_processor(self) -> None:
        """Test lazy loading of processor."""
        deps = LazyDependencies()
        processor1 = deps.processor
        processor2 = deps.processor
        # Should return same instance
        assert processor1 is processor2

    def test_lazy_dependencies_db_manager(self) -> None:
        """Test lazy loading of database manager."""
        deps = LazyDependencies()
        db_manager1 = deps.db_manager
        db_manager2 = deps.db_manager
        # Should return same instance
        assert db_manager1 is db_manager2

    def test_lazy_dependencies_db_manager_uses_processor(self) -> None:
        """Test that db_manager uses processor's db_manager."""
        deps = LazyDependencies()
        processor = deps.processor
        db_manager = deps.db_manager
        # db_manager should be the same as processor's db_manager
        assert db_manager is processor.db_manager


class TestGetProcessor:
    """Test get_processor function."""

    def test_get_processor(self) -> None:
        """Test getting processor."""
        processor = get_processor()
        assert processor is not None
        # Should return same instance from lazy_deps
        assert processor is lazy_deps.processor


class TestGetDBManager:
    """Test get_db_manager function."""

    def test_get_db_manager(self) -> None:
        """Test getting database manager."""
        db_manager = get_db_manager()
        assert db_manager is not None
        # Should return same instance from lazy_deps
        assert db_manager is lazy_deps.db_manager
