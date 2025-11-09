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

"""Translation endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from bank_importer.api.dependencies import get_config_manager
from bank_importer.api.security import require_auth
from bank_importer.config import ConfigManager
from bank_importer.library import (
    get_translation_service_from_config,
    translate_text,
)
from bank_importer.models.enums import Language, get_language_en, get_language_th

router = APIRouter()


@router.post("/translate", tags=["Translation"])
async def translate_text_endpoint(
    text: str,
    source_language: Language | None = None,
    target_language: Language | None = None,
    config: ConfigManager = Depends(get_config_manager),
    _: dict = Depends(require_auth),
) -> dict[str, str]:
    """Translate text."""
    # Get API key from config
    translation_config = config.config.get("translation", {})
    api_key = translation_config.get("google_translate_api_key")

    try:
        translated = translate_text(
            text,
            api_key=api_key,
            source_language=source_language or get_language_th(),
            target_language=target_language or get_language_en(),
        )

        return {
            "original": text,
            "translated": translated,
        }
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service not available. Install with: uv sync --group translate",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {e!s}",
        ) from e


@router.delete("/cache", status_code=status.HTTP_204_NO_CONTENT, tags=["Translation"])
async def clear_translation_cache(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> None:
    """Clear translation cache."""
    try:
        service = get_translation_service_from_config(config)
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Translation service not available. Install with: uv sync --group translate",
            )
        service.clear_cache()
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service not available. Install with: uv sync --group translate",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {e!s}",
        ) from e


@router.get("/cache", tags=["Translation"])
async def get_translation_cache_stats(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
    _: Annotated[dict, Depends(require_auth)],
) -> dict[str, Any]:
    """Get translation cache statistics."""
    try:
        service = get_translation_service_from_config(config)
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Translation service not available. Install with: uv sync --group translate",
            )
        stats = service.get_cache_stats()

        return {
            "total_cached": stats.get("total_cached", 0),
            "cache_file_size": stats.get("cache_file_size", 0),
            "cache_file_path": stats.get("cache_file_path", ""),
        }
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service not available. Install with: uv sync --group translate",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {e!s}",
        ) from e
