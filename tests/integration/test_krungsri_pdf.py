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

"""Integration tests for Krungsri PDF parser."""

from typing import Any

from tests.integration.base import BaseParserIntegrationTest


class TestKrungsriPdfIntegration(BaseParserIntegrationTest):
    """Integration tests for Krungsri PDF parser."""

    @property
    def parser_name(self) -> str:
        """Return the parser name."""
        return "krungsri_pdf"

    @property
    def test_file_name(self) -> str:
        """Return the test file name."""
        return "krungsri_valid.pdf"

    def create_account_config(self, **kwargs: Any) -> dict[str, Any]:
        """Create account configuration for Krungsri PDF."""
        config = super().create_account_config(**kwargs)
        # Password is optional - only include if provided
        # If PDF is password-protected and no password provided, parser will raise error
        password = kwargs.get("password")
        config.update(
            {
                "bank_name": "Krungsri",
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
        """Validate Krungsri PDF transactions."""
        super().validate_imported_transactions(transactions, expected_min_count)
        # Krungsri-specific validations can be added here
        for transaction in transactions:
            # Krungsri transactions typically have THB currency
            assert transaction.currency == "THB", "Krungsri transactions should be THB"
