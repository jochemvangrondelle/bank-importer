"""Main processor for bank importer pipeline."""

import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from .banks import KrungsriPdfParser, KrungsriTextParser
from .config import ConfigManager
from .interfaces.parser import Parser
from .models.database import DatabaseManager
from .models.import_session import ImportSession
from .models.transaction import Transaction


class Processor:
    """Main processor for bank importer pipeline."""

    def __init__(self, config_path: Path | None = None):
        """Initialize processor."""
        self.config_manager = ConfigManager(config_path)
        self.db_manager = DatabaseManager(self.config_manager.get_database_url())
        self.logger = logging.getLogger(__name__)
        self.parsers = {
            "krungsri_text": KrungsriTextParser(),
            "krungsri_pdf": KrungsriPdfParser(),
        }

    def identify_pending_import_jobs(self) -> list[dict]:
        """Identify pending import jobs from database."""
        return self.db_manager.get_pending_import_sessions()

    def get_parser(self, parser_name: str) -> Parser | None:
        """Get parser by name."""
        return self.parsers.get(parser_name)

    def _get_parser(self, parser_name: str) -> Parser:
        """Get parser by name, raising error if not found."""
        parser = self.get_parser(parser_name)
        if not parser:
            raise ValueError(f"Unknown parser type: {parser_name}")
        return parser

    def process_accounts(self) -> Iterator[dict]:
        """Process all configured accounts."""
        for account_config in self.config_manager.get_all_accounts():
            yield from self.process_account(account_config["name"])

    def process_account(self, account_name: str) -> Iterator[dict]:
        """Process a single account by name."""
        account_config = self.config_manager.get_account_config(account_name)
        if not account_config:
            self.logger.warning(f"Account '{account_name}' not found")
            return

        parser_name = account_config.get("parser")
        file_path = Path(account_config.get("file_path", "data/raw"))
        file_pattern = account_config.get("file_pattern", "*")

        # Get parser
        if not parser_name:
            self.logger.error(f"No parser specified for account '{account_name}'")
            yield {"account_name": account_name, "error_count": 1, "error_message": "No parser specified"}
            return

        try:
            parser = self._get_parser(parser_name)
        except ValueError as e:
            self.logger.exception("Parser error for account '%s'", account_name)
            yield {"account_name": account_name, "error_count": 1, "error_message": str(e)}
            return

        # Find files to process
        files = list(file_path.glob(file_pattern))
        if not files:
            self.logger.warning(f"No files found for account '{account_name}' in {file_path}")
            yield {"account_name": account_name, "error_count": 1, "error_message": f"No files found in {file_path}"}
            return

        # Process each file
        total_processed = 0
        total_errors = 0

        for file_path in files:
            if not parser.can_parse(file_path):
                self.logger.warning(f"Parser '{parser_name}' cannot parse file: {file_path}")
                total_errors += 1
                continue

            self.logger.info(f"Processing {file_path} for account '{account_name}'")
            try:
                transactions = list(self._process_file(file_path, account_config, parser_name))
                total_processed += len(transactions)
            except Exception:
                self.logger.exception("Error processing file %s", file_path)
                total_errors += 1

        yield {"account_name": account_name, "processed_transactions": total_processed, "error_count": total_errors}

    def _process_file(self, file_path: Path, account_config: dict, parser_name: str) -> list[Transaction]:
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

        session_id = self.db_manager.create_import_session(import_session)
        self.logger.info(f"Created import session {session_id} for {file_path}")

        transactions = []
        try:
            for transaction in parser.parse_file(file_path, account_config):
                # Store transaction in database
                transaction_id = self.db_manager.add_transaction(transaction)
                transactions.append(transaction)
                self.logger.debug(f"Stored transaction {transaction_id}: {transaction.description[:50]}...")

                # Update import session progress
                self.db_manager.update_import_session(session_id, processed_transactions=len(transactions))

        except Exception as e:
            error_message = str(e)
            self.logger.exception(f"Error processing file {file_path}: {error_message}")

            # Update import session with error
            self.db_manager.update_import_session(
                session_id, status="failed", error_count=1, error_message=error_message, completed_at=datetime.now()
            )
            raise

        # Mark import session as completed
        self.db_manager.update_import_session(
            session_id,
            status="completed",
            total_transactions=len(transactions),
            processed_transactions=len(transactions),
            completed_at=datetime.now(),
        )
        self.logger.info(f"Completed import session {session_id}: {len(transactions)} transactions processed")

        return transactions

    def _create_import_session(self, account_config: dict, file_path: Path, session_name: str) -> int:
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
        """Calculate file hash for deduplication."""
        import hashlib

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_unprocessed_transactions(self, target_name: str) -> list:
        """Get transactions not yet processed by target."""
        return self.db_manager.get_unprocessed_transactions(target_name)

    def mark_target_completed(self, transaction_id: int, target_name: str, error_message: str | None = None) -> None:
        """Mark transaction as completed for target."""
        self.db_manager.mark_target_completed(transaction_id, target_name, error_message)
