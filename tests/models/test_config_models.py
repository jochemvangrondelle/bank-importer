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

"""Tests for Pydantic configuration models."""

from pathlib import Path

import pytest

from bank_importer.models.config_models import (
    AccountConfig,
    ExportConfig,
    ImportJobInfo,
    ParserInfo,
    ProcessingResult,
    TargetConfig,
)


class TestAccountConfig:
    """Tests for AccountConfig model."""

    @pytest.mark.parametrize(
        ("name", "expected_currency", "expected_country"),
        [
            ("test_account", "THB", "TH"),
            ("account1", "THB", "TH"),
        ],
    )
    def test_init_minimal(
        self,
        name: str,
        expected_currency: str,
        expected_country: str,
    ) -> None:
        """Test minimal initialization."""
        config = AccountConfig(name=name)
        assert config.name == name
        assert config.currency == expected_currency
        assert config.country_code == expected_country

    @pytest.mark.parametrize(
        ("parser", "file_path", "file_pattern", "expected_parser"),
        [
            ("krungsri_text", "data/in", "*.txt", "krungsri_text"),
            ("scb_pdf", "data/in/SCB", "*.pdf", "scb_pdf"),
            (None, "data/in", "*", None),
        ],
    )
    def test_init_with_parser(
        self,
        parser: str | None,
        file_path: str,
        file_pattern: str,
        expected_parser: str | None,
    ) -> None:
        """Test initialization with parser configuration."""
        config = AccountConfig(
            name="test",
            parser=parser,
            file_path=file_path,
            file_pattern=file_pattern,
        )
        assert config.parser == expected_parser
        assert isinstance(config.file_path, Path)

    @pytest.mark.parametrize(
        ("file_path_input", "expected_type"),
        [
            ("data/in", Path),
            (Path("data/in"), Path),
            ("~/data/in", Path),
        ],
    )
    def test_file_path_conversion(
        self,
        file_path_input: str | Path,
        expected_type: type,
    ) -> None:
        """Test that file_path is converted to Path."""
        config = AccountConfig(name="test", file_path=file_path_input)
        assert isinstance(config.file_path, expected_type)

    @pytest.mark.parametrize(
        ("password_file_input", "expected_type"),
        [
            ("~/secrets/pass.txt", Path),
            (Path("secrets/pass.txt"), Path),
            (None, type(None)),
        ],
    )
    def test_password_file_conversion(
        self,
        password_file_input: str | Path | None,
        expected_type: type,
    ) -> None:
        """Test that password_file is converted to Path."""
        config = AccountConfig(name="test", password_file=password_file_input)
        if password_file_input is None:
            assert config.password_file is None
        else:
            assert isinstance(config.password_file, Path)

    def test_model_dump_dict(self) -> None:
        """Test converting to dictionary."""
        config = AccountConfig(name="test", file_path="data/in")
        data = config.model_dump_dict()
        assert isinstance(data, dict)
        assert data["name"] == "test"
        assert isinstance(data["file_path"], str)  # Converted back to string


class TestTargetConfig:
    """Tests for TargetConfig model."""

    @pytest.mark.parametrize(
        ("name", "expected_enabled"),
        [
            ("csv", True),
            ("yaml", True),
            ("firefly", True),
        ],
    )
    def test_init_minimal(self, name: str, expected_enabled: bool) -> None:
        """Test minimal initialization."""
        config = TargetConfig(name=name)
        assert config.name == name
        assert config.enabled == expected_enabled

    @pytest.mark.parametrize(
        ("enabled", "expected_enabled"),
        [
            (True, True),
            (False, False),
        ],
    )
    def test_init_with_enabled(self, enabled: bool, expected_enabled: bool) -> None:
        """Test initialization with enabled flag."""
        config = TargetConfig(name="csv", enabled=enabled)
        assert config.enabled == expected_enabled

    @pytest.mark.parametrize(
        ("output_dir_input", "expected_type"),
        [
            ("custom/output", Path),
            (Path("custom/output"), Path),
            (None, type(None)),
        ],
    )
    def test_output_dir_conversion(
        self,
        output_dir_input: str | Path | None,
        expected_type: type,
    ) -> None:
        """Test that output_dir is converted to Path."""
        config = TargetConfig(name="csv", output_dir=output_dir_input)
        if output_dir_input is None:
            assert config.output_dir is None
        else:
            assert isinstance(config.output_dir, Path)

    def test_model_dump_dict(self) -> None:
        """Test converting to dictionary."""
        config = TargetConfig(name="csv", output_dir="data/out")
        data = config.model_dump_dict()
        assert isinstance(data, dict)
        assert isinstance(data["output_dir"], str)  # Converted back to string


