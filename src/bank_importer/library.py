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

"""Public library API for bank-importer.

This module provides a clean, consistent API for parsing, importing, and exporting
bank transactions that can be used by CLI, API, and direct library usage.

The library API is designed to be:
- Simple: Easy to use functions for common operations
- Consistent: Same functions work across CLI, API, and library usage
- Flexible: Supports both pure parsing (no side effects) and full import/export workflows
"""

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bank_importer.config import ConfigManager
    from bank_importer.models.database import DatabaseManager
    from bank_importer.models.transaction import Transaction
    from bank_importer.translation_service import TranslationService
else:
    from bank_importer.config import ConfigManager  # noqa: TC001
from bank_importer.interfaces.parser import Parser
from bank_importer.interfaces.target import Target, TargetResult
from bank_importer.models.enums import Language, get_language_en, get_language_th
from bank_importer.models.transaction import Transaction
from bank_importer.parser_detector import ParserDetector
from bank_importer.telemetry import trace_function, trace_span

# Translation service import (optional dependency)
_translation_service_func: Any | None = None
try:
    from bank_importer.translation_service import (
        get_translation_service as _get_translation_service_func,
    )

    _translation_service_func = _get_translation_service_func
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False


# ============================================================================
# PARSING FUNCTIONS (Pure functions, no side effects)
# ============================================================================


def detect_parser(
    file_path: Path | str,
    parent_folder_hint: str | None = None,
) -> str | None:
    """Detect the best parser for a given file.

    This is a pure function that only analyzes the file and returns a parser name.
    No side effects, no database operations.

    Args:
        file_path: Path to the file to analyze
        parent_folder_hint: Optional hint from parent folder name (e.g., "SCB", "Krungsri")

    Returns:
        Name of the best parser, or None if no parser can handle the file

    Example:
        >>> parser_name = detect_parser(Path("statement.pdf"))
        >>> if parser_name:
        ...     transactions = parse_file(Path("statement.pdf"), parser_name, account_config)

    """
    file_path = Path(file_path)
    detector = ParserDetector()
    return detector.detect_parser(file_path, parent_folder_hint)


def get_parser(parser_name: str) -> Parser | None:
    """Get a parser instance by name.

    Args:
        parser_name: Name of the parser (e.g., "krungsri_pdf", "generic_csv")

    Returns:
        Parser instance or None if not found

    Example:
        >>> parser = get_parser("krungsri_pdf")
        >>> if parser:
        ...     transactions = list(parser.parse_file(file_path, account_config))

    """
    detector = ParserDetector()
    return detector.get_parser(parser_name)


def list_parsers() -> list[str]:
    """List all available parser names.

    Returns:
        List of parser names

    Example:
        >>> parsers = list_parsers()
        >>> print(f"Available parsers: {', '.join(parsers)}")

    """
    detector = ParserDetector()
    return detector.list_available_parsers()


def parse_file(
    file_path: Path | str,
    parser_name: str | None = None,
    account_config: dict[str, Any] | None = None,
    config_manager: "ConfigManager | None" = None,
    *,
    auto_detect: bool = True,
) -> Iterator[Transaction]:
    """Parse a bank statement file and yield transactions.

    This is a pure function that only parses the file and returns transactions.
    No side effects, no database operations, no file writes.

    Args:
        file_path: Path to the file to parse
        parser_name: Name of the parser to use. If None and auto_detect=True, will auto-detect
        account_config: Account configuration dictionary with fields like:
            - name: Account name
            - account_number: Account number
            - account_name: Display name
            - bank_name: Bank name
            - currency: Currency code (e.g., "THB")
            - country_code: Country code (e.g., "TH")
            - password: Optional password for password-protected PDFs
        config_manager: Optional ConfigManager instance for parser-specific config
        auto_detect: If True and parser_name is None, auto-detect the parser

    Yields:
        Transaction objects

    Raises:
        ValueError: If parser cannot be determined or file cannot be parsed

    Example:
        >>> account_config = {
        ...     "name": "my_account",
        ...     "account_number": "1234567890",
        ...     "account_name": "My Account",
        ...     "bank_name": "Krungsri",
        ...     "currency": "THB",
        ...     "country_code": "TH",
        ... }
        >>> transactions = list(parse_file("statement.pdf", "krungsri_pdf", account_config))
        >>> print(f"Parsed {len(transactions)} transactions")

    """
    file_path = Path(file_path)

    # Auto-detect parser if not provided
    if parser_name is None and auto_detect:
        parser_name = detect_parser(file_path)
        if parser_name is None:
            msg = f"Could not detect parser for file: {file_path}"
            raise ValueError(msg)

    if parser_name is None:
        msg = "parser_name is required when auto_detect=False"
        raise ValueError(msg)

    # Get parser instance
    parser = get_parser(parser_name)
    if parser is None:
        msg = f"Parser '{parser_name}' not found"
        raise ValueError(msg)

    # Validate parser can handle this file
    if not parser.can_parse(file_path):
        msg = f"Parser '{parser_name}' cannot parse file: {file_path}"
        raise ValueError(msg)

    # Use default account config if not provided
    if account_config is None:
        account_config = {
            "name": parser.get_default_account_name(),
            "account_number": parser.get_default_account_number(),
            "account_name": parser.get_default_account_name(),
            "bank_name": parser.get_bank_type(),
            "currency": parser.get_default_currency(),
            "country_code": parser.get_default_country_code(),
        }

    # Parse file and yield transactions
    yield from parser.parse_file(file_path, account_config, config_manager)


