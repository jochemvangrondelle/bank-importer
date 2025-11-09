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

"""Tests for configuration resolver."""

import os
import tempfile
from pathlib import Path

from bank_importer.config_resolver import ConfigResolver


class TestConfigResolver:
    """Test configuration resolver functionality."""

    def test_resolve_from_environment_variable(self) -> None:
        """Test resolving configuration from environment variable."""
        os.environ["TEST_PASSWORD"] = "env-password"
        config = {"password": "toml-password"}
        resolved = ConfigResolver.resolve_config(config, "TEST")
        assert resolved["password"] == "env-password"
        del os.environ["TEST_PASSWORD"]

    def test_resolve_from_file(self) -> None:
        """Test resolving configuration from file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("file-password\n")
            temp_path = f.name

        try:
            config = {"password": "toml-password", "password_file": temp_path}
            resolved = ConfigResolver.resolve_config(config, "TEST")
            assert resolved["password"] == "file-password"
        finally:
            Path(temp_path).unlink()

    def test_resolve_from_toml_fallback(self) -> None:
        """Test resolving configuration from TOML when env/file not available."""
        config = {"password": "toml-password"}
        resolved = ConfigResolver.resolve_config(config, "TEST")
        assert resolved["password"] == "toml-password"

    def test_resolve_account_config(self) -> None:
        """Test resolving account configuration."""
        os.environ["ACCOUNTS_MY_ACCOUNT_PASSWORD"] = "account-password"
        config = {"name": "my-account", "password": "toml-password"}
        resolved = ConfigResolver.resolve_account_config(config, "my-account")
        assert resolved["password"] == "account-password"
        assert resolved["name"] == "my-account"
        del os.environ["ACCOUNTS_MY_ACCOUNT_PASSWORD"]

    def test_resolve_nested_config(self) -> None:
        """Test resolving nested configuration."""
        os.environ["TRANSLATION_GOOGLE_TRANSLATE_API_KEY"] = "env-api-key"
        config = {
            "translation": {
                "google_translate_api_key": "toml-api-key",
            },
        }
        resolved = ConfigResolver.resolve_config(config)
        assert resolved["translation"]["google_translate_api_key"] == "env-api-key"
        del os.environ["TRANSLATION_GOOGLE_TRANSLATE_API_KEY"]

    def test_resolve_account_with_hyphens(self) -> None:
        """Test resolving account configuration with hyphens in name."""
        os.environ["ACCOUNTS_MY_ACCOUNT_PASSWORD"] = "hyphen-password"
        config = {"name": "my-account", "password": "toml-password"}
        resolved = ConfigResolver.resolve_account_config(config, "my-account")
        assert resolved["password"] == "hyphen-password"
        del os.environ["ACCOUNTS_MY_ACCOUNT_PASSWORD"]

    def test_file_expands_home_directory(self) -> None:
        """Test that file paths expand ~ to home directory."""
        home = Path.home()
        secret_file = home / ".test_secret"
        try:
            secret_file.write_text("home-password\n")
            config = {"password": "toml-password", "password_file": "~/.test_secret"}
            resolved = ConfigResolver.resolve_config(config, "TEST")
            assert resolved["password"] == "home-password"
        finally:
            if secret_file.exists():
                secret_file.unlink()

    def test_file_not_found_uses_toml(self) -> None:
        """Test that missing file falls back to TOML value."""
        config = {"password": "toml-password", "password_file": "/nonexistent/file.txt"}
        resolved = ConfigResolver.resolve_config(config, "TEST")
        assert resolved["password"] == "toml-password"

    def test_priority_order(self) -> None:
        """Test that environment variable takes priority over file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("file-password\n")
            temp_path = f.name

        try:
            os.environ["TEST_PASSWORD"] = "env-password"
            config = {"password": "toml-password", "password_file": temp_path}
            resolved = ConfigResolver.resolve_config(config, "TEST")
            assert resolved["password"] == "env-password"
        finally:
            del os.environ["TEST_PASSWORD"]
            Path(temp_path).unlink()