class TestExportConfig:
    """Tests for ExportConfig model."""

    @pytest.mark.parametrize(
        "export_type",
        [
            "all_consolidated",
            "bank_consolidated",
            "source_file",
            "account_reference",
        ],
    )
    def test_init_with_export_type(self, export_type: str) -> None:
        """Test initialization with different export types."""
        config = ExportConfig(export_type=export_type)
        assert config.export_type == export_type

    @pytest.mark.parametrize(
        ("output_dir_input", "expected_type"),
        [
            ("data/out", Path),
            (Path("data/out"), Path),
            (None, type(None)),
        ],
    )
    def test_output_dir_conversion(
        self,
        output_dir_input: str | Path | None,
        expected_type: type,
    ) -> None:
        """Test that output_dir is converted to Path."""
        config = ExportConfig(
            export_type="all_consolidated",
            output_dir=output_dir_input,
        )
        if output_dir_input is None:
            assert config.output_dir is None
        else:
            assert isinstance(config.output_dir, Path)

    @pytest.mark.parametrize(
        ("data_dict", "expected_type"),
        [
            ({"export_type": "all_consolidated"}, "all_consolidated"),
            (
                {
                    "export_type": "source_file",
                    "account_reference": "test",
                },
                "source_file",
            ),
        ],
    )
    def test_from_dict(self, data_dict: dict, expected_type: str) -> None:
        """Test creating from dictionary."""
        config = ExportConfig.from_dict(data_dict)
        assert config.export_type == expected_type

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        config = ExportConfig(export_type="all_consolidated", output_dir="data/out")
        data = config.to_dict()
        assert isinstance(data, dict)
        assert data["export_type"] == "all_consolidated"
        assert isinstance(data["output_dir"], str)  # Converted back to string


class TestParserInfo:
    """Tests for ParserInfo model."""

    @pytest.mark.parametrize(
        ("name", "bank_type", "extensions", "description"),
        [
            ("krungsri_text", "Krungsri", [".txt"], "Krungsri text parser"),
            ("scb_pdf", "SCB", [".pdf"], "SCB PDF parser"),
            ("generic_csv", "Generic", [".csv"], "Generic CSV parser"),
        ],
    )
    def test_init(
        self,
        name: str,
        bank_type: str,
        extensions: list[str],
        description: str,
    ) -> None:
        """Test initialization."""
        info = ParserInfo(
            name=name,
            bank_type=bank_type,
            supported_extensions=extensions,
            description=description,
        )
        assert info.name == name
        assert info.bank_type == bank_type
        assert info.supported_extensions == extensions


class TestImportJobInfo:
    """Tests for ImportJobInfo model."""

    @pytest.mark.parametrize(
        ("session_id", "account_name", "session_name", "status", "file_path"),
        [
            (1, "test_account", "2024-01", "completed", "test.txt"),
            (2, "account2", "2024-02", "failed", "test2.txt"),
            (3, "account3", "2024-03", "processing", "test3.txt"),
        ],
    )
    def test_init(
        self,
        session_id: int,
        account_name: str,
        session_name: str,
        status: str,
        file_path: str,
    ) -> None:
        """Test initialization."""
        info = ImportJobInfo(
            id=session_id,
            account_name=account_name,
            session_name=session_name,
            status=status,
            file_path=file_path,
        )
        assert info.id == session_id
        assert info.account_name == account_name
        assert info.status == status


class TestProcessingResult:
    """Tests for ProcessingResult model."""

    @pytest.mark.parametrize(
        (
            "account_name",
            "processed",
            "errors",
            "skipped",
            "expected_processed",
            "expected_errors",
        ),
        [
            ("test_account", 10, 0, 0, 10, 0),
            ("account2", 5, 2, 1, 5, 2),
            ("account3", 0, 0, 0, 0, 0),
        ],
    )
    def test_init(
        self,
        account_name: str,
        processed: int,
        errors: int,
        skipped: int,
        expected_processed: int,
        expected_errors: int,
    ) -> None:
        """Test initialization."""
        result = ProcessingResult(
            account_name=account_name,
            processed_transactions=processed,
            error_count=errors,
            skipped_files=skipped,
        )
        assert result.account_name == account_name
        assert result.processed_transactions == expected_processed
        assert result.error_count == expected_errors
        assert result.skipped_files == skipped