# ============================================================================
# IMPORT FUNCTIONS (With database side effects)
# ============================================================================


def _ensure_managers(
    config_manager: "ConfigManager | None",
    db_manager: "DatabaseManager | None",
) -> tuple["ConfigManager", "DatabaseManager"]:
    """Ensure config and database managers are available."""
    from bank_importer.models.database import DatabaseManager

    if db_manager is None:
        if config_manager is None:
            msg = "Either db_manager or config_manager must be provided"
            raise ValueError(msg)
        db_manager = DatabaseManager(config_manager.get_database_url())

    if config_manager is None:
        from bank_importer.config import ConfigManager

        config_manager = ConfigManager()

    return config_manager, db_manager


def _create_import_session(
    file_path: Path,
    account_config: dict[str, Any] | None,
    db_manager: "DatabaseManager",
) -> int | None:
    """Create import session and return session_id or None if failed."""
    from datetime import UTC, datetime

    from bank_importer.models.enums import ImportStatus
    from bank_importer.models.import_session import ImportSession

    import_session = ImportSession(
        account_name=account_config.get("name", "unknown")
        if account_config
        else "unknown",
        bank_name=account_config.get("bank_name", "unknown")
        if account_config
        else "unknown",
        session_name=_generate_session_name(file_path),
        file_path=str(file_path),
        file_hash=_calculate_file_hash(file_path),
        status=ImportStatus.PROCESSING.value,
        started_at=datetime.now(UTC),
    )

    try:
        return db_manager.create_import_session(import_session)
    except ValueError:
        return None


def _parse_file_with_error_handling(
    file_path: Path,
    parser_name: str | None,
    account_config: dict[str, Any] | None,
    config_manager: "ConfigManager",
    db_manager: "DatabaseManager",
    session_id: int | None,
    *,
    auto_detect: bool,
) -> list[Transaction] | None:
    """Parse file and return transactions list, or None if parsing failed."""
    from datetime import UTC, datetime

    from bank_importer.models.enums import ImportStatus

    try:
        return list(
            parse_file(
                file_path,
                parser_name=parser_name,
                account_config=account_config,
                config_manager=config_manager,
                auto_detect=auto_detect,
            ),
        )
    except Exception as e:
        if session_id is not None:
            error_message = str(e)
            db_manager.update_import_session(
                session_id,
                status=ImportStatus.FAILED.value,
                error_count=1,
                error_message=error_message,
                completed_at=datetime.now(UTC),
            )
        return None


def _process_transactions(
    transactions_list: list[Transaction],
    db_manager: "DatabaseManager",
    session_id: int,
    config_manager: "ConfigManager | None",
    account_config: dict[str, Any] | None,
    *,
    translate: bool,
) -> tuple[list[Transaction], list[Transaction]]:
    """Process and store transactions, returning new and skipped lists."""
    with trace_span(
        "process_transactions",
        {"transaction_count": len(transactions_list), "translate": translate},
    ):
        new_transactions = []
        skipped_transactions = []
        translation_service = None

        if translate and config_manager:
            translation_service = _get_translation_service(
                config_manager,
                account_config,
            )

        for transaction in transactions_list:
            # Translate if enabled
            if translate and translation_service and account_config:
                _translate_transaction(transaction, account_config, translation_service)

            # Store in database
            _, is_new = db_manager.add_transaction(transaction)

            if is_new:
                new_transactions.append(transaction)
            else:
                skipped_transactions.append(transaction)

            # Update import session progress
            total_processed = len(new_transactions) + len(skipped_transactions)
            db_manager.update_import_session(
                session_id,
                processed_transactions=total_processed,
            )

        return new_transactions, skipped_transactions


