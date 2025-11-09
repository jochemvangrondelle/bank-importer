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

"""Configure command for interactive configuration management."""

import datetime
import getpass
from pathlib import Path
from typing import Any

import pytz
import toml
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from bank_importer.cli.parameters import CONFIG_FILE_PARAM
from bank_importer.cli.utils import cli_error_handler
from bank_importer.logging_config import get_console, log_success
from bank_importer.parser_detector import ParserDetector


def _get_local_timezone() -> str:
    """Get local timezone or default to Asia/Bangkok."""
    try:
        local_tz = datetime.datetime.now(datetime.UTC).astimezone().tzinfo
        # Try to get timezone name
        if local_tz is not None and hasattr(local_tz, "zone"):
            tz_name = getattr(local_tz, "zone", None)
            if tz_name:
                return str(tz_name)
        return "Asia/Bangkok"
    except Exception:
        return "Asia/Bangkok"


def _select_from_list(
    console: Console,
    prompt_text: str,
    items: list[str],
    default: str | None = None,
) -> str | None:
    """Select an item from a list by index number or identifier.

    Args:
        console: Rich console instance
        prompt_text: Prompt text to display
        items: List of items to choose from
        default: Default value (identifier, not index)

    Returns:
        Selected item identifier, or None if invalid

    """
    if not items:
        return None

    # Display numbered list
    console.print(f"\n[bold]{prompt_text}:[/bold]")
    for idx, item in enumerate(items, 1):
        console.print(f"  {idx}. {item}")

    # Build choices: numbers as strings + identifiers
    choices = [str(i) for i in range(1, len(items) + 1)] + items

    # Build help text
    help_text = f"Enter number (1-{len(items)}) or identifier"
    if default:
        help_text += f" (default: {default})"

    while True:
        selection = Prompt.ask(f"\n{help_text}", choices=choices, default=default or "")

        # Check if it's a number
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(items):
                return items[idx]
            console.print(
                f"[red]Invalid number. Please enter 1-{len(items)} or an identifier[/red]",
            )
        except ValueError:
            # It's an identifier - check if it's valid
            if selection in items:
                return selection
            console.print(
                "[red]Invalid identifier. Please enter a number or valid identifier[/red]",
            )


def _select_account_index(
    console: Console,
    config: dict[str, Any],
    prompt_text: str = "Enter account number or name",
) -> int | None:
    """Select an account by index number or name.

    Args:
        console: Rich console instance
        config: Configuration dictionary
        prompt_text: Prompt text to display

    Returns:
        Account index (0-based), or None if invalid/cancelled

    """
    accounts = config.get("accounts", [])
    if not accounts:
        return None

    _list_accounts(console, config)

    # Build list of account names
    account_names = []
    for account in accounts:
        if isinstance(account, dict):
            account_names.append(account.get("name", "Unknown"))
        else:
            account_names.append("Unknown")

    # Display selection options
    console.print(f"\n[bold]{prompt_text}:[/bold]")
    for idx, name in enumerate(account_names, 1):
        console.print(f"  {idx}. {name}")

    choices = [str(i) for i in range(1, len(accounts) + 1)] + account_names

    while True:
        selection = Prompt.ask(
            f"\nEnter number (1-{len(accounts)}) or account name",
            choices=choices,
            default="",
        )

        # Check if it's a number
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(accounts):
                return idx
            console.print(
                f"[red]Invalid number. Please enter 1-{len(accounts)} or an account name[/red]",
            )
        except ValueError:
            # It's an account name - find the index
            if selection in account_names:
                return account_names.index(selection)
            console.print(
                "[red]Invalid account name. Please enter a number or valid account name[/red]",
            )


