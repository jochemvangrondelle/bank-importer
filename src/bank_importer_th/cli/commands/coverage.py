"""Coverage command for the bank importer CLI."""

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import typer

from ...cli_parameters import ACCOUNT_PARAM, CONFIG_FILE_PARAM, VERBOSE_PARAM
from ...cli_utils import cli_error_handler
from ...config import ConfigManager
from ...logging_config import (
    get_logger,
    log_error,
    log_info,
    setup_logging,
)
from ...models.database import DatabaseManager


@cli_error_handler
def coverage(
    config_file: str = CONFIG_FILE_PARAM,
    account: str = ACCOUNT_PARAM,
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

            print(f"\n📋 Account: {account_name} ({account_number})")
            log_info(f"\n📋 Account: {account_name} ({account_number})")

            # Get transactions for this account
            transactions = db.get_transactions_by_account(account_number)

            if not transactions:
                log_info("  No transactions found")
                continue

            # Group transactions by date
            date_counts: dict[str, int] = defaultdict(int)
            dates = []

            for tx in transactions:
                try:
                    tx_date = datetime.fromisoformat(
                        tx["date"].replace("Z", "+00:00")
                    ).date()
                    date_counts[str(tx_date)] += 1
                    dates.append(tx_date)
                except Exception as e:
                    print(
                        f"DEBUG: Error parsing date for transaction: {tx.get('date')} - {e}"
                    )
                    continue

            if not dates:
                log_info("  No valid transaction dates found")
                continue

            # Find date range
            min_date = min(dates)
            max_date = max(dates)

            print(f"  Date range: {min_date} to {max_date}")
            print(f"  Total transactions: {len(transactions)}")
            print(f"  Days with transactions: {len(date_counts)}")
            print(f"  Days in range: {(max_date - min_date).days + 1}")

            # Show missing dates
            missing_dates = []
            current_date = min_date
            while current_date <= max_date:
                if current_date not in date_counts:
                    missing_dates.append(current_date)
                current_date += timedelta(days=1)

            if missing_dates:
                print(f"  Missing dates: {len(missing_dates)}")
                if len(missing_dates) <= 10:
                    for missing_date in missing_dates:
                        print(f"    - {missing_date}")
                else:
                    print(
                        f"    First 5: {', '.join(str(d) for d in missing_dates[:5])}"
                    )
                    print(
                        f"    Last 5: {', '.join(str(d) for d in missing_dates[-5:])}"
                    )
            else:
                print("  ✅ No missing dates")

            # Show transaction count by date (top 10 and bottom 10)
            sorted_dates = sorted(date_counts.items(), key=lambda x: x[1], reverse=True)

            if sorted_dates:
                print("  📈 Top 10 busiest days:")
                for date, count in sorted_dates[:10]:
                    print(f"    {date}: {count} transactions")

                if len(sorted_dates) > 10:
                    print("  📉 Quietest days:")
                    for date, count in sorted_dates[-10:]:
                        print(f"    {date}: {count} transactions")

    except Exception as e:
        log_error(f"Error analyzing coverage: {e}")
        raise typer.Exit(1) from e
