"""Parser detection utility for automatically determining the best parser for a file."""

import logging
from pathlib import Path
from typing import Any

from .banks import (
    GenericCsvParser,
    GenericFixedWidthParser,
    GenericJsonParser,
    KrungsriPdfParser,
    KrungsriTextParser,
    ScbPdfParser,
)
from .interfaces.parser import Parser


class ParserDetector:
    """Detect the best parser for a given file by trying each parser."""

    def __init__(self):
        """Initialize parser detector with all available parsers."""
        self.parsers = {
            "krungsri_text": KrungsriTextParser(),
            "krungsri_pdf": KrungsriPdfParser(),
            "scb_pdf": ScbPdfParser(),
            "generic_csv": GenericCsvParser(),
            "generic_json": GenericJsonParser(),
            "generic_fixed_width": GenericFixedWidthParser(),
        }
        self.logger = logging.getLogger(__name__)

    def detect_parser(self, file_path: Path) -> str | None:
        """
        Detect the best parser for a given file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Name of the best parser, or None if no parser can handle the file
        """
        if not file_path.exists():
            self.logger.warning(f"File does not exist: {file_path}")
            return None

        # Get file extension for initial filtering
        file_extension = file_path.suffix.lower()

        # Try parsers in order of specificity (most specific first)
        parser_order = [
            # Bank-specific parsers first
            ("krungsri_pdf", [".pdf"]),
            ("krungsri_text", [".txt"]),
            ("scb_pdf", [".pdf"]),
            # Generic parsers last
            ("generic_csv", [".csv"]),
            ("generic_json", [".json"]),
            ("generic_fixed_width", [".txt", ".dat", ".prn"]),
        ]

        for parser_name, supported_extensions in parser_order:
            if file_extension in supported_extensions:
                if self._test_parser(parser_name, file_path):
                    self.logger.info(
                        f"Detected parser '{parser_name}' for file: {file_path}"
                    )
                    return parser_name

        self.logger.warning(f"No suitable parser found for file: {file_path}")
        return None

    def _test_parser(self, parser_name: str, file_path: Path) -> bool:
        """
        Test if a parser can successfully parse a file.

        Args:
            parser_name: Name of the parser to test
            file_path: Path to the file to test

        Returns:
            True if the parser can parse the file, False otherwise
        """
        parser = self.parsers.get(parser_name)
        if not parser:
            self.logger.warning(f"Parser '{parser_name}' not found")
            return False

        try:
            # Create a minimal account config for testing
            test_account_config = {
                "account_number": "TEST123",
                "account_name": "Test Account",
                "bank_name": "Test Bank",
                "currency": "THB",
                "country_code": "TH",
            }

            # Try to parse the file
            transactions = list(parser.parse_file(file_path, test_account_config))

            # Check if we got any transactions
            if transactions and len(transactions) > 0:
                self.logger.debug(
                    f"Parser '{parser_name}' successfully parsed {len(transactions)} transactions from {file_path}"
                )
                return True
            else:
                self.logger.debug(
                    f"Parser '{parser_name}' parsed file but found no transactions: {file_path}"
                )
                return False

        except Exception as e:
            self.logger.debug(
                f"Parser '{parser_name}' failed to parse {file_path}: {e}"
            )
            return False

    def get_parser(self, parser_name: str) -> Parser | None:
        """
        Get a parser instance by name.

        Args:
            parser_name: Name of the parser

        Returns:
            Parser instance or None if not found
        """
        return self.parsers.get(parser_name)

    def list_available_parsers(self) -> list[str]:
        """
        Get a list of available parser names.

        Returns:
            List of parser names
        """
        return list(self.parsers.keys())

    def get_parser_info(self, parser_name: str) -> dict[str, Any] | None:
        """
        Get information about a parser.

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
            "description": getattr(parser, "__doc__", "No description available"),
            "supported_extensions": getattr(parser, "supported_extensions", []),
        }
