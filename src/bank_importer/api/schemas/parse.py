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

"""Parse API schemas."""

from pydantic import BaseModel, Field, SecretStr

from bank_importer.api.schemas.transaction import TransactionResponse
from bank_importer.models.enums import (
    CountryCode,
    Currency,
    ParserDetectionBehavior,
    ParserName,
    TargetName,
)


class ParseFileRequest(BaseModel):
    """Parse file request schema.

    Security Note: For better security, use `account_config_name` instead of providing
    password directly. Passwords stored in config can use environment variables or
    file-based secrets. Direct password is less secure but useful for one-off operations.
    """

    parser_name: ParserName | None = Field(
        None,
        description="Parser name to use. If not provided, will auto-detect.",
    )
    account_number: str | None = Field(
        None,
        description="Account number (required if account_config_name not provided)",
    )
    account_name: str | None = Field(
        None,
        description="Account display name (required if account_config_name not provided)",
    )
    bank_name: str | None = Field(
        None,
        description="Bank name (required if account_config_name not provided)",
    )
    currency: Currency = Field(
        default=Currency.THB,  # type: ignore[attr-defined]
        description="Currency code (ISO 4217)",
    )
    country_code: CountryCode = Field(
        default=CountryCode.TH,  # type: ignore[attr-defined]
        description="Country code (ISO 3166-1 alpha-2)",
    )
    account_config_name: str | None = Field(
        None,
        description=(
            "Name of account configuration to use (recommended). "
            "If provided, account settings including password will be loaded from config. "
            "Password can be stored in config using environment variables or file-based secrets."
        ),
    )
    password: SecretStr | None = Field(
        None,
        description=(
            "Password for password-protected PDFs (less secure - prefer account_config_name). "
            "This field uses SecretStr to prevent accidental logging, but passwords are still "
            "transmitted over the network."
        ),
    )
    parser_detection_behavior: ParserDetectionBehavior = Field(
        default=ParserDetectionBehavior.AUTOMATIC,
        description="Parser detection behavior: automatic (auto-detect if not specified) or manual (require parser to be specified)",
    )


class ParseFileResponse(BaseModel):
    """Parse file response schema."""

    transactions: list[TransactionResponse] = Field(
        ...,
        description="List of parsed transactions",
    )
    parser_name: str = Field(..., description="Parser name used")
    total_transactions: int = Field(
        ...,
        description="Total number of transactions parsed",
    )


class ParseAndExportRequest(BaseModel):
    """Parse and export request schema.

    Security Note: For better security, use `account_config_name` instead of providing
    password directly. Passwords stored in config can use environment variables or
    file-based secrets.
    """

    parser_name: ParserName | None = Field(
        None,
        description="Parser name to use. If not provided and detection behavior is automatic, will auto-detect.",
    )
    account_number: str | None = Field(
        None,
        description="Account number (required if account_config_name not provided)",
    )
    account_name: str | None = Field(
        None,
        description="Account display name (required if account_config_name not provided)",
    )
    bank_name: str | None = Field(
        None,
        description="Bank name (required if account_config_name not provided)",
    )
    currency: Currency = Field(
        default=Currency.THB,  # type: ignore[attr-defined]
        description="Currency code (ISO 4217)",
    )
    country_code: CountryCode = Field(
        default=CountryCode.TH,  # type: ignore[attr-defined]
        description="Country code (ISO 3166-1 alpha-2)",
    )
    account_config_name: str | None = Field(
        None,
        description=(
            "Name of account configuration to use (recommended). "
            "If provided, account settings including password will be loaded from config."
        ),
    )
    password: SecretStr | None = Field(
        None,
        description=(
            "Password for password-protected PDFs (less secure - prefer account_config_name). "
            "This field uses SecretStr to prevent accidental logging."
        ),
    )
    target_name: TargetName = Field(
        default=TargetName.CSV,
        description="Export target name",
    )
    parser_detection_behavior: ParserDetectionBehavior = Field(
        default=ParserDetectionBehavior.AUTOMATIC,
        description="Parser detection behavior: automatic (auto-detect if not specified) or manual (require parser to be specified)",
    )


class ParseAndExportResponse(BaseModel):
    """Parse and export response schema."""

    total_transactions: int = Field(
        ...,
        description="Total number of transactions parsed",
    )
    exported_count: int = Field(..., description="Number of transactions exported")
    parser_name: str = Field(..., description="Parser name used")
    target_name: str = Field(..., description="Export target name")
    output_file: str | None = Field(
        None,
        description="Path to output file (if applicable)",
    )
