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

"""Lazy import utilities for heavy modules.

This module provides lazy loading for modules that have significant import overhead,
improving startup time by deferring imports until they're actually needed.

Uses lazy_loader library for consistent lazy loading patterns.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # Type checkers see the real imports
    pass
else:
    # Runtime uses lazy loading
    try:
        import lazy_loader as lazy

        # Lazy load Firefly client (editable install overhead)
        firefly_iii_api_client = lazy.load("firefly_iii_api_client")

        # Lazy load Rich (CLI formatting, only needed for CLI)
        rich = lazy.load("rich")
        rich_console = lazy.load("rich.console")
        rich_table = lazy.load("rich.table")

        # Note: Pydantic is used extensively and is relatively fast to import,
        # so we don't lazy load it. It's also required for type checking.
    except ImportError:
        # Fallback to regular imports if lazy_loader not available
        import firefly_iii_api_client
        from rich import console as rich_console
        from rich import table as rich_table


def get_firefly_client() -> Any:
    """Get Firefly III API client module (lazy loaded).

    Returns:
        firefly_iii_api_client module

    """
    return firefly_iii_api_client


def get_rich_console() -> Any:
    """Get Rich Console class (lazy loaded).

    Returns:
        Rich Console class

    """
    return rich_console.Console


def get_rich_table() -> Any:
    """Get Rich Table class (lazy loaded).

    Returns:
        Rich Table class

    """
    return rich_table.Table
