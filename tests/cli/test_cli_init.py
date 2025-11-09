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

"""Tests for cli/__init__.py."""

import sys
from unittest.mock import patch


class TestCliInit:
    """Tests for CLI __init__ module."""

    def test_cli_init_with_imports_available(self) -> None:
        """Test CLI __init__ when imports are available."""
        import importlib

        import bank_importer.cli

        importlib.reload(bank_importer.cli)

        # Should have __all__ defined
        assert hasattr(bank_importer.cli, "__all__")
        assert "app" in bank_importer.cli.__all__
        assert "main" in bank_importer.cli.__all__

    def test_cli_init_structure(self) -> None:
        """Test CLI __init__ structure."""
        import bank_importer.cli

        # Should have __all__ defined
        assert hasattr(bank_importer.cli, "__all__")
        # __all__ should be a list (empty or with items)
        assert isinstance(bank_importer.cli.__all__, list)

    def test_cli_init_exports(self) -> None:
        """Test that CLI module exports expected items."""
        import bank_importer.cli

        # Should export app and main if CLI is available
        if hasattr(bank_importer.cli, "__all__") and bank_importer.cli.__all__:
            assert "app" in bank_importer.cli.__all__
            assert "main" in bank_importer.cli.__all__
