"""Clean command for the bank importer CLI."""

import shutil
from pathlib import Path

import typer

from ...cli_parameters import CONFIG_FILE_PARAM, VERBOSE_PARAM
from ...cli_utils import cli_error_handler
from ...config import ConfigManager
from ...logging_config import (
    get_logger,
    log_error,
    log_info,
    log_success,
    log_warning,
    setup_logging,
)
from ...models.database import DatabaseManager


@cli_error_handler
def clean(
    config_file: str = CONFIG_FILE_PARAM,
    verbose: bool = VERBOSE_PARAM,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    output_only: bool = typer.Option(
        False, "--output-only", help="Only clean output directories, not database"
    ),
    db_only: bool = typer.Option(
        False, "--db-only", help="Only clean database, not output directories"
    ),
) -> None:
    """**Clean** output directories and internal database."""
    # Setup logging
    console_level = "DEBUG" if verbose else "INFO"
    setup_logging(
        enable_rich=True,
        console_level=console_level,
        file_level="DEBUG",
    )
    logger = get_logger("cli")

    logger.info("🧹 Starting Bank Importer - Clean Mode")

    # Load configuration
    config_manager = ConfigManager(Path(config_file))
    output_dir = config_manager.config.get("output", {}).get("output_dir", "data/out")
    database_url = config_manager.get_database_url()

    # Get paths to clean
    output_path = Path(output_dir)
    db_path = Path(database_url.replace("sqlite:///", ""))

    # Show what will be cleaned
    items_to_clean = []

    if not db_only:
        if output_path.exists():
            items_to_clean.append(f"Output directory: {output_path}")
        else:
            log_warning(f"Output directory does not exist: {output_path}")

    if not output_only:
        if db_path.exists():
            items_to_clean.append(f"Database file: {db_path}")
        else:
            log_warning(f"Database file does not exist: {db_path}")

    if not items_to_clean:
        log_warning(
            "Nothing to clean - no existing output directories or database found"
        )
        return

    # Show what will be cleaned
    logger.info("The following items will be cleaned:")
    for item in items_to_clean:
        logger.info(f"  - {item}")

    # Confirm with user unless --force is used
    if not force:
        try:
            confirm = typer.confirm(
                "⚠️  This will permanently delete all exported files and database data. Continue?",
                default=False,
            )
            if not confirm:
                logger.info("Clean operation cancelled by user")
                return
        except Exception:
            # If confirmation fails (e.g., in non-interactive mode), require --force
            log_error("Confirmation required. Use --force to skip confirmation.")
            raise typer.Exit(1) from None

    # Clean output directories
    if not db_only and output_path.exists():
        try:
            if output_path.is_dir():
                shutil.rmtree(output_path)
                log_success(f"Cleaned output directory: {output_path}")
            else:
                output_path.unlink()
                log_success(f"Cleaned output file: {output_path}")
        except Exception as e:
            log_error(f"Failed to clean output directory {output_path}: {e}")
            raise typer.Exit(1) from e

    # Clean database
    if not output_only and db_path.exists():
        try:
            # Close any existing database connections
            DatabaseManager(database_url)

            # Delete the database file
            db_path.unlink()
            log_success(f"Cleaned database file: {db_path}")

            # Also clean any associated files (like WAL files)
            for suffix in [".wal", ".shm", "-journal"]:
                wal_path = Path(str(db_path) + suffix)
                if wal_path.exists():
                    wal_path.unlink()
                    log_info(f"Cleaned database file: {wal_path}")

        except Exception as e:
            log_error(f"Failed to clean database {db_path}: {e}")
            raise typer.Exit(1) from e

    log_success("✅ Clean operation completed successfully")
    logger.info("All exported files and database data have been removed.")
    logger.info("You can now start fresh with a new import.")
