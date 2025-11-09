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

"""Logging configuration for CLI applications with Rich formatting."""

import logging
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from bank_importer.models.enums import LogLevel
from bank_importer.models.function_models import LoggingConfig

# Rich imports are optional and only loaded when actually needed (CLI mode)
# This allows API/library code to use logging_config without requiring Rich
_RICH_AVAILABLE: bool = False
_RichHandler: Any = None
_Console: Any = None
_Theme: Any = None
_Traceback: Any = None
_install: Any = None


def _ensure_rich_available() -> None:
    """Ensure Rich is available, raise ImportError if not."""
    global _RICH_AVAILABLE, _RichHandler, _Console, _Theme, _Traceback, _install
    if _RICH_AVAILABLE:
        return

    try:
        from rich.console import Console as _ConsoleType
        from rich.logging import (
            RichHandler as _RichHandlerType,
        )
        from rich.theme import Theme as _ThemeType
        from rich.traceback import (
            Traceback as _TracebackType,
        )
        from rich.traceback import install as _install_func

        _Console = _ConsoleType
        _RichHandler = _RichHandlerType
        _Theme = _ThemeType
        _Traceback = _TracebackType
        _install = _install_func
        _RICH_AVAILABLE = True
    except ImportError as e:
        msg = (
            "Rich is required for CLI logging features. Install with: pip install rich"
        )
        raise ImportError(
            msg,
        ) from e


# Type hints for type checkers
if TYPE_CHECKING:
    from rich.console import Console

# Constants for secret masking
MIN_VALUE_LENGTH_FOR_PARTIAL_MASK = 8
MASK_PREFIX_LENGTH = 4
MASK_SUFFIX_LENGTH = 4
SIMPLE_PATTERN_GROUPS = 2
URL_PATTERN_GROUPS = 3

# Custom theme for different log levels (only created when Rich is available)
_console = None


def get_console() -> "Console":
    """Get or create the global Rich console instance."""
    global _console
    _ensure_rich_available()
    if _console is None:
        CUSTOM_THEME = _Theme(
            {
                "info": "cyan",
                "warning": "yellow",
                "error": "red",
                "critical": "red bold",
                "debug": "dim",
                "success": "green",
            },
        )
        _console = _Console(theme=CUSTOM_THEME)
    # Type checker knows _console is Console at this point
    from typing import cast

    return cast("Console", _console)


