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

"""Target manager for handling transaction exports."""

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bank_importer.models.transaction import Transaction
    from bank_importer.processor import Processor

from bank_importer.config import ConfigManager
from bank_importer.interfaces.target import Target, TargetResult
from bank_importer.logging_config import get_logger
from bank_importer.models.database import DatabaseManager
from bank_importer.models.enums import ExportStatus
from bank_importer.targets.csv_target import CsvTarget
from bank_importer.targets.yaml_target import YamlTarget

# Try to import firefly target (optional dependency)
try:
    from bank_importer.targets.firefly_target import FireflyTarget

    FIREFLY_AVAILABLE = True
except ImportError:
    FIREFLY_AVAILABLE = False


class TargetManager:
    """Manages transaction exports to different targets."""

    def __init__(
        self,
        config_manager: ConfigManager,
        db_manager: DatabaseManager,
    ) -> None:
        """Initialize target manager.

        Args:
            config_manager: Configuration manager instance
            db_manager: Database manager instance

        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.targets: dict[str, Target] = {}
        self.processor: Processor | None = None  # Will be initialized when needed
        self._initialize_targets()

    def _get_processor(self) -> "Processor":
        """Get or create processor instance."""
        if self.processor is None:
            # Import here to avoid circular dependency
            from bank_importer.processor import Processor

            # Use the same config file path as the config manager
            config_path = self.config_manager.config_path
            self.processor = Processor(config_path)
        return self.processor

    def _initialize_targets(self) -> None:
        """Initialize available targets."""
        # Initialize CSV target
        output_dir = self.config_manager.config.get("output_dir", "data/out")
        self.targets["csv"] = CsvTarget(output_dir=output_dir)

        # Initialize YAML target
        self.targets["yaml"] = YamlTarget(output_dir=output_dir)

        # Initialize Firefly-III target (only if dependency is available)
        if FIREFLY_AVAILABLE:
            self.targets["firefly"] = FireflyTarget(output_dir=output_dir)

    def get_target(self, target_name: str) -> Target | None:
        """Get a target by name."""
        return self.targets.get(target_name)

    def get_available_targets(self) -> list[str]:
        """Get list of available target names."""
        return list(self.targets.keys())

    def _get_bank_type_from_source_file(self, source_file: str) -> str:
        """Extract bank type from source file path using parser metadata."""
        source_path = Path(source_file)

        # Get processor and use parser detector
        processor = self._get_processor()

        # Get parent folder hint for better detection
        parent_folder = source_path.parent.name

        # Use parser detector to find the appropriate parser
        detected_parser_name = processor.parser_detector.detect_parser(
            source_path,
            parent_folder,
        )

        if not detected_parser_name:
            msg = (
                f"No parser can handle file: {source_file}. "
                f"This file should not have been imported in the first place. "
                f"Please check the parser configuration and ensure all files can be parsed by an appropriate parser."
            )
            raise ValueError(
                msg,
            )

        # Get the parser and return its bank type
        parser = processor.get_parser(detected_parser_name)
        if not parser:
            msg = f"Parser '{detected_parser_name}' not found"
            raise ValueError(msg)

        return str(parser.get_bank_type())

    def _get_organized_output_dir(self, bank_type: str, base_output_dir: str) -> Path:
        """Get organized output directory for a bank type."""
        output_dir = Path(base_output_dir)
        organized_dir = output_dir / bank_type
        organized_dir.mkdir(parents=True, exist_ok=True)
        return organized_dir

    def sync_to_target(
        self,
        target_name: str,
        account_reference: str | None = None,
    ) -> TargetResult:
        """Sync unexported transactions to a target.

        Args:
            target_name: Name of the target to sync to
            account_reference: Optional account reference to filter transactions

        Returns:
            TargetResult with sync results

        """
        target = self.get_target(target_name)
        if not target:
            return TargetResult(
                target_name=target_name,
                success=False,
                exported_count=0,
                skipped_count=0,
                error_count=0,
                output_file=None,
                error_message=f"Target '{target_name}' not found",
            )

        # Get unexported transactions
        transactions = self.db_manager.get_unexported_transactions(
            target_name,
            account_reference,
        )

        if not transactions:
            return TargetResult(
                target_name=target_name,
                success=True,
                exported_count=0,
                output_file=None,
                error_message=None,
                skipped_count=0,
                error_count=0,
                metadata={"message": "No unexported transactions found"},
            )

        # Create export session
        session_name = (
            f"export_{target_name}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        )
        if account_reference:
            session_name += f"_{account_reference}"

        export_session_id = self.db_manager.create_export_session(
            session_name,
            target_name,
            account_reference or "all",
        )

        # Get account config for the first transaction (assuming all are from same account)
        account_config = {}
        if transactions and account_reference:
            account_config = (
                self.config_manager.get_account_config(account_reference) or {}
            )

        # Export transactions
        try:
            result = target.export_transactions(transactions, account_config)

            # Mark transactions as exported
            for transaction in transactions:
                self.db_manager.mark_transaction_exported(
                    transaction.id or 0,
                    target_name,
                    export_session_id,
                )

            # Update export session with completion status
            self.db_manager.update_export_session(
                export_session_id,
                status=ExportStatus.COMPLETED.value,
                total_transactions=len(transactions),
                exported_transactions=result.exported_count,
                skipped_transactions=result.skipped_count,
                error_transactions=result.error_count,
                output_file=result.metadata.get("output_file")
                if result.metadata
                else None,
                completed_at=datetime.now(UTC),
            )

            return result

        except Exception as e:
            # Update export session with error status
            self.db_manager.update_export_session(
                export_session_id,
                status=ExportStatus.FAILED.value,
                total_transactions=len(transactions),
                error_transactions=len(transactions),
                error_message=str(e),
                completed_at=datetime.now(UTC),
            )

            return TargetResult(
                target_name=target_name,
                success=False,
                exported_count=0,
                skipped_count=0,
                error_count=len(transactions),
                output_file=None,
                error_message=str(e),
            )

    def sync_all_targets(
        self,
        account_reference: str | None = None,
    ) -> dict[str, TargetResult]:
        """Sync unexported transactions to all targets.

        Args:
            account_reference: Optional account reference to filter transactions

        Returns:
            Dictionary of target results

        """
        results = {}
        for target_name in self.get_available_targets():
            results[target_name] = self.sync_to_target(target_name, account_reference)
        return results

    def _get_account_config_from_source_file(
        self,
        source_file: str,
        transactions: list["Transaction"],
    ) -> dict[str, Any]:
        """Get account configuration for a source file."""
        account_config: dict[str, Any] = {}
        if not transactions:
            return account_config

        source_path = Path(source_file)
        processor = self._get_processor()
        parent_folder = source_path.parent.name

        detected_parser_name = processor.parser_detector.detect_parser(
            source_path,
            parent_folder,
        )

        if detected_parser_name:
            parser = processor.get_parser(detected_parser_name)
            if parser:
                account_config = {
                    "name": parser.get_parser_name(),
                    "bank_name": parser.get_export_config().get(
                        "bank_name",
                        "Unknown Bank",
                    ),
                    "account_name": parser.get_default_account_name(),
                    "account_number": parser.get_default_account_number(),
                    "currency": parser.get_default_currency(),
                    "country_code": parser.get_default_country_code(),
                    "translation": {
                        "enabled": parser.get_export_config().get(
                            "supports_translation",
                            False,
                        ),
                        "source_language": parser.get_export_config().get(
                            "translation_source_language",
                            "en",
                        ),
                        "target_language": parser.get_export_config().get(
                            "translation_target_language",
                            "en",
                        ),
                    },
                }

        if not account_config:
            account_number = transactions[0].account_number
            for acc in self.config_manager.get_all_accounts():
                if acc.get("account_number") == account_number:
                    account_config = acc
                    break

        return account_config

    def _get_account_config_from_transactions(
        self,
        transactions: list["Transaction"],
    ) -> dict[str, Any]:
        """Get account configuration from transactions by account number."""
        account_config: dict[str, Any] = {}
        if not transactions:
            return account_config

        account_number = transactions[0].account_number
        for acc in self.config_manager.get_all_accounts():
            if acc.get("account_number") == account_number:
                account_config = acc
                break

        return account_config

    def _mark_transactions_exported_and_update_session(
        self,
        transactions: list["Transaction"],
        target_name: str,
        export_session_id: int,
        result: TargetResult,
    ) -> None:
        """Mark transactions as exported and update export session."""
        for transaction in transactions:
            self.db_manager.mark_transaction_exported(
                transaction.id or 0,
                target_name,
                export_session_id,
            )

        self.db_manager.update_export_session(
            export_session_id,
            status="completed",
            total_transactions=len(transactions),
            exported_transactions=result.exported_count,
            skipped_transactions=result.skipped_count,
            error_transactions=result.error_count,
            output_file=result.metadata.get("output_file") if result.metadata else None,
            completed_at=datetime.now(UTC),
        )

    def _export_source_file(
        self,
        source_file: str,
        transactions: list["Transaction"],
        target: Target,
        target_name: str,
        base_output_dir: str,
        bank_transactions: dict[str, list["Transaction"]],
        all_transactions: list["Transaction"],
        results: dict[str, TargetResult],
    ) -> None:
        """Export a single source file."""
        logger = get_logger("target_manager")

        try:
            bank_type = self._get_bank_type_from_source_file(source_file)
            organized_dir = self._get_organized_output_dir(
                bank_type,
                base_output_dir,
            )

            logger.info(
                "📄 Processing file: %s (%s transactions)",
                source_file,
                len(transactions),
            )

            if bank_type not in bank_transactions:
                bank_transactions[bank_type] = []
            bank_transactions[bank_type].extend(transactions)
            all_transactions.extend(transactions)

        except ValueError as e:
            logger.exception(
                "❌ Cannot export file %s: %s. "
                "This file should not have been imported in the first place. "
                "Skipping export for this file.",
                source_file,
                e,
            )
            results[f"error_{source_file}"] = TargetResult(
                target_name=target_name,
                success=False,
                exported_count=0,
                skipped_count=0,
                error_count=len(transactions),
                output_file=None,
                error_message=str(e),
            )
            return

        session_name = (
            f"export_{target_name}_source_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        )
        export_session_id = self.db_manager.create_export_session(
            session_name,
            target_name,
            f"source_file_{source_file}",
        )

        source_path = Path(source_file)
        original_filename = source_path.stem
        account_config = self._get_account_config_from_source_file(
            source_file,
            transactions,
        )

        config = {
            "export_type": "source_file",
            "source_file": source_file,
            "account_reference": transactions[0].account_number
            if transactions
            else "unknown",
            "output_dir": str(organized_dir),
            "original_filename": original_filename,
            "account_config": account_config,
        }

        try:
            temp_target = target.__class__(output_dir=str(organized_dir))  # type: ignore[call-arg]
            result = temp_target.export_transactions(transactions, config)

            self._mark_transactions_exported_and_update_session(
                transactions,
                target_name,
                export_session_id,
                result,
            )

            results[f"source_file_{source_file}"] = result

        except Exception as e:
            self.db_manager.update_export_session(
                export_session_id,
                status="failed",
                total_transactions=len(transactions),
                error_transactions=len(transactions),
                error_message=str(e),
                completed_at=datetime.now(UTC),
            )

            results[f"source_file_{source_file}"] = TargetResult(
                target_name=target_name,
                success=False,
                exported_count=0,
                skipped_count=0,
                error_count=len(transactions),
                output_file=None,
                error_message=str(e),
            )

    def _export_consolidated_bank(
        self,
        bank_type: str,
        transactions: list["Transaction"],
        target: Target,
        target_name: str,
        base_output_dir: str,
        results: dict[str, TargetResult],
    ) -> None:
        """Export bank-specific consolidated transactions."""
        organized_dir = self._get_organized_output_dir(
            bank_type,
            base_output_dir,
        )

        session_name = f"export_{target_name}_bank_{bank_type}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        export_session_id = self.db_manager.create_export_session(
            session_name,
            target_name,
            f"bank_{bank_type}",
        )

        account_config = self._get_account_config_from_transactions(transactions)

        config = {
            "export_type": "bank_consolidated",
            "account_reference": f"{bank_type}_all",
            "output_dir": str(organized_dir),
            "bank_type": bank_type,
            "account_config": account_config,
        }

        try:
            temp_target = target.__class__(output_dir=str(organized_dir))  # type: ignore[call-arg]
            result = temp_target.export_transactions(transactions, config)

            self._mark_transactions_exported_and_update_session(
                transactions,
                target_name,
                export_session_id,
                result,
            )

            results[f"bank_{bank_type}"] = result

        except Exception as e:
            self.db_manager.update_export_session(
                export_session_id,
                status="failed",
                total_transactions=len(transactions),
                error_transactions=len(transactions),
                error_message=str(e),
                completed_at=datetime.now(UTC),
            )

            results[f"bank_{bank_type}"] = TargetResult(
                target_name=target_name,
                success=False,
                exported_count=0,
                skipped_count=0,
                error_count=len(transactions),
                output_file=None,
                error_message=str(e),
            )

    def _export_all_transactions(
        self,
        all_transactions: list["Transaction"],
        target: Target,
        target_name: str,
        base_output_dir: str,
        results: dict[str, TargetResult],
    ) -> None:
        """Export all-transactions consolidated file."""
        all_dir = self._get_organized_output_dir("all", base_output_dir)

        session_name = (
            f"export_{target_name}_all_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        )
        export_session_id = self.db_manager.create_export_session(
            session_name,
            target_name,
            "all_transactions",
        )

        account_config = self._get_account_config_from_transactions(all_transactions)

        config = {
            "export_type": "all_consolidated",
            "account_reference": "all_accounts",
            "output_dir": str(all_dir),
            "account_config": account_config,
        }

        try:
            temp_target = target.__class__(output_dir=str(all_dir))  # type: ignore[call-arg]
            result = temp_target.export_transactions(all_transactions, config)

            self._mark_transactions_exported_and_update_session(
                all_transactions,
                target_name,
                export_session_id,
                result,
            )

            results["all_transactions"] = result

        except Exception as e:
            self.db_manager.update_export_session(
                export_session_id,
                status="failed",
                total_transactions=len(all_transactions),
                error_transactions=len(all_transactions),
                error_message=str(e),
                completed_at=datetime.now(UTC),
            )

            results["all_transactions"] = TargetResult(
                target_name=target_name,
                success=False,
                exported_count=0,
                skipped_count=0,
                error_count=len(all_transactions),
                output_file=None,
                error_message=str(e),
            )

    def export_all_files_and_consolidated(
        self,
        target_name: str,
    ) -> dict[str, TargetResult]:
        """Export transactions to a target with organized structure.

        - One file per source file in bank-specific subdirectories
        - One consolidated file with all unique transactions in 'all' directory
        - Summary and import config files in each directory.

        Args:
            target_name: Name of the target to export to

        Returns:
            Dictionary of export results

        """
        target = self.get_target(target_name)
        if not target:
            return {
                "error": TargetResult(
                    target_name=target_name,
                    success=False,
                    exported_count=0,
                    skipped_count=0,
                    error_count=0,
                    output_file=None,
                    error_message=f"Target '{target_name}' not found",
                ),
            }

        results = {}
        base_output_dir = self.config_manager.config.get("output_dir", "data/out")

        source_files = self.db_manager.get_unique_source_files()
        bank_transactions: dict[str, list[Transaction]] = {}
        all_transactions: list[Transaction] = []

        logger = get_logger("target_manager")

        # Export each source file separately
        for source_file in source_files:
            transactions = self.db_manager.get_transactions_by_source_file(source_file)
            if not transactions:
                continue

            if self.db_manager.has_source_file_been_exported(
                source_file,
                target_name,
            ):
                logger.info(
                    "⏭️  Skipping %s - already exported to %s",
                    source_file,
                    target_name,
                )
                results[f"skipped_{source_file}"] = TargetResult(
                    target_name=target_name,
                    success=True,
                    exported_count=0,
                    skipped_count=len(transactions),
                    error_count=0,
                    output_file=None,
                    error_message=None,
                )
                continue

            self._export_source_file(
                source_file,
                transactions,
                target,
                target_name,
                base_output_dir,
                bank_transactions,
                all_transactions,
                results,
            )

        # Export bank-specific consolidated files
        for bank_type, transactions in bank_transactions.items():
            if transactions:
                self._export_consolidated_bank(
                    bank_type,
                    transactions,
                    target,
                    target_name,
                    base_output_dir,
                    results,
                )

        # Export all-transactions consolidated file
        if all_transactions:
            self._export_all_transactions(
                all_transactions,
                target,
                target_name,
                base_output_dir,
                results,
            )

        return results
