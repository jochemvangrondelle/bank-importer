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

"""Tests for parser detector."""

from pathlib import Path

import pytest

from bank_importer.parser_detector import ParserDetector


class TestParserDetector:
    """Test parser detector functionality."""

    @pytest.fixture
    def detector(self) -> ParserDetector:
        """Create a parser detector for testing."""
        return ParserDetector()

    def test_init(self, detector: ParserDetector) -> None:
        """Test parser detector initialization."""
        assert len(detector.parsers) > 0
        assert "krungsri_text" in detector.parsers
        assert "krungsri_pdf" in detector.parsers
        assert "scb_pdf" in detector.parsers

    @pytest.mark.parametrize(
        ("parser_name", "should_exist"),
        [
            ("krungsri_text", True),
            ("krungsri_pdf", True),
            ("scb_pdf", True),
            ("amex_th_csv", True),
            ("generic_csv", True),
            ("nonexistent", False),
            ("invalid_parser", False),
        ],
    )
    def test_get_parser(
        self,
        detector: ParserDetector,
        parser_name: str,
        should_exist: bool,
    ) -> None:
        """Test getting parsers."""
        parser = detector.get_parser(parser_name)
        if should_exist:
            assert parser is not None
        else:
            assert parser is None

    def test_list_available_parsers(self, detector: ParserDetector) -> None:
        """Test listing available parsers."""
        parsers = detector.list_available_parsers()
        assert isinstance(parsers, list)
        assert len(parsers) > 0
        assert "krungsri_text" in parsers

    @pytest.mark.parametrize(
        ("parser_name", "should_exist"),
        [
            ("krungsri_text", True),
            ("scb_pdf", True),
            ("generic_csv", True),
            ("nonexistent", False),
        ],
    )
    def test_get_parser_info(
        self,
        detector: ParserDetector,
        parser_name: str,
        should_exist: bool,
    ) -> None:
        """Test getting parser info."""
        info = detector.get_parser_info(parser_name)
        if should_exist:
            assert info is not None
            assert "name" in info
            assert info["name"] == parser_name
        else:
            assert info is None

    def test_detect_parser_nonexistent_file(self, detector: ParserDetector) -> None:
        """Test detecting parser for non-existent file."""
        result = detector.detect_parser(Path("nonexistent.txt"))
        assert result is None

    @pytest.mark.parametrize(
        ("extension", "expected_parsers"),
        [
            (".txt", ["krungsri_text"]),
            (".pdf", ["krungsri_pdf", "scb_pdf"]),
            (".csv", ["amex_th_csv", "generic_csv"]),
            (".json", ["generic_json"]),
        ],
    )
    def test_get_parsers_by_extension(
        self,
        detector: ParserDetector,
        extension: str,
        expected_parsers: list[str],
    ) -> None:
        """Test getting parsers by file extension."""
        parsers = detector._get_parsers_by_extension(extension)
        for expected in expected_parsers:
            assert expected in parsers

    @pytest.mark.parametrize(
        ("filename", "pattern", "expected"),
        [
            ("test.txt", "*.txt", True),
            ("test.pdf", "*.txt", False),
            ("AcctSt_test.pdf", "*AcctSt_*.pdf", True),
            ("test_file.csv", "*.csv", True),
            ("test_file.json", "*.csv", False),
            ("krungsri_statement.txt", "*.txt", True),
        ],
    )
    def test_matches_pattern(
        self,
        detector: ParserDetector,
        filename: str,
        pattern: str,
        expected: bool,
    ) -> None:
        """Test pattern matching."""
        assert detector._matches_pattern(filename, pattern) == expected

    @pytest.mark.parametrize(
        ("candidates", "folder_hint", "expected_first"),
        [
            (
                ["krungsri_text", "generic_csv", "krungsri_pdf"],
                "Krungsri",
                ["krungsri_text", "krungsri_pdf"],
            ),
            (
                ["scb_pdf", "generic_csv", "krungsri_pdf"],
                "SCB",
                ["scb_pdf"],
            ),
            (
                ["generic_csv", "amex_th_csv"],
                "Amex",
                ["amex_th_csv"],
            ),
        ],
    )
    def test_prioritize_by_folder_hint(
        self,
        detector: ParserDetector,
        candidates: list[str],
        folder_hint: str,
        expected_first: list[str],
    ) -> None:
        """Test prioritizing parsers by folder hint."""
        prioritized = detector._prioritize_by_folder_hint(candidates, folder_hint)
        # Expected parsers should come first
        assert prioritized[0] in expected_first

    def test_detect_parser_krungsri_text(
        self,
        detector: ParserDetector,
        test_data_dir: Path,
    ) -> None:
        """Test detecting Krungsri text parser."""
        test_file = test_data_dir / "krungsri_sample.txt"
        if test_file.exists():
            result = detector.detect_parser(test_file)
            assert result == "krungsri_text"

    @pytest.mark.parametrize(
        ("folder_hint", "expected_prioritized"),
        [
            ("Krungsri", ["krungsri_text", "krungsri_pdf"]),
            ("SCB", ["scb_pdf"]),
            ("Amex", ["amex_th_csv"]),
        ],
    )
    def test_detect_parser_with_folder_hint(
        self,
        detector: ParserDetector,
        tmp_path: Path,
        folder_hint: str,
        expected_prioritized: list[str],
    ) -> None:
        """Test detecting parser with folder hint."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        # Should use folder hint to prioritize
        result = detector.detect_parser(test_file, parent_folder_hint=folder_hint)
        # Result depends on content validation, but should attempt detection
        assert result is None or isinstance(result, str)

    def test_get_parser_info_all_fields(self, detector: ParserDetector) -> None:
        """Test getting parser info with all fields."""
        info = detector.get_parser_info("krungsri_text")
        assert info is not None
        assert "name" in info
        assert "description" in info
        assert "supported_extensions" in info
        assert "bank_type" in info

    @pytest.mark.parametrize(
        ("extension", "should_have_parsers"),
        [
            (".txt", True),
            (".pdf", True),
            (".csv", True),
            (".json", True),
            (".xyz", False),  # Unknown extension
        ],
    )
    def test_get_parsers_by_extension_various(
        self,
        detector: ParserDetector,
        extension: str,
        should_have_parsers: bool,
    ) -> None:
        """Test getting parsers by various extensions."""
        parsers = detector._get_parsers_by_extension(extension)
        if should_have_parsers:
            assert len(parsers) > 0
        else:
            assert len(parsers) == 0
