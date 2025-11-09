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

"""Tests for export targets."""

from pathlib import Path

import pytest

from bank_importer.targets.csv_target import CsvTarget
from bank_importer.targets.yaml_target import YamlTarget


class TestCsvTarget:
    """Test CSV target functionality."""

    @pytest.fixture
    def csv_target(self, tmp_path: Path) -> CsvTarget:
        """Create a CSV target for testing."""
        return CsvTarget(output_dir=str(tmp_path / "output"))

    def test_init(self, csv_target: CsvTarget, tmp_path: Path) -> None:
        """Test CSV target initialization."""
        assert csv_target.output_dir.exists()
        assert csv_target.get_name() == "csv"

    def test_get_name(self, csv_target: CsvTarget) -> None:
        """Test getting target name."""
        assert csv_target.get_name() == "csv"

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("test_file.txt", "test_file"),
            ("test-file.txt", "test_file"),
            ("test file.txt", "test_file"),
            (
                "very_long_filename_that_should_be_truncated.txt",
                "very_long_filename_that_should",
            ),
            ("test@file#123.txt", "testfile123"),
        ],
    )
    def test_clean_filename(
        self,
        csv_target: CsvTarget,
        filename: str,
        expected: str,
    ) -> None:
        """Test filename cleaning."""
        result = csv_target._clean_filename(filename)
        assert result == expected
        assert len(result) <= 30

    def test_export_transactions_empty(self, csv_target: CsvTarget) -> None:
        """Test exporting empty transaction list."""
        result = csv_target.export_transactions([], {})
        assert result.success is True
        assert result.exported_count == 0

    def test_export_transactions_consolidated(
        self,
        csv_target: CsvTarget,
        sample_transaction,
    ) -> None:
        """Test exporting transactions with consolidated export type."""
        config = {
            "export_type": "all_consolidated",
            "account_reference": "all_accounts",
        }
        result = csv_target.export_transactions([sample_transaction], config)
        assert result.success is True
        assert result.exported_count == 1
        assert result.output_file is not None
        assert result.metadata is not None
        assert "filename" in result.metadata

    def test_export_transactions_source_file(
        self,
        csv_target: CsvTarget,
        sample_transaction,
    ) -> None:
        """Test exporting transactions with source file export type."""
        config = {
            "export_type": "source_file",
            "source_file": "test.txt",
            "account_reference": "test_account",
        }
        result = csv_target.export_transactions([sample_transaction], config)
        assert result.success is True
        assert result.exported_count == 1

    def test_export_transactions_custom_output_dir(
        self,
        csv_target: CsvTarget,
        sample_transaction,
        tmp_path: Path,
    ) -> None:
        """Test exporting with custom output directory."""
        custom_dir = tmp_path / "custom_output"
        config = {
            "export_type": "all_consolidated",
            "output_dir": str(custom_dir),
        }
        result = csv_target.export_transactions([sample_transaction], config)
        assert result.success is True
        assert custom_dir.exists()

    def test_transaction_to_csv_row(
        self,
        csv_target: CsvTarget,
        sample_transaction,
    ) -> None:
        """Test converting transaction to CSV row."""
        config = {
            "account_config": {
                "name": "test_account",
                "account_number": "123-456-789",
            },
        }
        row = csv_target._transaction_to_csv_row(sample_transaction, config)
        assert isinstance(row, dict)
        assert "date" in row
        assert "description" in row
        assert "amount" in row

    @pytest.mark.parametrize(
        ("transaction_type", "expected_negative"),
        [
            ("debit", True),
            ("withdrawal", True),
            ("payment", True),
            ("credit", False),
            ("deposit", False),
            ("receipt", False),
        ],
    )
    def test_transaction_to_csv_row_amount_sign(
        self,
        csv_target: CsvTarget,
        transaction_factory,
        transaction_type: str,
        expected_negative: bool,
    ) -> None:
        """Test that transaction amount sign is correct based on type."""
        transaction = transaction_factory(
            transaction_type=transaction_type,
            amount="100.00",
        )
        config = {"account_config": {}}
        row = csv_target._transaction_to_csv_row(transaction, config)
        amount = float(row["amount"])
        if expected_negative:
            assert amount < 0
        else:
            assert amount > 0

    def test_extract_opposing_account(self, csv_target: CsvTarget) -> None:
        """Test extracting opposing account from description."""
        description = "Transfer From Acc No. : X123456"
        name, number = csv_target._extract_opposing_account(description)
        assert isinstance(name, str)
        assert isinstance(number, str)

    def test_generate_external_id(
        self,
        csv_target: CsvTarget,
        sample_transaction,
    ) -> None:
        """Test generating external ID for transaction."""
        external_id = csv_target._generate_external_id(sample_transaction)
        assert isinstance(external_id, str)
        assert len(external_id) > 0

    def test_looks_like_transaction_id(self, csv_target: CsvTarget) -> None:
        """Test checking if reference looks like transaction ID."""
        # Valid transaction IDs (don't contain generic patterns)
        assert csv_target._looks_like_transaction_id("TXN20240101123456") is True
        assert csv_target._looks_like_transaction_id("ID123456789") is True
        assert csv_target._looks_like_transaction_id("ABC-123-456") is True
        assert csv_target._looks_like_transaction_id("XYZ_123_456") is True
        # Invalid - contains generic patterns (ref, test, etc.)
        assert (
            csv_target._looks_like_transaction_id("REF123456") is False
        )  # contains "ref"
        assert (
            csv_target._looks_like_transaction_id("REF-123-456") is False
        )  # contains "ref"
        assert (
            csv_target._looks_like_transaction_id("TEST123456") is False
        )  # contains "test"
        # Invalid - contains spaces or special chars
        assert csv_target._looks_like_transaction_id("Normal description") is False
        assert csv_target._looks_like_transaction_id("REF 123 456") is False
        # Invalid - too short
        assert csv_target._looks_like_transaction_id("test") is False
        assert csv_target._looks_like_transaction_id("") is False
        # Invalid - generic patterns
        assert csv_target._looks_like_transaction_id("scb_main") is False
        assert csv_target._looks_like_transaction_id("reference") is False


