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

"""Status command for the bank importer CLI."""

from calendar import monthrange
from datetime import UTC, datetime, timedelta
from typing import Any

from rich.table import Table

from bank_importer.cli.parameters import CONFIG_FILE_PARAM
from bank_importer.cli.utils import CLIContext, cli_error_handler
from bank_importer.logging_config import get_console


@cli_error_handler
def status(
    config_file: str = CONFIG_FILE_PARAM,
) -> None:
    """**Show** the current status and statistics of the bank importer."""
    console = get_console()

    # Get configuration using dependency injection with lazy loading
    with CLIContext(config_file) as context:
        config_manager = context.get_config_manager()
        db_manager = context.get_db_manager()
        accounts = config_manager.get_all_accounts()

        # Create rich table for accounts
        table = Table(
            title="🏦 Account Status Overview",
            show_header=True,
            header_style="bold magenta",
            border_style="blue",
        )

        # Add columns
        table.add_column("Account Name", style="cyan", no_wrap=True)
        table.add_column("Bank", style="green", no_wrap=True)
        table.add_column("Account Number", style="yellow", no_wrap=True)
        table.add_column("Parser", style="blue", no_wrap=True)
        table.add_column("Transaction Count", style="red", no_wrap=True)
        table.add_column("Last Import", style="magenta", no_wrap=True)
        table.add_column("Date Range", style="purple", no_wrap=True)

        # Add account rows
        for account in accounts:
            account_name = account["name"]

            # Get transaction count for this account
            transactions = db_manager.get_transactions_by_account(
                account["account_number"],
            )
            transaction_count = len(transactions)

            # Get last import session
            import_sessions = db_manager.get_import_sessions_by_account(account_name)
            last_import = "Never"
            if import_sessions:
                # Sort by started_at and get the most recent
                sorted_sessions = sorted(
                    import_sessions,
                    key=lambda x: x.get("started_at", ""),
                    reverse=True,
                )
                if sorted_sessions[0].get("started_at"):
                    # started_at is already an ISO string from to_dict()
                    last_import = sorted_sessions[0]["started_at"][:16].replace(
                        "T",
                        " ",
                    )

            # Calculate date range for transactions
            date_range = "No transactions"
            if transactions:
                dates = [t.get("date", "") for t in transactions if t.get("date")]
                if dates:
                    min_date = min(dates)
                    max_date = max(dates)
                    date_range = f"{min_date} to {max_date}"

            table.add_row(
                account_name,
                account["bank_name"],
                account["account_number"],
                account.get("parser", "Unknown"),
                str(transaction_count),
                last_import,
                date_range,
            )

        # Display the table
        console.print(table)

        # Show summary statistics
        total_accounts = len(accounts)
        total_transactions = sum(
            len(db_manager.get_transactions_by_account(acc["account_number"]))
            for acc in accounts
        )

        console.print(
            f"\n📊 Summary: {total_accounts} accounts, {total_transactions} total transactions",
        )

        # Show import session statistics
        console.print("\n📈 Import Session Statistics")

        # Get all import sessions
        all_sessions = []
        for account in accounts:
            sessions = db_manager.get_import_sessions_by_account(account["name"])
            all_sessions.extend(sessions)

        if all_sessions:
            # Create import sessions table
            sessions_table = Table(
                title="📥 Import Sessions Overview",
                show_header=True,
                header_style="bold cyan",
                border_style="green",
            )

            # Add columns
            sessions_table.add_column("Session Name", style="bold", no_wrap=True)
            sessions_table.add_column("Account", style="yellow", no_wrap=True)
            sessions_table.add_column("Status", style="blue", no_wrap=True)
            sessions_table.add_column("Transactions", style="magenta", no_wrap=True)
            sessions_table.add_column("Started", style="red", no_wrap=True)
            sessions_table.add_column("Min Date", style="purple", no_wrap=True)
            sessions_table.add_column(
                "Max Date",
                no_wrap=True,
            )  # Will be styled dynamically
            sessions_table.add_column("Last Month", style="cyan", no_wrap=True)
            sessions_table.add_column("EXPENSE", style="red", no_wrap=True, width=12)
            sessions_table.add_column("DEPOSIT", style="green", no_wrap=True, width=12)

            # Add rows (show all sessions, not just last 10)
            # Sort by Min Date with fallback to filename
            def sort_key(session: dict[str, Any]) -> tuple[datetime, str]:
                # Get transactions for this session to find min date
                transactions_in_session = db_manager.get_transactions_by_session(
                    session["id"],
                )
                max_date_obj = None
                if transactions_in_session:
                    dates = [
                        t.get("date", "")
                        for t in transactions_in_session
                        if t.get("date")
                    ]
                    if dates:
                        max_date_str = max(dates)
                        try:
                            # Parse the date string to datetime
                            if isinstance(max_date_str, str):
                                max_date_obj = datetime.fromisoformat(
                                    max_date_str,
                                )
                                # Ensure timezone-aware
                                if max_date_obj.tzinfo is None:
                                    max_date_obj = max_date_obj.replace(tzinfo=UTC)
                            elif isinstance(max_date_str, datetime):
                                max_date_obj = max_date_str
                                # Ensure timezone-aware
                                if max_date_obj.tzinfo is None:
                                    max_date_obj = max_date_obj.replace(tzinfo=UTC)
                            else:
                                max_date_obj = None
                        except (ValueError, AttributeError):
                            max_date_obj = None

                # Return tuple for sorting: (max_date, filename)
                # Use filename as fallback if no max_date
                filename = (
                    session.get("file_path", "").split("/")[-1]
                    if session.get("file_path")
                    else ""
                )
                return (
                    max_date_obj if max_date_obj else datetime(1900, 1, 1, tzinfo=UTC),
                    filename,
                )  # Use far past date if no max_date

            all_sorted_sessions = sorted(
                all_sessions,
                key=sort_key,
                reverse=False,  # Show oldest first
            )

            for session in all_sorted_sessions:
                status_icon = (
                    "✅"
                    if session["status"] == "completed"
                    else "❌"
                    if session["status"] == "failed"
                    else "🔄"
                )
                started_at = session.get("started_at", "")
                if started_at:
                    # started_at is already an ISO string from to_dict()
                    started_at = started_at[:16].replace("T", " ")
                else:
                    started_at = "Unknown"

                # Calculate date range for transactions in this session
                transactions_in_session = db_manager.get_transactions_by_session(
                    session["id"],
                )
                min_date = "N/A"
                max_date = "N/A"
                last_month_date = "N/A"
                max_date_style = "purple"  # Default style

                # Calculate expense and deposit amounts
                expense_amount = 0.0
                deposit_amount = 0.0

                if transactions_in_session:
                    for transaction in transactions_in_session:
                        amount = transaction.get("amount", 0)
                        if isinstance(amount, int | float):
                            if amount < 0:
                                expense_amount += abs(amount)
                            elif amount > 0:
                                deposit_amount += amount

                    dates = []
                    for t in transactions_in_session:
                        date_val = t.get("date")
                        if date_val:
                            # Convert to string if datetime object
                            if isinstance(date_val, datetime):
                                dates.append(date_val.isoformat())
                            elif isinstance(date_val, str):
                                dates.append(date_val)
                    if dates:
                        min_date = (
                            min(dates)[:10]
                            if isinstance(min(dates), str)
                            else str(min(dates))[:10]
                        )
                        max_date = (
                            max(dates)[:10]
                            if isinstance(max(dates), str)
                            else str(max(dates))[:10]
                        )

                        # Calculate the last date of the month being covered
                        max_date_obj = datetime.strptime(max_date, "%Y-%m-%d").replace(
                            tzinfo=UTC,
                        )
                        # Get the last day of the current month (the month being covered)
                        last_day_current_month = monthrange(
                            max_date_obj.year,
                            max_date_obj.month,
                        )[1]
                        last_month_date_obj = datetime(
                            max_date_obj.year,
                            max_date_obj.month,
                            last_day_current_month,
                            tzinfo=UTC,
                        )

                        # If the last date of the month is in the future, use yesterday's date instead
                        today = datetime.now(UTC).date()
                        if last_month_date_obj.date() > today:
                            yesterday = today - timedelta(days=1)
                            last_month_date_obj = datetime.combine(
                                yesterday,
                                datetime.min.time(),
                            )

                        last_month_date = last_month_date_obj.strftime("%Y-%m-%d")

                        # Check if max_date equals last_month_date
                        if max_date != last_month_date:
                            max_date_style = "red"  # Make it red if they don't match

                sessions_table.add_row(
                    session["session_name"],
                    session["account_name"],
                    f"{status_icon} {session['status']}",
                    f"{session['processed_transactions']}/{session['total_transactions']}",
                    started_at,
                    min_date,
                    f"[red]{max_date}[/red]" if max_date_style == "red" else max_date,
                    last_month_date,
                    f"{expense_amount:,.2f}",
                    f"{deposit_amount:,.2f}",
                )

            # Add consolidated summary row (same as 'all' export)
            all_transactions = []
            for account in accounts:
                transactions = db_manager.get_transactions_by_account(
                    account["account_number"],
                )
                all_transactions.extend(transactions)

            if all_transactions:
                # Calculate consolidated statistics
                consolidated_min_date = "N/A"
                consolidated_max_date = "N/A"
                consolidated_last_month_date = "N/A"
                consolidated_max_date_style = "purple"

                # Calculate consolidated expense and deposit amounts
                consolidated_expense_amount = 0.0
                consolidated_deposit_amount = 0.0

                for transaction in all_transactions:
                    amount = transaction.get("amount", 0)
                    if isinstance(amount, int | float):
                        if amount < 0:
                            consolidated_expense_amount += abs(amount)
                        elif amount > 0:
                            consolidated_deposit_amount += amount

                dates = []
                for t in all_transactions:
                    date_val = t.get("date")
                    if date_val:
                        # Convert to string if datetime object
                        if isinstance(date_val, datetime):
                            dates.append(date_val.isoformat())
                        elif isinstance(date_val, str):
                            dates.append(date_val)
                if dates:
                    min_date_str = min(dates)
                    max_date_str = max(dates)
                    consolidated_min_date = (
                        min_date_str[:10]
                        if isinstance(min_date_str, str)
                        else str(min_date_str)[:10]
                    )
                    consolidated_max_date = (
                        max_date_str[:10]
                        if isinstance(max_date_str, str)
                        else str(max_date_str)[:10]
                    )

                    # Calculate the last date of the month being covered
                    max_date_obj = datetime.strptime(
                        consolidated_max_date,
                        "%Y-%m-%d",
                    ).replace(tzinfo=UTC)
                    last_day_current_month = monthrange(
                        max_date_obj.year,
                        max_date_obj.month,
                    )[1]
                    last_month_date_obj = datetime(
                        max_date_obj.year,
                        max_date_obj.month,
                        last_day_current_month,
                        tzinfo=UTC,
                    )

                    # If the last date of the month is in the future, use yesterday's date instead
                    today = datetime.now(UTC).date()
                    if last_month_date_obj.date() > today:
                        yesterday = today - timedelta(days=1)
                        last_month_date_obj = datetime.combine(
                            yesterday,
                            datetime.min.time(),
                        )

                    consolidated_last_month_date = last_month_date_obj.strftime(
                        "%Y-%m-%d",
                    )

                    # Check if max_date equals last_month_date
                    if consolidated_max_date != consolidated_last_month_date:
                        consolidated_max_date_style = "red"

                # Add consolidated summary row
                sessions_table.add_row(
                    "📊 ALL TRANSACTIONS (Consolidated)",
                    "All Accounts",
                    "✅ consolidated",
                    f"{len(all_transactions)}/0",
                    "N/A",
                    consolidated_min_date,
                    f"[red]{consolidated_max_date}[/red]"
                    if consolidated_max_date_style == "red"
                    else consolidated_max_date,
                    consolidated_last_month_date,
                    f"{consolidated_expense_amount:,.2f}",
                    f"{consolidated_deposit_amount:,.2f}",
                    style="bold cyan",
                )

            console.print(sessions_table)

            # Show summary
            completed_sessions = sum(
                1 for s in all_sessions if s["status"] == "completed"
            )
            failed_sessions = sum(1 for s in all_sessions if s["status"] == "failed")
            console.print(
                f"📊 Import Sessions: {len(all_sessions)} total, {completed_sessions} completed, {failed_sessions} failed",
            )
        else:
            console.print("📊 No import sessions found")
