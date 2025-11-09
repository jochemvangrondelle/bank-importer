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

"""Integration tests for SCB PDF parser."""

from typing import Any

from tests.integration.base import BaseParserIntegrationTest


class TestScbPdfIntegration(BaseParserIntegrationTest):
    """Integration tests for SCB PDF parser."""

    @property
    def parser_name(self) -> str:
        """Return the parser name."""
        return "scb_pdf"

    @property
    def test_file_name(self) -> str:
        """Return the test file name."""
        return "scb_valid.pdf"

    def create_account_config(self, **kwargs: Any) -> dict[str, Any]:
        """Create account configuration for SCB PDF."""
        config = super().create_account_config(**kwargs)
        # Password is optional - only include if provided
        # If PDF is password-protected and no password provided, parser will raise error
        password = kwargs.get("password")
        config.update(
            {
                "bank_name": "SCB",
            },
        )
        if password:
            config["password"] = password
        return config

    def validate_imported_transactions(
        self,
        transactions: list[Any],
        expected_min_count: int = 1,
    ) -> None:
        """Validate SCB PDF transactions."""
        super().validate_imported_transactions(transactions, expected_min_count)
        # SCB-specific validations
        for transaction in transactions:
            assert transaction.currency == "THB", "SCB transactions should be THB"