def _select_target_index(
    console: Console,
    config: dict[str, Any],
    prompt_text: str = "Enter target number or name",
) -> int | None:
    """Select a target by index number or name.

    Args:
        console: Rich console instance
        config: Configuration dictionary
        prompt_text: Prompt text to display

    Returns:
        Target index (0-based), or None if invalid/cancelled

    """
    targets = config.get("targets", [])
    if not targets:
        return None

    _list_targets(console, config)

    # Build list of target names
    target_names = []
    for target in targets:
        if isinstance(target, dict):
            target_names.append(target.get("name", "Unknown"))
        else:
            target_names.append("Unknown")

    # Display selection options
    console.print(f"\n[bold]{prompt_text}:[/bold]")
    for idx, name in enumerate(target_names, 1):
        console.print(f"  {idx}. {name}")

    choices = [str(i) for i in range(1, len(targets) + 1)] + target_names

    while True:
        selection = Prompt.ask(
            f"\nEnter number (1-{len(targets)}) or target name",
            choices=choices,
            default="",
        )

        # Check if it's a number
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(targets):
                return idx
            console.print(
                f"[red]Invalid number. Please enter 1-{len(targets)} or a target name[/red]",
            )
        except ValueError:
            # It's a target name - find the index
            if selection in target_names:
                return target_names.index(selection)
            console.print(
                "[red]Invalid target name. Please enter a number or valid target name[/red]",
            )


def _get_default_config() -> dict[str, Any]:
    """Get default configuration (without accounts)."""
    return {
        "app": {"timezone": _get_local_timezone()},
        "database": {"url": "sqlite:///bank_importer.db"},
        "output": {"output_dir": "data/out"},
        "translation": {
            "enable_translation": True,
            "default_source_language": "TH",
            "default_target_language": "en",
            "translation_cache_file": "translation_cache.json",
            "google_translate_api_key": "",
            "term_mappings": {
                "th_en": {
                    "ATM": "ATM",
                    "IB": "Internet Banking",
                    "POS": "Point of Sale",
                    "CDM": "Cash Deposit Machine",
                    "INT": "Interest",
                    "FEE": "Fee",
                    "Transfer": "Transfer",
                    "Withdrawal": "Withdrawal",
                    "Deposit": "Deposit",
                    "Credit": "Credit",
                    "Debit": "Debit",
                    "Payment": "Payment",
                    "Interest": "Interest",
                    "Fee": "Fee",
                    "จ่ายบิล": "Bill Payment",
                    "ถอนเงิน": "Withdrawal",
                    "โอนเงิน": "Transfer",
                    "ฝากเงิน": "Deposit",
                },
            },
        },
        "targets": [
            {
                "name": "csv",
                "enabled": True,
                "csv_config": {
                    "date_format": "Y-m-d",
                    "delimiter": "comma",
                    "include_headers": True,
                    "add_import_tag": True,
                    "duplicate_detection": "classic",
                    "ignore_duplicate_lines": True,
                    "ignore_duplicate_transactions": True,
                    "map_currency": True,
                    "map_account_name": True,
                    "map_account_iban": True,
                    "map_opposing_name": True,
                    "map_opposing_iban": True,
                    "map_category": True,
                    "map_budget": True,
                    "map_bill": True,
                    "use_external_id": True,
                    "external_id_format": "{account_number}_{date}_{transaction_id}",
                    "default_tags": ["imported", "bank-importer"],
                    "include_parser_tag": True,
                    "include_balance_info": True,
                    "include_transaction_type": True,
                },
            },
            {
                "name": "yaml",
                "enabled": True,
                "yaml_config": {
                    "include_summary": True,
                    "group_by_month": True,
                },
            },
            {
                "name": "firefly",
                "enabled": False,
            },
        ],
        "accounts": [],
    }


def _load_raw_config(config_path: Path) -> dict[str, Any]:
    """Load raw config without resolution for editing."""
    if not config_path.exists():
        return {}
    try:
        with config_path.open() as f:
            return toml.load(f)
    except Exception:
        return {}


