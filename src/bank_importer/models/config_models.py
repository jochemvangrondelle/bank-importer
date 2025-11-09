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

"""Pydantic models for configuration and API responses."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AccountConfig(BaseModel):
    """Account configuration model."""

    name: str = Field(..., description="Account name/identifier")
    parser: str | None = Field(None, description="Parser name for this account")
    file_path: str | Path = Field("data/in", description="Path to input files")
    file_pattern: str = Field("*", description="File pattern to match")
    account_number: str | None = Field(None, description="Account number")
    account_name: str | None = Field(None, description="Display name for account")
    bank_name: str | None = Field(None, description="Bank name")
    password: str | None = Field(None, description="Password for encrypted files")
    password_file: str | Path | None = Field(None, description="Path to password file")
    currency: str = Field("THB", description="Currency code")
    country_code: str = Field("TH", description="Country code")
    reference: str | None = Field(None, description="Account reference")
    translation: dict[str, Any] | None = Field(None, description="Translation settings")

    @field_validator("file_path", "password_file", mode="before")
    @classmethod
    def convert_to_path(cls, v: str | Path | None) -> Path | None:
        """Convert string paths to Path objects."""
        if v is None:
            return None
        if isinstance(v, Path):
            return v
        # v must be str at this point
        return Path(v)

    def model_dump_dict(self) -> dict[str, Any]:
        """Convert to dictionary for TOML serialization."""
        data = self.model_dump(mode="python", exclude_none=True)
        # Convert Path objects back to strings for TOML
        for key in ["file_path", "password_file"]:
            if key in data and isinstance(data[key], Path):
                data[key] = str(data[key])
        return data


class TargetConfig(BaseModel):
    """Target configuration model."""

    name: str = Field(..., description="Target name")
    enabled: bool = Field(default=True, description="Whether target is enabled")
    output_dir: str | Path | None = Field(None, description="Custom output directory")
    config: dict[str, Any] | None = Field(
        None,
        description="Target-specific configuration",
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def convert_to_path(cls, v: str | Path | None) -> Path | None:
        """Convert string paths to Path objects."""
        if v is None:
            return None
        if isinstance(v, Path):
            return v
        # v must be str at this point
        return Path(v)

    def model_dump_dict(self) -> dict[str, Any]:
        """Convert to dictionary for TOML serialization."""
        data = self.model_dump(mode="python", exclude_none=True)
        if "output_dir" in data and isinstance(data["output_dir"], Path):
            data["output_dir"] = str(data["output_dir"])
        return data


class ExportConfig(BaseModel):
    """Export configuration for targets."""

    export_type: str = Field(..., description="Type of export")
    account_reference: str | None = Field(None, description="Account reference")
    source_file: str | None = Field(None, description="Source file path")
    original_filename: str | None = Field(None, description="Original filename")
    bank_type: str | None = Field(None, description="Bank type identifier")
    output_dir: str | Path | None = Field(None, description="Output directory")
    account_config: dict[str, Any] | None = Field(
        None,
        description="Account configuration",
    )
    account_name: str | None = Field(None, description="Account name")
    account_number: str | None = Field(None, description="Account number")
    bank_name: str | None = Field(None, description="Bank name")
    country_code: str | None = Field(None, description="Country code")

    @field_validator("output_dir", mode="before")
    @classmethod
    def convert_to_path(cls, v: str | Path | None) -> Path | None:
        """Convert string paths to Path objects."""
        if v is None:
            return None
        if isinstance(v, Path):
            return v
        # v must be str at this point
        return Path(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExportConfig":
        """Create ExportConfig from dictionary (for backward compatibility)."""
        return cls.model_validate(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (for backward compatibility)."""
        data = self.model_dump(mode="python")
        # Convert Path objects back to strings
        if "output_dir" in data and isinstance(data["output_dir"], Path):
            data["output_dir"] = str(data["output_dir"])
        return data


class ParserInfo(BaseModel):
    """Parser information model."""

    name: str = Field(..., description="Parser name")
    bank_type: str = Field(..., description="Bank type identifier")
    supported_extensions: list[str] = Field(
        default_factory=list,
        description="Supported file extensions",
    )
    supported_patterns: list[str] = Field(
        default_factory=list,
        description="Supported filename patterns",
    )
    description: str | None = Field(None, description="Parser description")


class ImportJobInfo(BaseModel):
    """Import job information model."""

    id: int | None = Field(None, description="Session ID")
    account_name: str = Field(..., description="Account name")
    session_name: str = Field(..., description="Session name")
    status: str = Field(..., description="Status")
    file_path: str = Field(..., description="File path")
    started_at: str | None = Field(None, description="Start timestamp")
    completed_at: str | None = Field(None, description="Completion timestamp")
    total_transactions: int = Field(0, description="Total transactions")
    processed_transactions: int = Field(0, description="Processed transactions")
    error_count: int = Field(0, description="Error count")
    error_message: str | None = Field(None, description="Error message")


class ProcessingResult(BaseModel):
    """Result of processing operations."""

    account_name: str = Field(..., description="Account name")
    processed_transactions: int = Field(
        0,
        description="Number of processed transactions",
    )
    error_count: int = Field(0, description="Number of errors")
    skipped_files: int = Field(0, description="Number of skipped files")
    error_message: str | None = Field(None, description="Error message if any")
