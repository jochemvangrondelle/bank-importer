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

"""Translation service for converting transaction descriptions between languages."""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from bank_importer.logging_config import (
    get_logger,
    log_error,
    log_info,
    log_success,
    log_warning,
)
from bank_importer.models.enums import Language, get_language_en, get_language_th
from bank_importer.models.function_models import TranslationConfig

if TYPE_CHECKING:
    from googletrans import Translator

# Check for available translation libraries
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator

    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False

try:
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False


class TranslationService:
    """Service for translating transaction descriptions."""

    def __init__(
        self,
        cache_file: Path | None = None,
        api_key: str | None = None,
        source_language: Language | None = None,
        target_language: Language | None = None,
        term_mappings: dict[str, str] | None = None,
    ) -> None:
        """Initialize translation service.

        Args:
            cache_file: Path to translation cache file
            api_key: API key for translation service
            source_language: Source language code (ISO 639-1)
            target_language: Target language code (ISO 639-1)
            term_mappings: Dictionary of term mappings

        """
        # Convert empty string to None for api_key
        self.api_key = api_key if api_key else None
        # Handle both enum instances and strings for language codes
        # Use enum values directly (enum with type=str stores value as string)
        # Type annotation: these are always strings after initialization
        if source_language is not None:
            self.source_language: str = (
                source_language.value
                if hasattr(source_language, "value")
                else str(source_language)
            )
        else:
            self.source_language = get_language_th().value
        if target_language is not None:
            self.target_language: str = (
                target_language.value
                if hasattr(target_language, "value")
                else str(target_language)
            )
        else:
            self.target_language = get_language_en().value
        self.term_mappings = term_mappings or {}
        self.cache_file = cache_file or Path("translation_cache.json")
        self.translation_cache = self._load_cache()
        self.translator: GoogleTranslator | Translator | None = None
        self._googletrans_disabled = False  # Flag to prevent repeated warnings
        self.logger = get_logger("translation_service")
        self._init_translator()

        # Common patterns that don't need translation
        self.skip_patterns = [
            r"^\d+\.?\d*$",  # Numbers
            r"^[A-Z0-9\-_]+$",  # Codes like X2/ENET
            r"^[A-Z]{2,4}$",  # Short codes
            r"^[0-9,]+\.\d{2}$",  # Amounts
            r"^[A-Za-z0-9@\.]+$",  # Email addresses
            r"^[A-Za-z0-9\-_\.]+@[A-Za-z0-9\-_\.]+\.[A-Za-z]{2,}$",  # Full emails
        ]

        # Language-specific character detection patterns
        self.language_patterns = {
            "th": r"[\u0E00-\u0E7F]",  # Thai Unicode range
            "TH": r"[\u0E00-\u0E7F]",  # Thai Unicode range (alternative code)
            "zh": r"[\u4E00-\u9FFF]",  # Chinese Unicode range
            "ja": r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]",  # Japanese Unicode range
            "ko": r"[\uAC00-\uD7AF]",  # Korean Unicode range
            "ar": r"[\u0600-\u06FF]",  # Arabic Unicode range
            "he": r"[\u0590-\u05FF]",  # Hebrew Unicode range
            "ru": r"[\u0400-\u04FF]",  # Cyrillic Unicode range
        }

    def _init_translator(self) -> None:
        """Initialize the translation service."""
        # Prefer deep-translator over googletrans
        if DEEP_TRANSLATOR_AVAILABLE:
            try:
                # deep-translator expects lowercase language codes
                source_lang = self.source_language.lower()
                target_lang = self.target_language.lower()
                self.translator = GoogleTranslator(
                    source=source_lang,
                    target=target_lang,
                )
                # Only log once during initialization
                log_success(
                    f"Translation service initialized ({source_lang} -> {target_lang})",
                )
            except Exception as e:
                log_warning(f"Failed to initialize deep-translator: {e}")
                self.translator = None
        elif GOOGLETRANS_AVAILABLE:
            try:
                # Import here to avoid loading if not available
                from googletrans import Translator

                self.translator = Translator()
                log_success(
                    f"Translation service initialized with googletrans ({self.source_language} -> {self.target_language})",
                )
            except Exception as e:
                log_warning(f"Failed to initialize googletrans: {e}")
                self.translator = None
        else:
            log_warning("No translation library available")
            self.translator = None

    def _load_cache(self) -> dict[str, str]:
        """Load translation cache from file."""
        try:
            if self.cache_file.exists():
                with self.cache_file.open(encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
                    log_warning("Cache file contains non-dict data, using empty cache")
        except Exception as e:
            log_warning(f"Could not load translation cache: {e}")
        return {}

    def _save_cache(self) -> None:
        """Save translation cache to file."""
        try:
            with self.cache_file.open("w", encoding="utf-8") as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_warning(f"Could not save translation cache: {e}")

    def _should_skip_translation(self, text: str) -> bool:
        """Check if text should be skipped for translation."""
        if not text or len(text.strip()) < 2:
            return True

        # Check against skip patterns
        for pattern in self.skip_patterns:
            if re.match(pattern, text.strip()):
                return True

        # Check if text contains characters from the source language
        if self.source_language in self.language_patterns:
            pattern = self.language_patterns[self.source_language]
            if not re.search(pattern, text):
                return True

        return False

    def _apply_term_mapping(self, text: str) -> str:
        """Apply language-specific term mappings."""
        if not self.term_mappings:
            return text

        result = text
        for source_term, target_term in self.term_mappings.items():
            # For non-ASCII text (like Thai), word boundaries may not work correctly
            # Try exact match first, then word boundaries for ASCII text
            if source_term == text:
                # Exact match - replace entire text
                return target_term
            # Use word boundaries for ASCII text to avoid partial matches
            if source_term.isascii():
                pattern = r"\b" + re.escape(source_term) + r"\b"
                result = re.sub(pattern, target_term, result, flags=re.IGNORECASE)
            else:
                # For non-ASCII, use simple replacement (word boundaries don't work well)
                result = result.replace(source_term, target_term)

        return result

    def _translate_with_api(self, text: str) -> str | None:
        """Translate text using Google Translate API."""
        if not self.api_key:
            # API key not provided, skip API translation
            return None
        if not REQUESTS_AVAILABLE:
            log_warning("requests library not available for API translation")
            return None

        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            params = {
                "key": self.api_key,
                "q": text,
                "source": self.source_language,
                "target": self.target_language,
            }

            response = requests.post(url, data=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if (
                isinstance(data, dict)
                and "data" in data
                and "translations" in data["data"]
            ):
                translations = data["data"]["translations"]
                if isinstance(translations, list) and len(translations) > 0:
                    first_translation = translations[0]
                    if (
                        isinstance(first_translation, dict)
                        and "translatedText" in first_translation
                    ):
                        translated_text = first_translation["translatedText"]
                        if isinstance(translated_text, str):
                            return translated_text

        except Exception as e:
            log_error(f"API translation error: {e}")

        return None

    def _translate_with_deep_translator(self, text: str) -> str | None:
        """Translate text using deep-translator library."""
        if not self.translator or not DEEP_TRANSLATOR_AVAILABLE:
            return None

        try:
            # deep-translator uses a different API
            if hasattr(self.translator, "translate"):
                result = self.translator.translate(text)
                return str(result) if result else None
            return None
        except Exception as e:
            log_error(f"Deep-translator error: {e}")
            return None

    def _translate_with_googletrans(self, text: str) -> str | None:
        """Translate text using googletrans library (fallback)."""
        if (
            not self.translator
            or self._googletrans_disabled
            or not GOOGLETRANS_AVAILABLE
        ):
            return None

        try:
            result = self.translator.translate(
                text,
                src=self.source_language,
                dest=self.target_language,
            )
            # Handle both sync and async results
            if hasattr(result, "text"):
                return str(result.text)
            if hasattr(result, "__await__"):
                # It's a coroutine, we can't handle it synchronously
                # Disable googletrans for this session to avoid repeated warnings
                if not self._googletrans_disabled:
                    log_warning(
                        "Warning: googletrans returned coroutine, disabling googletrans",
                    )
                    self._googletrans_disabled = True
                self.translator = None
                return None
            # Try to access the result directly
            return str(result)
        except Exception as e:
            if not self._googletrans_disabled:
                log_error(f"Google Translate error: {e}")
                self._googletrans_disabled = True
            return None

    def _try_api_translation(
        self,
        text: str,
        original_text: str,
    ) -> str | None:
        """Try API translation methods and return translated text or None."""
        # Try deep-translator first (most reliable)
        deep_translation = self._translate_with_deep_translator(text)
        if deep_translation:
            if deep_translation != original_text:
                log_info(
                    f"Translated '{original_text[:50]}...' -> '{deep_translation[:50]}...' ({self.source_language} -> {self.target_language})",
                )
            return deep_translation

        # Try API translation (if API key is available)
        api_translation = self._translate_with_api(text)
        if api_translation:
            if api_translation != original_text:
                log_info(
                    f"Translated '{original_text[:50]}...' -> '{api_translation[:50]}...' ({self.source_language} -> {self.target_language})",
                )
            return api_translation

        # Try googletrans fallback if API key is provided
        if self.api_key:
            googletrans_translation = self._translate_with_googletrans(text)
            if googletrans_translation:
                if googletrans_translation != original_text:
                    log_info(
                        f"Translated '{original_text[:50]}...' -> '{googletrans_translation[:50]}...' ({self.source_language} -> {self.target_language})",
                    )
                return googletrans_translation
            log_warning(
                f"Translation failed for '{original_text[:50]}...' (all methods failed)",
            )
        else:
            log_info(
                f"No translation attempted for '{original_text[:50]}...' (no API key)",
            )

        return None

    def translate_description(
        self,
        description: str,
        *,
        use_cache: bool = True,
        use_term_mapping: bool = True,
        use_api_translation: bool = True,
    ) -> str:
        """Translate a description from source language to target language.

        Args:
            description: Text to translate
            use_cache: Whether to use translation cache
            use_term_mapping: Whether to apply term mappings
            use_api_translation: Whether to use API translation

        Returns:
            Translated description or original if translation fails

        """
        if not description or self._should_skip_translation(description):
            return description

        # Check cache first
        cache_key = f"{self.source_language}_{self.target_language}_{description}"
        if use_cache and cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        original_text = description
        translated_text = description

        # Step 1: Apply term mappings if enabled
        if use_term_mapping and self.term_mappings:
            translated_text = self._apply_term_mapping(translated_text)

        # Step 2: Use API translation if enabled and available
        if use_api_translation and translated_text == original_text:
            api_result = self._try_api_translation(translated_text, original_text)
            if api_result:
                translated_text = api_result
        elif translated_text != original_text:
            # Term mapping was applied
            log_info(
                f"Applied term mapping '{original_text[:50]}...' -> '{translated_text[:50]}...'",
            )

        # Cache the result
        if use_cache and translated_text != original_text:
            self.translation_cache[cache_key] = translated_text
            self._save_cache()

        return translated_text

    def translate_batch(
        self,
        descriptions: list[str],
        *,
        use_cache: bool = True,
        use_term_mapping: bool = True,
        use_api_translation: bool = True,
    ) -> dict[str, str]:
        """Translate a batch of descriptions.

        Args:
            descriptions: List of descriptions to translate
            use_cache: Whether to use translation cache
            use_term_mapping: Whether to apply term mappings
            use_api_translation: Whether to use API translation

        Returns:
            Dictionary mapping original descriptions to translated versions

        """
        results = {}

        for description in descriptions:
            if description:
                translated = self.translate_description(
                    description,
                    use_cache=use_cache,
                    use_term_mapping=use_term_mapping,
                    use_api_translation=use_api_translation,
                )
                results[description] = translated

        return results

    def get_cache_stats(self) -> dict[str, int | str]:
        """Get translation cache statistics."""
        return {
            "total_entries": len(self.translation_cache),
            "cache_file": str(self.cache_file),
            "source_language": self.source_language,
            "target_language": self.target_language,
        }

    def clear_cache(self) -> None:
        """Clear the translation cache."""
        self.translation_cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()

    def add_custom_mapping(self, source_term: str, target_term: str) -> None:
        """Add a custom term mapping."""
        self.term_mappings[source_term] = target_term

    def export_cache(self, output_file: Path) -> None:
        """Export translation cache to file."""
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)

    def import_cache(self, input_file: Path) -> None:
        """Import translation cache from file."""
        try:
            with input_file.open(encoding="utf-8") as f:
                imported_cache = json.load(f)
                self.translation_cache.update(imported_cache)
                self._save_cache()
        except Exception as e:
            log_error(f"Error importing cache: {e}")

    def set_language_pair(
        self,
        source_language: Language | str,
        target_language: Language | str,
    ) -> None:
        """Set the source and target languages."""
        # Handle both enum instances and strings for language codes
        self.source_language = (
            source_language.value
            if hasattr(source_language, "value")
            else source_language
        )
        self.target_language = (
            target_language.value
            if hasattr(target_language, "value")
            else target_language
        )
        # Reinitialize translator with new language pair
        self._init_translator()

    def set_term_mappings(self, term_mappings: dict[str, str]) -> None:
        """Set the term mappings for the current language pair."""
        self.term_mappings = term_mappings


# Global singleton instance
_translation_service_instance: TranslationService | None = None


def get_translation_service(
    api_key: str | None = None,
    source_language: Language | None = None,
    target_language: Language | None = None,
    term_mappings: dict[str, str] | None = None,
    cache_file: Path | None = None,
) -> TranslationService:
    """Get a translation service instance with the specified configuration."""
    global _translation_service_instance

    # Return existing instance if it exists
    if _translation_service_instance is not None:
        return _translation_service_instance

    # Create new instance only once
    _translation_service_instance = TranslationService(
        api_key=api_key,
        source_language=source_language or get_language_th(),
        target_language=target_language or get_language_en(),
        term_mappings=term_mappings,
        cache_file=cache_file,
    )

    return _translation_service_instance


def translate_description(
    description: str,
    *,
    use_cache: bool = True,
    api_key: str | None = None,
    source_language: Language | None = None,
    target_language: Language | None = None,
    term_mappings: dict[str, str] | None = None,
    use_term_mapping: bool = True,
    use_api_translation: bool = True,
) -> str:
    """Translate a description using the specified configuration.

    Args:
        description: Text to translate
        use_cache: Whether to use translation cache
        api_key: Google Translate API key
        source_language: Source language code
        target_language: Target language code
        term_mappings: Dictionary of term mappings
        use_term_mapping: Whether to apply term mappings
        use_api_translation: Whether to use API translation

    Returns:
        Translated description or original if translation fails

    """
    config = TranslationConfig(
        description=description,
        use_cache=use_cache,
        api_key=api_key,
        source_language=source_language or get_language_th(),
        target_language=target_language or get_language_en(),
        term_mappings=term_mappings,
        use_term_mapping=use_term_mapping,
        use_api_translation=use_api_translation,
    )
    return _translate_description_impl(config)


def _translate_description_impl(config: TranslationConfig) -> str:
    """Internal implementation of translation using TranslationConfig."""
    service = get_translation_service(
        api_key=config.api_key,
        source_language=config.source_language,
        target_language=config.target_language,
        term_mappings=config.term_mappings,
    )

    return service.translate_description(
        config.description,
        use_cache=config.use_cache,
        use_term_mapping=config.use_term_mapping,
        use_api_translation=config.use_api_translation,
    )
