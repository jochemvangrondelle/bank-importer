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

"""Tests for translation service."""

import json
from pathlib import Path

import pytest

from bank_importer.translation_service import (
    TranslationService,
    get_translation_service,
    translate_description,
)


class TestTranslationService:
    """Tests for TranslationService."""

    @pytest.fixture
    def translation_service(self, tmp_path: Path) -> TranslationService:
        """Create a translation service for testing."""
        cache_file = tmp_path / "translation_cache.json"
        return TranslationService(
            cache_file=cache_file,
            api_key=None,
        )

    @pytest.mark.parametrize(
        ("api_key", "expected_key"),
        [
            (None, None),
            ("test-key", "test-key"),
            ("", None),
        ],
    )
    def test_init_with_api_key(
        self,
        tmp_path: Path,
        api_key: str | None,
        expected_key: str | None,
    ) -> None:
        """Test initialization with API key."""
        cache_file = tmp_path / "cache.json"
        service = TranslationService(
            cache_file=cache_file,
            api_key=api_key,
        )
        assert service.api_key == expected_key

    @pytest.mark.parametrize(
        ("source_lang", "target_lang"),
        [
            ("th", "en"),
            ("en", "th"),
            ("th", "de"),
        ],
    )
    def test_init_with_languages(
        self,
        tmp_path: Path,
        source_lang: str,
        target_lang: str,
    ) -> None:
        """Test initialization with different language pairs."""
        cache_file = tmp_path / "cache.json"
        service = TranslationService(
            cache_file=cache_file,
            source_language=source_lang,
            target_language=target_lang,
        )
        assert service.source_language == source_lang
        assert service.target_language == target_lang

    @pytest.mark.parametrize(
        ("text", "expected_result"),
        [
            ("", ""),
            (None, ""),  # type: ignore[list-item]
            ("Hello", "Hello"),  # English text may not need translation
        ],
    )
    def test_translate_empty_or_none(
        self,
        translation_service: TranslationService,
        text: str | None,
        expected_result: str,
    ) -> None:
        """Test translating empty or None text."""
        result = translation_service.translate_description(text or "")  # type: ignore[arg-type]
        assert result == expected_result

    def test_translate_cached(self, translation_service: TranslationService) -> None:
        """Test that translations are cached."""
        text = "Test translation"
        result1 = translation_service.translate_description(text)
        result2 = translation_service.translate_description(text)
        assert result1 == result2

    @pytest.mark.parametrize(
        ("term_mappings", "text", "expected"),
        [
            ({"สวัสดี": "Hello"}, "สวัสดี", "Hello"),
            ({"คำ": "word", "ภาษา": "language"}, "คำ", "word"),
            ({}, "สวัสดี", "สวัสดี"),  # No mapping, returns original
        ],
    )
    def test_translate_with_term_mappings(
        self,
        translation_service: TranslationService,
        term_mappings: dict[str, str],
        text: str,
        expected: str,
    ) -> None:
        """Test translation with custom term mappings."""
        translation_service.set_term_mappings(term_mappings)
        # When term mappings are empty, disable API translation to get original text
        use_api_translation = bool(term_mappings)
        result = translation_service.translate_description(
            text,
            use_api_translation=use_api_translation,
        )
        # Result should contain expected (may have additional translation)
        assert expected in result or result == expected

    def test_get_cache_stats(self, translation_service: TranslationService) -> None:
        """Test getting cache statistics."""
        # Translate some text to populate cache
        translation_service.translate_description("Test")
        stats = translation_service.get_cache_stats()
        assert isinstance(stats, dict)
        assert "total_entries" in stats
        assert "cache_file" in stats

    @pytest.mark.parametrize(
        "term_mappings",
        [
            {"คำ": "word"},
            {"คำ": "word", "ภาษา": "language"},
            {},
        ],
    )
    def test_set_term_mappings(
        self,
        translation_service: TranslationService,
        term_mappings: dict[str, str],
    ) -> None:
        """Test setting term mappings."""
        translation_service.set_term_mappings(term_mappings)
        assert translation_service.term_mappings == term_mappings

    def test_clear_cache(self, translation_service: TranslationService) -> None:
        """Test clearing the cache."""
        # Manually add to cache since translation libraries may not be available
        cache_key = f"{translation_service.source_language}_{translation_service.target_language}_Test"
        translation_service.translation_cache[cache_key] = "Test Translated"
        assert len(translation_service.translation_cache) > 0

        # Clear cache
        translation_service.clear_cache()
        assert len(translation_service.translation_cache) == 0

    def test_add_custom_mapping(self, translation_service: TranslationService) -> None:
        """Test adding custom term mapping."""
        translation_service.add_custom_mapping("คำ", "word")
        assert translation_service.term_mappings["คำ"] == "word"

    def test_should_skip_translation(
        self,
        translation_service: TranslationService,
    ) -> None:
        """Test skip translation logic."""
        # Numbers should be skipped
        assert translation_service._should_skip_translation("123.45") is True
        # Short text should be skipped
        assert translation_service._should_skip_translation("A") is True
        # Normal text in source language should not be skipped
        # For Thai source language, use Thai text
        assert translation_service._should_skip_translation("สวัสดี") is False
        # English text with Thai source language will be skipped (no Thai characters)
        assert translation_service._should_skip_translation("Hello World") is True

    def test_load_cache(self, tmp_path: Path) -> None:
        """Test loading cache from file."""
        cache_file = tmp_path / "cache.json"
        cache_data = {"th_en_Test": "Translation"}
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        service = TranslationService(cache_file=cache_file)
        assert "th_en_Test" in service.translation_cache

    def test_save_cache(self, tmp_path: Path) -> None:
        """Test saving cache to file."""
        cache_file = tmp_path / "cache.json"
        service = TranslationService(cache_file=cache_file)
        service.translation_cache["test_key"] = "test_value"
        service._save_cache()

        assert cache_file.exists()
        loaded = json.loads(cache_file.read_text(encoding="utf-8"))
        assert loaded["test_key"] == "test_value"

    @pytest.mark.parametrize(
        ("descriptions", "expected_count"),
        [
            (["Test1", "Test2", "Test3"], 3),
            (["สวัสดี", "Hello"], 2),
            ([], 0),
        ],
    )
    def test_translate_batch(
        self,
        translation_service: TranslationService,
        descriptions: list[str],
        expected_count: int,
    ) -> None:
        """Test batch translation."""
        results = translation_service.translate_batch(descriptions)
        assert isinstance(results, dict)
        assert len(results) == expected_count
        assert all(isinstance(v, str) for v in results.values())

    def test_export_cache(
        self,
        translation_service: TranslationService,
        tmp_path: Path,
    ) -> None:
        """Test exporting cache."""
        # Add some translations
        translation_service.translate_description("Test")
        output_file = tmp_path / "exported_cache.json"
        translation_service.export_cache(output_file)
        assert output_file.exists()

    def test_import_cache(
        self,
        translation_service: TranslationService,
        tmp_path: Path,
    ) -> None:
        """Test importing cache."""
        cache_file = tmp_path / "cache.json"
        cache_data = {"th_en_Test1": "Translation1", "th_en_Test2": "Translation2"}
        import json

        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        translation_service.import_cache(cache_file)
        assert "th_en_Test1" in translation_service.translation_cache

    @pytest.mark.parametrize(
        ("source_lang", "target_lang"),
        [
            ("th", "en"),
            ("en", "th"),
        ],
    )
    def test_set_language_pair(
        self,
        translation_service: TranslationService,
        source_lang: str,
        target_lang: str,
    ) -> None:
        """Test setting language pair."""
        translation_service.set_language_pair(source_lang, target_lang)
        assert translation_service.source_language == source_lang
        assert translation_service.target_language == target_lang