@trace_function(attributes={"operation": "import_file"})  # type: ignore[misc]
def import_file(
    file_path: Path | str,
    parser_name: str | None = None,
    account_config: dict[str, Any] | None = None,
    config_manager: "ConfigManager | None" = None,
    db_manager: "DatabaseManager | None" = None,
    *,
    auto_detect: bool = True,
    reprocess_existing: bool = False,
    translate: bool = True,
) -> dict[str, Any]:
    """Import a bank statement file: parse it and store transactions in the database.

    This function combines parsing with database storage. It:
    1. Parses the file to extract transactions
    2. Optionally translates transaction descriptions
    3. Stores transactions in the database
    4. Tracks import sessions

    Args:
        file_path: Path to the file to import
        parser_name: Name of the parser to use. If None and auto_detect=True, will auto-detect
        account_config: Account configuration dictionary
        config_manager: ConfigManager instance (required for translation)
        db_manager: DatabaseManager instance (required for storage)
        auto_detect: If True and parser_name is None, auto-detect the parser
        reprocess_existing: If True, reprocess files that have already been imported
        translate: If True, translate transaction descriptions if translation is enabled

    Returns:
        Dictionary with import results:
            - transactions: List of new Transaction objects
            - skipped: List of skipped (duplicate) Transaction objects
            - session_id: Import session ID
            - total_processed: Total number of transactions processed
            - error_count: Number of errors encountered

    Raises:
        ValueError: If required parameters are missing or file cannot be parsed

    Example:
        >>> from bank_importer import ConfigManager, DatabaseManager
        >>> config = ConfigManager("config.toml")
        >>> db = DatabaseManager(config.get_database_url())
        >>> account_config = config.get_account_config("my_account")
        >>> result = import_file("statement.pdf", account_config=account_config,
        ...                      config_manager=config, db_manager=db)
        >>> print(f"Imported {len(result['transactions'])} new transactions")

    """
    from datetime import UTC, datetime

    from bank_importer.models.enums import ImportStatus

    file_path = Path(file_path)

    # Validate required parameters
    config_manager, db_manager = _ensure_managers(config_manager, db_manager)

    # Check if file has been imported (unless reprocessing)
    if not reprocess_existing:
        if db_manager.has_source_file_been_imported(str(file_path)):
            return {
                "transactions": [],
                "skipped": [],
                "session_id": None,
                "total_processed": 0,
                "error_count": 0,
                "message": f"File {file_path} already imported (use reprocess_existing=True to override)",
            }

    # Create import session BEFORE parsing (so we can track failures)
    session_id = _create_import_session(file_path, account_config, db_manager)
    if session_id is None:
        return {
            "transactions": [],
            "skipped": [],
            "session_id": None,
            "total_processed": 0,
            "error_count": 0,
            "message": "File already processed or being processed",
        }

    # Parse the file (with error handling to mark session as failed)
    transactions_list = _parse_file_with_error_handling(
        file_path,
        parser_name,
        account_config,
        config_manager,
        db_manager,
        session_id,
        auto_detect=auto_detect,
    )

    if transactions_list is None:
        return {
            "transactions": [],
            "skipped": [],
            "session_id": session_id,
            "total_processed": 0,
            "error_count": 1,
            "message": "Parsing failed",
        }

    if not transactions_list:
        # Mark as completed but with no transactions
        db_manager.update_import_session(
            session_id,
            status=ImportStatus.COMPLETED.value,
            total_transactions=0,
            processed_transactions=0,
            completed_at=datetime.now(UTC),
        )
        return {
            "transactions": [],
            "skipped": [],
            "session_id": session_id,
            "total_processed": 0,
            "error_count": 0,
            "message": f"No transactions found in {file_path}",
        }

    # Translate and store transactions
    new_transactions, skipped_transactions = _process_transactions(
        transactions_list,
        db_manager,
        session_id,
        config_manager,
        account_config,
        translate=translate,
    )

    # Determine session status
    total_transactions = len(new_transactions) + len(skipped_transactions)
    if len(new_transactions) == 0 and len(skipped_transactions) > 0:
        status = ImportStatus.SKIPPED.value
    else:
        status = ImportStatus.COMPLETED.value

    # Mark import session as completed
    db_manager.update_import_session(
        session_id,
        status=status,
        total_transactions=total_transactions,
        processed_transactions=total_transactions,
        completed_at=datetime.now(UTC),
    )

    return {
        "transactions": new_transactions,
        "skipped": skipped_transactions,
        "session_id": session_id,
        "total_processed": total_transactions,
        "error_count": 0,
    }


