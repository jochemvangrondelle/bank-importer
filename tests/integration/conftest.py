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

"""Pytest fixtures for integration tests."""

from pathlib import Path
from typing import Any

import pytest

from bank_importer.config import ConfigManager
from bank_importer.models.database import DatabaseManager
from bank_importer.processor import Processor
from bank_importer.target_manager import TargetManager


@pytest.fixture
def integration_db_manager(tmp_path: Path) -> DatabaseManager:
    """Create a database manager with temporary database for integration tests."""
    db_path = tmp_path / "integration_test.db"
    db_url = f"sqlite:///{db_path}"
    # DatabaseManager automatically creates tables in __init__
    return DatabaseManager(db_url)


@pytest.fixture
def integration_config_manager(tmp_path: Path) -> ConfigManager:
    """Create a config manager with temporary config for integration tests."""
    config_path = tmp_path / "integration_config.toml"
    # Create minimal config
    config_content = """
[settings]
output_dir = "{output_dir}"

[[accounts]]
name = "test_account"
bank_name = "Test Bank"
account_number = "123-456-789"
account_name = "Test User"
currency = "THB"
country_code = "TH"

[[targets]]
name = "csv"
enabled = true

[[targets]]
name = "yaml"
enabled = true
""".format(output_dir=str(tmp_path / "output"))
    config_path.write_text(config_content)
    return ConfigManager(config_path)


@pytest.fixture
def integration_processor(
    integration_config_manager: ConfigManager,
    integration_db_manager: DatabaseManager,
) -> Processor:
    """Create a processor instance for integration tests."""
    # Create processor with custom config and db
    processor = Processor(integration_config_manager.config_path)
    # Replace db_manager with our test one
    processor.db_manager = integration_db_manager
    # Also update target_manager to use the same db_manager
    processor.target_manager.db_manager = integration_db_manager
    return processor


@pytest.fixture
def integration_target_manager(
    integration_config_manager: ConfigManager,
    integration_db_manager: DatabaseManager,
) -> TargetManager:
    """Create a target manager for integration tests."""
    return TargetManager(integration_config_manager, integration_db_manager)


@pytest.fixture
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Get output directory for integration tests."""
    output = tmp_path / "output"
    output.mkdir(exist_ok=True)
    return output


def create_account_config(
    parser_name: str,
    account_name: str = "test_account",
    **kwargs: Any,
) -> dict[str, Any]:
    """Create account configuration for a parser.

    Args:
        parser_name: Name of the parser
        account_name: Account name
        **kwargs: Additional account config fields

    Returns:
        Account configuration dictionary

    """
    default_config = {
        "name": account_name,
        "bank_name": "Test Bank",
        "account_number": "123-456-789",
        "account_name": "Test User",
        "currency": "THB",
        "country_code": "TH",
        "parser": parser_name,
    }
    default_config.update(kwargs)
    return default_config