class TestGetTranslationService:
    """Tests for get_translation_service function."""

    def test_get_translation_service_singleton(self) -> None:
        """Test that get_translation_service returns singleton."""
        # Reset global instance for testing
        import bank_importer.translation_service as ts_module

        ts_module._translation_service_instance = None
        service1 = get_translation_service()
        service2 = get_translation_service()
        assert service1 is service2

    @pytest.mark.parametrize(
        ("api_key", "source_lang", "target_lang"),
        [
            ("test-key", "th", "en"),
            (None, "en", "th"),
            ("key2", "th", "de"),
        ],
    )
    def test_get_translation_service_with_params(
        self,
        api_key: str | None,
        source_lang: str,
        target_lang: str,
    ) -> None:
        """Test getting translation service with parameters."""
        # Reset global instance
        import bank_importer.translation_service as ts_module

        ts_module._translation_service_instance = None
        service = get_translation_service(
            api_key=api_key,
            source_language=source_lang,
            target_language=target_lang,
        )
        assert service is not None
        assert service.api_key == api_key
        assert service.source_language == source_lang
        assert service.target_language == target_lang


class TestTranslateDescription:
    """Tests for translate_description function."""

    @pytest.mark.parametrize(
        ("description", "expected_type"),
        [
            ("Test", str),
            ("", str),
            ("สวัสดี", str),
        ],
    )
    def test_translate_description(self, description: str, expected_type: type) -> None:
        """Test translate_description function."""
        result = translate_description(description)
        assert isinstance(result, expected_type)
        assert len(result) >= 0

    def test_translate_description_with_term_mappings(self) -> None:
        """Test translate_description with term mappings."""
        # Reset singleton to ensure clean state
        import bank_importer.translation_service as ts_module

        ts_module._translation_service_instance = None

        term_mappings = {"สวัสดี": "Hello"}
        result = translate_description(
            "สวัสดี",
            term_mappings=term_mappings,
            use_api_translation=False,  # Disable API translation to test term mappings only
        )
        # Term mapping should be applied - result should be "Hello"
        assert result == "Hello" or result.lower() == "hello"