class SecretMaskingFormatter(logging.Formatter):
    """Formatter that automatically masks sensitive information in log messages."""

    # Patterns for sensitive data
    SENSITIVE_PATTERNS: ClassVar[list[str]] = [
        # API keys and tokens
        r'(api_key["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        r'(access_token["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        r'(token["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        r'(app_id["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        r'(secret["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        r'(password["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        r'(key["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        # URLs with tokens
        r"(https?://[^/]+/[^?\s]+[?&][^=]*=)([^&\s]+)",
        # Bearer tokens
        r"(Bearer\s+)([a-zA-Z0-9._-]+)",
        # Authorization headers
        r'(Authorization["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        # Database connection strings
        r"(postgresql://[^:]+:)([^@]+)(@[^/]+)",
        r"(mysql://[^:]+:)([^@]+)(@[^/]+)",
        # Environment variables
        r'(\$[A-Z_]+["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        # Common sensitive field names
        r'(private_key["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        r'(public_key["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        r'(certificate["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
        r'(signature["\']?\s*[:=]\s*["\']?)([^"\s,}]+)',
    ]

    # Compile patterns for efficiency
    COMPILED_PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        re.compile(pattern, re.IGNORECASE) for pattern in SENSITIVE_PATTERNS
    ]

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
    ) -> None:
        """Initialize sensitive data formatter.

        Args:
            fmt: Format string for log messages
            datefmt: Date format string
            style: Format style (% or { or $)

        """
        super().__init__(fmt, datefmt, style)

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with sensitive data masking."""
        # Get the original message
        original_msg = record.getMessage()

        # Mask sensitive data
        masked_msg = self._mask_sensitive_data(original_msg)

        # Create a copy of the record with masked message
        masked_record = logging.LogRecord(
            name=record.name,
            level=record.levelno,
            pathname=record.pathname,
            lineno=record.lineno,
            msg=masked_msg,
            args=(),
            exc_info=record.exc_info,
            func=record.funcName,
        )

        # Copy other attributes
        for attr in [
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
            "exc_text",
            "stack_info",
        ]:
            if hasattr(record, attr):
                setattr(masked_record, attr, getattr(record, attr))

        return super().format(masked_record)

    def _mask_sensitive_data(self, message: str) -> str:
        """Mask sensitive data in the message."""
        if not message:
            return message

        masked_message = message

        # Apply each pattern
        for pattern in self.COMPILED_PATTERNS:
            masked_message = pattern.sub(self._mask_replacement, masked_message)

        return masked_message

    def _mask_replacement(self, match: re.Match[str]) -> str:
        """Replace sensitive data with masked version."""
        groups = match.groups()

        if len(groups) == SIMPLE_PATTERN_GROUPS:
            # Simple key=value pattern
            prefix, value = groups
            masked_value = (
                value[:MASK_PREFIX_LENGTH]
                + "*" * (len(value) - MIN_VALUE_LENGTH_FOR_PARTIAL_MASK)
                + value[-MASK_SUFFIX_LENGTH:]
                if len(value) > MIN_VALUE_LENGTH_FOR_PARTIAL_MASK
                else "*" * len(value)
            )
            return f"{prefix}{masked_value}"

        if len(groups) == URL_PATTERN_GROUPS:
            # URL pattern with username:password@host
            prefix, password, suffix = groups
            masked_password = "*" * len(password)
            return f"{prefix}{masked_password}{suffix}"

        # Fallback: mask the entire match
        return "[MASKED]"


class RichCLIHandler(logging.Handler):
    """Custom Rich handler for CLI applications with filtered output."""

    def __init__(self, console: "Console | None" = None, **kwargs: object) -> None:
        """Initialize Rich CLI handler.

        Args:
            console: Rich console instance to use
            **kwargs: Additional arguments passed to RichHandler

        """
        _ensure_rich_available()
        super().__init__()
        if console is None:
            console = get_console()

        self._rich_handler = _RichHandler(
            console=console,
            show_time=False,  # Don't show timestamps in CLI output
            show_path=False,  # Don't show file paths in CLI output
            markup=True,  # Enable Rich markup
            rich_tracebacks=True,  # Pretty tracebacks
            **kwargs,
        )

    def emit(self, record: logging.LogRecord) -> None:
        """Filter console output to show only important messages."""
        # Always show ERROR and CRITICAL
        if record.levelno >= logging.ERROR:
            self._rich_handler.emit(record)
            return

        # For WARNING and INFO, only show user-friendly messages
        if record.levelno >= logging.WARNING:
            # Check if this is a user-friendly message (has emoji or specific format)
            if any(
                emoji in record.getMessage()
                for emoji in [
                    "✅",
                    "⚠️",
                    "❌",
                    "i",
                    "🚀",
                    "📋",
                    "💾",
                    "🛑",
                    "📊",
                    "🌐",
                    "👷",
                    "📋",
                ]
            ):
                self._rich_handler.emit(record)
            return

        # For INFO level, only show high-level progress and status messages
        if record.levelno >= logging.INFO:
            message = record.getMessage()
            # Show only important info messages
            if any(
                keyword in message.lower()
                for keyword in [
                    "starting",
                    "completed",
                    "successfully",
                    "failed",
                    "error",
                    "processing",
                    "pushing",
                    "enqueued",
                    "waiting",
                    "cleared",
                    "connection",
                    "authentication",
                    "rate limit",
                    "timeout",
                ]
            ):
                self._rich_handler.emit(record)
            return

        # For DEBUG level, show all debug messages when console level is set to DEBUG
        if record.levelno >= logging.DEBUG:
            # Check if the handler's level allows DEBUG messages
            if self.level <= logging.DEBUG:
                self._rich_handler.emit(record)
            return


class DetailedFileHandler(logging.FileHandler):
    """File handler for detailed logging with full context and secret masking."""

    def __init__(
        self,
        filename: str | Path,
        mode: str = "a",
        encoding: str | None = None,
        *,
        delay: bool = False,
    ) -> None:
        """Initialize detailed file handler.

        Args:
            filename: Path to log file
            mode: File open mode
            encoding: File encoding
            delay: Whether to delay file opening

        """
        super().__init__(filename, mode, encoding, delay)

        # Detailed formatter for file output with secret masking
        formatter = SecretMaskingFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
        )
        self.setFormatter(formatter)


def setup_logging(
    log_level: LogLevel | str | None = None,
    log_file: str | None = None,
    log_dir: str = "./logs",
    *,
    enable_rich: bool = True,
    console_level: LogLevel | str = LogLevel.INFO,
    file_level: LogLevel | str = LogLevel.DEBUG,
) -> logging.Logger:
    """Set up logging configuration for CLI applications.

    Args:
        log_level: Overall logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  If None, reads from LOG_LEVEL environment variable or defaults to INFO
        log_file: Optional log file path. If None, reads from LOG_FILE environment variable
        log_dir: Directory for log files
        enable_rich: Whether to use Rich formatting for console output
        console_level: Console logging level (default: INFO for user-friendly output)
        file_level: File logging level (default: DEBUG for detailed debugging)

    Returns:
        Configured logger instance

    """
    config = LoggingConfig(
        log_level=log_level,
        log_file=log_file,
        log_dir=log_dir,
        enable_rich=enable_rich,
        console_level=console_level,
        file_level=file_level,
    )
    return _setup_logging_impl(config)


def _setup_logging_impl(config: LoggingConfig) -> logging.Logger:
    """Internal implementation of logging setup using LoggingConfig."""
    # Create log directory if it doesn't exist
    log_path = Path(config.log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get log level from environment variable if not provided
    log_level = config.log_level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    # Convert LogLevel enum to string if needed
    if isinstance(log_level, LogLevel):
        log_level = log_level.value

    # Get log file from environment variable if not provided
    log_file = config.log_file
    if log_file is None:
        log_file = os.getenv("LOG_FILE")

    # Get logger
    logger = logging.getLogger("bank_importer")
    logger.setLevel(getattr(logging, str(log_level).upper()))

    # Clear existing handlers - close file handlers first to avoid ResourceWarnings
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        logger.removeHandler(handler)

    # Convert console_level and file_level to strings if they are enums
    console_level_str = (
        config.console_level.value
        if isinstance(config.console_level, LogLevel)
        else config.console_level
    )
    file_level_str = (
        config.file_level.value
        if isinstance(config.file_level, LogLevel)
        else config.file_level
    )

    # Console handler with Rich formatting and filtered output
    if config.enable_rich:
        rich_handler = RichCLIHandler()
        rich_handler.setLevel(getattr(logging, console_level_str.upper()))
        logger.addHandler(rich_handler)
    else:
        # Standard console handler with secret masking
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(getattr(logging, console_level_str.upper()))
        console_formatter = SecretMaskingFormatter("%(levelname)s: %(message)s")
        stream_handler.setFormatter(console_formatter)
        logger.addHandler(stream_handler)

    # File handler for detailed logging with secret masking
    file_path = log_path / log_file if log_file else log_path / "bank_importer.log"

    file_handler = DetailedFileHandler(file_path)
    file_handler.setLevel(
        getattr(logging, file_level_str.upper()),
    )  # File captures everything
    logger.addHandler(file_handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (optional)

    Returns:
        Logger instance

    """
    if name:
        return logging.getLogger(f"bank_importer.{name}")
    return logging.getLogger("bank_importer")


def mask_sensitive_data(data: str) -> str:
    """Mask sensitive data in strings."""
    formatter = SecretMaskingFormatter()
    return formatter._mask_sensitive_data(data)


def log_sensitive_data_safely(
    logger: logging.Logger,
    level: str,
    message: str,
    sensitive_data: dict[str, object] | None = None,
) -> None:
    """Safely log messages that might contain sensitive data.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Base message to log
        sensitive_data: Optional dict of sensitive data to include (will be masked)

    """
    if sensitive_data:
        # Create a safe representation of sensitive data
        safe_data = _mask_sensitive_dict(sensitive_data)
        full_message = f"{message} - Data: {safe_data}"
    else:
        full_message = message

    log_method = getattr(logger, level.lower(), logger.info)
    log_method(full_message)


def _mask_sensitive_dict(data: dict[str, object]) -> dict[str, object]:
    """Recursively mask sensitive data in dictionaries."""
    safe_data: dict[str, object] = {}
    sensitive_keys = {
        "api_key",
        "access_token",
        "token",
        "app_id",
        "secret",
        "password",
        "key",
        "private_key",
        "public_key",
        "certificate",
        "signature",
        "authorization",
        "bearer",
    }

    for key, value in data.items():
        if isinstance(value, dict):
            safe_data[key] = _mask_sensitive_dict(value)
        elif isinstance(value, str):
            # Check if the key contains sensitive information
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                # For sensitive keys, always mask the value
                masked_value = (
                    value[:MASK_PREFIX_LENGTH]
                    + "*" * (len(value) - MIN_VALUE_LENGTH_FOR_PARTIAL_MASK)
                    + value[-MASK_SUFFIX_LENGTH:]
                    if len(value) > MIN_VALUE_LENGTH_FOR_PARTIAL_MASK
                    else "*" * len(value)
                )
                safe_data[key] = masked_value
            else:
                # For non-sensitive keys, only mask if the value contains sensitive patterns
                safe_data[key] = mask_sensitive_data(value)
        elif isinstance(value, list | tuple):
            # Handle lists/tuples by masking sensitive strings within them
            safe_data[key] = [
                mask_sensitive_data(str(item)) if isinstance(item, str) else item
                for item in value
            ]
        else:
            # For other types, convert to string and check for sensitive patterns
            str_value = str(value)
            safe_data[key] = mask_sensitive_data(str_value)

    return safe_data


# Convenience functions for common log messages
def log_success(message: str) -> None:
    """Log a success message."""
    logger = get_logger()
    logger.info("✅ %s", message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    logger = get_logger()
    logger.warning("⚠️  %s", message)


def log_error(message: str) -> None:
    """Log an error message."""
    logger = get_logger()
    logger.error("❌ %s", message)


def log_info(message: str) -> None:
    """Log an info message."""
    logger = get_logger()
    logger.info("i  %s", message)


def log_debug(message: str) -> None:
    """Log a debug message."""
    logger = get_logger()
    logger.debug("🔍 %s", message)


def get_log_file_path() -> str:
    """Get the current log file path."""
    # Get log directory and file from environment or defaults
    log_dir = os.getenv("LOG_DIR", "./logs")
    log_file = os.getenv("LOG_FILE", "bank_importer.log")

    log_path = Path(log_dir)
    file_path = log_path / log_file

    return str(file_path.absolute())


def on_error(error: Exception, message: str = "", exit_code: int = 1) -> None:
    """Standardized error handling with rich traceback and exit.

    Args:
        error: The exception that occurred
        message: Optional additional message to display
        exit_code: Exit code to use (default: 1)

    """
    _ensure_rich_available()
    # Install rich traceback handler
    _install(show_locals=True)

    # Get console for rich output
    console = get_console()

    # Get log file path for reference
    log_file_path = get_log_file_path()

    # Print rich traceback first
    console.print("\n[bold red]Traceback:[/bold red]")
    tb = _Traceback.from_exception(type(error), error, error.__traceback__)
    console.print(tb)

    # Print error header
    console.print("\n[bold red]❌ CRITICAL ERROR[/bold red]")

    if message:
        console.print(f"[red]{message}[/red]")

    # Print the error details
    console.print(f"[red]Error: {error}[/red]")

    # Print log file location
    console.print(f"[yellow]📋 Detailed logs available in: {log_file_path}[/yellow]")

    # Exit with specified code
    sys.exit(exit_code)


def log_progress(current: int, total: int, description: str = "Processing") -> None:
    """Log progress information."""
    logger = get_logger()
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info("📊 %s: %s/%s (%.1f%%)", description, current, total, percentage)


def log_startup() -> None:
    """Log startup information."""
    logger = get_logger()
    logger.info("🚀 Starting Bank Importer")
    logger.info("📋 Loading configuration and initializing components...")


def log_shutdown() -> None:
    """Log shutdown information."""
    logger = get_logger()
    logger.info("🛑 Shutting down Bank Importer")
    logger.info("💾 Saving data and cleaning up...")


def log_database_operation(operation: str, table: str, count: int = 1) -> None:
    """Log database operations."""
    logger = get_logger()
    if count == 1:
        logger.debug("💾 %s 1 record in %s", operation, table)
    else:
        logger.debug("💾 %s %s records in %s", operation, count, table)


def log_api_request(
    provider: str,
    endpoint: str,
    status: str = "success",
    sensitive_data: dict[str, object] | None = None,
) -> None:
    """Log API requests with sensitive data masking."""
    logger = get_logger()

    if status == "success":
        base_message = f"🌐 {provider}: {endpoint} - ✅ Success"
    elif status == "requesting":
        base_message = f"🌐 {provider}: {endpoint} - 🔄 Requesting"
    else:
        base_message = f"🌐 {provider}: {endpoint} - ❌ {status}"

    # Determine log level based on status
    if status == "success":
        log_level = "debug"
    elif status == "requesting":
        log_level = "debug"  # Changed from warning to debug
    else:
        log_level = "warning"

    log_sensitive_data_safely(
        logger,
        log_level,
        base_message,
        sensitive_data,
    )


def log_queue_operation(operation: str, item_id: str, status: str = "pending") -> None:
    """Log queue operations."""
    logger = get_logger()
    logger.debug("📋 Queue %s: %s (%s)", operation, item_id, status)


def log_worker_activity(worker_id: int, action: str, details: str = "") -> None:
    """Log worker activity."""
    logger = get_logger()
    message = f"👷 Worker {worker_id}: {action}"
    if details:
        message += f" - {details}"
    logger.debug(message)


def log_task_progress(
    task_type: str,
    current: int,
    total: int,
    details: str = "",
) -> None:
    """Log task progress with context."""
    logger = get_logger()
    percentage = (current / total) * 100 if total > 0 else 0
    message = f"📋 {task_type}: {current}/{total} ({percentage:.1f}%)"
    if details:
        message += f" - {details}"
    logger.debug(message)


def log_target_operation(
    target_name: str,
    operation: str,
    status: str = "success",
    details: str | dict[str, object] | None = None,
) -> None:
    """Log target operations."""
    logger = get_logger()

    # Define which statuses should be treated as info vs warning
    info_statuses = {"success", "processing", "completed", "ready"}
    warning_statuses = {"failed", "error", "timeout", "retry"}

    if status in info_statuses:
        message = f"🎯 {target_name}: {operation} - ✅ {status.title()}"
    elif status in warning_statuses:
        message = f"🎯 {target_name}: {operation} - ❌ {status.title()}"
    else:
        # Default to info for unknown statuses
        message = f"🎯 {target_name}: {operation} - i {status.title()}"

    if details:
        if isinstance(details, dict):
            # Use the improved masking function
            safe_details = _mask_sensitive_dict(details)
            details_str = f" - {safe_details}"
        else:
            details_str = f" - {details}"
        message += details_str

    if status in warning_statuses:
        logger.warning(message)
    else:
        logger.debug(message)


def log_progress_with_logging(
    task_description: str,
    current: int,
    total: int,
    details: str = "",
    logger_name: str = "progress",
) -> None:
    """Log progress information using the existing logging system.

    This function integrates progress tracking with the existing logging infrastructure
    to ensure consistent formatting and output.

    Args:
        task_description: Description of the task being performed
        current: Current progress value
        total: Total progress value
        details: Additional details about the current operation
        logger_name: Name of the logger to use

    """
    logger = get_logger(logger_name)

    if total > 0:
        percentage = (current / total) * 100
        progress_msg = f"{task_description}: {current}/{total} ({percentage:.1f}%)"
    else:
        progress_msg = f"{task_description}: {current} completed"

    if details:
        progress_msg += f" - {details}"

    logger.info(progress_msg)


def log_configuration_loading(
    config_data: dict[str, object],
    section_name: str = "root",
) -> dict[str, object]:
    """Safely log configuration loading with sensitive data masking."""
    logger = get_logger()

    # Use the improved masking function
    safe_config = _mask_sensitive_dict(config_data)

    # Only log the top-level configuration to avoid duplicates
    if section_name == "root":
        logger.debug("📋 Configuration loaded: %s", safe_config)

    return safe_config
