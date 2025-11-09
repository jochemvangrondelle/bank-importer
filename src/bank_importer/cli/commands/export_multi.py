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

"""Export multi command for the bank importer CLI."""

import logging

from bank_importer.cli.parameters import (
    CONFIG_FILE_PARAM,
    DRY_RUN_PARAM,
    TARGET_PARAM,
    VERBOSE_PARAM,
    get_processor,
)
from bank_importer.interfaces.target import TargetResult
from bank_importer.logging_config import (
    get_logger,
    log_error,
    log_info,
    log_success,
    setup_logging,
)


def export_multi(
    config_file: str = CONFIG_FILE_PARAM,
    target: str = TARGET_PARAM,
    *,
    verbose: bool = VERBOSE_PARAM,
    dry_run: bool = DRY_RUN_PARAM,
) -> None:
    """**Export** transactions to targets with multiple files (per source file + consolidated)."""
    # Setup logging
    console_level = "DEBUG" if verbose else "INFO"
    setup_logging(
        enable_rich=True,
        console_level=console_level,
        file_level="DEBUG",
    )
    logger = get_logger("cli")

    logger.info("🚀 Starting Bank Importer - Multi-File Export Mode")

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No exports will be performed")

    # Get processor and target manager
    processor = get_processor()
    target_manager = processor.target_manager

    if target:
        # Export to specific target
        logger.info("Exporting to target: %s", target)
        results = target_manager.export_all_files_and_consolidated(target)

        for export_name, result in results.items():
            logger.info("Export: %s", export_name)
            _log_export_result(result)
    else:
        # Export to all enabled targets
        logger.info("Exporting to all enabled targets")
        targets_config = processor.config_manager.config.get("targets", [])

        for target_config in targets_config:
            target_name = target_config.get("name")
            enabled = target_config.get("enabled", False)

            if enabled and target_name in target_manager.targets:
                logger.info("Target: %s", target_name)
                results = target_manager.export_all_files_and_consolidated(target_name)

                for export_name, result in results.items():
                    logger.info("  Export: %s", export_name)
                    _log_export_result(result)

    if dry_run:
        logger.info("✅ Dry run completed successfully (no exports performed)")
    else:
        logger.info("✅ Multi-file export processing completed successfully")


def _log_export_result(result: TargetResult) -> None:
    """Log details for an export result."""
    target_name = result.target_name
    status = "SUCCESS" if result.success else "FAILED"

    if result.success:
        log_success(f"Target {target_name}: {status}")
        if result.exported_count > 0 or result.skipped_count > 0:
            # Only log these at DEBUG level
            logging.getLogger("cli").debug("  Exported: %s", result.exported_count)
            logging.getLogger("cli").debug("  Skipped: %s", result.skipped_count)
        if result.error_count > 0:
            log_error(f"  Errors: {result.error_count}")
        if result.output_file:
            log_info(f"  Output: {result.output_file}")
    else:
        log_error(f"Target {target_name}: {status}")
        if result.error_message:
            log_error(f"  Error: {result.error_message}")
