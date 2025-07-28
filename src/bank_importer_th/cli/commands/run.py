"""Run command for the bank importer CLI."""

from pathlib import Path

from ...cli_parameters import (
    ACCOUNT_PARAM,
    CONFIG_FILE_PARAM,
    DRY_RUN_PARAM,
    VERBOSE_PARAM,
)
from ...logging_config import (
    get_logger,
    setup_logging,
)
from . import export_multi, import_files, status


def run(
    config_file: str = CONFIG_FILE_PARAM,
    account: str = ACCOUNT_PARAM,
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
    import_files.import_files([Path("data/")], config_file, account, verbose, dry_run)

    # Step 3: Export transactions
    logger.info("📤 Step 3: Export Transactions")
    export_multi.export_multi(config_file, "", verbose, dry_run)

    # Step 4: Show final status
    logger.info("📊 Step 4: Final Status")
    status.status(config_file)

    if dry_run:
        logger.info("✅ Dry run completed successfully")
    else:
        logger.info("✅ Full pipeline completed successfully")
