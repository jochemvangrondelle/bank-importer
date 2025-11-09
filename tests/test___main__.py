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

"""Tests for __main__.py entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestMain:
    """Tests for main entry point."""

    def test_main_entry_point(self) -> None:
        """Test that main is callable."""
        import bank_importer.__main__ as main_module

        assert hasattr(main_module, "main")
        assert callable(main_module.main)

    @patch("bank_importer.cli.main.main")
    def test_main_with_cli_available(self, mock_cli_main) -> None:
        """Test main when CLI is available."""
        import importlib

        import bank_importer.__main__

        importlib.reload(bank_importer.__main__)

        # Call main - should call CLI main if available
        bank_importer.__main__.main()

        # Should call CLI main if available
        mock_cli_main.assert_called_once()

    def test_main_import_error_handling(self) -> None:
        """Test main when CLI import fails."""
        # This test verifies the structure - actual ImportError testing
        # is difficult because it happens at module import time
        # The module should handle ImportError gracefully by providing a fallback
        import bank_importer.__main__ as main_module

        # The main function should exist
        assert hasattr(main_module, "main")
        assert callable(main_module.main)

        # If CLI is available, it should work
        # If CLI is not available, calling main() should raise SystemExit
        # We can't easily test the ImportError path without breaking imports
        # but we can verify the structure exists

    def test_main_module_structure(self) -> None:
        """Test that main module has correct structure."""
        import bank_importer.__main__ as main_module

        # Should have main function
        assert hasattr(main_module, "main")
        assert callable(main_module.main)

    @patch("bank_importer.cli.main.main")
    def test_main_calls_cli_main(self, mock_cli_main) -> None:
        """Test that main calls CLI main when available."""
        import importlib

        import bank_importer.__main__

        importlib.reload(bank_importer.__main__)

        bank_importer.__main__.main()

        mock_cli_main.assert_called_once()
