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

"""Configuration API schemas."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from bank_importer.models.config_models import AccountConfig, TargetConfig
from bank_importer.models.enums import Language, get_language_en, get_language_th


class AppSettings(BaseModel):
    """Application settings schema."""

    timezone: str = Field(default="Asia/Bangkok", description="Timezone")


class DatabaseSettings(BaseModel):
    """Database settings schema."""

    url: str = Field(..., description="Database URL")


class OutputSettings(BaseModel):
    """Output settings schema."""

    output_dir: str = Field(..., description="Output directory path")


class TranslationSettings(BaseModel):
    """Translation settings schema."""

    enable_translation: bool = Field(default=True, description="Enable translation")
    default_source_language: Language = Field(
        default_factory=get_language_th,
        description="Default source language",
    )
    default_target_language: Language = Field(
        default_factory=get_language_en,
        description="Default target language",
    )
    translation_cache_file: str = Field(
        default="translation_cache.json",
        description="Translation cache file path",
    )
    google_translate_api_key: str | None = Field(
        None,
        description="Google Translate API key (write-only, never returned)",
    )
    term_mappings: dict[str, dict[str, str]] | None = Field(
        None,
        description="Term mappings",
    )

    @field_validator("google_translate_api_key", mode="before")
    @classmethod
    def hide_api_key(cls, v: str | None) -> str | None:
        """Hide API key in responses."""
        return None if v else None


class SettingsResponse(BaseModel):
    """Settings response schema."""

    app: AppSettings
    database: DatabaseSettings
    output: OutputSettings
    translation: TranslationSettings


class SettingsUpdate(BaseModel):
    """Settings update schema."""

    app: AppSettings | None = None
    database: DatabaseSettings | None = None
    output: OutputSettings | None = None
    translation: TranslationSettings | None = None


class AccountConfigResponse(BaseModel):
    """Account configuration response schema (password excluded)."""

    name: str
    parser: str | None = None
    file_path: str
    file_pattern: str = "*"
    account_number: str | None = None
    account_name: str | None = None
    bank_name: str | None = None
    branch_name: str | None = None
    currency: str = "THB"
    country_code: str = "TH"
    reference: str | None = None
    translation: dict[str, Any] | None = None

    @classmethod
    def from_account_config(cls, account: AccountConfig) -> "AccountConfigResponse":
        """Create from AccountConfig model."""
        return cls(
            name=account.name,
            parser=account.parser,
            file_path=str(account.file_path),
            file_pattern=account.file_pattern,
            account_number=account.account_number,
            account_name=account.account_name,
            bank_name=account.bank_name,
            currency=account.currency,
            country_code=account.country_code,
            reference=account.reference,
            translation=account.translation,
        )

    @classmethod
    def from_dict(cls, account: dict[str, Any]) -> "AccountConfigResponse":
        """Create from dictionary (excluding password)."""
        data = account.copy()
        data.pop("password", None)
        data.pop("password_file", None)
        if "file_path" in data and hasattr(data["file_path"], "__str__"):
            data["file_path"] = str(data["file_path"])
        return cls(**data)


class TargetConfigResponse(BaseModel):
    """Target configuration response schema."""

    name: str
    enabled: bool = True
    output_dir: str | None = None
    config: dict[str, Any] | None = None

    @classmethod
    def from_target_config(cls, target: TargetConfig) -> "TargetConfigResponse":
        """Create from TargetConfig model."""
        return cls(
            name=target.name,
            enabled=target.enabled,
            output_dir=str(target.output_dir) if target.output_dir else None,
            config=target.config,
        )

    @classmethod
    def from_dict(cls, target: dict[str, Any]) -> "TargetConfigResponse":
        """Create from dictionary."""
        data = target.copy()
        if "output_dir" in data and hasattr(data["output_dir"], "__str__"):
            data["output_dir"] = str(data["output_dir"])
        # Handle nested config keys (e.g., csv_config, yaml_config)
        if "csv_config" in data:
            data["config"] = data.pop("csv_config")
        elif "yaml_config" in data:
            data["config"] = data.pop("yaml_config")
        elif "firefly_config" in data:
            data["config"] = data.pop("firefly_config")
        return cls(**data)


class ConfigResponse(BaseModel):
    """Full configuration response schema."""

    app: AppSettings
    database: DatabaseSettings
    output: OutputSettings
    translation: TranslationSettings
    accounts: list[AccountConfigResponse]
    targets: list[TargetConfigResponse]


class ConfigUpdate(BaseModel):
    """Full configuration update schema."""

    app: AppSettings | None = None
    database: DatabaseSettings | None = None
    output: OutputSettings | None = None
    translation: TranslationSettings | None = None
    accounts: list[AccountConfig] | None = None
    targets: list[TargetConfig] | None = None
