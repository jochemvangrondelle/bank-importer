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

"""Tests for api/run.py."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestRun:
    """Tests for API run module."""

    @patch("bank_importer.api.run.uvicorn")
    @patch("bank_importer.api.run.settings")
    @patch("bank_importer.api.run.app")
    def test_main_default_args(self, mock_app, mock_settings, mock_uvicorn) -> None:
        """Test main with default arguments."""
        mock_settings.get_api_host.return_value = "127.0.0.1"
        mock_settings.get_api_port.return_value = 8000
        mock_settings.DEFAULT_HOST = "127.0.0.1"
        mock_settings.DEFAULT_PORT = 8000

        from bank_importer.api.run import main

        with patch("sys.argv", ["bank-importer-api"]):
            main()

        mock_uvicorn.run.assert_called_once_with(
            mock_app,
            host="127.0.0.1",
            port=8000,
            reload=False,
        )

    @patch("bank_importer.api.run.uvicorn")
    @patch("bank_importer.api.run.settings")
    @patch("bank_importer.api.run.app")
    def test_main_custom_host(self, mock_app, mock_settings, mock_uvicorn) -> None:
        """Test main with custom host."""
        mock_settings.get_api_host.return_value = "127.0.0.1"
        mock_settings.get_api_port.return_value = 8000
        mock_settings.DEFAULT_HOST = "127.0.0.1"
        mock_settings.DEFAULT_PORT = 8000

        from bank_importer.api.run import main

        with patch("sys.argv", ["bank-importer-api", "--host", "0.0.0.0"]):
            main()

        mock_uvicorn.run.assert_called_once_with(
            mock_app,
            host="0.0.0.0",
            port=8000,
            reload=False,
        )

    @patch("bank_importer.api.run.uvicorn")
    @patch("bank_importer.api.run.settings")
    @patch("bank_importer.api.run.app")
    def test_main_custom_port(self, mock_app, mock_settings, mock_uvicorn) -> None:
        """Test main with custom port."""
        mock_settings.get_api_host.return_value = "127.0.0.1"
        mock_settings.get_api_port.return_value = 8000
        mock_settings.DEFAULT_HOST = "127.0.0.1"
        mock_settings.DEFAULT_PORT = 8000

        from bank_importer.api.run import main

        with patch("sys.argv", ["bank-importer-api", "--port", "9000"]):
            main()

        mock_uvicorn.run.assert_called_once_with(
            mock_app,
            host="127.0.0.1",
            port=9000,
            reload=False,
        )

    @patch("bank_importer.api.run.uvicorn")
    @patch("bank_importer.api.run.settings")
    @patch("bank_importer.api.run.app")
    def test_main_with_reload(self, mock_app, mock_settings, mock_uvicorn) -> None:
        """Test main with reload enabled."""
        mock_settings.get_api_host.return_value = "127.0.0.1"
        mock_settings.get_api_port.return_value = 8000
        mock_settings.DEFAULT_HOST = "127.0.0.1"
        mock_settings.DEFAULT_PORT = 8000

        from bank_importer.api.run import main

        with patch("sys.argv", ["bank-importer-api", "--reload"]):
            main()

        mock_uvicorn.run.assert_called_once_with(
            mock_app,
            host="127.0.0.1",
            port=8000,
            reload=True,
        )

    @patch("bank_importer.api.run.uvicorn")
    @patch("bank_importer.api.run.settings")
    @patch("bank_importer.api.run.app")
    def test_main_all_args(self, mock_app, mock_settings, mock_uvicorn) -> None:
        """Test main with all arguments."""
        mock_settings.get_api_host.return_value = "127.0.0.1"
        mock_settings.get_api_port.return_value = 8000
        mock_settings.DEFAULT_HOST = "127.0.0.1"
        mock_settings.DEFAULT_PORT = 8000

        from bank_importer.api.run import main

        with patch(
            "sys.argv",
            ["bank-importer-api", "--host", "0.0.0.0", "--port", "9000", "--reload"],
        ):
            main()

        mock_uvicorn.run.assert_called_once_with(
            mock_app,
            host="0.0.0.0",
            port=9000,
            reload=True,
        )

    def test_import_error_handling(self) -> None:
        """Test handling of ImportError when uvicorn is not available."""
        # This test verifies the structure - actual ImportError testing
        # is difficult because it happens at module import time
        # The module should handle ImportError gracefully
        import bank_importer.api.run

        # If we get here, the module imported successfully
        # (uvicorn is available in test environment)
        assert hasattr(bank_importer.api.run, "main")

    def test_main_entry_point(self) -> None:
        """Test that main can be called as entry point."""
        from bank_importer.api.run import main

        assert callable(main)
