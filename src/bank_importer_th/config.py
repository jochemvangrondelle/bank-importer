"""Configuration management for bank importer."""

from pathlib import Path
from typing import Any

import toml


class ConfigManager:
    """Manage configuration for bank importer."""

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration manager."""
        self.config_path = config_path or Path("config.toml")
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from TOML file."""
        if not self.config_path.exists():
            return self._get_default_config()

        try:
            with open(self.config_path) as f:
                config_data: dict[str, Any] = toml.load(f)
                return config_data
        except Exception as e:
            print(f"Error loading config: {e}")
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
                }
            ],
            "targets": [{"name": "firefly", "enabled": False, "config": {}}],
        }

    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, "w") as f:
                toml.dump(self.config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_account_config(self, account_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific account."""
        accounts = self.config.get("accounts", [])
        if not isinstance(accounts, list):
            return None
        for account in accounts:
            if isinstance(account, dict) and account.get("name") == account_name:
                return account
        return None

    def get_all_accounts(self) -> list[dict[str, Any]]:
        """Get all account configurations."""
        accounts = self.config.get("accounts", [])
        if isinstance(accounts, list):
            return accounts
        return []

    def get_database_url(self) -> str:
        """Get database URL from configuration."""
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
