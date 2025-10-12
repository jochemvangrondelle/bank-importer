"""Generic fixed-width text parser for transaction data."""

import json
import re
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..config import ConfigManager

from ..interfaces.parser import Parser
from ..models.transaction import Transaction


class GenericFixedWidthParser(Parser):
    """Generic parser for fixed-width text files."""

    def get_bank_type(self) -> str:
        """Get the bank type identifier for this parser."""
        return "generic"

    def get_export_config(self) -> dict[str, Any]:
        """Get export configuration specific to this parser."""
        return {
            "bank_name": "Generic Bank",
            "default_account_name": "Generic Account",
            "default_account_number": "0000000000",
            "default_currency": "THB",
            "default_country_code": "TH",
            "supports_foreign_currency": False,
            "supports_translation": False,
            "translation_source_language": "en",
            "translation_target_language": "en",
        }

    def get_parser_name(self) -> str:
        """Get the parser name identifier."""
        return "generic_fixed_width"

    def get_default_account_name(self) -> str:
        """Get the default account name for this parser."""
        return "Generic Account"

    def get_default_account_number(self) -> str:
        """Get the default account number for this parser."""
        return "0000000000"

    def get_default_currency(self) -> str:
        """Get the default currency for this parser."""
        return "THB"

    def get_default_country_code(self) -> str:
        """Get the default country code for this parser."""
        return "TH"

    def get_supported_file_patterns(self) -> list[str]:
        """Get list of supported file patterns for this parser."""
        return ["*.txt", "*.dat", "*.prn"]

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for this parser."""
        return [".txt", ".dat", ".prn"]

    def get_parser_description(self) -> str:
        """Get a human-readable description of this parser."""
        return "Generic fixed-width text parser for legacy bank formats"

    def get_parser_version(self) -> str:
        """Get the parser version."""
        return "1.0.0"

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in [".txt", ".dat", ".prn"]

    def parse_file(
        self,
        file_path: Path,
        account_config: dict[str, Any],
        config_manager: "ConfigManager | None" = None,
    ) -> Iterator[Transaction]:
        """Parse fixed-width text file and yield Transaction objects."""
        try:
            with open(file_path, encoding="utf-8") as file:
                # Try to detect encoding if UTF-8 fails
                try:
                    lines = file.readlines()
                except UnicodeDecodeError:
                    with open(file_path, encoding="latin-1") as file2:
                        lines = file2.readlines()

                # Auto-detect field positions from header or first few lines
                field_positions = self._detect_field_positions(lines)

                if not field_positions:
                    raise ValueError("Could not detect field positions")

                # Process each line
                for line_num, line in enumerate(lines, start=1):
                    line = line.rstrip("\n\r")
                    if not line.strip():
                        continue

                    try:
                        transaction = self._parse_line(
                            line, field_positions, account_config, file_path, line_num
                        )
                        if transaction:
                            yield transaction
                    except Exception as e:
                        print(f"Error parsing line {line_num} in {file_path}: {e}")
                        continue

        except Exception as e:
            raise ValueError("Error parsing fixed-width file") from e

    def _detect_field_positions(
        self, lines: list[str]
    ) -> dict[str, tuple[int, int]] | None:
        """Auto-detect field positions from the file content."""
        if not lines:
            return None

        # Look for header line or analyze first few lines
        header_candidates = lines[:5]  # Check first 5 lines

        for line in header_candidates:
            line = line.strip()
            if not line:
                continue

            # Try to identify common field patterns
            positions = self._analyze_line_structure(line)
            if positions:
                return positions

        # If no clear header found, try to infer from data patterns
        return self._infer_field_positions(lines[:10])  # Use first 10 lines

    def _analyze_line_structure(self, line: str) -> dict[str, tuple[int, int]] | None:
        """Analyze line structure to identify field positions."""
        # Common field patterns to look for
        patterns = {
            "date": [
                r"\d{2}/\d{2}/\d{4}",
                r"\d{4}-\d{2}-\d{2}",
                r"\d{2}-\d{2}-\d{4}",
            ],
            "amount": [
                r"[\d,]+\.\d{2}",
                r"[\d,]+\.\d{2}",
                r"[\d,]+\.\d{2}",
            ],
            "balance": [
                r"[\d,]+\.\d{2}",
                r"[\d,]+\.\d{2}",
            ],
        }

        positions = {}

        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, line)
                if match:
                    positions[field] = (match.start(), match.end())
                    break

        # If we found at least date and amount, we have a good structure
        if "date" in positions and "amount" in positions:
            return positions

        return None

    def _infer_field_positions(
        self, lines: list[str]
    ) -> dict[str, tuple[int, int]] | None:
        """Infer field positions from data patterns."""
        if not lines:
            return None

        # Find lines with consistent patterns
        date_positions = []
        amount_positions = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for date patterns
            date_match = re.search(r"\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2}", line)
            if date_match:
                date_positions.append((date_match.start(), date_match.end()))

            # Look for amount patterns
            amount_match = re.search(r"[\d,]+\.\d{2}", line)
            if amount_match:
                amount_positions.append((amount_match.start(), amount_match.end()))

        # If we have consistent positions, use them
        if date_positions and amount_positions:
            # Use the most common position
            positions = {}

            # Find most common date position
            if date_positions:
                date_pos = max(set(date_positions), key=date_positions.count)
                positions["date"] = date_pos

            # Find most common amount position
            if amount_positions:
                amount_pos = max(set(amount_positions), key=amount_positions.count)
                positions["amount"] = amount_pos

            return positions

        return None

    def _parse_line(
        self,
        line: str,
        field_positions: dict[str, tuple[int, int]],
        account_config: dict[str, Any],
        file_path: Path,
        line_num: int,
    ) -> Transaction | None:
        """Parse a single line into a Transaction object."""
        try:
            # Extract fields based on positions
            data = {}
            for field, (start, end) in field_positions.items():
                if start < len(line) and end <= len(line):
                    value = line[start:end].strip()
                    if value:
                        data[field] = value

            # Parse required fields
            date = self._parse_date(data.get("date"))
            if not date:
                return None

            amount = self._parse_amount(data.get("amount"))
            if amount is None:
                return None

            balance = self._parse_amount(data.get("balance"))
            if balance is None:
                # If no balance field, try to extract from the line
                balance_match = re.search(r"[\d,]+\.\d{2}", line)
                if balance_match and balance_match.group() != data.get("amount", ""):
                    balance = self._parse_amount(balance_match.group())

            if balance is None:
                balance = Decimal("0")  # Default balance if not found

            # Extract description from remaining parts of the line
            description = self._extract_description(line, field_positions)

            # Determine transaction type
            transaction_type = "withdrawal" if amount < 0 else "deposit"

            # Create transaction object
            return Transaction(
                date=date,
                description=description,
                amount=amount,
                balance=balance,
                transaction_type=transaction_type,
                account_number=account_config.get("account_number", ""),
                currency=account_config.get("currency", "THB"),
                country_code=account_config.get("country_code", "TH"),
                channel=None,
                reference=None,
                file_path=str(file_path),
                raw_text=line,
                raw_json=json.dumps({"line": line, "field_positions": field_positions}),
                parser_name="generic_fixed_width",
            )

        except Exception as e:
            print(f"Error parsing line {line_num}: {e}")
            return None

    def _extract_description(
        self, line: str, field_positions: dict[str, tuple[int, int]]
    ) -> str:
        """Extract description from the line, excluding known fields."""
        # Find the largest gap between known fields
        known_positions = sorted(field_positions.values())

        if not known_positions:
            return line.strip()

        # Find the largest gap
        max_gap_start = 0
        max_gap_end = 0
        max_gap_size = 0

        # Check gap before first field
        if known_positions[0][0] > 0:
            gap_size = known_positions[0][0]
            if gap_size > max_gap_size:
                max_gap_size = gap_size
                max_gap_start = 0
                max_gap_end = known_positions[0][0]

        # Check gaps between fields
        for i in range(len(known_positions) - 1):
            gap_start = known_positions[i][1]
            gap_end = known_positions[i + 1][0]
            gap_size = gap_end - gap_start

            if gap_size > max_gap_size:
                max_gap_size = gap_size
                max_gap_start = gap_start
                max_gap_end = gap_end

        # Check gap after last field
        last_field_end = known_positions[-1][1]
        if last_field_end < len(line):
            gap_size = len(line) - last_field_end
            if gap_size > max_gap_size:
                max_gap_size = gap_size
                max_gap_start = last_field_end
                max_gap_end = len(line)

        # Extract description from the largest gap
        if max_gap_size > 0:
            description = line[max_gap_start:max_gap_end].strip()
            if description:
                return description

        # Fallback: return the whole line
        return line.strip()

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string into datetime object."""
        if not date_str:
            return None

        # Common date formats to try
        date_formats = [
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%Y/%m/%d",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _parse_amount(self, amount_str: str | None) -> Decimal | None:
        """Parse amount string into Decimal object."""
        if not amount_str:
            return None

        # Clean the amount string
        cleaned = re.sub(r"[^\d.-]", "", amount_str.strip())

        if not cleaned:
            return None

        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None
