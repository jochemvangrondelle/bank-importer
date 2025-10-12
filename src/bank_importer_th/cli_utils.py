"""CLI utilities for centralized error handling and configuration loading."""

import sys
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from .config import ConfigManager
from .logging_config import log_error
from .models.database import DatabaseManager

F = TypeVar("F", bound=Callable[..., Any])


def cli_error_handler(func: F) -> F:
    """Simple error handler for CLI commands.

    This decorator provides minimal error handling - just logs the error
    and exits with code 1. The actual error message comes from the exception's __str__.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the error (exception __str__ provides the message)
            log_error(str(e))
            sys.exit(1)

    return cast(F, wrapper)


def load_cli_config(config_file: str) -> tuple[ConfigManager, DatabaseManager]:
    """Load configuration for CLI commands.

    Args:
        config_file: Path to the configuration file

    Returns:
        Tuple of (ConfigManager, DatabaseManager) for use in CLI commands
    """
    from pathlib import Path

    config_manager = ConfigManager(Path(config_file))
    db_manager = DatabaseManager(config_manager.get_database_url())
    return config_manager, db_manager


class CLIContext:
    """Context manager for CLI operations with dependency injection.

    This class provides a centralized way to manage CLI dependencies
    and ensures proper initialization and cleanup.
    """

    def __init__(self, config_file: str = "config.toml"):
        """Initialize CLI context.

        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self._config_manager: ConfigManager | None = None
        self._db_manager: DatabaseManager | None = None

    def __repr__(self) -> str:
        """String representation of CLIContext."""
        return f"CLIContext(config_file='{self.config_file}')"

    def __enter__(self) -> "CLIContext":
        """Enter the CLI context and load configuration."""
        if self._config_manager is None or self._db_manager is None:
            self._config_manager, self._db_manager = load_cli_config(self.config_file)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the CLI context."""
        # Cleanup if needed
        pass

    def get_config_manager(self) -> ConfigManager:
        """Get the configuration manager (lazy loaded)."""
        if self._config_manager is None:
            self._config_manager, self._db_manager = load_cli_config(self.config_file)
        return self._config_manager

    def get_db_manager(self) -> DatabaseManager:
        """Get the database manager (lazy loaded)."""
        if self._db_manager is None:
            self._config_manager, self._db_manager = load_cli_config(self.config_file)
        return self._db_manager