# ============================================================================
# EXPORT FUNCTIONS (With file system side effects)
# ============================================================================


def export_transactions(
    transactions: list[Transaction],
    target_name: str,
    output_dir: Path | str | None = None,
    account_config: dict[str, Any] | None = None,
    config_manager: "ConfigManager | None" = None,
) -> TargetResult:
    """Export transactions to a target format (CSV, YAML, etc.).

    This function exports transactions to a file without database operations.
    It's a pure export function that takes transactions and writes them to a file.

    Args:
        transactions: List of Transaction objects to export
        target_name: Name of the target (e.g., "csv", "yaml", "firefly")
        output_dir: Output directory for the export file. If None, uses config default
        account_config: Optional account configuration for export settings
        config_manager: Optional ConfigManager instance for export configuration

    Returns:
        TargetResult with export results

    Raises:
        ValueError: If target is not found or export fails

    Example:
        >>> transactions = list(parse_file("statement.pdf", "krungsri_pdf", account_config))
        >>> result = export_transactions(transactions, "csv", output_dir="exports/")
        >>> print(f"Exported {result.exported_count} transactions to {result.output_file}")

    """
    from bank_importer.targets.csv_target import CsvTarget
    from bank_importer.targets.yaml_target import YamlTarget

    # Try to import firefly target (optional dependency)
    try:
        from bank_importer.targets.firefly_target import FireflyTarget

        FIREFLY_AVAILABLE = True
    except ImportError:
        FIREFLY_AVAILABLE = False

    file_path = Path(output_dir) if output_dir else None

    # Get target instance
    target_map: dict[str, type[Target]] = {
        "csv": CsvTarget,
        "yaml": YamlTarget,
    }

    # Add firefly target only if available
    if FIREFLY_AVAILABLE:
        target_map["firefly"] = FireflyTarget

    target_class = target_map.get(target_name)
    if target_class is None:
        msg = f"Target '{target_name}' not found. Available targets: {', '.join(target_map.keys())}"
        raise ValueError(msg)

    # Create target instance
    if file_path:
        target = target_class(output_dir=str(file_path))  # type: ignore[call-arg]
    else:
        # Use default output directory
        default_output = "data/out"
        if config_manager:
            default_output = config_manager.config.get("output", {}).get(
                "output_dir",
                default_output,
            )
        target = target_class(output_dir=default_output)  # type: ignore[call-arg]

    # Prepare export config
    export_config: dict[str, Any] = {}
    if account_config:
        export_config["account_config"] = account_config
    if config_manager:
        # Merge target-specific config from config_manager
        targets_config = config_manager.config.get("targets", [])
        for target_config in targets_config:
            if target_config.get("name") == target_name:
                export_config.update(target_config.get(f"{target_name}_config", {}))

    # Export transactions
    # result is already a TargetResult, just return it
    return target.export_transactions(transactions, export_config)


def list_targets() -> list[str]:
    """List all available target names.

    Returns:
        List of target names (only includes targets with dependencies installed)

    Example:
        >>> targets = list_targets()
        >>> print(f"Available targets: {', '.join(targets)}")

    """
    targets = ["csv", "yaml"]

    # Check if firefly target is available
    try:
        from bank_importer.targets.firefly_target import FireflyTarget

        targets.append("firefly")
    except ImportError:
        # Firefly target not available (firefly dependency group not installed)
        pass

    return targets


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _generate_session_name(file_path: Path) -> str:
    """Generate a session name from file path."""
    DATE_PART_LENGTH = 8  # YYYYMMDD format
    filename = file_path.stem
    if "_" in filename:
        # Extract date part (e.g., "20250721" from "20250721_krungsri_jochemvangrondelle")
        date_part = filename.split("_")[0]
        if len(date_part) == DATE_PART_LENGTH and date_part.isdigit():
            # Convert YYYYMMDD to YYYY-MM format
            year = date_part[:4]
            month = date_part[4:6]
            return f"{year}-{month}"

    # Fallback to filename
    return filename


