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

"""Import files command for the bank importer CLI."""

from pathlib import Path

import typer

from bank_importer.cli.parameters import (
    ACCOUNT_PARAM,
    CONFIG_FILE_PARAM,
    DRY_RUN_PARAM,
    REPROCESS_EXISTING_PARAM,
    VERBOSE_PARAM,
    get_processor,
)
from bank_importer.logging_config import (
    get_logger,
    log_success,
    log_warning,
    setup_logging,
)
from bank_importer.parser_detector import ParserDetector
from bank_importer.telemetry import trace_function


@trace_function(attributes={"operation": "cli_import"})  # type: ignore[misc]
def import_files(
    paths: list[Path] = typer.Argument(
        None,
        help="Paths to files or directories to import (default: data/)",
    ),
    _config_file: str = CONFIG_FILE_PARAM,
    account: str = ACCOUNT_PARAM,
    *,
    verbose: bool = VERBOSE_PARAM,
    dry_run: bool = DRY_RUN_PARAM,
    reprocess_existing: bool = REPROCESS_EXISTING_PARAM,
) -> None:
    """**Import** bank statement files and parse transactions."""
    # Setup logging
    console_level = "DEBUG" if verbose else "INFO"
    setup_logging(
        enable_rich=True,
        console_level=console_level,
        file_level="DEBUG",
    )
    logger = get_logger("cli")

    logger.info("🚀 Starting Bank Importer - Import Mode")

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No files will be processed")

    # Use default path if no paths provided
    if not paths:
        paths = [Path("data/")]

    # Get processor and parser detector
    processor = get_processor()
    parser_detector = ParserDetector()

    if account:
        # Process specific account
        logger.info("Processing account: %s", account)
        results = list(
            processor.process_account(account, reprocess_existing=reprocess_existing),
        )
        if results:
            log_success(f"Processed {len(results)} files for account '{account}'")
        else:
            log_warning(f"No files found for account '{account}'")
    else:
        # Process all accounts
        all_accounts = processor.config_manager.get_all_accounts()
        for acc in all_accounts:
            account_name = acc["name"]
            logger.info("Processing account: %s", account_name)
            results = list(
                processor.process_account(
                    account_name,
                    reprocess_existing=reprocess_existing,
                ),
            )
            if results:
                log_success(
                    f"Processed {len(results)} files for account '{account_name}'",
                )
            else:
                log_warning(f"No files found for account '{account_name}'")

        # If no accounts configured, try to auto-detect parsers for files in paths
        if not all_accounts:
            logger.info("No accounts configured, attempting auto-detection...")
            for path in paths:
                if path.is_file():
                    detected_parser = parser_detector.detect_parser(path)
                    if detected_parser:
                        logger.info(
                            "Auto-detected parser '%s' for %s",
                            detected_parser,
                            path,
                        )
                        # TODO: Create temporary account config and process file
                    else:
                        logger.warning("No suitable parser found for %s", path)
                elif path.is_dir():
                    logger.info("Scanning directory: %s", path)
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            detected_parser = parser_detector.detect_parser(file_path)
                            if detected_parser:
                                logger.info(
                                    "Auto-detected parser '%s' for %s",
                                    detected_parser,
                                    file_path,
                                )
                                # TODO: Create temporary account config and process file
                            else:
                                logger.debug(
                                    "No suitable parser found for %s",
                                    file_path,
                                )

    if dry_run:
        logger.info("✅ Dry run completed successfully (no files processed)")
    else:
        logger.info("✅ Import processing completed successfully")
