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

"""Coverage command for the bank importer CLI."""

from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import typer

from bank_importer.cli.parameters import (
    ACCOUNT_PARAM,
    CONFIG_FILE_PARAM,
    VERBOSE_PARAM,
)
from bank_importer.cli.utils import cli_error_handler
from bank_importer.config import ConfigManager
from bank_importer.logging_config import (
    get_logger,
    log_error,
    log_info,
    setup_logging,
)
from bank_importer.models.database import DatabaseManager

# Constants for coverage reporting
MAX_MISSING_DATES_DISPLAY = 10
MAX_QUIETEST_DAYS_DISPLAY = 10


def _group_transactions_by_date(
    transactions: list[dict[str, str]],
) -> tuple[dict[str, int], list[date]]:
    """Group transactions by date and return date counts and list of dates."""
    date_counts: dict[str, int] = defaultdict(int)
    dates = []

    for tx in transactions:
        try:
            tx_date = datetime.fromisoformat(tx["date"]).date()
            date_counts[str(tx_date)] += 1
            dates.append(tx_date)
        except Exception as e:
            log_info(
                f"DEBUG: Error parsing date for transaction: {tx.get('date')} - {e}",
            )
            continue

    return date_counts, dates


def _find_missing_dates(
    min_date: date,
    max_date: date,
    date_counts: dict[str, int],
) -> list[date]:
    """Find missing dates in the range."""
    missing_dates = []
    current_date = min_date
    while current_date <= max_date:
        if current_date not in date_counts:
            missing_dates.append(current_date)
        current_date += timedelta(days=1)
    return missing_dates


def _display_missing_dates(missing_dates: list[date]) -> None:
    """Display missing dates."""
    if not missing_dates:
        log_info("  ✅ No missing dates")
        return

    log_info(f"  Missing dates: {len(missing_dates)}")
    if len(missing_dates) <= MAX_MISSING_DATES_DISPLAY:
        for missing_date in missing_dates:
            log_info(f"    - {missing_date}")
    else:
        log_info(
            f"    First 5: {', '.join(str(d) for d in missing_dates[:5])}",
        )
        log_info(
            f"    Last 5: {', '.join(str(d) for d in missing_dates[-5:])}",
        )


def _display_transaction_stats(
    date_counts: dict[str, int],
    transactions: list[dict[str, str]],
    min_date: date,
    max_date: date,
) -> None:
    """Display transaction statistics."""
    log_info(f"  Date range: {min_date} to {max_date}")
    log_info(f"  Total transactions: {len(transactions)}")
    log_info(f"  Days with transactions: {len(date_counts)}")
    log_info(f"  Days in range: {(max_date - min_date).days + 1}")


def _display_busiest_days(date_counts: dict[str, int]) -> None:
    """Display busiest and quietest days."""
    sorted_dates = sorted(date_counts.items(), key=lambda x: x[1], reverse=True)

    if not sorted_dates:
        return

    log_info("  📈 Top 10 busiest days:")
    for date, count in sorted_dates[:10]:
        log_info(f"    {date}: {count} transactions")

    if len(sorted_dates) > MAX_QUIETEST_DAYS_DISPLAY:
        log_info("  📉 Quietest days:")
        for date, count in sorted_dates[-MAX_QUIETEST_DAYS_DISPLAY:]:
            log_info(f"    {date}: {count} transactions")


def _analyze_account_coverage(
    account_name: str,
    account_number: str,
    db: DatabaseManager,
) -> None:
    """Analyze coverage for a single account."""
    log_info(f"\n📋 Account: {account_name} ({account_number})")

    # Get transactions for this account
    transactions = db.get_transactions_by_account(account_number)

    if not transactions:
        log_info("  No transactions found")
        return

    # Group transactions by date
    date_counts, dates = _group_transactions_by_date(transactions)

    if not dates:
        log_info("  No valid transaction dates found")
        return

    # Find date range
    min_date = min(dates)
    max_date = max(dates)

    # Display statistics
    _display_transaction_stats(date_counts, transactions, min_date, max_date)

    # Show missing dates
    missing_dates = _find_missing_dates(min_date, max_date, date_counts)
    _display_missing_dates(missing_dates)

    # Show transaction count by date
    _display_busiest_days(date_counts)


@cli_error_handler
def coverage(
    config_file: str = CONFIG_FILE_PARAM,
    account: str = ACCOUNT_PARAM,
    *,
    verbose: bool = VERBOSE_PARAM,
) -> None:
    """**Show** transaction date coverage for each account."""
    # Setup logging
    console_level = "DEBUG" if verbose else "INFO"
    setup_logging(
        enable_rich=True,
        console_level=console_level,
        file_level="DEBUG",
    )
    logger = get_logger("cli")

    logger.info("📊 Starting Bank Importer - Coverage Analysis")

    try:
        # Load configuration
        config_manager = ConfigManager(Path(config_file))
        database_url = config_manager.get_database_url()
        db = DatabaseManager(database_url)

        # Get all accounts
        accounts = config_manager.get_all_accounts()
        if account is not None:
            accounts = [acc for acc in accounts if acc.get("name") == account]

        if not accounts:
            log_error("No accounts found")
            return

        for acc in accounts:
            account_name = acc.get("name", "Unknown")
            account_number = acc.get("account_number", "Unknown")
            _analyze_account_coverage(account_name, account_number, db)

    except Exception as e:
        log_error(f"Error analyzing coverage: {e}")
        raise typer.Exit(1) from e
