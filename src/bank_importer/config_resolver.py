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

"""Configuration resolver for environment variables and file-based secrets."""

import os
from pathlib import Path
from typing import Any

from bank_importer.logging_config import get_logger

logger = get_logger(__name__)


class ConfigResolver:
    """Resolve configuration values from TOML, environment variables, and files."""

    @staticmethod
    def resolve_config(config_data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """Resolve configuration values from multiple sources.

        Priority order:
        1. Environment variables
        2. File-based secrets ({key}_file attributes)
        3. TOML values

        Args:
            config_data: Configuration dictionary from TOML
            prefix: Prefix for environment variable names (e.g., "ACCOUNTS_MY_ACCOUNT")

        Returns:
            Resolved configuration dictionary

        """
        resolved = {}
        for key, value in config_data.items():
            # Skip file references (they're used to load values, not stored)
            if key.endswith("_file"):
                continue

            # Handle nested dictionaries recursively
            if isinstance(value, dict):
                nested_prefix = ConfigResolver._build_env_prefix(prefix, key)
                resolved[key] = ConfigResolver.resolve_config(value, nested_prefix)
            # Handle lists (e.g., accounts list)
            elif isinstance(value, list):
                resolved_list: list[Any] = [
                    ConfigResolver.resolve_config(item, prefix)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
                resolved[key] = resolved_list  # type: ignore[assignment]
            else:
                # Try to resolve from environment variable or file
                resolved_value = ConfigResolver._resolve_value(
                    key,
                    value,
                    prefix,
                    config_data,
                )
                resolved[key] = resolved_value

        return resolved

    @staticmethod
    def _resolve_value(
        key: str,
        toml_value: Any,
        prefix: str,
        config_data: dict[str, Any],
    ) -> Any:
        """Resolve a single configuration value.

        Args:
            key: Configuration key
            toml_value: Value from TOML (fallback)
            prefix: Environment variable prefix
            config_data: Full config data (to check for _file keys)

        Returns:
            Resolved value

        """
        # Build environment variable name
        env_key = ConfigResolver._build_env_key(prefix, key)

        # Priority 1: Check environment variable
        env_value = os.getenv(env_key)
        if env_value is not None:
            logger.debug("Using environment variable %s for %s", env_key, key)
            return env_value.strip()

        # Priority 2: Check for file-based secret
        file_key = f"{key}_file"
        if file_key in config_data:
            file_path_str = config_data[file_key]
            if isinstance(file_path_str, str):
                file_value = ConfigResolver._read_file_secret(file_path_str, key)
                if file_value is not None:
                    logger.debug("Using file %s for %s", file_path_str, key)
                    return file_value

        # Priority 3: Use TOML value
        return toml_value

    @staticmethod
    def _read_file_secret(file_path_str: str, key: str) -> str | None:
        """Read secret value from file.

        Args:
            file_path_str: Path to file (supports ~ expansion)
            key: Configuration key (for logging)

        Returns:
            File contents (stripped) or None if file doesn't exist

        """
        try:
            # Expand ~ to home directory
            file_path = Path(file_path_str).expanduser()

            if not file_path.exists():
                logger.warning(
                    "Secret file not found: %s (for key: %s)",
                    file_path,
                    key,
                )
                return None

            if not file_path.is_file():
                logger.warning(
                    "Secret path is not a file: %s (for key: %s)",
                    file_path,
                    key,
                )
                return None

            # Read file and strip whitespace
            with file_path.open(encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    logger.warning(
                        "Secret file is empty: %s (for key: %s)",
                        file_path,
                        key,
                    )
                    return None
                return content

        except Exception as e:
            logger.exception(
                "Error reading secret file %s (for key: %s): %s",
                file_path_str,
                key,
                e,
            )
            return None

    @staticmethod
    def _build_env_prefix(prefix: str, key: str) -> str:
        """Build environment variable prefix for nested configs.

        Args:
            prefix: Current prefix
            key: Current key

        Returns:
            New prefix

        """
        key_upper = ConfigResolver._normalize_key(key)
        if prefix:
            return f"{prefix}_{key_upper}"
        return key_upper

    @staticmethod
    def _build_env_key(prefix: str, key: str) -> str:
        """Build full environment variable name.

        Args:
            prefix: Prefix (e.g., "ACCOUNTS_MY_ACCOUNT")
            key: Configuration key (e.g., "password")

        Returns:
            Environment variable name (e.g., "ACCOUNTS_MY_ACCOUNT_PASSWORD")

        """
        key_upper = ConfigResolver._normalize_key(key)
        if prefix:
            return f"{prefix}_{key_upper}"
        return key_upper

    @staticmethod
    def _normalize_key(key: str) -> str:
        """Normalize key for environment variable name.

        Converts to uppercase and replaces hyphens/underscores consistently.

        Args:
            key: Configuration key

        Returns:
            Normalized key (uppercase, underscores)

        """
        # Replace hyphens with underscores, then uppercase
        return key.replace("-", "_").upper()

    @staticmethod
    def resolve_account_config(
        account_config: dict[str, Any],
        account_name: str,
    ) -> dict[str, Any]:
        """Resolve account configuration with environment variables and files.

        Args:
            account_config: Account configuration from TOML
            account_name: Account name (for environment variable prefix)

        Returns:
            Resolved account configuration

        Example:
            Account name "my-account" with password can be set via:
            - Environment: ACCOUNTS_MY_ACCOUNT_PASSWORD
            - File: password_file = "~/secrets/password.txt"
            - TOML: password = "123"

        """
        prefix = f"ACCOUNTS_{ConfigResolver._normalize_key(account_name)}"
        return ConfigResolver.resolve_config(account_config, prefix)
