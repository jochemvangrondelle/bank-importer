"""Common CLI parameters and utilities for reducing code duplication."""

import typer

from .config import ConfigManager
from .logging_config import get_console
from .models.database import DatabaseManager
from .processor import Processor

# Common CLI parameter definitions for reuse
CONFIG_FILE_PARAM = typer.Option(
    "config.toml", "--config", "-c", help="Configuration file path"
)

VERBOSE_PARAM = typer.Option(
    False, "--verbose", "-v", help="**Verbose console output**"
)

DRY_RUN_PARAM = typer.Option(
    False, "--dry-run", "-d", help="**Dry run mode - disable file operations**"
)

FORMAT_PARAM = typer.Option("csv", "--format", "-f", help="Export format (csv, json)")

OUTPUT_PARAM = typer.Option(
    "-", "--output", "-o", help="Output file (use - for stdout)"
)


def get_available_accounts() -> list[str]:
    """Get list of available account names from config."""
    try:
        config_manager = ConfigManager()
        accounts = config_manager.get_all_accounts()
        return [account.get("name", "") for account in accounts if account.get("name")]
    except Exception:
        # Return empty list if config can't be loaded
        return []


def _validate_account(
    ctx: typer.Context, param: typer.CallbackParam, value: str | None
) -> str | None:
    """Validate account parameter and provide suggestions if invalid."""
    if value is None:
        return value

    # Skip validation for help flags and other special values
    if value.startswith("--"):
        return value

    available_accounts = get_available_accounts()

    if value not in available_accounts:
        # Get the console for rich output
        console = get_console()

        console.print(f"\n❌ Invalid account: '{value}'", style="red")
        console.print("\n📋 Available accounts:", style="yellow")

        if available_accounts:
            for account in available_accounts:
                console.print(f"  • {account}", style="cyan")
        else:
            console.print("  No accounts configured in config.toml", style="dim")

        console.print(
            f"\n💡 Usage: {ctx.command_path} --account <account_name>", style="blue"
        )
        console.print(
            "💡 Run 'bank-importer-th list-accounts' to see all accounts", style="blue"
        )

        raise typer.BadParameter(f"Invalid account: '{value}'")

    return value


def _autocomplete_accounts(
    ctx: typer.Context, args: list[str], incomplete: str
) -> list[str]:
    """Autocomplete function for account names."""
    available_accounts = get_available_accounts()
    return [account for account in available_accounts if account.startswith(incomplete)]


ACCOUNT_PARAM = typer.Option(
    None,
    "--account",
    "-a",
    help="Process specific account only",
    callback=_validate_account,
    autocompletion=_autocomplete_accounts,
)

TARGET_PARAM = typer.Option(None, "--target", "-t", help="Target name for export")

FORCE_PARAM = typer.Option(False, "--force", "-f", help="Overwrite existing files")

PATH_PARAM = typer.Option(
    "data/", "--path", "-p", help="Path to import files (default: data/)"
)

LIMIT_PARAM = typer.Option(
    10000, "--limit", help="Maximum number of transactions to process"
)

REPROCESS_EXISTING_PARAM = typer.Option(
    False,
    "--reprocess-existing",
    help="Reprocess files that have already been exported",
)


class LazyDependencies:
    """Lazy loading container for common CLI dependencies."""

    def __init__(self):
        self._processor: Processor | None = None
        self._db_manager: DatabaseManager | None = None

    @property
    def processor(self) -> Processor:
        """Get processor instance (lazy loaded)."""
        if self._processor is None:
            self._processor = Processor()
        return self._processor

    @property
    def db_manager(self) -> DatabaseManager:
        """Get database manager instance (lazy loaded)."""
        if self._db_manager is None:
            processor = self.processor
            self._db_manager = processor.db_manager
        return self._db_manager


# Global lazy dependencies instance
lazy_deps = LazyDependencies()


def get_processor() -> Processor:
    """Get processor instance (lazy loaded)."""
    return lazy_deps.processor


def get_db_manager() -> DatabaseManager:
    """Get database manager instance (lazy loaded)."""
    return lazy_deps.db_manager
