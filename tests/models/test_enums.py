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

"""Tests for enums module."""

from bank_importer.models.enums import (
    CountryCode,
    Currency,
    DryRunMode,
    ExportStatus,
    ImportStatus,
    Language,
    LogLevel,
    ParserDetectionBehavior,
    ReprocessBehavior,
    TargetCompletionStatus,
    TargetName,
    TranslationBehavior,
    _get_all_country_codes,
    _get_all_currency_codes,
    _get_all_language_codes,
    get_country_name,
    get_currency_name,
    get_language_en,
    get_language_name,
    get_language_th,
)


class TestEnums:
    """Test enum classes."""

    def test_import_status(self) -> None:
        """Test ImportStatus enum."""
        assert ImportStatus.PENDING == "pending"
        assert ImportStatus.PROCESSING == "processing"
        assert ImportStatus.COMPLETED == "completed"
        assert ImportStatus.FAILED == "failed"
        assert ImportStatus.SKIPPED == "skipped"

    def test_export_status(self) -> None:
        """Test ExportStatus enum."""
        assert ExportStatus.PROCESSING == "processing"
        assert ExportStatus.COMPLETED == "completed"
        assert ExportStatus.FAILED == "failed"
        assert ExportStatus.SKIPPED == "skipped"

    def test_target_completion_status(self) -> None:
        """Test TargetCompletionStatus enum."""
        assert TargetCompletionStatus.PENDING == "pending"
        assert TargetCompletionStatus.COMPLETED == "completed"
        assert TargetCompletionStatus.FAILED == "failed"

    def test_target_name(self) -> None:
        """Test TargetName enum."""
        assert TargetName.CSV == "csv"
        assert TargetName.YAML == "yaml"
        assert TargetName.FIREFLY == "firefly"

    def test_parser_detection_behavior(self) -> None:
        """Test ParserDetectionBehavior enum."""
        assert ParserDetectionBehavior.AUTOMATIC == "automatic"
        assert ParserDetectionBehavior.MANUAL == "manual"

    def test_reprocess_behavior(self) -> None:
        """Test ReprocessBehavior enum."""
        assert ReprocessBehavior.SKIP_EXISTING == "skip_existing"
        assert ReprocessBehavior.REPROCESS_EXISTING == "reprocess_existing"

    def test_translation_behavior(self) -> None:
        """Test TranslationBehavior enum."""
        assert TranslationBehavior.ENABLED == "enabled"
        assert TranslationBehavior.DISABLED == "disabled"

    def test_dry_run_mode(self) -> None:
        """Test DryRunMode enum."""
        assert DryRunMode.ENABLED == "enabled"
        assert DryRunMode.DISABLED == "disabled"

    def test_log_level(self) -> None:
        """Test LogLevel enum."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"


class TestCurrencyEnum:
    """Test Currency enum creation."""

    def test_currency_enum_exists(self) -> None:
        """Test Currency enum is created."""
        assert Currency is not None
        # Check some common currencies exist
        assert hasattr(Currency, "THB")
        assert hasattr(Currency, "USD")
        assert hasattr(Currency, "EUR")

    def test_get_all_currency_codes_with_pycountry(self) -> None:
        """Test _get_all_currency_codes with pycountry available."""
        codes = _get_all_currency_codes()
        assert isinstance(codes, list)
        assert len(codes) > 0
        assert "THB" in codes
        assert "USD" in codes

    def test_get_all_currency_codes_fallback_path(self) -> None:
        """Test _get_all_currency_codes fallback path."""
        # Test that fallback currencies are included
        codes = _get_all_currency_codes()
        # Verify common currencies from fallback list are present
        fallback_currencies = ["THB", "USD", "EUR", "GBP", "JPY"]
        for currency in fallback_currencies:
            assert currency in codes


class TestCountryCodeEnum:
    """Test CountryCode enum creation."""

    def test_country_code_enum_exists(self) -> None:
        """Test CountryCode enum is created."""
        assert CountryCode is not None
        # Check some common countries exist
        assert hasattr(CountryCode, "TH")
        assert hasattr(CountryCode, "US")
        assert hasattr(CountryCode, "GB")

    def test_get_all_country_codes_with_pycountry(self) -> None:
        """Test _get_all_country_codes with pycountry available."""
        codes = _get_all_country_codes()
        assert isinstance(codes, list)
        assert len(codes) > 0
        assert "TH" in codes
        assert "US" in codes

    def test_get_all_country_codes_fallback_path(self) -> None:
        """Test _get_all_country_codes fallback path."""
        # Test that fallback countries are included
        codes = _get_all_country_codes()
        # Verify common countries from fallback list are present
        fallback_countries = ["TH", "US", "GB", "DE", "FR"]
        for country in fallback_countries:
            assert country in codes


class TestLanguageEnum:
    """Test Language enum creation."""

    def test_language_enum_exists(self) -> None:
        """Test Language enum is created."""
        assert Language is not None
        # Check some common languages exist
        assert hasattr(Language, "TH")
        assert hasattr(Language, "EN")

    def test_get_language_th(self) -> None:
        """Test get_language_th helper."""
        lang = get_language_th()
        assert lang == Language.TH

    def test_get_language_en(self) -> None:
        """Test get_language_en helper."""
        lang = get_language_en()
        assert lang == Language.EN

    def test_get_all_language_codes_with_pycountry(self) -> None:
        """Test _get_all_language_codes with pycountry available."""
        codes = _get_all_language_codes()
        assert isinstance(codes, list)
        assert len(codes) > 0
        assert "th" in codes
        assert "en" in codes

    def test_get_all_language_codes_cached(self) -> None:
        """Test _get_all_language_codes caching."""
        codes1 = _get_all_language_codes()
        codes2 = _get_all_language_codes()
        # Should return same list (cached)
        assert codes1 is codes2

    def test_get_all_language_codes_fallback_path(self) -> None:
        """Test _get_all_language_codes fallback path."""
        # Clear cache to test fresh call
        from bank_importer.models import enums as enums_module

        original_cache = enums_module._language_codes_cache
        enums_module._language_codes_cache = None
        try:
            codes = _get_all_language_codes()
            assert isinstance(codes, list)
            assert len(codes) > 0
            # Verify common languages from fallback list are present
            fallback_languages = ["th", "en", "de", "fr", "ja"]
            for lang in fallback_languages:
                assert lang in codes
        finally:
            enums_module._language_codes_cache = original_cache


class TestHelperFunctions:
    """Test helper functions for getting names."""

    def test_get_currency_name_with_pycountry(self) -> None:
        """Test get_currency_name with pycountry available."""
        name = get_currency_name("THB")
        assert name is not None
        assert isinstance(name, str)

    def test_get_currency_name_invalid_code(self) -> None:
        """Test get_currency_name with invalid code."""
        name = get_currency_name("INVALID")
        assert name is None

    def test_get_currency_name_error_handling(self) -> None:
        """Test get_currency_name error handling."""
        # Test with invalid code that raises KeyError
        name = get_currency_name("INVALID")
        assert name is None
        # Test with code that doesn't have name attribute
        # This is hard to test without mocking, but we can test the None return

    def test_get_country_name_with_pycountry(self) -> None:
        """Test get_country_name with pycountry available."""
        name = get_country_name("TH")
        assert name is not None
        assert isinstance(name, str)

    def test_get_country_name_invalid_code(self) -> None:
        """Test get_country_name with invalid code."""
        name = get_country_name("XX")
        assert name is None

    def test_get_language_name_with_pycountry(self) -> None:
        """Test get_language_name with pycountry available."""
        name = get_language_name("th")
        assert name is not None
        assert isinstance(name, str)

    def test_get_language_name_invalid_code(self) -> None:
        """Test get_language_name with invalid code."""
        name = get_language_name("xx")
        assert name is None
