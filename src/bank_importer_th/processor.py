"""Main processor for bank importer pipeline."""

import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from .banks import (
    AmexThCsvParser,
    GenericCsvParser,
    GenericFixedWidthParser,
    GenericJsonParser,
    KrungsriPdfParser,
    KrungsriTextParser,
    ScbPdfParser,
)
from .config import ConfigManager
from .interfaces.parser import Parser
from .models.database import DatabaseManager
from .models.import_session import ImportSession
from .models.transaction import Transaction
from .parser_detector import ParserDetector
from .target_manager import TargetManager


class Processor:
    """Main processor for bank importer pipeline."""

    def __init__(self, config_path: Path | None = None):
        """Initialize processor."""
        self.config_manager = ConfigManager(config_path)
        self.db_manager = DatabaseManager(self.config_manager.get_database_url())
        self.target_manager = TargetManager(self.config_manager, self.db_manager)
        self.logger = logging.getLogger(__name__)
        self.parser_detector = ParserDetector()
        # Initialize translation service once
        self.translation_service = None
        self._init_translation_service()

    def identify_pending_import_jobs(self) -> list[dict]:
        """Identify pending import jobs from database."""
        return self.db_manager.get_pending_import_sessions()

    def get_parser(self, parser_name: str) -> Parser | None:
        """Get parser by name."""
        return self.parser_detector.get_parser(parser_name)

    def _get_parser(self, parser_name: str | None) -> Parser:
        """Get parser by name, raising error if not found."""
        if not parser_name:
            raise ValueError("Parser name is required")
        parser = self.get_parser(parser_name)
        if not parser:
            raise ValueError(f"Unknown parser type: {parser_name}")
        return parser

    def process_accounts(self) -> Iterator[dict]:
        """Process all configured accounts."""
        for account_config in self.config_manager.get_all_accounts():
            yield from self.process_account(account_config["name"])

    def process_account(
        self, account_name: str, reprocess_existing: bool = False
    ) -> Iterator[dict]:
        """Process a single account by name."""
        account_config = self.config_manager.get_account_config(account_name)
        if not account_config:
            raise ValueError("Account not found")

        parser_name = account_config.get("parser")
        file_path = Path(account_config.get("file_path", "data/in"))
        file_pattern = account_config.get("file_pattern", "*")

        # Get parser - use parser detection if no parser specified
        if not parser_name:
            self.logger.warning(
                f"No parser specified for account '{account_name}', will use auto-detection"
            )

        try:
            if parser_name:
                parser = self._get_parser(parser_name)
            else:
                parser = None  # Will be detected per file
        except ValueError as e:
            self.logger.exception("Parser error for account '%s'", account_name)
            yield {
                "account_name": account_name,
                "error_count": 1,
                "error_message": str(e),
            }
            return

        # Find files to process
        files = list(file_path.glob(file_pattern))
        if not files:
            self.logger.warning(
                f"No files found for account '{account_name}' in {file_path}"
            )
            yield {
                "account_name": account_name,
                "error_count": 1,
                "error_message": f"No files found in {file_path}",
            }
            return

        # Process each file
        total_processed = 0
        total_errors = 0
        total_skipped = 0

        for file_path in files:
            # Detect parser for this file if not specified
            detected_parser_name = parser_name
            if not parser_name:
                # Get parent folder hint for better detection
                parent_folder = file_path.parent.name
                detected_parser_name = self.parser_detector.detect_parser(
                    file_path, parent_folder
                )

                if not detected_parser_name:
                    self.logger.error(f"Could not detect parser for file: {file_path}")
                    total_errors += 1
                    continue

                self.logger.info(
                    f"Detected parser '{detected_parser_name}' for file: {file_path}"
                )

            # Get the parser instance
            try:
                file_parser = self._get_parser(detected_parser_name)
            except ValueError as e:
                self.logger.error(f"Parser '{detected_parser_name}' not found: {e}")
                total_errors += 1
                continue

            # Validate parser can handle this file
            if not file_parser.can_parse(file_path):
                self.logger.warning(
                    f"Parser '{detected_parser_name}' cannot parse file: {file_path}"
                )
                total_errors += 1
                continue

            # Check if file has been imported or exported (unless reprocessing is requested)
            if not reprocess_existing:
                if self.db_manager.has_source_file_been_imported(str(file_path)):
                    self.logger.info(
                        f"Skipping {file_path} - already imported (use --reprocess-existing to override)"
                    )
                    total_skipped += 1
                    continue
                elif self.db_manager.has_source_file_been_exported(str(file_path)):
                    self.logger.info(
                        f"Skipping {file_path} - already exported (use --reprocess-existing to override)"
                    )
                    total_skipped += 1
                    continue

            self.logger.info(
                f"Processing {file_path} for account '{account_name}' with parser '{detected_parser_name}'"
            )
            try:
                transactions = list(
                    self._process_file(file_path, account_config, detected_parser_name)
                )
                total_processed += len(transactions)
            except Exception:
                self.logger.exception("Error processing file %s", file_path)
                total_errors += 1

        yield {
            "account_name": account_name,
            "processed_transactions": total_processed,
            "error_count": total_errors,
            "skipped_files": total_skipped,
        }

    def _process_file(
        self, file_path: Path, account_config: dict, parser_name: str
    ) -> list[Transaction]:
        """Process a single file with the given parser."""
        parser = self._get_parser(parser_name)

        # Create import session
        import_session = ImportSession(
            account_name=account_config.get("name", "unknown"),
            bank_name=account_config.get("bank_name", "unknown"),
            session_name=self._generate_session_name(file_path),
            file_path=str(file_path),
            file_hash=self._calculate_file_hash(file_path),
            status="processing",
            started_at=datetime.now(),
        )

        try:
            session_id = self.db_manager.create_import_session(import_session)
            self.logger.info(f"Created import session {session_id} for {file_path}")
        except ValueError as e:
            # File already processed or being processed
            self.logger.warning(f"Skipping {file_path}: {e}")
            return []

        transactions = []
        skipped_transactions = []
        try:
            for transaction in parser.parse_file(
                file_path, account_config, self.config_manager
            ):
                # Translate description if translation is enabled for this account
                self._translate_transaction_description(transaction, account_config)

                # Store transaction in database
                transaction_id, is_new = self.db_manager.add_transaction(transaction)

                if is_new:
                    transactions.append(transaction)
                    self.logger.debug(
                        f"Stored new transaction {transaction_id}: {transaction.description[:50]}..."
                    )
                else:
                    skipped_transactions.append(transaction)
                    self.logger.debug(
                        f"Skipped duplicate transaction {transaction_id}: {transaction.description[:50]}..."
                    )

                # Update import session progress
                total_processed = len(transactions) + len(skipped_transactions)
                self.db_manager.update_import_session(
                    session_id, processed_transactions=total_processed
                )

        except Exception as e:
            error_message = str(e)
            self.logger.exception(f"Error processing file {file_path}: {error_message}")

            # Update import session with error
            self.db_manager.update_import_session(
                session_id,
                status="failed",
                error_count=1,
                error_message=error_message,
                completed_at=datetime.now(),
            )
            raise

        # Determine session status based on results
        total_transactions = len(transactions) + len(skipped_transactions)

        if len(transactions) == 0 and len(skipped_transactions) > 0:
            # All transactions were duplicates - mark as skipped
            status = "skipped"
            self.logger.info(
                f"Skipped import session {session_id}: {len(skipped_transactions)} duplicate transactions found"
            )
        else:
            # Some or all transactions were new - mark as completed
            status = "completed"
            self.logger.info(
                f"Completed import session {session_id}: {len(transactions)} new transactions, {len(skipped_transactions)} duplicates"
            )

        # Mark import session as completed or skipped
        self.db_manager.update_import_session(
            session_id,
            status=status,
            total_transactions=total_transactions,
            processed_transactions=total_transactions,
            completed_at=datetime.now(),
        )

        return transactions

    def _init_translation_service(self) -> None:
        """Initialize translation service once for the processor."""
        try:
            from .translation_service import get_translation_service

            # Get global translation settings
            global_config = self.config_manager.config.get("translation", {})
            api_key = global_config.get("google_translate_api_key")
            source_language = global_config.get("default_source_language", "th")
            target_language = global_config.get("default_target_language", "en")

            # Use lowercase for the term mappings key
            term_mappings_key = f"{source_language.lower()}_{target_language.lower()}"
            term_mappings = global_config.get("term_mappings", {}).get(
                term_mappings_key, {}
            )

            self.translation_service = get_translation_service(
                api_key=api_key,
                source_language=source_language,
                target_language=target_language,
                term_mappings=term_mappings,
            )

        except (ImportError, Exception) as e:
            self.logger.debug(f"Translation service not available: {e}")
            self.translation_service = None

    def _translate_transaction_description(
        self, transaction: Transaction, account_config: dict
    ) -> None:
        """Translate transaction description if translation is enabled for this account."""
        # Get account configuration for translation settings
        translation_config = account_config.get("translation", {})

        # Check if translation is enabled for this account
        if not translation_config.get("enabled", False):
            return

        # Check if translation service is available
        if not self.translation_service:
            return

        try:
            # Use account-specific settings or fall back to global settings
            source_language = translation_config.get(
                "source_language",
                self.config_manager.config.get("translation", {}).get(
                    "default_source_language", "th"
                ),
            )
            target_language = translation_config.get(
                "target_language",
                self.config_manager.config.get("translation", {}).get(
                    "default_target_language", "en"
                ),
            )

            use_term_mapping = translation_config.get("use_term_mapping", True)
            use_api_translation = translation_config.get("use_api_translation", True)

            # Translate the description
            translated_description = self.translation_service.translate_description(
                transaction.description,
                use_term_mapping=use_term_mapping,
                use_api_translation=use_api_translation,
            )

            if translated_description != transaction.description:
                transaction.translated_description = translated_description
                # Log successful translation
                self.logger.info(
                    f"Translated: '{transaction.description[:30]}...' -> '{translated_description[:30]}...'"
                )

        except Exception as e:
            # Translation service failed, keep original description
            self.logger.debug(
                f"Translation failed for '{transaction.description[:50]}...': {e}"
            )
            pass

    def _create_import_session(
        self, account_config: dict, file_path: Path, session_name: str
    ) -> int:
        """Create an import session and return its ID."""
        import_session = ImportSession(
            account_name=account_config.get("name", "unknown"),
            bank_name=account_config.get("bank_name", "unknown"),
            session_name=session_name,
            file_path=str(file_path),
            file_hash=self._calculate_file_hash(file_path),
            status="pending",
            started_at=datetime.now(),
        )
        return self.db_manager.create_import_session(import_session)

    def _update_import_session(self, session_id: int, **kwargs) -> None:
        """Update import session fields."""
        self.db_manager.update_import_session(session_id, **kwargs)

    def _generate_session_name(self, file_path: Path) -> str:
        """Generate a session name from file path."""
        # Try to extract date from filename
        filename = file_path.stem
        if "_" in filename:
            # Extract date part (e.g., "20250721" from "20250721_krungsri_jochemvangrondelle")
            date_part = filename.split("_")[0]
            if len(date_part) == 8 and date_part.isdigit():
                # Convert YYYYMMDD to YYYY-MM format
                year = date_part[:4]
                month = date_part[4:6]
                return f"{year}-{month}"

        # Fallback to filename
        return filename

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        import hashlib

        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def get_unprocessed_transactions(self, target_name: str) -> list:
        """Get transactions not yet processed by target."""
        return self.db_manager.get_unprocessed_transactions(target_name)

    def mark_target_completed(
        self, transaction_id: int, target_name: str, error_message: str | None = None
    ) -> None:
        """Mark transaction as completed for target."""
        self.db_manager.mark_target_completed(
            transaction_id, target_name, error_message
        )

    def sync_to_target(self, target_name: str, account_reference: str | None = None):
        """Sync transactions to a specific target."""
        return self.target_manager.sync_to_target(target_name, account_reference)

    def sync_all_targets(self, account_reference: str | None = None):
        """Sync transactions to all enabled targets."""
        return self.target_manager.sync_all_targets(account_reference)

    def get_export_sessions(self, target_name: str | None = None):
        """Get export sessions."""
        return self.db_manager.get_export_sessions(target_name)
