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

"""Parser interface for bank statements."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bank_importer.models.transaction import Transaction

if TYPE_CHECKING:
    from bank_importer.config import ConfigManager


@dataclass
class ReconciliationTotals:
    """Structured totals for reconciliation verification."""

    debit_count: int
    debit_total: Decimal
    credit_count: int
    credit_total: Decimal

    def __post_init__(self) -> None:
        """Validate totals."""
        if self.debit_count < 0 or self.credit_count < 0:
            msg = "Counts cannot be negative"
            raise ValueError(msg)
        if self.debit_total < 0 or self.credit_total < 0:
            msg = "Totals cannot be negative"
            raise ValueError(msg)


class Parser(ABC):
    """Abstract base class for bank statement parsers."""

    @abstractmethod
    def parse_file(
        self,
        file_path: Path,
        account_config: dict[str, Any],
        config_manager: "ConfigManager | None" = None,
    ) -> Iterator[Transaction]:
        """Parse a bank statement file and yield transactions."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""

    def get_bank_type(self) -> str:
        """Get the bank type identifier for this parser."""
        msg = "Subclasses must implement get_bank_type()"
        raise NotImplementedError(msg)

    def get_export_config(self) -> dict[str, Any]:
        """Get export configuration specific to this parser."""
        msg = "Subclasses must implement get_export_config()"
        raise NotImplementedError(msg)

    def get_parser_name(self) -> str:
        """Get the parser name identifier."""
        msg = "Subclasses must implement get_parser_name()"
        raise NotImplementedError(msg)

    def get_default_account_name(self) -> str:
        """Get the default account name for this parser."""
        msg = "Subclasses must implement get_default_account_name()"
        raise NotImplementedError(
            msg,
        )

    def get_default_account_number(self) -> str:
        """Get the default account number for this parser."""
        msg = "Subclasses must implement get_default_account_number()"
        raise NotImplementedError(
            msg,
        )

    def get_default_currency(self) -> str:
        """Get the default currency for this parser."""
        msg = "Subclasses must implement get_default_currency()"
        raise NotImplementedError(msg)

    def get_default_country_code(self) -> str:
        """Get the default country code for this parser."""
        msg = "Subclasses must implement get_default_country_code()"
        raise NotImplementedError(
            msg,
        )

    def get_supported_file_patterns(self) -> list[str]:
        """Get list of supported file patterns for this parser."""
        msg = "Subclasses must implement get_supported_file_patterns()"
        raise NotImplementedError(
            msg,
        )

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for this parser."""
        msg = "Subclasses must implement get_supported_extensions()"
        raise NotImplementedError(
            msg,
        )

    def get_parser_description(self) -> str:
        """Get a human-readable description of this parser."""
        msg = "Subclasses must implement get_parser_description()"
        raise NotImplementedError(msg)

    def get_parser_version(self) -> str:
        """Get the parser version."""
        msg = "Subclasses must implement get_parser_version()"
        raise NotImplementedError(msg)

    def supports_reconciliation(self) -> bool:
        """Check if this parser supports reconciliation verification.

        Returns:
            True if parser can extract and verify totals from the statement

        """
        return False

    def extract_reconciliation_totals(
        self,
        file_path: Path,
        account_config: dict[str, Any],
    ) -> ReconciliationTotals | None:
        """Extract reconciliation totals from the statement file.

        This method should extract the totals shown at the bottom of the statement
        (typically on the last page) that summarize debit/credit counts and amounts.

        Args:
            file_path: Path to the statement file
            account_config: Account configuration including password if needed

        Returns:
            ReconciliationTotals if totals can be extracted, None otherwise

        Raises:
            NotImplementedError: If parser doesn't support reconciliation

        """
        if not self.supports_reconciliation():
            return None
        msg = "Parser supports reconciliation but extract_reconciliation_totals() not implemented"
        raise NotImplementedError(msg)

    def verify_reconciliation(
        self,
        transactions: list[Transaction],
        expected_totals: ReconciliationTotals,
        file_path: Path,
        tolerance: Decimal | None = None,
    ) -> None:
        """Verify that parsed transactions match expected reconciliation totals.

        This is a helper method that can be called by parsers to verify totals.
        Parsers can override this for custom verification logic.

        Args:
            transactions: List of parsed transactions
            expected_totals: Expected totals from the statement
            file_path: Path to the statement file (for error messages)
            tolerance: Allowed difference in amounts (default: 0.01)

        Raises:
            ValueError: If reconciliation fails

        """
        if tolerance is None:
            tolerance = Decimal("0.01")

        # Calculate actual totals
        debits = [t for t in transactions if t.amount < 0]
        credits = [t for t in transactions if t.amount > 0]

        actual_debit_total = sum(abs(t.amount) for t in debits)
        actual_credit_total = sum(t.amount for t in credits)
        actual_debit_count = len(debits)
        actual_credit_count = len(credits)

        # Verify totals match
        errors = []

        if abs(actual_debit_total - expected_totals.debit_total) > tolerance:
            errors.append(
                f"Debit total mismatch - Expected: {expected_totals.debit_total}, "
                f"Actual: {actual_debit_total}, "
                f"Difference: {abs(actual_debit_total - expected_totals.debit_total)}",
            )

        if abs(actual_credit_total - expected_totals.credit_total) > tolerance:
            errors.append(
                f"Credit total mismatch - Expected: {expected_totals.credit_total}, "
                f"Actual: {actual_credit_total}, "
                f"Difference: {abs(actual_credit_total - expected_totals.credit_total)}",
            )

        if actual_debit_count != expected_totals.debit_count:
            errors.append(
                f"Debit count mismatch - Expected: {expected_totals.debit_count}, "
                f"Actual: {actual_debit_count}",
            )

        if actual_credit_count != expected_totals.credit_count:
            errors.append(
                f"Credit count mismatch - Expected: {expected_totals.credit_count}, "
                f"Actual: {actual_credit_count}",
            )

        if errors:
            msg = f"Reconciliation failed for {file_path}: " + "; ".join(errors)
            logger = logging.getLogger("bank_importer.interfaces.parser")
            logger.error(msg)
            raise ValueError(msg)
