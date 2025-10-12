"""Translate command for the bank importer CLI."""

import typer

from ...cli_parameters import CONFIG_FILE_PARAM, VERBOSE_PARAM
from ...cli_utils import cli_error_handler
from ...config import ConfigManager
from ...logging_config import (
    get_logger,
    log_error,
    log_info,
    setup_logging,
)


@cli_error_handler
def translate(
    text: str = typer.Option(None, "--text", "-t", help="Translate specific text"),
    clear_cache: bool = typer.Option(
        False, "--clear-cache", help="Clear translation cache"
    ),
    stats: bool = typer.Option(
        False, "--stats", help="Show translation cache statistics"
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
        f"DEBUG: Parameters - text: '{text}', clear_cache: {clear_cache}, stats: {stats}"
    )

    try:
        # Get API key from config
        from pathlib import Path

        from ...translation_service import get_translation_service

        config_manager = ConfigManager(Path(config_file))
        # Look for API key in CSV target config
        api_key = None
        for target in config_manager.config.get("targets", []):
            if target.get("name") == "csv" and "csv_config" in target:
                api_key = target["csv_config"].get("google_translate_api_key")
                break

        service = get_translation_service(api_key=api_key)

        if clear_cache:
            service.clear_cache()
            log_info("Translation cache cleared")

        elif stats:
            stats_data = service.get_cache_stats()
            log_info("Translation cache statistics:")
            log_info(f"  Total cached translations: {stats_data['total_cached']}")
            log_info(f"  Cache file size: {stats_data['cache_file_size']} bytes")

        elif text:
            translated = service.translate_description(text)
            log_info(f"Original: {text}")
            log_info(f"Translated: {translated}")

        else:
            log_info("Translation service commands:")
            log_info("  --text 'text'          - Translate specific text")
            log_info("  --clear-cache          - Clear translation cache")
            log_info("  --stats                - Show cache statistics")

    except ImportError:
        log_error(
            "Translation service not available. Install with: pip install googletrans==4.0.0rc1"
        )
    except Exception as e:
        log_error(f"Error with translation service: {e}")
        raise typer.Exit(1) from e