def _calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file content."""
    import hashlib

    hash_sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def get_translation_service_from_config(
    config_manager: "ConfigManager",
    account_config: dict[str, Any] | None = None,
) -> Any | None:
    """Get translation service from configuration.

    This is a public library function that API and CLI should use instead of
    directly importing from translation_service.

    Args:
        config_manager: ConfigManager instance
        account_config: Optional account configuration

    Returns:
        TranslationService instance or None if translation is not available or disabled

    Raises:
        ImportError: If translation dependencies are not installed

    """
    if not TRANSLATION_AVAILABLE:
        msg = (
            "Translation service not available. Install with: uv sync --group translate"
        )
        raise ImportError(
            msg,
        )

    try:
        # Get global translation settings
        global_config = config_manager.config.get("translation", {})
        api_key = global_config.get("google_translate_api_key")
        source_language = global_config.get("default_source_language", "th")
        target_language = global_config.get("default_target_language", "en")

        # Check if translation is enabled for this account
        if account_config:
            translation_config = account_config.get("translation", {})
            if not translation_config.get("enabled", False):
                return None

        # Use lowercase for the term mappings key
        term_mappings_key = f"{source_language.lower()}_{target_language.lower()}"
        term_mappings = global_config.get("term_mappings", {}).get(
            term_mappings_key,
            {},
        )

        if _translation_service_func is None:
            msg = "Translation service not available. Install with: uv sync --group translate"
            raise ImportError(
                msg,
            )
        return _translation_service_func(
            api_key=api_key,
            source_language=source_language,
            target_language=target_language,
            term_mappings=term_mappings,
        )
    except Exception:
        return None


def translate_text(
    text: str,
    *,
    api_key: str | None = None,
    source_language: Language | None = None,
    target_language: Language | None = None,
    term_mappings: dict[str, str] | None = None,
) -> str:
    """Translate text using the translation service.

    This is a public library function that API and CLI should use instead of
    directly importing from translation_service.

    Args:
        text: Text to translate
        api_key: Optional Google Translate API key
        source_language: Source language code (default: "th")
        target_language: Target language code (default: "en")
        term_mappings: Optional term mappings dictionary

    Returns:
        Translated text

    Raises:
        ImportError: If translation dependencies are not installed

    """
    if not TRANSLATION_AVAILABLE:
        msg = (
            "Translation service not available. Install with: uv sync --group translate"
        )
        raise ImportError(
            msg,
        )

    if _translation_service_func is None:
        msg = (
            "Translation service not available. Install with: uv sync --group translate"
        )
        raise ImportError(
            msg,
        )
    service = _translation_service_func(
        api_key=api_key,
        source_language=source_language or get_language_th(),
        target_language=target_language or get_language_en(),
        term_mappings=term_mappings,
    )
    result = service.translate_description(text)
    return str(result) if result else text


def _get_translation_service(
    config_manager: "ConfigManager",
    account_config: dict[str, Any] | None = None,
) -> Any | None:
    """Get translation service if enabled (internal use only)."""
    if not TRANSLATION_AVAILABLE:
        return None

    try:
        # Get global translation settings
        global_config = config_manager.config.get("translation", {})
        api_key = global_config.get("google_translate_api_key")
        source_language = global_config.get("default_source_language", "th")
        target_language = global_config.get("default_target_language", "en")

        # Check if translation is enabled for this account
        if account_config:
            translation_config = account_config.get("translation", {})
            if not translation_config.get("enabled", False):
                return None

        # Use lowercase for the term mappings key
        term_mappings_key = f"{source_language.lower()}_{target_language.lower()}"
        term_mappings = global_config.get("term_mappings", {}).get(
            term_mappings_key,
            {},
        )

        if _translation_service_func is None:
            msg = "Translation service not available. Install with: uv sync --group translate"
            raise ImportError(
                msg,
            )
        return _translation_service_func(
            api_key=api_key,
            source_language=source_language,
            target_language=target_language,
            term_mappings=term_mappings,
        )
    except Exception:
        return None


def _translate_transaction(
    transaction: Transaction,
    account_config: dict[str, Any],
    translation_service: "TranslationService",
) -> None:
    """Translate transaction description if translation is enabled."""
    translation_config = account_config.get("translation", {})

    use_term_mapping = translation_config.get("use_term_mapping", True)
    use_api_translation = translation_config.get("use_api_translation", True)

    try:
        translated_description = translation_service.translate_description(
            transaction.description,
            use_term_mapping=use_term_mapping,
            use_api_translation=use_api_translation,
        )

        if translated_description != transaction.description:
            transaction.translated_description = translated_description
    except Exception:
        # Translation failed, keep original description
        pass
