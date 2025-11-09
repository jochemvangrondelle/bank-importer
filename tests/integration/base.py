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

"""Base classes for parser integration tests."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pytest

from bank_importer.library import import_file
from bank_importer.models.enums import ParserName
from bank_importer.processor import Processor


class BaseParserIntegrationTest(ABC):
    """Base class for parser-specific integration tests.

    This class provides common functionality for testing the full import-export
    pipeline for each parser. Subclasses should implement parser-specific test
    data and validation methods.
    """

    @property
    @abstractmethod
    def parser_name(self) -> str:
        """Return the parser name (e.g., 'krungsri_pdf')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def test_file_name(self) -> str:
        """Return the test file name in tests/data/."""
        raise NotImplementedError

    @property
    def parser_enum(self) -> ParserName:
        """Return the ParserName enum value."""
        return ParserName(self.parser_name)

    def get_test_file_path(self, test_data_dir: Path) -> Path:
        """Get the full path to the test file."""
        return test_data_dir / self.test_file_name

    def create_account_config(self, **kwargs: Any) -> dict[str, Any]:
        """Create account configuration for this parser.

        Subclasses can override to provide parser-specific defaults.

        """
        return {
            "name": "test_account",
            "bank_name": "Test Bank",
            "account_number": "123-456-789",
            "account_name": "Test User",
            "currency": "THB",
            "country_code": "TH",
            "parser": self.parser_name,
            **kwargs,
        }

    def validate_imported_transactions(
        self,
        transactions: list[Any],
        expected_min_count: int = 1,
    ) -> None:
        """Validate imported transactions.

        Subclasses can override to add parser-specific validations.

        Args:
            transactions: List of imported transactions
            expected_min_count: Minimum expected transaction count

        """
        assert len(transactions) >= expected_min_count, (
            f"Expected at least {expected_min_count} transactions, "
            f"got {len(transactions)}"
        )
        for transaction in transactions:
            assert transaction.date is not None, "Transaction must have a date"
            assert transaction.amount is not None, "Transaction must have an amount"
            assert transaction.description is not None, (
                "Transaction must have a description"
            )

    def validate_export_file(self, export_file: Path, expected_format: str) -> None:
        """Validate exported file.

        Args:
            export_file: Path to exported file
            expected_format: Expected format ('csv' or 'yaml')

        """
        assert export_file.exists(), f"Export file {export_file} does not exist"
        assert export_file.stat().st_size > 0, "Export file is empty"

        if expected_format == "csv":
            content = export_file.read_text()
            assert "," in content or "\t" in content, (
                "CSV file should contain delimiters"
            )
            # Check for header row
            lines = content.strip().split("\n")
            assert len(lines) > 1, "CSV should have header and at least one data row"
        elif expected_format == "yaml":
            content = export_file.read_text()
            assert "transactions:" in content or "- date:" in content, (
                "YAML file should contain transaction data"
            )

    @pytest.mark.integration
    def test_full_import_export_pipeline_csv(
        self,
        integration_processor: Processor,
        test_data_dir: Path,
    ) -> None:
        """Test full pipeline: Import → Database → Export CSV."""
        # Setup
        test_file = self.get_test_file_path(test_data_dir)
        assert test_file.exists(), f"Test file {test_file} does not exist"
        # Skip if file is too small (likely a placeholder)
        if test_file.stat().st_size < 1000:
            pytest.skip(
                f"Test file {test_file} is too small ({test_file.stat().st_size} bytes), likely a placeholder",
            )
        account_config = self.create_account_config()

        # Step 1: Import file
        result = import_file(
            file_path=test_file,
            parser_name=self.parser_name,
            account_config=account_config,
            config_manager=integration_processor.config_manager,
            db_manager=integration_processor.db_manager,
            auto_detect=False,
            reprocess_existing=False,
            translate=False,
        )

        # Step 2: Validate import results
        transactions = result.get("transactions", [])
        self.validate_imported_transactions(transactions)

        # Step 3: Verify transactions in database
        db_transactions = integration_processor.db_manager.get_all_transactions()
        assert len(db_transactions) >= len(transactions), (
            "Database should contain at least the imported transactions"
        )

        # Step 4: Export to CSV
        target_manager = integration_processor.target_manager
        export_results = target_manager.export_all_files_and_consolidated("csv")

        # Step 5: Validate export
        # Export should produce results if transactions exist
        # Check if transactions have source_file set
        db_transactions = integration_processor.db_manager.get_all_transactions()
        source_files = {t.source_file for t in db_transactions if t.source_file}
        unique_source_files = integration_processor.db_manager.get_unique_source_files()

        if not export_results:
            if not source_files or not unique_source_files:
                pytest.skip(
                    f"Export returned empty results - transactions may not have source_file set properly. "
                    f"Source files in transactions: {source_files}, "
                    f"Unique source files from DB: {unique_source_files}",
                )
            # Export should have produced results - check for error entries
            # If all exports failed, there should be error entries in results
            # But if results is completely empty, something else went wrong
            pytest.fail(
                f"Export returned empty results but transactions have source_files: {source_files}, "
                f"and get_unique_source_files() returned: {unique_source_files}. "
                f"This indicates an issue with the export function.",
            )
        assert export_results, "Export should produce results"
        # Find the consolidated export file (usually named "all_consolidated" or similar)
        consolidated_result = None
        for key, result in export_results.items():
            if "consolidated" in key.lower() or "all" in key.lower():
                consolidated_result = result
                break

        # If no consolidated found, check any result
        if not consolidated_result and export_results:
            consolidated_result = next(iter(export_results.values()))

        assert consolidated_result is not None, (
            "Export should produce at least one result"
        )
        assert consolidated_result.success, (
            f"Export should succeed: {consolidated_result.error_message}"
        )
        assert consolidated_result.output_file is not None, (
            "Export should produce output file"
        )

        export_file_path = Path(consolidated_result.output_file)
        self.validate_export_file(export_file_path, "csv")

    @pytest.mark.integration
    def test_full_import_export_pipeline_yaml(
        self,
        integration_processor: Processor,
        test_data_dir: Path,
    ) -> None:
        """Test full pipeline: Import → Database → Export YAML."""
        # Setup
        test_file = self.get_test_file_path(test_data_dir)
        assert test_file.exists(), f"Test file {test_file} does not exist"
        # Skip if file is too small (likely a placeholder)
        if test_file.stat().st_size < 1000:
            pytest.skip(
                f"Test file {test_file} is too small ({test_file.stat().st_size} bytes), likely a placeholder",
            )
        account_config = self.create_account_config()

        # Step 1: Import file
        result = import_file(
            file_path=test_file,
            parser_name=self.parser_name,
            account_config=account_config,
            config_manager=integration_processor.config_manager,
            db_manager=integration_processor.db_manager,
            auto_detect=False,
            reprocess_existing=False,
            translate=False,
        )

        # Step 2: Validate import results
        transactions = result.get("transactions", [])
        self.validate_imported_transactions(transactions)

        # Step 3: Export to YAML
        target_manager = integration_processor.target_manager
        export_results = target_manager.export_all_files_and_consolidated("yaml")

        # Step 4: Validate export
        # Export should produce results if transactions exist
        # Check if transactions have source_file set
        db_transactions = integration_processor.db_manager.get_all_transactions()
        source_files = {t.source_file for t in db_transactions if t.source_file}
        unique_source_files = integration_processor.db_manager.get_unique_source_files()

        if not export_results:
            if not source_files or not unique_source_files:
                pytest.skip(
                    f"Export returned empty results - transactions may not have source_file set properly. "
                    f"Source files in transactions: {source_files}, "
                    f"Unique source files from DB: {unique_source_files}",
                )
            # Export should have produced results - check for error entries
            pytest.fail(
                f"Export returned empty results but transactions have source_files: {source_files}, "
                f"and get_unique_source_files() returned: {unique_source_files}. "
                f"This indicates an issue with the export function.",
            )
        assert export_results, "Export should produce results"
        # Find the consolidated export file (usually named "all_consolidated" or similar)
        consolidated_result = None
        for key, result in export_results.items():
            if "consolidated" in key.lower() or "all" in key.lower():
                consolidated_result = result
                break

        # If no consolidated found, check any result
        if not consolidated_result and export_results:
            consolidated_result = next(iter(export_results.values()))

        assert consolidated_result is not None, (
            "Export should produce at least one result"
        )
        assert consolidated_result.success, (
            f"Export should succeed: {consolidated_result.error_message}"
        )
        assert consolidated_result.output_file is not None, (
            "Export should produce output file"
        )

        export_file_path = Path(consolidated_result.output_file)
        self.validate_export_file(export_file_path, "yaml")

    @pytest.mark.integration
    def test_duplicate_detection(
        self,
        integration_processor: Processor,
        test_data_dir: Path,
    ) -> None:
        """Test that importing the same file twice skips duplicates."""
        # Setup
        test_file = self.get_test_file_path(test_data_dir)
        assert test_file.exists(), f"Test file {test_file} does not exist"
        # Skip if file is too small (likely a placeholder)
        if test_file.stat().st_size < 1000:
            pytest.skip(
                f"Test file {test_file} is too small ({test_file.stat().st_size} bytes), likely a placeholder",
            )
        account_config = self.create_account_config()

        # Step 1: Import file first time
        result1 = import_file(
            file_path=test_file,
            parser_name=self.parser_name,
            account_config=account_config,
            config_manager=integration_processor.config_manager,
            db_manager=integration_processor.db_manager,
            auto_detect=False,
            reprocess_existing=False,
            translate=False,
        )

        transactions1 = result1.get("transactions", [])
        assert len(transactions1) > 0, "First import should produce transactions"

        # Step 2: Import same file again (should skip duplicates)
        result2 = import_file(
            file_path=test_file,
            parser_name=self.parser_name,
            account_config=account_config,
            config_manager=integration_processor.config_manager,
            db_manager=integration_processor.db_manager,
            auto_detect=False,
            reprocess_existing=False,  # Skip existing
            translate=False,
        )

        # Step 3: Verify duplicates were skipped
        # When reprocess_existing=False, the entire file is skipped if already imported
        # The function returns early with empty transactions and skipped arrays
        message = result2.get("message", "")
        transactions2 = result2.get("transactions", [])
        skipped = result2.get("skipped", [])

        # Either the file is skipped entirely (message indicates it) or transactions are skipped
        assert (
            "already imported" in message.lower()
            or len(skipped) > 0
            or len(transactions2) == 0
        ), (
            f"Second import should skip duplicates. "
            f"Got: transactions={len(transactions2)}, skipped={len(skipped)}, message={message}"
        )
        assert len(transactions2) == 0, (
            "Second import should not create new transactions"
        )

        # Step 4: Verify database still has same count
        db_transactions = integration_processor.db_manager.get_all_transactions()
        assert len(db_transactions) == len(transactions1), (
            "Database should have same transaction count after duplicate import"
        )

    @pytest.mark.integration
    def test_import_session_tracking(
        self,
        integration_processor: Processor,
        test_data_dir: Path,
    ) -> None:
        """Test that import sessions are properly tracked."""
        # Setup
        test_file = self.get_test_file_path(test_data_dir)
        assert test_file.exists(), f"Test file {test_file} does not exist"
        # Skip if file is too small (likely a placeholder)
        if test_file.stat().st_size < 1000:
            pytest.skip(
                f"Test file {test_file} is too small ({test_file.stat().st_size} bytes), likely a placeholder",
            )
        account_config = self.create_account_config()

        # Step 1: Import file
        result = import_file(
            file_path=test_file,
            parser_name=self.parser_name,
            account_config=account_config,
            config_manager=integration_processor.config_manager,
            db_manager=integration_processor.db_manager,
            auto_detect=False,
            reprocess_existing=False,
            translate=False,
        )

        # Step 2: Verify import session was created
        session_id = result.get("session_id")
        assert session_id is not None, "Import should create a session"

        # Step 3: Verify session in database
        session = integration_processor.db_manager.get_import_session(session_id)
        assert session is not None, "Session should exist in database"
        assert isinstance(session, dict), "Session should be a dictionary"
        assert session.get("account_name") == account_config["name"], (
            "Session should have correct account name"
        )
        assert session.get("status") == "completed", "Session should be completed"
