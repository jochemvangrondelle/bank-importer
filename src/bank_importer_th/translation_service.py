"""Translation service for converting transaction descriptions between languages."""

import json
import re
from pathlib import Path

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
    from googletrans import Translator

    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False


class TranslationService:
    """Service for translating transaction descriptions."""

    def __init__(
        self,
        cache_file: Path | None = None,
        api_key: str | None = None,
        source_language: str = "th",
        target_language: str = "en",
        term_mappings: dict[str, str] | None = None,
    ):
        self.api_key = api_key
        self.source_language = source_language
        self.target_language = target_language
        self.term_mappings = term_mappings or {}
        self.cache_file = cache_file or Path("translation_cache.json")
        self.translation_cache = self._load_cache()
        self.translator = None
        self._googletrans_disabled = False  # Flag to prevent repeated warnings
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
                    source=source_lang, target=target_lang
                )
                # Only print once during initialization
                print(
                    f"INFO: Translation service initialized ({source_lang} -> {target_lang})"
                )
            except Exception as e:
                print(f"Warning: Failed to initialize deep-translator: {e}")
                self.translator = None
        elif GOOGLETRANS_AVAILABLE:
            try:
                from googletrans import Translator

                self.translator = Translator()
                print(
                    f"INFO: Translation service initialized with googletrans ({self.source_language} -> {self.target_language})"
                )
            except Exception as e:
                print(f"Warning: Failed to initialize googletrans: {e}")
                self.translator = None
        else:
            print("Warning: No translation library available")
            self.translator = None

    def _load_cache(self) -> dict[str, str]:
        """Load translation cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load translation cache: {e}")
        return {}

    def _save_cache(self) -> None:
        """Save translation cache to file."""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save translation cache: {e}")

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
            # Use word boundaries to avoid partial matches
            pattern = r"\b" + re.escape(source_term) + r"\b"
            result = re.sub(pattern, target_term, result, flags=re.IGNORECASE)

        return result

    def _translate_with_api(self, text: str) -> str | None:
        """Translate text using Google Translate API."""
        if not self.api_key:
            # API key not provided, skip API translation
            return None
        if not REQUESTS_AVAILABLE:
            print("Warning: requests library not available for API translation")
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
            if "data" in data and "translations" in data["data"]:
                return data["data"]["translations"][0]["translatedText"]

        except Exception as e:
            print(f"API translation error: {e}")

        return None

    def _translate_with_deep_translator(self, text: str) -> str | None:
        """Translate text using deep-translator library."""
        if not self.translator or not DEEP_TRANSLATOR_AVAILABLE:
            return None

        try:
            # deep-translator uses a different API
            if hasattr(self.translator, "translate"):
                result = self.translator.translate(text)
                return result
            else:
                return None
        except Exception as e:
            print(f"Deep-translator error: {e}")
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
                text, src=self.source_language, dest=self.target_language
            )
            # Handle both sync and async results
            if hasattr(result, "text"):
                return result.text
            elif hasattr(result, "__await__"):
                # It's a coroutine, we can't handle it synchronously
                # Disable googletrans for this session to avoid repeated warnings
                if not self._googletrans_disabled:
                    print(
                        "Warning: googletrans returned coroutine, disabling googletrans"
                    )
                    self._googletrans_disabled = True
                self.translator = None
                return None
            else:
                # Try to access the result directly
                return str(result)
        except Exception as e:
            if not self._googletrans_disabled:
                print(f"Google Translate error: {e}")
                self._googletrans_disabled = True
            return None

    def translate_description(
        self,
        description: str,
        use_cache: bool = True,
        use_term_mapping: bool = True,
        use_api_translation: bool = True,
    ) -> str:
        """
        Translate a description from source language to target language.

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
            # Try deep-translator first (most reliable)
            deep_translation = self._translate_with_deep_translator(translated_text)
            if deep_translation:
                translated_text = deep_translation
                # Only log successful translations, not every attempt
                if translated_text != original_text:
                    print(
                        f"INFO: Translated '{original_text[:50]}...' -> '{deep_translation[:50]}...' ({self.source_language} -> {self.target_language})"
                    )
            else:
                # Try API translation (if API key is available)
                api_translation = self._translate_with_api(translated_text)
                if api_translation:
                    translated_text = api_translation
                    if translated_text != original_text:
                        print(
                            f"INFO: Translated '{original_text[:50]}...' -> '{api_translation[:50]}...' ({self.source_language} -> {self.target_language})"
                        )
                elif self.api_key:
                    # API key is provided but translation failed, try googletrans fallback
                    googletrans_translation = self._translate_with_googletrans(
                        translated_text
                    )
                    if googletrans_translation:
                        translated_text = googletrans_translation
                        if translated_text != original_text:
                            print(
                                f"INFO: Translated '{original_text[:50]}...' -> '{googletrans_translation[:50]}...' ({self.source_language} -> {self.target_language})"
                            )
                    else:
                        print(
                            f"DEBUG: Translation failed for '{original_text[:50]}...' (all methods failed)"
                        )
                # If no API key is provided, skip API translation entirely
                # Term mapping has already been applied above
                else:
                    print(
                        f"DEBUG: No translation attempted for '{original_text[:50]}...' (no API key)"
                    )
        elif translated_text != original_text:
            # Term mapping was applied
            print(
                f"INFO: Applied term mapping '{original_text[:50]}...' -> '{translated_text[:50]}...'"
            )

        # Cache the result
        if use_cache and translated_text != original_text:
            self.translation_cache[cache_key] = translated_text
            self._save_cache()

        return translated_text

    def translate_batch(
        self,
        descriptions: list[str],
        use_cache: bool = True,
        use_term_mapping: bool = True,
        use_api_translation: bool = True,
    ) -> dict[str, str]:
        """
        Translate a batch of descriptions.

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

    def get_cache_stats(self) -> dict[str, int]:
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
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)

    def import_cache(self, input_file: Path) -> None:
        """Import translation cache from file."""
        try:
            with open(input_file, encoding="utf-8") as f:
                imported_cache = json.load(f)
                self.translation_cache.update(imported_cache)
                self._save_cache()
        except Exception as e:
            print(f"Error importing cache: {e}")

    def set_language_pair(self, source_language: str, target_language: str) -> None:
        """Set the source and target languages."""
        self.source_language = source_language
        self.target_language = target_language

    def set_term_mappings(self, term_mappings: dict[str, str]) -> None:
        """Set the term mappings for the current language pair."""
        self.term_mappings = term_mappings


# Global singleton instance
_translation_service_instance = None


def get_translation_service(
    api_key: str | None = None,
    source_language: str = "th",
    target_language: str = "en",
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
        source_language=source_language,
        target_language=target_language,
        term_mappings=term_mappings,
        cache_file=cache_file,
    )

    return _translation_service_instance


def translate_description(
    description: str,
    use_cache: bool = True,
    api_key: str | None = None,
    source_language: str = "th",
    target_language: str = "en",
    term_mappings: dict[str, str] | None = None,
    use_term_mapping: bool = True,
    use_api_translation: bool = True,
) -> str:
    """
    Translate a description using the specified configuration.

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
    service = get_translation_service(
        api_key=api_key,
        source_language=source_language,
        target_language=target_language,
        term_mappings=term_mappings,
    )

    return service.translate_description(
        description,
        use_cache=use_cache,
        use_term_mapping=use_term_mapping,
        use_api_translation=use_api_translation,
    )
