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

"""Target interface for exporting transactions."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from bank_importer.models.config_models import ExportConfig
from bank_importer.models.transaction import Transaction


class Target(ABC):
    """Abstract base class for transaction export targets."""

    @abstractmethod
    def export_transactions(
        self,
        transactions: list[Transaction],
        config: ExportConfig | dict[str, Any],
    ) -> "TargetResult":
        """Export transactions to the target.

        Args:
            transactions: List of transactions to export
            config: Target-specific configuration (ExportConfig or dict for backward compatibility)

        Returns:
            Export result with metadata

        """

    @abstractmethod
    def get_name(self) -> str:
        """Get the target name."""


class TargetResult(BaseModel):
    """Result of a target export operation."""

    target_name: str = Field(..., description="Name of the target")
    success: bool = Field(..., description="Whether the export was successful")
    exported_count: int = Field(0, description="Number of transactions exported")
    skipped_count: int = Field(0, description="Number of transactions skipped")
    error_count: int = Field(0, description="Number of errors encountered")
    output_file: str | None = Field(
        None,
        description="Path to output file if applicable",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the export",
    )
    error_message: str | None = Field(
        None,
        description="Error message if export failed",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp of the result",
    )

    def model_dump_dict(self) -> dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(mode="python")
