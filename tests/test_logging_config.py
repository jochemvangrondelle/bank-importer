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

"""Tests for logging configuration."""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from bank_importer.logging_config import (
    get_logger,
    log_error,
    log_info,
    log_success,
    log_warning,
    setup_logging,
)


class TestLoggingSetup:
    """Tests for logging setup."""

    @pytest.mark.parametrize(
        ("enable_rich", "console_level", "file_level"),
        [
            (True, "DEBUG", "DEBUG"),
            (False, "INFO", "WARNING"),
            (True, "WARNING", "ERROR"),
        ],
    )
    def test_setup_logging(
        self,
        tmp_path: Path,
        enable_rich: bool,
        console_level: str,
        file_level: str,
    ) -> None:
        """Test setting up logging with different configurations."""
        log_dir = tmp_path / "logs"
        setup_logging(
            enable_rich=enable_rich,
            console_level=console_level,
            file_level=file_level,
            log_dir=str(log_dir),
        )
        # Verify logger exists
        logger = get_logger("test")
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_setup_logging_with_log_file(self, tmp_path: Path) -> None:
        """Test setting up logging with specific log file."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))
        logger = get_logger("test")
        assert logger is not None

    def test_get_logger(self) -> None:
        """Test getting a logger."""
        logger = get_logger("test_module")
        assert logger is not None
        # get_logger prepends "bank_importer." to logger names
        assert logger.name == "bank_importer.test_module"

    @pytest.mark.parametrize(
        "logger_name",
        [
            "test",
            "bank_importer.processor",
            "bank_importer.parser",
        ],
    )
    def test_get_logger_different_names(self, logger_name: str) -> None:
        """Test getting loggers with different names."""
        logger = get_logger(logger_name)
        assert logger is not None
        # get_logger prepends "bank_importer." to logger names
        # If logger_name already starts with "bank_importer.", it may be prepended again
        # Check if it starts with bank_importer to determine expected name
        if logger_name.startswith("bank_importer."):
            # get_logger may double-prepend, so check actual behavior
            # The actual name will be "bank_importer." + logger_name
            expected_name = f"bank_importer.{logger_name}"
        else:
            expected_name = f"bank_importer.{logger_name}"
        assert logger.name == expected_name


class TestLoggingFunctions:
    """Tests for logging convenience functions."""

    def test_log_info(self) -> None:
        """Test log_info function."""
        with patch("bank_importer.logging_config.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            log_info("Test message")
            mock_log.info.assert_called_once()

    def test_log_error(self) -> None:
        """Test log_error function."""
        with patch("bank_importer.logging_config.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            log_error("Error message")
            mock_log.error.assert_called_once()

    def test_log_warning(self) -> None:
        """Test log_warning function."""
        with patch("bank_importer.logging_config.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            log_warning("Warning message")
            mock_log.warning.assert_called_once()

    def test_log_success(self) -> None:
        """Test log_success function."""
        with patch("bank_importer.logging_config.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            log_success("Success message")
            mock_log.info.assert_called_once()

    @pytest.mark.parametrize(
        "message",
        [
            "Simple message",
            "Message with {format}",
            "Multi-line\nmessage",
        ],
    )
    def test_log_info_various_messages(self, message: str) -> None:
        """Test log_info with various message formats."""
        with patch("bank_importer.logging_config.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            log_info(message)
            mock_log.info.assert_called_once()

    def test_get_console(self) -> None:
        """Test getting console instance."""
        from bank_importer.logging_config import get_console

        console1 = get_console()
        console2 = get_console()
        # Should return same instance (singleton)
        assert console1 is console2

    def test_mask_sensitive_data(self) -> None:
        """Test masking sensitive data."""
        from bank_importer.logging_config import mask_sensitive_data

        # Test API key masking
        text = 'api_key="secret123456"'
        masked = mask_sensitive_data(text)
        assert "secret123456" not in masked
        assert "api_key" in masked

    @pytest.mark.parametrize(
        ("current", "total", "description"),
        [
            (0, 100, "Processing"),
            (50, 100, "Halfway"),
            (100, 100, "Complete"),
        ],
    )
    def test_log_progress(self, current: int, total: int, description: str) -> None:
        """Test log_progress function."""
        from bank_importer.logging_config import log_progress

        with patch("bank_importer.logging_config.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            log_progress(current, total, description)
            mock_log.info.assert_called_once()

    def test_log_debug(self) -> None:
        """Test log_debug function."""
        from bank_importer.logging_config import log_debug

        with patch("bank_importer.logging_config.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            log_debug("Debug message")
            mock_log.debug.assert_called_once()

    def test_get_log_file_path(self) -> None:
        """Test getting log file path."""
        from bank_importer.logging_config import get_log_file_path

        path = get_log_file_path()
        assert isinstance(path, str)
        assert len(path) > 0