def _save_raw_config(config_path: Path, config: dict[str, Any]) -> None:
    """Save raw config to file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w") as f:
        toml.dump(config, f)


def _list_settings(
    console: Console,
    config: dict[str, Any],
    *,
    show_title: bool = True,
) -> None:
    """List all current settings."""
    if show_title:
        console.print("\n[bold]Current settings:[/bold]")

    table = Table(
        show_header=True,
        header_style="bold",
        box=None,
        padding=(0, 2),
    )
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    # Database URL
    db_url = config.get("database", {}).get("url", "sqlite:///bank_importer.db")
    table.add_row("Database URL", db_url)

    # Output directory
    output_dir = config.get("output", {}).get("output_dir", "data/out")
    table.add_row("Output directory", output_dir)

    # Timezone
    timezone = config.get("app", {}).get("timezone", _get_local_timezone())
    table.add_row("Timezone", timezone)

    console.print(table)


def _configure_database_url(console: Console, config: dict[str, Any]) -> None:
    """Configure database URL."""
    current_db_url = config.get("database", {}).get("url", "sqlite:///bank_importer.db")
    db_url = Prompt.ask(
        "Database URL",
        default=current_db_url,
    )
    if "database" not in config:
        config["database"] = {}
    config["database"]["url"] = db_url
    console.print("[green]✓ Database URL updated[/green]")


def _configure_output_dir(console: Console, config: dict[str, Any]) -> None:
    """Configure output directory."""
    current_output_dir = config.get("output", {}).get("output_dir", "data/out")
    output_dir = Prompt.ask(
        "Output directory",
        default=current_output_dir,
    )
    if "output" not in config:
        config["output"] = {}
    config["output"]["output_dir"] = output_dir
    console.print("[green]✓ Output directory updated[/green]")


def _configure_timezone(console: Console, config: dict[str, Any]) -> None:
    """Configure timezone."""
    current_tz = config.get("app", {}).get("timezone", _get_local_timezone())
    timezone = Prompt.ask(
        "Timezone",
        default=current_tz,
    )
    # Validate timezone
    try:
        pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        console.print(
            f"[yellow]Warning: Unknown timezone '{timezone}', using default[/yellow]",
        )
        timezone = _get_local_timezone()

    if "app" not in config:
        config["app"] = {}
    config["app"]["timezone"] = timezone
    console.print("[green]✓ Timezone updated[/green]")


def _configure_settings(console: Console, config: dict[str, Any]) -> None:
    """Configure application settings."""
    while True:
        # Always show settings list first (like rclone config)
        _list_settings(console, config, show_title=True)

        console.print("\n[bold]Settings Configuration:[/bold]")
        console.print("1) Database URL")
        console.print("2) Output directory")
        console.print("3) Timezone")
        console.print("q) Quit to main menu")

        choice = Prompt.ask(
            "\nSelect option",
            choices=["1", "2", "3", "q"],
            default="q",
        )

        if choice == "1":
            _configure_database_url(console, config)
        elif choice == "2":
            _configure_output_dir(console, config)
        elif choice == "3":
            _configure_timezone(console, config)
        elif choice == "q":
            break


def _list_accounts(
    console: Console,
    config: dict[str, Any],
    *,
    show_title: bool = True,
) -> None:
    """List all configured accounts."""
    accounts = config.get("accounts", [])

    if show_title:
        console.print("\n[bold]Current accounts:[/bold]")

    if not accounts:
        console.print("[yellow]No accounts configured[/yellow]")
        return

    table = Table(
        show_header=True,
        header_style="bold",
        box=None,
        padding=(0, 2),
    )
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Parser", style="green")
    table.add_column("File Path", style="yellow")

    for account in accounts:
        if isinstance(account, dict):
            table.add_row(
                account.get("name", "N/A"),
                account.get("parser", "N/A"),
                account.get("file_path", "N/A"),
            )

    console.print(table)


def _create_account(console: Console, config: dict[str, Any]) -> None:
    """Create a new account interactively."""
    console.print("\n[bold cyan]Create New Account[/bold cyan]")

    parser_detector = ParserDetector()
    available_parsers = parser_detector.list_available_parsers()

    name = Prompt.ask("Account name (unique identifier)")
    if not name:
        console.print("[red]Account name is required[/red]")
        return

    # Check if account name already exists
    accounts = config.get("accounts", [])
    for account in accounts:
        if isinstance(account, dict) and account.get("name") == name:
            console.print(f"[red]Account '{name}' already exists[/red]")
            return

    parser = _select_from_list(console, "Select parser", available_parsers)
    if not parser:
        console.print("[red]Parser selection is required[/red]")
        return
    file_pattern = Prompt.ask("File pattern (e.g., *.pdf, *.csv)", default="*.*")
    file_path = Prompt.ask(
        "File path (directory containing statements)",
        default="data/in",
    )
    account_number = Prompt.ask("Account number")
    account_name = Prompt.ask("Account name (display name)")
    bank_name = Prompt.ask("Bank name")
    branch_name = Prompt.ask("Branch name", default="")
    currency = Prompt.ask("Currency code", default="THB")
    country_code = Prompt.ask("Country code", default="TH")
    reference = Prompt.ask("Reference", default=name)

    # Password (optional)
    password_prompt = "Password (for password-protected PDFs, press Enter to skip)"
    try:
        password = getpass.getpass(f"{password_prompt}: ")
    except (KeyboardInterrupt, EOFError):
        password = ""

    new_account: dict[str, Any] = {
        "name": name,
        "parser": parser,
        "file_pattern": file_pattern,
        "file_path": file_path,
        "account_number": account_number,
        "account_name": account_name,
        "bank_name": bank_name,
        "branch_name": branch_name,
        "currency": currency,
        "country_code": country_code,
        "reference": reference,
    }

    if password:
        new_account["password"] = password

    if "accounts" not in config:
        config["accounts"] = []
    config["accounts"].append(new_account)

    console.print(f"[green]✓ Account '{name}' created[/green]")


def _modify_account(console: Console, config: dict[str, Any]) -> None:
    """Modify an existing account."""
    accounts = config.get("accounts", [])
    if not accounts:
        console.print("[yellow]No accounts to modify[/yellow]")
        return

    idx = _select_account_index(console, config, "Select account to modify")
    if idx is None:
        console.print("[red]Invalid account selection[/red]")
        return

    account = accounts[idx]
    if not isinstance(account, dict):
        console.print("[red]Invalid account configuration[/red]")
        return

    console.print(
        f"\n[bold cyan]Modifying account: {account.get('name', 'N/A')}[/bold cyan]",
    )
    console.print("[dim]Press Enter to keep current value[/dim]\n")

    # Allow modifying key fields
    parser_detector = ParserDetector()
    available_parsers = parser_detector.list_available_parsers()

    name = Prompt.ask("Account name", default=account.get("name", ""))
    parser = Prompt.ask(
        "Parser",
        choices=available_parsers,
        default=account.get("parser", ""),
    )
    file_pattern = Prompt.ask(
        "File pattern",
        default=account.get("file_pattern", "*.*"),
    )
    file_path = Prompt.ask("File path", default=account.get("file_path", "data/in"))
    account_number = Prompt.ask(
        "Account number",
        default=account.get("account_number", ""),
    )
    account_name = Prompt.ask(
        "Account name (display)",
        default=account.get("account_name", ""),
    )
    bank_name = Prompt.ask("Bank name", default=account.get("bank_name", ""))
    branch_name = Prompt.ask("Branch name", default=account.get("branch_name", ""))
    currency = Prompt.ask("Currency code", default=account.get("currency", "THB"))
    country_code = Prompt.ask("Country code", default=account.get("country_code", "TH"))
    reference = Prompt.ask("Reference", default=account.get("reference", name))

    # Update account
    account["name"] = name
    account["parser"] = parser
    account["file_pattern"] = file_pattern
    account["file_path"] = file_path
    account["account_number"] = account_number
    account["account_name"] = account_name
    account["bank_name"] = bank_name
    account["branch_name"] = branch_name
    account["currency"] = currency
    account["country_code"] = country_code
    account["reference"] = reference

    # Password update (optional)
    if "password" in account:
        update_password = Confirm.ask("Update password?", default=False)
        if update_password:
            try:
                password = getpass.getpass("Password: ")
            except (KeyboardInterrupt, EOFError):
                password = ""
            if password:
                account["password"] = password

    console.print("[green]✓ Account updated[/green]")


def _delete_account(console: Console, config: dict[str, Any]) -> None:
    """Delete an account."""
    accounts = config.get("accounts", [])
    if not accounts:
        console.print("[yellow]No accounts to delete[/yellow]")
        return

    idx = _select_account_index(console, config, "Select account to delete")
    if idx is None:
        console.print("[red]Invalid account selection[/red]")
        return

    account = accounts[idx]
    account_name = (
        account.get("name", "Unknown") if isinstance(account, dict) else "Unknown"
    )

    if Confirm.ask(f"Delete account '{account_name}'?", default=False):
        accounts.pop(idx)
        console.print(f"[green]✓ Account '{account_name}' deleted[/green]")
    else:
        console.print("[yellow]Deletion cancelled[/yellow]")


def _configure_accounts(console: Console, config: dict[str, Any]) -> None:
    """Configure accounts submenu."""
    while True:
        # Always show accounts list first (like rclone config)
        accounts = config.get("accounts", [])
        _list_accounts(console, config, show_title=True)

        # If no accounts, offer to create one directly
        if not accounts:
            if Confirm.ask("\nNo accounts configured. Create one?", default=True):
                _create_account(console, config)
            else:
                break
            continue

        # Show full menu when accounts exist
        console.print("\n[bold]Accounts Configuration:[/bold]")
        console.print("e) Edit existing account")
        console.print("n) New account")
        console.print("d) Delete account")
        console.print("q) Quit to main menu")

        choice = Prompt.ask(
            "\nSelect option",
            choices=["e", "n", "d", "q"],
            default="q",
        )

        if choice == "e":
            _modify_account(console, config)
        elif choice == "n":
            _create_account(console, config)
        elif choice == "d":
            _delete_account(console, config)
        elif choice == "q":
            break


def _list_targets(
    console: Console,
    config: dict[str, Any],
    *,
    show_title: bool = True,
) -> None:
    """List all configured targets."""
    targets = config.get("targets", [])
    if not targets:
        if show_title:
            console.print("\n[yellow]No targets configured[/yellow]")
        return

    if show_title:
        console.print("\n[bold]Current targets:[/bold]")

    table = Table(
        show_header=True,
        header_style="bold",
        box=None,
        padding=(0, 2),
    )
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Enabled", style="blue")

    for target in targets:
        if isinstance(target, dict):
            enabled = "✓" if target.get("enabled", False) else "✗"
            table.add_row(
                target.get("name", "N/A"),
                target.get("name", "N/A"),  # Type is same as name for now
                enabled,
            )

    console.print(table)


def _create_target(console: Console, config: dict[str, Any]) -> None:
    """Create a new target."""
    console.print("\n[bold cyan]Create New Target[/bold cyan]")

    # Get available targets dynamically (firefly may not be available)
    from bank_importer.library import list_targets

    available_targets = list_targets()
    name = _select_from_list(console, "Select target", available_targets)
    if not name:
        console.print("[red]Target selection is required[/red]")
        return
    enabled = Confirm.ask("Enable this target?", default=True)

    new_target: dict[str, Any] = {
        "name": name,
        "enabled": enabled,
    }

    # Add target-specific config if needed
    if name == "csv":
        console.print(
            "\n[dim]CSV target configuration (press Enter for defaults)[/dim]",
        )
        date_format = Prompt.ask("Date format", default="Y-m-d")
        delimiter = Prompt.ask(
            "Delimiter (comma/semicolon/tab)",
            default="comma",
            choices=["comma", "semicolon", "tab"],
        )
        include_headers = Confirm.ask("Include headers?", default=True)

        new_target["csv_config"] = {
            "date_format": date_format,
            "delimiter": delimiter,
            "include_headers": include_headers,
        }
    elif name == "yaml":
        console.print(
            "\n[dim]YAML target configuration (press Enter for defaults)[/dim]",
        )
        include_summary = Confirm.ask("Include summary?", default=True)
        group_by_month = Confirm.ask("Group by month?", default=True)

        new_target["yaml_config"] = {
            "include_summary": include_summary,
            "group_by_month": group_by_month,
        }

    if "targets" not in config:
        config["targets"] = []
    config["targets"].append(new_target)

    console.print(f"[green]✓ Target '{name}' created[/green]")


def _modify_target(console: Console, config: dict[str, Any]) -> None:
    """Modify an existing target."""
    targets = config.get("targets", [])
    if not targets:
        console.print("[yellow]No targets to modify[/yellow]")
        return

    idx = _select_target_index(console, config, "Select target to modify")
    if idx is None:
        console.print("[red]Invalid target selection[/red]")
        return

    target = targets[idx]
    if not isinstance(target, dict):
        console.print("[red]Invalid target configuration[/red]")
        return

    console.print(
        f"\n[bold cyan]Modifying target: {target.get('name', 'N/A')}[/bold cyan]",
    )

    enabled = Confirm.ask("Enable this target?", default=target.get("enabled", False))
    target["enabled"] = enabled

    console.print("[green]✓ Target updated[/green]")


def _delete_target(console: Console, config: dict[str, Any]) -> None:
    """Delete a target."""
    targets = config.get("targets", [])
    if not targets:
        console.print("[yellow]No targets to delete[/yellow]")
        return

    idx = _select_target_index(console, config, "Select target to delete")
    if idx is None:
        console.print("[red]Invalid target selection[/red]")
        return

    target = targets[idx]
    target_name = (
        target.get("name", "Unknown") if isinstance(target, dict) else "Unknown"
    )

    if Confirm.ask(f"Delete target '{target_name}'?", default=False):
        targets.pop(idx)
        console.print(f"[green]✓ Target '{target_name}' deleted[/green]")
    else:
        console.print("[yellow]Deletion cancelled[/yellow]")


def _configure_targets(console: Console, config: dict[str, Any]) -> None:
    """Configure targets submenu."""
    while True:
        # Always show targets list first (like rclone config)
        targets = config.get("targets", [])
        _list_targets(console, config, show_title=True)

        # If no targets, offer to create one directly
        if not targets:
            if Confirm.ask("\nNo targets configured. Create one?", default=True):
                _create_target(console, config)
            else:
                break
            continue

        # Show full menu when targets exist
        console.print("\n[bold]Targets Configuration:[/bold]")
        console.print("e) Edit existing target")
        console.print("n) New target")
        console.print("d) Delete target")
        console.print("q) Quit to main menu")

        choice = Prompt.ask(
            "\nSelect option",
            choices=["e", "n", "d", "q"],
            default="q",
        )

        if choice == "e":
            _modify_target(console, config)
        elif choice == "n":
            _create_target(console, config)
        elif choice == "d":
            _delete_target(console, config)
        elif choice == "q":
            break


@cli_error_handler
def configure(
    config_file: str = CONFIG_FILE_PARAM,
) -> None:
    """**Configure** the application interactively."""
    console = get_console()
    config_path = Path(config_file)

    # Check if config exists
    if not config_path.exists():
        console.print("[yellow]There is no configuration yet.[/yellow]")
        if not Confirm.ask("Create a new one?", default=True):
            console.print("[yellow]Configuration cancelled[/yellow]")
            return
        # Initialize with default config (without accounts) and save immediately
        config = _get_default_config()
        _save_raw_config(config_path, config)
        console.print(f"[green]Created default configuration at {config_file}[/green]")
        console.print(
            "[dim]You can now configure accounts and customize settings.[/dim]",
        )
    else:
        # Load existing config
        config = _load_raw_config(config_path)
        console.print(f"[green]Loaded configuration from {config_file}[/green]")

    # Main menu loop
    while True:
        # Show current configuration status (like rclone config)
        _list_accounts(console, config, show_title=True)
        _list_targets(console, config, show_title=True)

        console.print("\n[bold]Configuration Options:[/bold]")
        console.print("1) Settings (database_url, output_dir, timezone)")
        console.print("2) Accounts")
        console.print("3) Targets")
        console.print("s) Save and exit")
        console.print("q) Quit without saving")

        choice = Prompt.ask(
            "\nSelect option",
            choices=["1", "2", "3", "s", "q"],
            default="s",
        )

        if choice == "1":
            _configure_settings(console, config)
        elif choice == "2":
            _configure_accounts(console, config)
        elif choice == "3":
            _configure_targets(console, config)
        elif choice == "s":
            _save_raw_config(config_path, config)
            log_success(f"Configuration saved to {config_file}")
            break
        elif choice == "q" and Confirm.ask(
            "Quit without saving? All changes will be lost.",
            default=False,
        ):
            console.print("[yellow]Exiting without saving[/yellow]")
            break
            # Continue loop if user cancels
