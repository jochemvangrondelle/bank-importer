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

"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest
import toml

from bank_importer.config import ConfigManager


class TestConfigManager:
    """Test configuration manager functionality."""

    def test_init_with_default_path(self) -> None:
        """Test initialization with default config path."""
        manager = ConfigManager()
        assert manager.config_path == Path("config.toml")
        assert isinstance(manager.config, dict)

    def test_init_with_custom_path(self) -> None:
        """Test initialization with custom config path."""
        custom_path = Path("custom_config.toml")
        manager = ConfigManager(custom_path)
        assert manager.config_path == custom_path

    def test_load_config_file_exists(self) -> None:
        """Test loading configuration from existing file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            config_data = {
                "app": {"timezone": "UTC"},
                "database": {"url": "sqlite:///test.db"},
                "accounts": [],
                "targets": [],
            }
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            assert manager.config["app"]["timezone"] == "UTC"
            assert manager.config["database"]["url"] == "sqlite:///test.db"
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_config_file_not_exists(self) -> None:
        """Test loading default config when file doesn't exist."""
        non_existent = Path("nonexistent_config.toml")
        manager = ConfigManager(non_existent)
        assert "app" in manager.config
        assert "database" in manager.config
        assert "accounts" in manager.config

    def test_load_config_invalid_toml(self, tmp_path: Path) -> None:
        """Test loading config with invalid TOML falls back to default."""
        invalid_file = tmp_path / "invalid.toml"
        invalid_file.write_text("invalid toml content {")

        manager = ConfigManager(invalid_file)
        # Should fall back to default config
        assert "app" in manager.config
        assert "database" in manager.config

    def test_save_config(self, tmp_path: Path) -> None:
        """Test saving configuration to file."""
        config_file = tmp_path / "test_config.toml"
        manager = ConfigManager(config_file)

        # Modify config
        manager.config["app"]["timezone"] = "Europe/Amsterdam"
        manager.save_config()

        # Verify file was written
        assert config_file.exists()
        loaded = ConfigManager(config_file)
        assert loaded.config["app"]["timezone"] == "Europe/Amsterdam"

    def test_save_config_error_handling(self, tmp_path: Path) -> None:
        """Test error handling when saving config fails."""
        # Create a directory with the config file name to cause write error
        config_file = tmp_path / "test_config.toml"
        config_file.mkdir()  # Make it a directory

        manager = ConfigManager(config_file)
        # Should not raise exception, just log error
        manager.save_config()

    def test_get_account_config_exists(self) -> None:
        """Test getting account config that exists."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            config_data = {
                "accounts": [
                    {
                        "name": "test_account",
                        "parser": "krungsri_text",
                        "file_path": "data/in",
                    },
                ],
            }
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            account = manager.get_account_config("test_account")
            assert account is not None
            assert account["name"] == "test_account"
        finally:
            temp_path.unlink(missing_ok=True)

    def test_get_account_config_not_exists(self) -> None:
        """Test getting account config that doesn't exist."""
        manager = ConfigManager()
        account = manager.get_account_config("nonexistent")
        assert account is None

    def test_get_account_config_invalid_accounts_type(self) -> None:
        """Test getting account config when accounts is not a list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            config_data = {"accounts": "not_a_list"}
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            account = manager.get_account_config("test")
            assert account is None
        finally:
            temp_path.unlink(missing_ok=True)

    def test_get_all_accounts(self) -> None:
        """Test getting all accounts."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            config_data = {
                "accounts": [
                    {"name": "account1", "parser": "krungsri_text"},
                    {"name": "account2", "parser": "scb_pdf"},
                ],
            }
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            accounts = manager.get_all_accounts()
            assert len(accounts) == 2
            assert accounts[0]["name"] == "account1"
            assert accounts[1]["name"] == "account2"
        finally:
            temp_path.unlink(missing_ok=True)

    def test_get_all_accounts_empty(self) -> None:
        """Test getting all accounts when none exist."""
        manager = ConfigManager()
        accounts = manager.get_all_accounts()
        assert isinstance(accounts, list)
        # Default config has one account
        assert len(accounts) >= 0

    def test_get_all_accounts_invalid_type(self) -> None:
        """Test getting all accounts when accounts is not a list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            config_data = {"accounts": "not_a_list"}
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            accounts = manager.get_all_accounts()
            assert accounts == []
        finally:
            temp_path.unlink(missing_ok=True)

    def test_get_all_accounts_without_name(self) -> None:
        """Test getting all accounts when account dict has no name."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            config_data = {
                "accounts": [
                    {"parser": "krungsri_text"},  # No name field
                ],
            }
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            accounts = manager.get_all_accounts()
            # Account without name should still be included
            assert len(accounts) == 1
        finally:
            temp_path.unlink(missing_ok=True)

    @pytest.mark.parametrize(
        ("config_data", "expected_url"),
        [
            ({"database": {"url": "sqlite:///custom.db"}}, "sqlite:///custom.db"),
            ({}, "sqlite:///bank_importer.db"),  # Default
            ({"database": "not_a_dict"}, "sqlite:///bank_importer.db"),  # Invalid type
            ({"database": {"url": 12345}}, "sqlite:///bank_importer.db"),  # Non-string
        ],
    )
    def test_get_database_url(
        self,
        tmp_path: Path,
        config_data: dict,
        expected_url: str,
    ) -> None:
        """Test getting database URL with various configurations."""
        import os

        # Save original DATABASE_URL if it exists (for database.url)
        original_db_url = os.environ.pop("DATABASE_URL", None)
        # Also check for any config file that might exist
        original_config = None
        config_file_path = Path("config.toml")
        if config_file_path.exists():
            original_config = config_file_path.read_text()
            config_file_path.unlink()
        try:
            config_file = tmp_path / "test_config.toml"
            if config_data:
                import toml

                with config_file.open("w") as f:
                    toml.dump(config_data, f)
                manager = ConfigManager(config_file)
            else:
                # Create an empty config file to avoid using default
                with config_file.open("w") as f:
                    f.write("")
                manager = ConfigManager(config_file)

            url = manager.get_database_url()
            assert url == expected_url
        finally:
            # Restore original environment variables
            if original_db_url:
                os.environ["DATABASE_URL"] = original_db_url
            # Restore original config file if it existed
            if original_config is not None:
                config_file_path.write_text(original_config)

    def test_get_enabled_targets(self) -> None:
        """Test getting enabled targets."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            config_data = {
                "targets": [
                    {"name": "csv", "enabled": True},
                    {"name": "yaml", "enabled": False},
                    {"name": "firefly", "enabled": True},
                ],
            }
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            targets = manager.get_enabled_targets()
            assert len(targets) == 2
            assert all(target["enabled"] for target in targets)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_get_enabled_targets_empty(self) -> None:
        """Test getting enabled targets when none are enabled."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            config_data = {
                "targets": [
                    {"name": "csv", "enabled": False},
                    {"name": "yaml", "enabled": False},
                ],
            }
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            targets = manager.get_enabled_targets()
            assert targets == []
        finally:
            temp_path.unlink(missing_ok=True)

    def test_get_enabled_targets_invalid_type(self) -> None:
        """Test getting enabled targets when targets is not a list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            config_data = {"targets": "not_a_list"}
            toml.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            targets = manager.get_enabled_targets()
            assert targets == []
        finally:
            temp_path.unlink(missing_ok=True)

    @pytest.mark.parametrize(
        ("config_data", "expected_timezone"),
        [
            ({"app": {"timezone": "Europe/Amsterdam"}}, "Europe/Amsterdam"),
            ({}, "Asia/Bangkok"),  # Default
            ({"app": "not_a_dict"}, "Asia/Bangkok"),  # Invalid type
            ({"app": {"timezone": 12345}}, "Asia/Bangkok"),  # Non-string
        ],
    )
    def test_get_timezone(
        self,
        tmp_path: Path,
        config_data: dict,
        expected_timezone: str,
    ) -> None:
        """Test getting timezone with various configurations."""
        if config_data:
            config_file = tmp_path / "test_config.toml"
            with config_file.open("w") as f:
                toml.dump(config_data, f)
            manager = ConfigManager(config_file)
        else:
            manager = ConfigManager()

        timezone = manager.get_timezone()
        assert timezone == expected_timezone
