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

"""Main processor for bank importer pipeline."""

import hashlib
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bank_importer.translation_service import TranslationService

from bank_importer.config import ConfigManager
from bank_importer.interfaces.parser import Parser
from bank_importer.interfaces.target import TargetResult
from bank_importer.models.database import DatabaseManager
from bank_importer.models.import_session import ImportSession
from bank_importer.models.transaction import Transaction
from bank_importer.parser_detector import ParserDetector
from bank_importer.target_manager import TargetManager
from bank_importer.translation_service import get_translation_service

# Constants for filename parsing
DATE_PART_LENGTH = 8  # YYYYMMDD format


class Processor:
    """Main processor for bank importer pipeline."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize processor."""
        self.config_manager = ConfigManager(config_path)
        self.db_manager = DatabaseManager(self.config_manager.get_database_url())
        self.target_manager = TargetManager(self.config_manager, self.db_manager)
        self.logger = logging.getLogger(__name__)
        self.parser_detector = ParserDetector()
        # Initialize translation service once
        self.translation_service: TranslationService | None = None
        self._init_translation_service()

    def identify_pending_import_jobs(self) -> list[dict[str, Any]]:
        """Identify pending import jobs from database."""
        return self.db_manager.get_pending_import_sessions()

    def get_parser(self, parser_name: str) -> Parser | None:
        """Get parser by name."""
        return self.parser_detector.get_parser(parser_name)

    def _get_parser(self, parser_name: str | None) -> Parser:
        """Get parser by name, raising error if not found."""
        if not parser_name:
            msg = "Parser name is required"
            raise ValueError(msg)
        parser = self.get_parser(parser_name)
        if not parser:
            msg = f"Unknown parser type: {parser_name}"
            raise ValueError(msg)
        return parser

    def process_accounts(self) -> Iterator[dict[str, Any]]:
        """Process all configured accounts."""
        for account_config in self.config_manager.get_all_accounts():
            yield from self.process_account(account_config["name"])

    def process_account(
        self,
        account_name: str,
        *,
        reprocess_existing: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """Process a single account by name.

        This method uses the library import_file function internally for consistency.
        """
        account_config = self.config_manager.get_account_config(account_name)
        if not account_config:
            msg = "Account not found"
            raise ValueError(msg)

        parser_name = account_config.get("parser")
        file_path = Path(account_config.get("file_path", "data/in"))
        file_pattern = account_config.get("file_pattern", "*")

        # Get parser - use parser detection if no parser specified
        if not parser_name:
            self.logger.warning(
                "No parser specified for account '%s', will use auto-detection",
                account_name,
            )

        try:
            if parser_name:
                self._get_parser(parser_name)
            # else: Will be detected per file
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
                "No files found for account '%s' in %s",
                account_name,
                file_path,
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
                    file_path,
                    parent_folder,
                )

                if not detected_parser_name:
                    self.logger.error("Could not detect parser for file: %s", file_path)
                    total_errors += 1
                    continue

                self.logger.info(
                    "Detected parser '%s' for file: %s",
                    detected_parser_name,
                    file_path,
                )

            # Get the parser instance
            try:
                file_parser = self._get_parser(detected_parser_name)
            except ValueError as e:
                self.logger.exception(
                    "Parser '%s' not found: %s",
                    detected_parser_name,
                    e,
                )
                total_errors += 1
                continue

            # Validate parser can handle this file
            if not file_parser.can_parse(file_path):
                self.logger.warning(
                    "Parser '%s' cannot parse file: %s",
                    detected_parser_name,
                    file_path,
                )
                total_errors += 1
                continue

            # Check if file has been imported or exported (unless reprocessing is requested)
            if not reprocess_existing:
                if self.db_manager.has_source_file_been_imported(str(file_path)):
                    self.logger.info(
                        "Skipping %s - already imported (use --reprocess-existing to override)",
                        file_path,
                    )
                    total_skipped += 1
                    continue
                elif self.db_manager.has_source_file_been_exported(str(file_path)):
                    self.logger.info(
                        "Skipping %s - already exported (use --reprocess-existing to override)",
                        file_path,
                    )
                    total_skipped += 1
                    continue

            self.logger.info(
                "Processing %s for account '%s' with parser '%s'",
                file_path,
                account_name,
                detected_parser_name,
            )
            try:
                transactions = self._process_file(
                    file_path,
                    account_config,
                    detected_parser_name,  # type: ignore[arg-type]
                    reprocess_existing=reprocess_existing,
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
        self,
        file_path: Path,
        account_config: dict[str, Any],
        parser_name: str,
        *,
        reprocess_existing: bool = False,
    ) -> list[Transaction]:
        """Process a single file with the given parser.

        This method uses the library import_file function internally for consistency.
        """
        from bank_importer.library import import_file

        # Use library function for consistency
        result = import_file(
            file_path=file_path,
            parser_name=parser_name,
            account_config=account_config,
            config_manager=self.config_manager,
            db_manager=self.db_manager,
            auto_detect=False,
            reprocess_existing=reprocess_existing,
            translate=True,
        )

        # Return new transactions (not skipped ones)
        transactions = result.get("transactions", [])
        if not isinstance(transactions, list):
            return []
        # Type assertion: result["transactions"] should be list[Transaction]
        return [t for t in transactions if isinstance(t, Transaction)]

    def _init_translation_service(self) -> None:
        """Initialize translation service once for the processor."""
        try:
            # Get global translation settings
            global_config = self.config_manager.config.get("translation", {})
            api_key = global_config.get("google_translate_api_key")
            source_language = global_config.get("default_source_language", "th")
            target_language = global_config.get("default_target_language", "en")

            # Use lowercase for the term mappings key
            term_mappings_key = f"{source_language.lower()}_{target_language.lower()}"
            term_mappings = global_config.get("term_mappings", {}).get(
                term_mappings_key,
                {},
            )

            self.translation_service = get_translation_service(
                api_key=api_key,
                source_language=source_language,
                target_language=target_language,
                term_mappings=term_mappings,
            )

        except (ImportError, Exception) as e:
            self.logger.debug("Translation service not available: %s", e)
            self.translation_service = None

    def _translate_transaction_description(
        self,
        transaction: Transaction,
        account_config: dict[str, Any],
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
                    "Translated: '%s...' -> '%s...'",
                    transaction.description[:30],
                    translated_description[:30],
                )

        except Exception as e:
            # Translation service failed, keep original description
            self.logger.debug(
                "Translation failed for '%s...': %s",
                transaction.description[:50],
                e,
            )

    def _create_import_session(
        self,
        account_config: dict[str, Any],
        file_path: Path,
        session_name: str,
    ) -> int:
        """Create an import session and return its ID."""
        import_session = ImportSession(
            account_name=account_config.get("name", "unknown"),
            bank_name=account_config.get("bank_name", "unknown"),
            session_name=session_name,
            file_path=str(file_path),
            file_hash=self._calculate_file_hash(file_path),
            status="pending",
            started_at=datetime.now(UTC),
        )
        return self.db_manager.create_import_session(import_session)

    def _update_import_session(self, session_id: int, **kwargs: object) -> None:
        """Update import session fields."""
        self.db_manager.update_import_session(session_id, **kwargs)

    def _generate_session_name(self, file_path: Path) -> str:
        """Generate a session name from file path."""
        # Try to extract date from filename
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

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content."""
        hash_sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def get_unprocessed_transactions(self, target_name: str) -> list[dict[str, Any]]:
        """Get transactions not yet processed by target."""
        return self.db_manager.get_unprocessed_transactions(target_name)

    def mark_target_completed(
        self,
        transaction_id: int,
        target_name: str,
        error_message: str | None = None,
    ) -> None:
        """Mark transaction as completed for target."""
        self.db_manager.mark_target_completed(
            transaction_id,
            target_name,
            error_message,
        )

    def sync_to_target(
        self,
        target_name: str,
        account_reference: str | None = None,
    ) -> TargetResult:
        """Sync transactions to a specific target."""
        return self.target_manager.sync_to_target(target_name, account_reference)

    def sync_all_targets(
        self,
        account_reference: str | None = None,
    ) -> dict[str, TargetResult]:
        """Sync transactions to all enabled targets."""
        return self.target_manager.sync_all_targets(account_reference)

    def get_export_sessions(
        self,
        target_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get export sessions."""
        return self.db_manager.get_export_sessions(target_name)
