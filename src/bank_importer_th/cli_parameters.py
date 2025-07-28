"""Common CLI parameters and utilities for reducing code duplication."""


import typer

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

ACCOUNT_PARAM = typer.Option(
    None, "--account", "-a", help="Process specific account only"
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
