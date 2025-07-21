"""Parser interface for bank statements."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from ..models.transaction import Transaction


class Parser(ABC):
    """Abstract base class for bank statement parsers."""

    @abstractmethod
    def parse_file(self, file_path: Path, account_config: dict) -> Iterator[Transaction]:
        """Parse a bank statement file and yield transactions."""
        pass

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        pass
