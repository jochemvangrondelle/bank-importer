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

"""Integration tests for Krungsri text parser."""

from typing import Any

from tests.integration.base import BaseParserIntegrationTest


class TestKrungsriTextIntegration(BaseParserIntegrationTest):
    """Integration tests for Krungsri text parser."""

    @property
    def parser_name(self) -> str:
        """Return the parser name."""
        return "krungsri_text"

    @property
    def test_file_name(self) -> str:
        """Return the test file name."""
        return "krungsri_valid.txt"

    def create_account_config(self, **kwargs: Any) -> dict[str, Any]:
        """Create account configuration for Krungsri text."""
        config = super().create_account_config(**kwargs)
        config.update({"bank_name": "Krungsri"})
        return config

    def validate_imported_transactions(
        self,
        transactions: list[Any],
        expected_min_count: int = 1,
    ) -> None:
        """Validate Krungsri text transactions."""
        super().validate_imported_transactions(transactions, expected_min_count)
        # Krungsri-specific validations
        for transaction in transactions:
            assert transaction.currency == "THB", "Krungsri transactions should be THB"
