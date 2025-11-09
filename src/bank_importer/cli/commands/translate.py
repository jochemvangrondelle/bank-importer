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

"""Translate command for the bank importer CLI."""

from pathlib import Path

import typer

from bank_importer.cli.parameters import CONFIG_FILE_PARAM, VERBOSE_PARAM
from bank_importer.cli.utils import cli_error_handler
from bank_importer.config import ConfigManager
from bank_importer.library import (
    get_translation_service_from_config,
    translate_text,
)
from bank_importer.logging_config import (
    get_logger,
    log_error,
    log_info,
    setup_logging,
)


@cli_error_handler
def translate(
    text: str = typer.Option(None, "--text", "-t", help="Translate specific text"),
    *,
    clear_cache: bool = typer.Option(
        False,
        "--clear-cache",
        help="Clear translation cache",
    ),
    stats: bool = typer.Option(
        False,
        "--stats",
        help="Show translation cache statistics",
    ),
    config_file: str = CONFIG_FILE_PARAM,
    verbose: bool = VERBOSE_PARAM,
) -> None:
    """**Manage** translation service."""
    # Setup logging
    console_level = "DEBUG" if verbose else "INFO"
    setup_logging(
        enable_rich=True,
        console_level=console_level,
        file_level="DEBUG",
    )
    logger = get_logger("cli")

    logger.info("🌐 Starting Bank Importer - Translation Mode")
    logger.info(
        "DEBUG: Parameters - text: '%s', clear_cache: %s, stats: %s",
        text,
        clear_cache,
        stats,
    )

    try:
        # Get config manager
        config_manager = ConfigManager(Path(config_file))

        # Get translation service from config (uses library function)
        service = get_translation_service_from_config(config_manager)

        if service is None:
            log_error(
                "Translation service not available. Install with: uv sync --group translate",
            )
            raise typer.Exit(1)

        if clear_cache:
            service.clear_cache()
            log_info("Translation cache cleared")

        elif stats:
            stats_data = service.get_cache_stats()
            log_info("Translation cache statistics:")
            log_info(f"  Total cached translations: {stats_data['total_cached']}")
            log_info(f"  Cache file size: {stats_data['cache_file_size']} bytes")

        elif text:
            # Get API key from config for direct translation
            translation_config = config_manager.config.get("translation", {})
            api_key = translation_config.get("google_translate_api_key")
            translated = translate_text(text, api_key=api_key)
            log_info(f"Original: {text}")
            log_info(f"Translated: {translated}")

        else:
            log_info("Translation service commands:")
            log_info("  --text 'text'          - Translate specific text")
            log_info("  --clear-cache          - Clear translation cache")
            log_info("  --stats                - Show cache statistics")

    except ImportError:
        log_error(
            "Translation service not available. Install with: uv sync --group translate",
        )
    except Exception as e:
        log_error(f"Error with translation service: {e}")
        raise typer.Exit(1) from e
