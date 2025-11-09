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

"""Parser detection utility for automatically determining the best parser for a file."""

import fnmatch
import logging
from pathlib import Path
from typing import Any

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None  # type: ignore[assignment, misc]

from bank_importer.banks import (
    AmexThCsvParser,
    GenericCsvParser,
    GenericFixedWidthParser,
    GenericJsonParser,
    KrungsriPdfParser,
    KrungsriTextParser,
    ScbPdfParser,
)
from bank_importer.interfaces.parser import Parser


class ParserDetector:
    """Detect the best parser for a given file using parser attributes and content validation."""

    def __init__(self) -> None:
        """Initialize parser detector with all available parsers."""
        self.parsers = {
            "amex_th_csv": AmexThCsvParser(),
            "krungsri_text": KrungsriTextParser(),
            "krungsri_pdf": KrungsriPdfParser(),
            "scb_pdf": ScbPdfParser(),
            "generic_csv": GenericCsvParser(),
            "generic_json": GenericJsonParser(),
            "generic_fixed_width": GenericFixedWidthParser(),
        }
        self.logger = logging.getLogger(__name__)

    def detect_parser(
        self,
        file_path: Path,
        parent_folder_hint: str | None = None,
    ) -> str | None:
        """Detect the best parser for a given file using a multi-step validation process.

        Args:
            file_path: Path to the file to analyze
            parent_folder_hint: Optional hint from parent folder name (e.g., "SCB", "Krungsri")

        Returns:
            Name of the best parser, or None if no parser can handle the file

        """
        if not file_path.exists():
            self.logger.warning("File does not exist: %s", file_path)
            return None

        # Step 1: Filter parsers by file extension
        file_extension = file_path.suffix.lower()
        extension_candidates = self._get_parsers_by_extension(file_extension)

        if not extension_candidates:
            self.logger.warning(
                "No parsers support extension %s for file: %s",
                file_extension,
                file_path,
            )
            return None

        # Step 2: Filter by file patterns if available
        pattern_candidates = self._get_parsers_by_filename_pattern(
            file_path,
            extension_candidates,
        )

        # Step 3: Use parent folder hint to prioritize parsers
        if parent_folder_hint:
            prioritized_candidates = self._prioritize_by_folder_hint(
                pattern_candidates,
                parent_folder_hint,
            )
        else:
            prioritized_candidates = pattern_candidates

        # Step 4: Content validation - try each parser in order
        for parser_name in prioritized_candidates:
            if self._validate_parser_content(parser_name, file_path):
                self.logger.info(
                    "Detected parser '%s' for file: %s",
                    parser_name,
                    file_path,
                )
                return parser_name

        # Step 5: If no parser validates content, try remaining candidates
        remaining_candidates = [
            p for p in pattern_candidates if p not in prioritized_candidates
        ]
        for parser_name in remaining_candidates:
            if self._validate_parser_content(parser_name, file_path):
                self.logger.info(
                    "Detected parser '%s' for file: %s",
                    parser_name,
                    file_path,
                )
                return parser_name

        self.logger.warning("No suitable parser found for file: %s", file_path)
        return None

    def _get_parsers_by_extension(self, file_extension: str) -> list[str]:
        """Get parsers that support the given file extension."""
        candidates: list[str] = []
        for parser_name, parser in self.parsers.items():
            supported_extensions = parser.get_supported_extensions()
            if file_extension in supported_extensions:
                candidates.append(parser_name)
        return candidates

    def _get_parsers_by_filename_pattern(
        self,
        file_path: Path,
        extension_candidates: list[str],
    ) -> list[str]:
        """Filter parsers by filename patterns if available."""
        filename = file_path.name
        candidates: list[str] = []

        for parser_name in extension_candidates:
            parser = self.parsers[parser_name]
            patterns = parser.get_supported_file_patterns()

            # If no patterns defined, include the parser
            if not patterns:
                candidates.append(parser_name)
                continue

            # Check if filename matches any pattern
            for pattern in patterns:
                if self._matches_pattern(filename, pattern):
                    candidates.append(parser_name)
                    break

        return candidates

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches the given pattern."""
        return fnmatch.fnmatch(filename.lower(), pattern.lower())

    def _prioritize_by_folder_hint(
        self,
        candidates: list[str],
        folder_hint: str,
    ) -> list[str]:
        """Prioritize parsers based on folder hint."""
        folder_hint_lower = folder_hint.lower()
        prioritized: list[str] = []
        others: list[str] = []

        for parser_name in candidates:
            parser = self.parsers[parser_name]
            bank_type = parser.get_bank_type().lower()

            # Check if bank type matches folder hint
            if folder_hint_lower in bank_type or bank_type in folder_hint_lower:
                prioritized.append(parser_name)
            else:
                others.append(parser_name)

        return prioritized + others

    def _validate_parser_content(self, parser_name: str, file_path: Path) -> bool:
        """Validate that a parser can successfully parse the file content.

        This method performs a lightweight content validation without full parsing.
        """
        parser = self.parsers.get(parser_name)
        if not parser:
            return False

        try:
            # First, check if the parser's can_parse method returns True
            if not parser.can_parse(file_path):
                return False

            # For PDF files, perform additional content validation
            if file_path.suffix.lower() == ".pdf":
                return self._validate_pdf_content(parser, file_path)

            # For CSV files, perform header validation
            if file_path.suffix.lower() == ".csv":
                return self._validate_csv_content(parser, file_path)

            # For other file types, rely on can_parse
            return True

        except Exception as e:
            self.logger.debug(
                "Parser '%s' validation failed for %s: %s",
                parser_name,
                file_path,
                e,
            )
            return False

    def _validate_pdf_content(self, parser: Parser, file_path: Path) -> bool:
        """Validate PDF content by checking for bank-specific indicators."""
        if pdfium is None:
            return False

        try:
            # Get password from a minimal test config
            test_config = {
                "password": "test",
            }  # This will fail, but we can catch the error

            # Open PDF with pypdfium2
            pdf = pdfium.PdfDocument(
                file_path,
                password=test_config.get("password") or None,
            )

            try:
                if len(pdf) == 0:
                    return False

                # Extract text from first page
                first_page = pdf[0]
                textpage = first_page.get_textpage()
                text = textpage.get_text_range()

                if not text:
                    return False

                # Check for bank-specific indicators based on parser type
                bank_type = parser.get_bank_type().lower()

                if bank_type == "scb":
                    scb_indicators = [
                        "ACCOUNT STATEMENT WITH NOTES",
                        "SCB",
                        "Siam Commercial Bank",
                        "012-3-45678-9",
                    ]
                    return any(indicator in text for indicator in scb_indicators)

                if bank_type == "krungsri":
                    krungsri_indicators = [
                        "Bank of Ayudhya",
                        "Krungsri",
                        "Statement of Savings Account",
                        "XXX-1-32483-X",
                    ]
                    return any(indicator in text for indicator in krungsri_indicators)

                # For other banks, return True if can_parse passed
                return True
            finally:
                pdf.close()

        except Exception as e:
            # If we can't open the PDF (e.g., wrong password), we can't validate content
            # In this case, we'll rely on the folder hint and file patterns
            self.logger.debug("Could not validate PDF content for %s: %s", file_path, e)
            return True  # Allow the parser to try

    def _validate_csv_content(self, parser: Parser, file_path: Path) -> bool:
        """Validate CSV content by checking headers."""
        try:
            with file_path.open(encoding="utf-8") as f:
                first_line = f.readline().strip()

                if not first_line:
                    return False

                # Check for bank-specific headers
                bank_type = parser.get_bank_type().lower()

                if bank_type == "amex_th":
                    amex_indicators = [
                        "Card Member",
                        "Statement Date",
                        "American Express",
                    ]
                    return any(indicator in first_line for indicator in amex_indicators)

                # For generic CSV, accept any CSV format
                return True

        except Exception as e:
            self.logger.debug("Could not validate CSV content for %s: %s", file_path, e)
            return True

    def get_parser(self, parser_name: str) -> Parser | None:
        """Get a parser instance by name.

        Args:
            parser_name: Name of the parser

        Returns:
            Parser instance or None if not found

        """
        return self.parsers.get(parser_name)

    def list_available_parsers(self) -> list[str]:
        """Get a list of available parser names.

        Returns:
            List of parser names

        """
        return list(self.parsers.keys())

    def get_parser_info(self, parser_name: str) -> dict[str, Any] | None:
        """Get information about a parser.

        Args:
            parser_name: Name of the parser

        Returns:
            Dictionary with parser information or None if not found

        """
        parser = self.parsers.get(parser_name)
        if not parser:
            return None

        return {
            "name": parser_name,
            "description": parser.get_parser_description(),
            "supported_extensions": parser.get_supported_extensions(),
            "supported_file_patterns": parser.get_supported_file_patterns(),
            "bank_type": parser.get_bank_type(),
            "parser_version": parser.get_parser_version(),
        }
