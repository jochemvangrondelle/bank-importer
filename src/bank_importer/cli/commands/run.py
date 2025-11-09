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

"""Run command for the bank importer CLI."""

from pathlib import Path

from bank_importer.cli.commands import export_multi, import_files, status
from bank_importer.cli.parameters import (
    ACCOUNT_PARAM,
    CONFIG_FILE_PARAM,
    DRY_RUN_PARAM,
    VERBOSE_PARAM,
)
from bank_importer.logging_config import get_logger, setup_logging


def run(
    config_file: str = CONFIG_FILE_PARAM,
    account: str = ACCOUNT_PARAM,
    *,
    verbose: bool = VERBOSE_PARAM,
    dry_run: bool = DRY_RUN_PARAM,
) -> None:
    """**Run** the complete pipeline: status + import + export + status."""
    # Setup logging
    console_level = "DEBUG" if verbose else "INFO"
    setup_logging(
        enable_rich=True,
        console_level=console_level,
        file_level="DEBUG",
    )
    logger = get_logger("cli")

    logger.info("🚀 Starting Bank Importer - Full Pipeline")

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No operations will be performed")

    # Step 1: Show initial status
    logger.info("📊 Step 1: Initial Status")
    status.status(config_file)

    # Step 2: Import files
    logger.info("📥 Step 2: Import Files")
    import_files.import_files(
        [Path("data/")],
        config_file,
        account,
        verbose=verbose,
        dry_run=dry_run,
    )

    # Step 3: Export transactions
    logger.info("📤 Step 3: Export Transactions")
    export_multi.export_multi(
        config_file,
        "",
        verbose=verbose,
        dry_run=dry_run,
    )

    # Step 4: Show final status
    logger.info("📊 Step 4: Final Status")
    status.status(config_file)

    if dry_run:
        logger.info("✅ Dry run completed successfully")
    else:
        logger.info("✅ Full pipeline completed successfully")