class TestYamlTarget:
    """Test YAML target functionality."""

    @pytest.fixture
    def yaml_target(self, tmp_path: Path) -> YamlTarget:
        """Create a YAML target for testing."""
        return YamlTarget(output_dir=str(tmp_path / "output"))

    def test_init(self, yaml_target: YamlTarget, tmp_path: Path) -> None:
        """Test YAML target initialization."""
        assert yaml_target.output_dir.exists()
        assert yaml_target.get_name() == "yaml"

    def test_get_name(self, yaml_target: YamlTarget) -> None:
        """Test getting target name."""
        assert yaml_target.get_name() == "yaml"

    def test_export_transactions_empty(self, yaml_target: YamlTarget) -> None:
        """Test exporting empty transaction list."""
        result = yaml_target.export_transactions([], {})
        assert result.success is True
        assert result.exported_count == 0

    def test_export_transactions_consolidated(
        self,
        yaml_target: YamlTarget,
        sample_transaction,
    ) -> None:
        """Test exporting transactions with consolidated export type."""
        config = {
            "export_type": "all_consolidated",
            "account_reference": "all_accounts",
        }
        result = yaml_target.export_transactions([sample_transaction], config)
        assert result.success is True
        assert result.exported_count == 1
        assert result.output_file is not None or (
            hasattr(result, "metadata") and "output_file" in result.metadata
        )
        assert hasattr(result, "metadata")

    def test_export_transactions_source_file(
        self,
        yaml_target: YamlTarget,
        sample_transaction,
    ) -> None:
        """Test exporting transactions with source file export type."""
        config = {
            "export_type": "source_file",
            "source_file": "test.txt",
            "account_reference": "test_account",
        }
        result = yaml_target.export_transactions([sample_transaction], config)
        assert result.success is True
        assert result.exported_count == 1

    def test_export_transactions_generates_summary(
        self,
        yaml_target: YamlTarget,
        sample_transactions,
    ) -> None:
        """Test that YAML export generates summary file."""
        config = {
            "export_type": "all_consolidated",
            "account_reference": "all_accounts",
        }
        result = yaml_target.export_transactions(sample_transactions, config)
        assert result.success is True
        assert result.metadata is not None
        assert (
            "summary_filename" in result.metadata or "summary_file" in result.metadata
        )
