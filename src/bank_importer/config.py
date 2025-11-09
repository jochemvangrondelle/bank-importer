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

"""Configuration management for bank importer."""

from pathlib import Path
from typing import Any

import toml

from bank_importer.config_resolver import ConfigResolver
from bank_importer.logging_config import log_error


class ConfigManager:
    """Manage configuration for bank importer."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize configuration manager."""
        self.config_path = config_path or Path("config.toml")
        raw_config = self._load_config()
        # Resolve environment variables and file-based secrets
        self.config = ConfigResolver.resolve_config(raw_config)

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from TOML file."""
        if not self.config_path.exists():
            return self._get_default_config()

        try:
            with self.config_path.open() as f:
                config_data: dict[str, Any] = toml.load(f)
                return config_data
        except Exception as e:
            log_error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            "app": {"timezone": "Asia/Bangkok"},
            "database": {"url": "sqlite:///bank_importer.db"},
            "accounts": [
                {
                    "name": "krungsri_main",
                    "parser": "krungsri_text",
                    "file_pattern": "*.txt",
                    "file_path": "data/in",
                    "account_number": "XXX-1-32483-X",
                    "account_name": "MR. JOCHEM GRONDELLE",
                    "bank_name": "Krungsri Bank",
                    "branch_name": "EMQUARTIER BRANCH",
                    "currency": "THB",
                    "country_code": "TH",
                    "reference": "krungsri_main",
                },
            ],
            "targets": [{"name": "firefly", "enabled": False, "config": {}}],
        }

    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with self.config_path.open("w") as f:
                toml.dump(self.config, f)
        except Exception as e:
            log_error(f"Error saving config: {e}")

    def get_account_config(self, account_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific account with resolved secrets.

        Resolves values from:
        1. Environment variables (e.g., ACCOUNTS_MY_ACCOUNT_PASSWORD)
        2. File-based secrets (e.g., password_file = "~/secrets/password.txt")
        3. TOML values

        Args:
            account_name: Name of the account

        Returns:
            Account configuration with resolved secrets, or None if not found

        """
        accounts = self.config.get("accounts", [])
        if not isinstance(accounts, list):
            return None
        for account in accounts:
            if isinstance(account, dict) and account.get("name") == account_name:
                # Resolve account-specific environment variables and files
                return ConfigResolver.resolve_account_config(account, account_name)
        return None

    def get_all_accounts(self) -> list[dict[str, Any]]:
        """Get all account configurations with resolved secrets.

        Each account configuration is resolved with environment variables and files.
        """
        accounts = self.config.get("accounts", [])
        if not isinstance(accounts, list):
            return []
        # Resolve each account configuration
        resolved_accounts = []
        for account in accounts:
            if isinstance(account, dict) and "name" in account:
                account_name = account.get("name", "")
                resolved_account = ConfigResolver.resolve_account_config(
                    account,
                    account_name,
                )
                resolved_accounts.append(resolved_account)
            else:
                resolved_accounts.append(account)
        return resolved_accounts

    def get_database_url(self) -> str:
        """Get database URL from configuration with environment variable support.

        Can be set via:
        - Environment: DATABASE_URL
        - File: url_file = "~/secrets/db_url.txt"
        - TOML: [database] url = "..."
        """
        database = self.config.get("database", {})
        if isinstance(database, dict):
            url = database.get("url", "sqlite:///bank_importer.db")
            if isinstance(url, str):
                return url
        return "sqlite:///bank_importer.db"

    def get_enabled_targets(self) -> list[dict[str, Any]]:
        """Get all enabled targets."""
        targets = self.config.get("targets", [])
        if not isinstance(targets, list):
            return []
        return [
            target
            for target in targets
            if isinstance(target, dict) and target.get("enabled", False)
        ]

    def get_timezone(self) -> str:
        """Get timezone from configuration."""
        app = self.config.get("app", {})
        if isinstance(app, dict):
            timezone = app.get("timezone", "Asia/Bangkok")
            if isinstance(timezone, str):
                return timezone
        return "Asia/Bangkok"

    def get_output_dir(self) -> str:
        """Get output directory from configuration."""
        output = self.config.get("output", {})
        if isinstance(output, dict):
            output_dir = output.get("output_dir", "data/out")
            if isinstance(output_dir, str):
                return output_dir
        return "data/out"
