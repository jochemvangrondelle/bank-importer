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

"""Tests for opposing account pattern matching."""

import pytest

from bank_importer.translation_terms.opposing_account_patterns import (
    extract_opposing_account,
)


class TestOpposingAccountPatterns:
    """Tests for opposing account pattern matching."""

    def test_extract_opposing_account_transfer(self) -> None:
        """Test extracting opposing account from transfer description."""
        description = "Transfer to BBL x9551 MR VASAN NARDVIRIY"
        name, number = extract_opposing_account(description)
        assert isinstance(name, str)
        assert isinstance(number, str)
        assert "VASAN" in name or "BBL" in name
        assert "9551" in number

    def test_extract_opposing_account_bill_payment(self) -> None:
        """Test extracting opposing account from bill payment."""
        description = "Bill Payment HARNG CENTRAL DEPARTMENT STORE L"
        name, _number = extract_opposing_account(description)
        assert isinstance(name, str)
        assert "HARNG" in name or "CENTRAL" in name

    def test_extract_opposing_account_empty(self) -> None:
        """Test extracting from empty description."""
        name, number = extract_opposing_account("")
        assert name == ""
        assert number == ""

    def test_extract_opposing_account_none(self) -> None:
        """Test extracting from None description."""
        name, number = extract_opposing_account(None)  # type: ignore[arg-type]
        assert name == ""
        assert number == ""

    def test_extract_opposing_account_no_match(self) -> None:
        """Test extracting when no pattern matches."""
        description = "Random transaction description"
        name, number = extract_opposing_account(description)
        assert isinstance(name, str)
        assert isinstance(number, str)

    @pytest.mark.parametrize(
        ("description", "expected_contains"),
        [
            ("Transfer to KBANK x1234 JOHN DOE", ["KBANK", "1234", "JOHN"]),
            ("Transfer to TTB x1863 PREEYANUT PAN", ["TTB", "1863", "PREEYANUT"]),
            ("จ่ายบิล HARNG CENTRAL DEPARTMENT STORE", ["HARNG", "CENTRAL"]),
        ],
    )
    def test_extract_opposing_account_various_patterns(
        self,
        description: str,
        expected_contains: list[str],
    ) -> None:
        """Test extracting from various description patterns."""
        name, number = extract_opposing_account(description)
        result_text = f"{name} {number}".upper()
        for expected in expected_contains:
            assert expected.upper() in result_text
