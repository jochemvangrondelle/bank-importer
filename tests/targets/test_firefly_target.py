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

"""Tests for Firefly-III target."""

from pathlib import Path

import pytest

from bank_importer.targets.firefly_target import FireflyTarget


class TestFireflyTarget:
    """Tests for FireflyTarget."""

    @pytest.fixture
    def firefly_target(self, tmp_path: Path) -> FireflyTarget:
        """Create a Firefly target for testing."""
        return FireflyTarget(output_dir=str(tmp_path / "output"))

    def test_init(self, firefly_target: FireflyTarget, tmp_path: Path) -> None:
        """Test Firefly target initialization."""
        assert firefly_target.output_dir.exists()
        assert firefly_target.get_name() == "firefly"

    def test_get_name(self, firefly_target: FireflyTarget) -> None:
        """Test getting target name."""
        assert firefly_target.get_name() == "firefly"

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("test_file.csv", "test_file"),
            ("test-file.csv", "test_file"),
            ("test file.csv", "test_file"),
            (
                "very_long_filename_that_should_be_truncated.csv",
                "very_long_filename_that_should",
            ),
        ],
    )
    def test_clean_filename(
        self,
        firefly_target: FireflyTarget,
        filename: str,
        expected: str,
    ) -> None:
        """Test filename cleaning."""
        result = firefly_target._clean_filename(filename)
        assert result == expected
        assert len(result) <= 30

    def test_export_transactions_empty(self, firefly_target: FireflyTarget) -> None:
        """Test exporting empty transaction list."""
        result = firefly_target.export_transactions([], {})
        assert result.success is True
        assert result.exported_count == 0

    @pytest.mark.parametrize(
        ("export_type", "account_ref", "expected_prefix"),
        [
            ("all_consolidated", "all_accounts", "firefly-all-transactions"),
            ("bank_consolidated", "bank_krungsri", "firefly-krungsri-all"),
            ("source_file", "test_account", "firefly-test_account"),
        ],
    )
    def test_export_transactions_filename(
        self,
        firefly_target: FireflyTarget,
        sample_transaction,
        export_type: str,
        account_ref: str,
        expected_prefix: str,
    ) -> None:
        """Test export generates correct filename."""
        config = {
            "export_type": export_type,
            "account_reference": account_ref,
            "bank_type": "krungsri" if export_type == "bank_consolidated" else None,
        }
        # For source_file type, provide original_filename to use account_ref in filename
        if export_type == "source_file":
            config["original_filename"] = account_ref
        result = firefly_target.export_transactions([sample_transaction], config)
        assert result.success is True
        assert result.output_file is not None
        assert expected_prefix in result.output_file
