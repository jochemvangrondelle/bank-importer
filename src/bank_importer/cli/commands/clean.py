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

"""Clean command for the bank importer CLI."""

import shutil
from pathlib import Path

import typer

from bank_importer.cli.parameters import CONFIG_FILE_PARAM, VERBOSE_PARAM
from bank_importer.cli.utils import cli_error_handler
from bank_importer.config import ConfigManager
from bank_importer.logging_config import (
    get_logger,
    log_error,
    log_info,
    log_success,
    log_warning,
    setup_logging,
)
from bank_importer.models.database import DatabaseManager


def _get_items_to_clean(
    output_path: Path,
    db_path: Path,
    *,
    db_only: bool,
    output_only: bool,
) -> list[str]:
    """Get list of items that will be cleaned."""
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
    return items_to_clean


def _confirm_clean(*, force: bool) -> bool:
    """Confirm clean operation with user unless --force is used."""
    if force:
        return True
    try:
        confirm = typer.confirm(
            "⚠️  This will permanently delete all exported files and database data. Continue?",
            default=False,
        )
        if not confirm:
            get_logger("cli").info("Clean operation cancelled by user")
            return False
        return True
    except Exception:
        log_error("Confirmation required. Use --force to skip confirmation.")
        raise typer.Exit(1) from None


def _clean_output_directory(output_path: Path) -> None:
    """Clean output directory or file."""
    if output_path.is_dir():
        shutil.rmtree(output_path)
        log_success(f"Cleaned output directory: {output_path}")
    else:
        output_path.unlink()
        log_success(f"Cleaned output file: {output_path}")


def _clean_database(database_url: str, db_path: Path) -> None:
    """Clean database file and associated files."""
    DatabaseManager(database_url)
    db_path.unlink()
    log_success(f"Cleaned database file: {db_path}")
    for suffix in [".wal", ".shm", "-journal"]:
        wal_path = Path(str(db_path) + suffix)
        if wal_path.exists():
            wal_path.unlink()
            log_info(f"Cleaned database file: {wal_path}")


@cli_error_handler
def clean(
    config_file: str = CONFIG_FILE_PARAM,
    *,
    verbose: bool = VERBOSE_PARAM,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),  # noqa: FBT003
    output_only: bool = typer.Option(
        False,  # noqa: FBT003
        "--output-only",
        help="Only clean output directories, not database",
    ),
    db_only: bool = typer.Option(
        False,  # noqa: FBT003
        "--db-only",
        help="Only clean database, not output directories",
    ),
) -> None:
    """**Clean** output directories and internal database."""
    console_level = "DEBUG" if verbose else "INFO"
    setup_logging(
        enable_rich=True,
        console_level=console_level,
        file_level="DEBUG",
    )
    logger = get_logger("cli")
    logger.info("🧹 Starting Bank Importer - Clean Mode")

    config_manager = ConfigManager(Path(config_file))
    output_dir = config_manager.config.get("output", {}).get("output_dir", "data/out")
    database_url = config_manager.get_database_url()

    output_path = Path(output_dir)
    db_path = Path(database_url.replace("sqlite:///", ""))

    # Debugging: log resolved values to help diagnose tests where nothing is found
    logger.debug("config_manager.config=%s", getattr(config_manager, "config", None))
    logger.debug("output_dir=%s", output_dir)
    logger.debug("database_url=%s", database_url)
    logger.debug("output_path=%s exists=%s", output_path, output_path.exists())
    logger.debug("db_path=%s exists=%s", db_path, db_path.exists())
    # Print to stdout so test output captures values even when logger is mocked

    # Typer uses Option objects as default values when the CLI is invoked by Typer.
    # When this function is called directly in tests the default argument values
    # may still be Typer Option objects (truthy), causing incorrect branching.
    # Normalize the flags to booleans or their underlying default values.
    def _resolve_flag(flag) -> object:  # noqa: ANN001
        try:
            # Typer Option/Argument objects expose a 'default' attribute
            return flag.default  # type: ignore[attr-defined]
        except Exception:
            return bool(flag)

    db_only = _resolve_flag(db_only)
    output_only = _resolve_flag(output_only)

    items_to_clean = _get_items_to_clean(
        output_path,
        db_path,
        db_only=db_only,
        output_only=output_only,
    )

    if not items_to_clean:
        log_warning(
            "Nothing to clean - no existing output directories or database found",
        )
        return

    logger.info("The following items will be cleaned:")
    for item in items_to_clean:
        logger.info("  - %s", item)

    if not _confirm_clean(force=force):
        return

    if not db_only and output_path.exists():
        try:
            _clean_output_directory(output_path)
        except Exception as e:
            log_error(f"Failed to clean output directory {output_path}: {e}")
            raise typer.Exit(1) from e

    if not output_only and db_path.exists():
        try:
            _clean_database(database_url, db_path)
        except Exception as e:
            log_error(f"Failed to clean database {db_path}: {e}")
            raise typer.Exit(1) from e

    log_success("✅ Clean operation completed successfully")
    logger.info("All exported files and database data have been removed.")
    logger.info("You can now start fresh with a new import.")
