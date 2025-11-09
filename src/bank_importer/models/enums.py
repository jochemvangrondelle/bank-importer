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

"""Enums for type-safe status and configuration values."""

from enum import Enum

try:
    import pycountry

    PYCOUNTRY_AVAILABLE = True
except ImportError:
    PYCOUNTRY_AVAILABLE = False


class ImportStatus(str, Enum):
    """Status values for import sessions."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExportStatus(str, Enum):
    """Status values for export sessions."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TargetCompletionStatus(str, Enum):
    """Status values for target completion tracking."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportedTransactionStatus(str, Enum):
    """Status values for exported transactions."""

    EXPORTED = "exported"
    FAILED = "failed"
    SKIPPED = "skipped"


class TransactionType(str, Enum):
    """Transaction type values."""

    DEBIT = "debit"
    CREDIT = "credit"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PAYMENT = "payment"
    RECEIPT = "receipt"
    TRANSFER = "transfer"


class ExportType(str, Enum):
    """Export type values for target exports."""

    CONSOLIDATED = "consolidated"
    SOURCE_FILE = "source_file"
    ACCOUNT_REFERENCE = "account_reference"
    ALL_CONSOLIDATED = "all_consolidated"
    BANK_CONSOLIDATED = "bank_consolidated"


class ParserName(str, Enum):
    """Available parser names."""

    AMEX_TH_CSV = "amex_th_csv"
    KRUNGSRI_PDF = "krungsri_pdf"
    KRUNGSRI_TEXT = "krungsri_text"
    SCB_PDF = "scb_pdf"
    GENERIC_CSV = "generic_csv"
    GENERIC_JSON = "generic_json"
    GENERIC_FIXED_WIDTH = "generic_fixed_width"


def _get_all_currency_codes() -> list[str]:
    """Get all ISO 4217 currency codes from pycountry."""
    if PYCOUNTRY_AVAILABLE:
        codes = []
        for currency in pycountry.currencies:
            if hasattr(currency, "alpha_3"):
                codes.append(currency.alpha_3)
        return sorted(codes)
    # Fallback to common currencies
    return [
        "AUD",
        "CAD",
        "CHF",
        "CNY",
        "EUR",
        "GBP",
        "HKD",
        "IDR",
        "INR",
        "JPY",
        "KRW",
        "MYR",
        "NZD",
        "PHP",
        "SGD",
        "THB",
        "USD",
        "VND",
    ]


# Create Currency enum with all available currencies
_currency_codes = _get_all_currency_codes()
Currency = Enum("Currency", {code: code for code in _currency_codes}, type=str)  # type: ignore[misc]


def _get_all_country_codes() -> list[str]:
    """Get all ISO 3166-1 alpha-2 country codes from pycountry."""
    if PYCOUNTRY_AVAILABLE:
        codes = []
        for country in pycountry.countries:
            if hasattr(country, "alpha_2"):
                codes.append(country.alpha_2)
        return sorted(codes)
    # Fallback to common countries
    return [
        "AT",
        "AU",
        "BE",
        "CA",
        "CH",
        "CN",
        "DE",
        "DK",
        "ES",
        "FI",
        "FR",
        "GB",
        "HK",
        "ID",
        "IN",
        "IT",
        "JP",
        "KR",
        "MY",
        "NL",
        "NO",
        "NZ",
        "PH",
        "SE",
        "SG",
        "TH",
        "US",
        "VN",
    ]


# Create CountryCode enum with all available countries
_country_codes = _get_all_country_codes()
CountryCode = Enum("CountryCode", {code: code for code in _country_codes}, type=str)  # type: ignore[misc]


def get_currency_name(code: str) -> str | None:
    """Get currency name for a given ISO 4217 code."""
    if PYCOUNTRY_AVAILABLE:
        try:
            currency = pycountry.currencies.get(alpha_3=code)
            return currency.name if currency else None
        except (KeyError, AttributeError):
            return None
    return None


def get_country_name(code: str) -> str | None:
    """Get country name for a given ISO 3166-1 alpha-2 code."""
    if PYCOUNTRY_AVAILABLE:
        try:
            country = pycountry.countries.get(alpha_2=code)
            return country.name if country else None
        except (KeyError, AttributeError):
            return None
    return None


# Cache for language codes to avoid regenerating on every import
_language_codes_cache: list[str] | None = None


def _get_all_language_codes() -> list[str]:
    """Get all ISO 639-1 language codes from pycountry.

    Uses pycountry library to automatically get all ISO 639-1 (alpha_2) language codes.
    No manual maintenance required - pycountry provides comprehensive language support.

    Results are cached to avoid regenerating on every import (performance optimization).
    """
    global _language_codes_cache

    if _language_codes_cache is not None:
        return _language_codes_cache

    if PYCOUNTRY_AVAILABLE:
        codes = []
        for lang in pycountry.languages:
            if hasattr(lang, "alpha_2") and lang.alpha_2:
                # Normalize to lowercase for consistency
                codes.append(lang.alpha_2.lower())
        _language_codes_cache = sorted(set(codes))
        return _language_codes_cache
    # Fallback to common languages if pycountry not available
    _language_codes_cache = [
        "ar",  # Arabic
        "de",  # German
        "en",  # English
        "es",  # Spanish
        "fr",  # French
        "he",  # Hebrew
        "ja",  # Japanese
        "ko",  # Korean
        "nl",  # Dutch
        "pt",  # Portuguese
        "ru",  # Russian
        "th",  # Thai
        "zh",  # Chinese
    ]
    return _language_codes_cache


# Create Language enum with all available languages from pycountry
# This automatically includes all ISO 639-1 language codes without manual maintenance
# Cached to avoid regenerating on every import
_language_codes = _get_all_language_codes()
# Build enum members dict explicitly for mypy
_language_enum_dict: dict[str, str] = {
    code.upper(): code.lower() for code in _language_codes
}
Language = Enum("Language", _language_enum_dict, type=str)  # type: ignore[misc]


# Helper functions to get common language enum values
def get_language_th() -> Language:
    """Get Thai language enum value."""
    # Access enum member by value
    for lang in Language:
        if lang.value == "th":
            return lang
    # Fallback (should never happen, but mypy needs it)
    # We know "th" exists in the enum, so this is safe
    return next(iter(Language))  # Return first enum member as fallback


def get_language_en() -> Language:
    """Get English language enum value."""
    # Access enum member by value
    for lang in Language:
        if lang.value == "en":
            return lang
    # Fallback (should never happen, but mypy needs it)
    # We know "en" exists in the enum, so this is safe
    return next(iter(Language))  # Return first enum member as fallback


def get_language_name(code: str) -> str | None:
    """Get language name for a given ISO 639-1 code."""
    if PYCOUNTRY_AVAILABLE:
        try:
            lang = pycountry.languages.get(alpha_2=code.lower())
            return lang.name if lang else None
        except (KeyError, AttributeError):
            return None
    return None


class TargetName(str, Enum):
    """Available export target names."""

    CSV = "csv"
    YAML = "yaml"
    FIREFLY = "firefly"


class ParserDetectionBehavior(str, Enum):
    """Parser detection behavior options."""

    AUTOMATIC = "automatic"  # Auto-detect parser if not specified
    MANUAL = "manual"  # Require parser to be specified, fail if not provided


class ReprocessBehavior(str, Enum):
    """File reprocessing behavior options."""

    SKIP_EXISTING = "skip_existing"  # Skip files that have already been imported
    REPROCESS_EXISTING = (
        "reprocess_existing"  # Reprocess files even if already imported
    )


class TranslationBehavior(str, Enum):
    """Translation behavior options."""

    ENABLED = "enabled"  # Translate transaction descriptions
    DISABLED = "disabled"  # Do not translate transaction descriptions


class DryRunMode(str, Enum):
    """Dry run mode options."""

    ENABLED = "enabled"  # Perform a dry run (simulate without making changes)
    DISABLED = "disabled"  # Execute normally (make actual changes)


class LogLevel(str, Enum):
    """Logging level values (standard Python logging levels)."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
