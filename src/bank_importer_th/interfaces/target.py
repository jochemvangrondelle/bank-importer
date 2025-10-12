"""Target interface for exporting transactions."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ..models.transaction import Transaction


class Target(ABC):
    """Abstract base class for transaction export targets."""

    @abstractmethod
    def export_transactions(
        self, transactions: list[Transaction], config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Export transactions to the target.

        Args:
            transactions: List of transactions to export
            config: Target-specific configuration

        Returns:
            Export result with metadata
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the target name."""
        pass


class TargetResult:
    """Result of a target export operation."""

    def __init__(
        self,
        target_name: str,
        success: bool,
        exported_count: int,
        skipped_count: int,
        error_count: int,
        output_file: str | None = None,
        metadata: dict[str, Any] | None = None,
        error_message: str | None = None,
    ):
        self.target_name = target_name
        self.success = success
        self.exported_count = exported_count
        self.skipped_count = skipped_count
        self.error_count = error_count
        self.output_file = output_file
        self.metadata = metadata or {}
        self.error_message = error_message
        self.timestamp = datetime.now()
