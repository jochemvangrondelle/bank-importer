"""Parser interface for bank statements."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..models.transaction import Transaction


class Parser(ABC):
    """Abstract base class for bank statement parsers."""

    @abstractmethod
    def parse_file(
        self, file_path: Path, account_config: dict, config_manager=None
    ) -> Iterator[Transaction]:
        """Parse a bank statement file and yield transactions."""
        pass

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        pass

    def get_bank_type(self) -> str:
        """Get the bank type identifier for this parser."""
        raise NotImplementedError("Subclasses must implement get_bank_type()")

    def get_export_config(self) -> dict[str, Any]:
        """Get export configuration specific to this parser."""
        raise NotImplementedError("Subclasses must implement get_export_config()")

    def get_parser_name(self) -> str:
        """Get the parser name identifier."""
        raise NotImplementedError("Subclasses must implement get_parser_name()")

    def get_default_account_name(self) -> str:
        """Get the default account name for this parser."""
        raise NotImplementedError(
            "Subclasses must implement get_default_account_name()"
        )

    def get_default_account_number(self) -> str:
        """Get the default account number for this parser."""
        raise NotImplementedError(
            "Subclasses must implement get_default_account_number()"
        )

    def get_default_currency(self) -> str:
        """Get the default currency for this parser."""
        raise NotImplementedError("Subclasses must implement get_default_currency()")

    def get_default_country_code(self) -> str:
        """Get the default country code for this parser."""
        raise NotImplementedError(
            "Subclasses must implement get_default_country_code()"
        )

    def get_supported_file_patterns(self) -> list[str]:
        """Get list of supported file patterns for this parser."""
        raise NotImplementedError(
            "Subclasses must implement get_supported_file_patterns()"
        )

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for this parser."""
        raise NotImplementedError(
            "Subclasses must implement get_supported_extensions()"
        )

    def get_parser_description(self) -> str:
        """Get a human-readable description of this parser."""
        raise NotImplementedError("Subclasses must implement get_parser_description()")

    def get_parser_version(self) -> str:
        """Get the parser version."""
        raise NotImplementedError("Subclasses must implement get_parser_version()")
