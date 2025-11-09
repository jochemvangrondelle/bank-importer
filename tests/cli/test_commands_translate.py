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

"""Tests for CLI translate command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer

from bank_importer.cli.commands import translate


class TestTranslateCommand:
    """Tests for translate command."""

    @patch("bank_importer.cli.commands.translate.setup_logging")
    @patch("bank_importer.cli.commands.translate.get_logger")
    @patch("bank_importer.cli.commands.translate.ConfigManager")
    @patch("bank_importer.cli.commands.translate.get_translation_service_from_config")
    def test_translate_with_text(
        self,
        mock_get_service,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test translate command with text."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager.config = {
            "translation": {"google_translate_api_key": "test_key"}
        }
        mock_config_manager_class.return_value = mock_config_manager
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        with patch(
            "bank_importer.cli.commands.translate.translate_text",
            return_value="translated_text",
        ):
            with patch(
                "bank_importer.cli.commands.translate.log_info"
            ) as mock_log_info:
                # Ensure clear_cache and stats are False explicitly
                translate.translate(
                    text="hello",
                    config_file="config.toml",
                    verbose=False,
                    clear_cache=False,
                    stats=False,
                )

                mock_log_info.assert_called()
                # Check that log_info was called with original and translated text
                # Get all call arguments - log_info can be called multiple times
                all_call_args = []
                for call in mock_log_info.call_args_list:
                    if call[0]:  # positional arguments exist
                        all_call_args.append(str(call[0][0]))
                all_calls_str = " ".join(all_call_args)
                # Should contain either the original text or translated text
                assert (
                    "hello" in all_calls_str
                    or "translated_text" in all_calls_str
                    or "Original:" in all_calls_str
                    or "Translated:" in all_calls_str
                )

    @patch("bank_importer.cli.commands.translate.setup_logging")
    @patch("bank_importer.cli.commands.translate.get_logger")
    @patch("bank_importer.cli.commands.translate.ConfigManager")
    @patch("bank_importer.cli.commands.translate.get_translation_service_from_config")
    def test_translate_clear_cache(
        self,
        mock_get_service,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test translate command with clear_cache."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager_class.return_value = mock_config_manager
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        with patch("bank_importer.cli.commands.translate.log_info") as mock_log_info:
            translate.translate(
                clear_cache=True, config_file="config.toml", verbose=False
            )

            mock_service.clear_cache.assert_called_once()
            mock_log_info.assert_called()

    @patch("bank_importer.cli.commands.translate.setup_logging")
    @patch("bank_importer.cli.commands.translate.get_logger")
    @patch("bank_importer.cli.commands.translate.ConfigManager")
    @patch("bank_importer.cli.commands.translate.get_translation_service_from_config")
    def test_translate_stats(
        self,
        mock_get_service,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test translate command with stats."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager_class.return_value = mock_config_manager
        mock_service = MagicMock()
        mock_service.get_cache_stats.return_value = {
            "total_cached": 10,
            "cache_file_size": 1024,
        }
        mock_get_service.return_value = mock_service

        with patch("bank_importer.cli.commands.translate.log_info") as mock_log_info:
            # Explicitly set all parameters to ensure stats branch is taken
            translate.translate(
                text=None,
                stats=True,
                clear_cache=False,
                config_file="config.toml",
                verbose=False,
            )

            mock_service.get_cache_stats.assert_called_once()
            mock_log_info.assert_called()
            # Check that stats were logged
            all_call_args = [
                call[0][0] if call[0] else "" for call in mock_log_info.call_args_list
            ]
            all_calls_str = " ".join(all_call_args)
            # Stats should contain the numbers
            assert "10" in all_calls_str or "1024" in all_calls_str

    @patch("bank_importer.cli.commands.translate.setup_logging")
    @patch("bank_importer.cli.commands.translate.get_logger")
    @patch("bank_importer.cli.commands.translate.ConfigManager")
    @patch("bank_importer.cli.commands.translate.get_translation_service_from_config")
    def test_translate_no_options(
        self,
        mock_get_service,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test translate command with no options."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager_class.return_value = mock_config_manager
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        with patch("bank_importer.cli.commands.translate.log_info") as mock_log_info:
            # Explicitly set all parameters to None/False to trigger the else branch
            translate.translate(
                text=None,
                stats=False,
                clear_cache=False,
                config_file="config.toml",
                verbose=False,
            )

            # Should show usage hints
            mock_log_info.assert_called()
            all_call_args = [
                call[0][0] if call[0] else "" for call in mock_log_info.call_args_list
            ]
            all_calls_str = " ".join(all_call_args)
            assert (
                "--text" in all_calls_str
                or "Translation service commands" in all_calls_str
            )

    @patch("bank_importer.cli.commands.translate.setup_logging")
    @patch("bank_importer.cli.commands.translate.get_logger")
    @patch("bank_importer.cli.commands.translate.ConfigManager")
    @patch("bank_importer.cli.commands.translate.get_translation_service_from_config")
    def test_translate_service_not_available(
        self,
        mock_get_service,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test translate command when service is not available."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager_class.return_value = mock_config_manager
        mock_get_service.return_value = None

        with patch("bank_importer.cli.commands.translate.log_error") as mock_log_error:
            # When service is None, the function raises typer.Exit(1) which becomes SystemExit
            with pytest.raises(SystemExit):
                translate.translate(config_file="config.toml", verbose=False)

            mock_log_error.assert_called()

    @patch("bank_importer.cli.commands.translate.setup_logging")
    @patch("bank_importer.cli.commands.translate.get_logger")
    @patch("bank_importer.cli.commands.translate.ConfigManager")
    def test_translate_import_error(
        self,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test translate command with ImportError."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager_class.return_value = mock_config_manager

        with patch(
            "bank_importer.cli.commands.translate.get_translation_service_from_config",
            side_effect=ImportError("Service not available"),
        ):
            with patch(
                "bank_importer.cli.commands.translate.log_error"
            ) as mock_log_error:
                translate.translate(config_file="config.toml", verbose=False)

                mock_log_error.assert_called()

    @patch("bank_importer.cli.commands.translate.setup_logging")
    @patch("bank_importer.cli.commands.translate.get_logger")
    @patch("bank_importer.cli.commands.translate.ConfigManager")
    @patch("bank_importer.cli.commands.translate.get_translation_service_from_config")
    def test_translate_with_verbose(
        self,
        mock_get_service,
        mock_config_manager_class,
        mock_get_logger,
        mock_setup_logging,
    ) -> None:
        """Test translate command with verbose flag."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_config_manager = MagicMock()
        mock_config_manager_class.return_value = mock_config_manager
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        translate.translate(config_file="config.toml", verbose=True)

        # Should setup logging with DEBUG level
        call_kwargs = mock_setup_logging.call_args[1]
        assert call_kwargs["console_level"] == "DEBUG"
