"""Target manager for handling transaction exports."""

from datetime import datetime
from pathlib import Path

from .config import ConfigManager
from .interfaces.target import Target, TargetResult
from .logging_config import get_logger
from .models.database import DatabaseManager
from .targets.csv_target import CsvTarget
from .targets.yaml_target import YamlTarget


class TargetManager:
    """Manages transaction exports to different targets."""

    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.targets: dict[str, Target] = {}
        self.processor = None  # Will be initialized when needed
        self._initialize_targets()

    def _get_processor(self):
        """Get or create processor instance."""
        if self.processor is None:
            from .processor import Processor

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
            source_path, parent_folder
        )

        if not detected_parser_name:
            raise ValueError(
                f"No parser can handle file: {source_file}. "
                f"This file should not have been imported in the first place. "
                f"Please check the parser configuration and ensure all files can be parsed by an appropriate parser."
            )

        # Get the parser and return its bank type
        parser = processor.get_parser(detected_parser_name)
        if not parser:
            raise ValueError(f"Parser '{detected_parser_name}' not found")

        return parser.get_bank_type()

    def _get_organized_output_dir(self, bank_type: str, base_output_dir: str) -> Path:
        """Get organized output directory for a bank type."""
        output_dir = Path(base_output_dir)
        organized_dir = output_dir / bank_type
        organized_dir.mkdir(parents=True, exist_ok=True)
        return organized_dir

    def sync_to_target(
        self, target_name: str, account_reference: str | None = None
    ) -> TargetResult:
        """
        Sync unexported transactions to a target.

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
                error_message=f"Target '{target_name}' not found",
            )

        # Get unexported transactions
        transactions = self.db_manager.get_unexported_transactions(
            target_name, account_reference
        )

        if not transactions:
            return TargetResult(
                target_name=target_name,
                success=True,
                exported_count=0,
                skipped_count=0,
                error_count=0,
                metadata={"message": "No unexported transactions found"},
            )

        # Create export session
        session_name = (
            f"export_{target_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        if account_reference:
            session_name += f"_{account_reference}"

        export_session_id = self.db_manager.create_export_session(
            session_name, target_name, account_reference or "all"
        )

        # Get account config for the first transaction (assuming all are from same account)
        account_config = {}
        if transactions and account_reference:
            account_config = (
                self.config_manager.get_account_config(account_reference) or {}
            )

        # Export transactions
        try:
            result_dict = target.export_transactions(transactions, account_config)
            result = TargetResult(**result_dict)

            # Mark transactions as exported
            for transaction in transactions:
                self.db_manager.mark_transaction_exported(
                    transaction.id or 0, target_name, export_session_id
                )

            # Update export session with completion status
            self.db_manager.update_export_session(
                export_session_id,
                status="completed",
                total_transactions=len(transactions),
                exported_transactions=result.exported_count,
                skipped_transactions=result.skipped_count,
                error_transactions=result.error_count,
                output_file=result.metadata.get("output_file")
                if result.metadata
                else None,
                completed_at=datetime.now(),
            )

            return result

        except Exception as e:
            # Update export session with error status
            self.db_manager.update_export_session(
                export_session_id,
                status="failed",
                total_transactions=len(transactions),
                error_transactions=len(transactions),
                error_message=str(e),
                completed_at=datetime.now(),
            )

            return TargetResult(
                target_name=target_name,
                success=False,
                exported_count=0,
                skipped_count=0,
                error_count=len(transactions),
                error_message=str(e),
            )

    def sync_all_targets(
        self, account_reference: str | None = None
    ) -> dict[str, TargetResult]:
        """
        Sync unexported transactions to all targets.

        Args:
            account_reference: Optional account reference to filter transactions

        Returns:
            Dictionary of target results
        """
        results = {}
        for target_name in self.get_available_targets():
            results[target_name] = self.sync_to_target(target_name, account_reference)
        return results

    def export_all_files_and_consolidated(
        self, target_name: str
    ) -> dict[str, TargetResult]:
        """
        Export transactions to a target with organized structure:
        - One file per source file in bank-specific subdirectories
        - One consolidated file with all unique transactions in 'all' directory
        - Summary and import config files in each directory

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
                    error_message=f"Target '{target_name}' not found",
                )
            }

        results = {}
        base_output_dir = self.config_manager.config.get("output_dir", "data/out")

        # Get all unique source files
        source_files = self.db_manager.get_unique_source_files()

        # Group transactions by bank type
        bank_transactions = {}
        all_transactions = []

        # Export each source file separately
        for source_file in source_files:
            transactions = self.db_manager.get_transactions_by_source_file(source_file)
            if transactions:
                # Check if this file has already been exported to this target
                if self.db_manager.has_source_file_been_exported(
                    source_file, target_name
                ):
                    logger = get_logger("target_manager")
                    logger.info(
                        f"⏭️  Skipping {source_file} - already exported to {target_name}"
                    )
                    # Add to results as skipped
                    results[f"skipped_{source_file}"] = TargetResult(
                        target_name=target_name,
                        success=True,
                        exported_count=0,
                        skipped_count=len(transactions),
                        error_count=0,
                        error_message=None,
                    )
                    continue

                try:
                    bank_type = self._get_bank_type_from_source_file(source_file)
                    organized_dir = self._get_organized_output_dir(
                        bank_type, base_output_dir
                    )

                    # Log file processing
                    logger = get_logger("target_manager")
                    logger.info(
                        f"📄 Processing file: {source_file} ({len(transactions)} transactions)"
                    )

                    # Add to bank-specific transactions
                    if bank_type not in bank_transactions:
                        bank_transactions[bank_type] = []
                    bank_transactions[bank_type].extend(transactions)
                    all_transactions.extend(transactions)

                except ValueError as e:
                    # File cannot be parsed by any parser - this is an error
                    logger = get_logger("target_manager")
                    logger.error(
                        f"❌ Cannot export file {source_file}: {e}. "
                        f"This file should not have been imported in the first place. "
                        f"Skipping export for this file."
                    )
                    # Add to results as an error
                    results[f"error_{source_file}"] = TargetResult(
                        target_name=target_name,
                        success=False,
                        exported_count=0,
                        skipped_count=0,
                        error_count=len(transactions),
                        error_message=str(e),
                    )
                    continue

                # Create export session for this source file
                session_name = f"export_{target_name}_source_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                export_session_id = self.db_manager.create_export_session(
                    session_name, target_name, f"source_file_{source_file}"
                )

                # Get original filename for export
                source_path = Path(source_file)
                original_filename = source_path.stem

                # Get account configuration for translation settings
                account_config = {}
                if transactions:
                    # Try to find the parser for this file
                    source_path = Path(source_file)
                    processor = self._get_processor()

                    # Get parent folder hint for better detection
                    parent_folder = source_path.parent.name

                    # Use parser detector to find the appropriate parser
                    detected_parser_name = processor.parser_detector.detect_parser(
                        source_path, parent_folder
                    )

                    if detected_parser_name:
                        parser = processor.get_parser(detected_parser_name)
                        if parser:
                            # Use parser's default configuration
                            account_config = {
                                "name": parser.get_parser_name(),
                                "bank_name": parser.get_export_config().get(
                                    "bank_name", "Unknown Bank"
                                ),
                                "account_name": parser.get_default_account_name(),
                                "account_number": parser.get_default_account_number(),
                                "currency": parser.get_default_currency(),
                                "country_code": parser.get_default_country_code(),
                                "translation": {
                                    "enabled": parser.get_export_config().get(
                                        "supports_translation", False
                                    ),
                                    "source_language": parser.get_export_config().get(
                                        "translation_source_language", "en"
                                    ),
                                    "target_language": parser.get_export_config().get(
                                        "translation_target_language", "en"
                                    ),
                                },
                            }

                    # Fallback to account number matching if parser not found
                    if not account_config:
                        account_number = transactions[0].account_number
                        for acc in self.config_manager.get_all_accounts():
                            if acc.get("account_number") == account_number:
                                account_config = acc
                                break

                # Export transactions for this source file
                config = {
                    "export_type": "source_file",
                    "source_file": source_file,
                    "account_reference": transactions[0].account_number
                    if transactions
                    else "unknown",
                    "output_dir": str(organized_dir),
                    "original_filename": original_filename,
                    "account_config": account_config,  # Include account configuration for translation
                }

                try:
                    # Create a temporary target with the organized directory
                    temp_target = target.__class__(output_dir=str(organized_dir))
                    result_dict = temp_target.export_transactions(transactions, config)
                    result = TargetResult(**result_dict)

                    # Mark transactions as exported
                    for transaction in transactions:
                        self.db_manager.mark_transaction_exported(
                            transaction.id or 0, target_name, export_session_id
                        )

                    # Update export session with completion status
                    self.db_manager.update_export_session(
                        export_session_id,
                        status="completed",
                        total_transactions=len(transactions),
                        exported_transactions=result.exported_count,
                        skipped_transactions=result.skipped_count,
                        error_transactions=result.error_count,
                        output_file=result.metadata.get("output_file")
                        if result.metadata
                        else None,
                        completed_at=datetime.now(),
                    )

                    results[f"source_file_{source_file}"] = result

                except Exception as e:
                    # Update export session with error status
                    self.db_manager.update_export_session(
                        export_session_id,
                        status="failed",
                        total_transactions=len(transactions),
                        error_transactions=len(transactions),
                        error_message=str(e),
                        completed_at=datetime.now(),
                    )

                    error_result = TargetResult(
                        target_name=target_name,
                        success=False,
                        exported_count=0,
                        skipped_count=0,
                        error_count=len(transactions),
                        error_message=str(e),
                    )
                    results[f"source_file_{source_file}"] = error_result

        # Export bank-specific consolidated files
        for bank_type, transactions in bank_transactions.items():
            if transactions:
                organized_dir = self._get_organized_output_dir(
                    bank_type, base_output_dir
                )

                # Create export session for bank-specific consolidated export
                session_name = f"export_{target_name}_bank_{bank_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                export_session_id = self.db_manager.create_export_session(
                    session_name, target_name, f"bank_{bank_type}"
                )

                # Get account configuration for the first transaction in this bank type
                account_config = {}
                if transactions:
                    account_number = transactions[0].account_number
                    # Find the account configuration by account number
                    for acc in self.config_manager.get_all_accounts():
                        if acc.get("account_number") == account_number:
                            account_config = acc
                            break

                # Export bank-specific transactions
                config = {
                    "export_type": "bank_consolidated",
                    "account_reference": f"{bank_type}_all",
                    "output_dir": str(organized_dir),
                    "bank_type": bank_type,
                    "account_config": account_config,  # Include account configuration
                }

                try:
                    # Create a temporary target with the organized directory
                    temp_target = target.__class__(output_dir=str(organized_dir))
                    result_dict = temp_target.export_transactions(transactions, config)
                    result = TargetResult(**result_dict)

                    # Mark transactions as exported
                    for transaction in transactions:
                        self.db_manager.mark_transaction_exported(
                            transaction.id or 0, target_name, export_session_id
                        )

                    # Update export session with completion status
                    self.db_manager.update_export_session(
                        export_session_id,
                        status="completed",
                        total_transactions=len(transactions),
                        exported_transactions=result.exported_count,
                        skipped_transactions=result.skipped_count,
                        error_transactions=result.error_count,
                        output_file=result.metadata.get("output_file")
                        if result.metadata
                        else None,
                        completed_at=datetime.now(),
                    )

                    results[f"bank_{bank_type}"] = result

                except Exception as e:
                    # Update export session with error status
                    self.db_manager.update_export_session(
                        export_session_id,
                        status="failed",
                        total_transactions=len(transactions),
                        error_transactions=len(transactions),
                        error_message=str(e),
                        completed_at=datetime.now(),
                    )

                    error_result = TargetResult(
                        target_name=target_name,
                        success=False,
                        exported_count=0,
                        skipped_count=0,
                        error_count=len(transactions),
                        error_message=str(e),
                    )
                    results[f"bank_{bank_type}"] = error_result

        # Export all-transactions consolidated file
        if all_transactions:
            all_dir = self._get_organized_output_dir("all", base_output_dir)

            # Create export session for all-transactions consolidated export
            session_name = (
                f"export_{target_name}_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            export_session_id = self.db_manager.create_export_session(
                session_name, target_name, "all_transactions"
            )

            # Get account configuration for the first transaction
            account_config = {}
            if all_transactions:
                account_number = all_transactions[0].account_number
                # Find the account configuration by account number
                for acc in self.config_manager.get_all_accounts():
                    if acc.get("account_number") == account_number:
                        account_config = acc
                        break

            # Export all transactions
            config = {
                "export_type": "all_consolidated",
                "account_reference": "all_accounts",
                "output_dir": str(all_dir),
                "account_config": account_config,  # Include account configuration
            }

            try:
                # Create a temporary target with the organized directory
                temp_target = target.__class__(output_dir=str(all_dir))
                result_dict = temp_target.export_transactions(all_transactions, config)
                result = TargetResult(**result_dict)

                # Mark transactions as exported
                for transaction in all_transactions:
                    self.db_manager.mark_transaction_exported(
                        transaction.id or 0, target_name, export_session_id
                    )

                # Update export session with completion status
                self.db_manager.update_export_session(
                    export_session_id,
                    status="completed",
                    total_transactions=len(all_transactions),
                    exported_transactions=result.exported_count,
                    skipped_transactions=result.skipped_count,
                    error_transactions=result.error_count,
                    output_file=result.metadata.get("output_file")
                    if result.metadata
                    else None,
                    completed_at=datetime.now(),
                )

                results["all_transactions"] = result

            except Exception as e:
                # Update export session with error status
                self.db_manager.update_export_session(
                    export_session_id,
                    status="failed",
                    total_transactions=len(all_transactions),
                    error_transactions=len(all_transactions),
                    error_message=str(e),
                    completed_at=datetime.now(),
                )

                error_result = TargetResult(
                    target_name=target_name,
                    success=False,
                    exported_count=0,
                    skipped_count=0,
                    error_count=len(all_transactions),
                    error_message=str(e),
                )
                results["all_transactions"] = error_result

        return results
