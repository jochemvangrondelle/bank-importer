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

"""Initialize command for the bank importer CLI."""

from pathlib import Path

from bank_importer.cli.parameters import CONFIG_FILE_PARAM, FORCE_PARAM
from bank_importer.cli.utils import cli_error_handler
from bank_importer.config import ConfigManager
from bank_importer.logging_config import log_success, log_warning


@cli_error_handler
def init(
    config_file: str = CONFIG_FILE_PARAM,
    *,
    force: bool = FORCE_PARAM,
) -> None:
    """**Initialize** the application with a sample configuration file."""
    config_path = Path(config_file)

    if config_path.exists() and not force:
        log_warning(
            f"Configuration file {config_file} already exists. Use --force to overwrite.",
        )
        return

    # Create sample configuration
    config_manager = ConfigManager(config_path)

    # Create a basic configuration
    sample_config = {
        "accounts": [
            {
                "name": "example_account",
                "parser": "generic_csv",
                "file_pattern": "*.csv",
                "file_path": "data/in",
                "account_number": "123456789",
                "account_name": "Example Account",
                "bank_name": "Example Bank",
                "branch_name": "",
                "currency": "THB",
                "country_code": "TH",
                "reference": "example_account",
            },
        ],
        "targets": [
            {
                "name": "csv",
                "enabled": True,
            },
            {
                "name": "firefly",
                "enabled": False,
            },
        ],
        "output": {
            "output_dir": "data/out",
        },
        "database": {
            "url": "sqlite:///bank_importer.db",
        },
    }

    # Set the configuration and save
    config_manager.config = sample_config
    config_manager.save_config()

    log_success(f"Configuration file created: {config_file}")
    log_warning(
        "Please update the configuration with your actual account details before running.",
    )
