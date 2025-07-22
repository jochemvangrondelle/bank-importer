"""CLI interface for bank importer."""

from pathlib import Path
from typing import Any

import click

from .logging_config import (
    log_error,
    log_info,
    log_success,
    log_warning,
    setup_logging,
)
from .processor import Processor


def _log_session_details(session: dict[str, Any]) -> None:
    """Log details for a single import session."""
    status = session["status"]
    session_name = session["session_name"]
    account_name = session["account_name"]

    if status == "completed":
        log_success(f"{session_name} ({account_name}) - {status}")
    elif status == "failed":
        log_error(f"{session_name} ({account_name}) - {status}")
    elif status == "processing":
        log_info(f"{session_name} ({account_name}) - {status}")
    else:
        log_info(f"{session_name} ({account_name}) - {status}")

    log_info(f"  File: {session['file_path']}")
    log_info(f"  Transactions: {session['processed_transactions']}/{session['total_transactions']}")
    if session["error_count"] > 0:
        log_warning(f"  Errors: {session['error_count']}")
    if session["started_at"]:
        log_info(f"  Started: {session['started_at']}")


@click.group()
def cli() -> None:
    """Bank Importer Thailand - Convert bank statements to structured data."""
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (default: config.toml)",
)
@click.option("--account", "-a", help="Process specific account only")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
def run(config: Path, account: str, log_level: str) -> None:
    """Run the bank importer pipeline."""
    # Setup logging
    setup_logging(log_level=log_level, enable_rich=True)

    try:
        processor = Processor(config)

        if account:
            # Process specific account
            account_config = processor.config_manager.get_account_config(account)
            if not account_config:
                log_error(f"Account '{account}' not found in configuration")
                return

            log_info(f"Processing account: {account}")
            transactions = list(processor.process_account(account))
        else:
            # Process all accounts
            log_info("Processing all accounts...")
            transactions = list(processor.process_accounts())

        log_success(f"Processed {len(transactions)} account results")

        # Show summary
        if transactions:
            total_processed = sum(t.get("processed_transactions", 0) for t in transactions)
            total_errors = sum(t.get("error_count", 0) for t in transactions)
            log_info(f"Total transactions processed: {total_processed}")
            if total_errors > 0:
                log_warning(f"Total errors: {total_errors}")

            # Show account results
            log_info("Account results:")
            for result in transactions:
                if result.get("error_count", 0) == 0:
                    log_success(f"{result['account_name']}: {result.get('processed_transactions', 0)} transactions")
                else:
                    log_error(f"{result['account_name']}: {result.get('processed_transactions', 0)} transactions")
                    if result.get("error_message"):
                        log_error(f"  Error: {result['error_message']}")

    except Exception as e:
        log_error(f"Pipeline error: {e}")
        raise click.Abort() from e


@cli.command()
@click.option(
    "--config", "-c", type=click.Path(path_type=Path), help="Path to configuration file (default: config.toml)"
)
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
def init(config: Path, log_level: str) -> None:
    """Initialize configuration file."""
    # Setup logging
    setup_logging(log_level=log_level, enable_rich=True)

    try:
        processor = Processor(config)
        processor.config_manager.save_config()
        log_success(f"Configuration saved to {processor.config_manager.config_path}")
    except Exception as e:
        log_error(f"Configuration error: {e}")
        raise click.Abort() from e


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (default: config.toml)",
)
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
def list_accounts(config: Path, log_level: str) -> None:
    """List configured accounts."""
    # Setup logging
    setup_logging(log_level=log_level, enable_rich=True)

    try:
        processor = Processor(config)
        accounts = processor.config_manager.get_all_accounts()

        if not accounts:
            log_warning("No accounts configured")
            return

        log_info("Configured accounts:")
        for account in accounts:
            log_info(f"  {account['name']}: {account['bank_name']} ({account['account_number']})")

    except Exception as e:
        log_error(f"Account listing error: {e}")
        raise click.Abort() from e


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (default: config.toml)",
)
@click.option("--account", "-a", help="Show sessions for specific account only")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
def list_sessions(config: Path, account: str, log_level: str) -> None:
    """List import sessions."""
    # Setup logging
    setup_logging(log_level=log_level, enable_rich=True)

    try:
        processor = Processor(config)

        if account:
            sessions = processor.db_manager.get_import_sessions_by_account(account)
        else:
            # Get all sessions by getting all accounts first
            accounts = processor.config_manager.get_all_accounts()
            sessions = []
            for acc in accounts:
                sessions.extend(processor.db_manager.get_import_sessions_by_account(acc["name"]))

        if not sessions:
            log_warning("No import sessions found")
            return

        log_info("Import sessions:")
        for session in sessions:
            _log_session_details(session)

    except Exception as e:
        log_error(f"Session listing error: {e}")
        raise click.Abort() from e


if __name__ == "__main__":
    cli()
