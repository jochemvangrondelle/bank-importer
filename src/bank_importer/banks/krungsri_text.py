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

"""Krungsri Bank text parser."""

import re
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bank_importer.config import ConfigManager

import pytz

from bank_importer.interfaces.parser import Parser
from bank_importer.logging_config import log_error
from bank_importer.models.transaction import Transaction


class KrungsriTextParser(Parser):
    """Parser for Krungsri Bank text statements."""

    # Constants for parsing
    MIN_AMOUNT_MATCHES = 2  # Need at least amount and balance
    MIN_LINE_PARTS = 2  # Need at least date and time parts
    MAX_CHANNEL_LENGTH = 10  # Maximum length for channel identifier

    def get_bank_type(self) -> str:
        """Get the bank type identifier for this parser."""
        return "krungsri"

    def get_export_config(self) -> dict[str, Any]:
        """Get export configuration specific to this parser."""
        return {
            "bank_name": "Krungsri Bank",
            "default_account_name": "Krungsri Savings Account",
            "default_account_number": "769-1-32483-6",
            "default_currency": "THB",
            "default_country_code": "TH",
            "supports_foreign_currency": False,
            "supports_translation": True,
            "translation_source_language": "TH",
            "translation_target_language": "en",
        }

    def get_parser_name(self) -> str:
        """Get the parser name identifier."""
        return "krungsri_text"

    def get_default_account_name(self) -> str:
        """Get the default account name for this parser."""
        return "Krungsri Savings Account"

    def get_default_account_number(self) -> str:
        """Get the default account number for this parser."""
        return "769-1-32483-6"

    def get_default_currency(self) -> str:
        """Get the default currency for this parser."""
        return "THB"

    def get_default_country_code(self) -> str:
        """Get the default country code for this parser."""
        return "TH"

    def get_supported_file_patterns(self) -> list[str]:
        """Get list of supported file patterns for this parser."""
        return ["*.txt"]

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for this parser."""
        return [".txt"]

    def get_parser_description(self) -> str:
        """Get a human-readable description of this parser."""
        return "Krungsri Bank text statement parser"

    def get_parser_version(self) -> str:
        """Get the parser version."""
        return "1.0.0"

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        if not file_path.exists():
            msg = "File does not exist"
            raise ValueError(msg)

        if not file_path.is_file():
            msg = "Path is not a file"
            raise ValueError(msg)

        try:
            with file_path.open(encoding="utf-8") as f:
                first_line = f.readline().strip()
                # Check for Krungsri header pattern
                return (
                    "Date/Time Transaction Withdrawal/Deposit Outstanding Balance Channel Description"
                    in first_line
                )
        except (UnicodeDecodeError, FileNotFoundError):
            return False

    def parse_file(
        self,
        file_path: Path,
        account_config: dict[str, Any],
        config_manager: "ConfigManager | None" = None,
    ) -> Iterator[Transaction]:
        """Parse Krungsri text file and yield transactions."""
        with file_path.open(encoding="utf-8") as f:
            lines = f.readlines()

        # Skip header line
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue

            try:
                transaction = self._parse_line(
                    line,
                    account_config,
                    str(file_path),
                    config_manager,
                )
                if transaction:
                    yield transaction
            except Exception as e:
                # Log error but continue processing
                log_error(f"Error parsing line: {line[:50]}... - {e}")
                continue

    def _parse_line(
        self,
        line: str,
        account_config: dict[str, Any],
        source_file: str,
        config_manager: "ConfigManager | None" = None,
    ) -> Transaction:
        """Parse a single transaction line."""
        # Use regex to find amount and balance patterns (numbers with commas and decimals)
        amount_pattern = r"([0-9,]+\.\d{2})"
        matches = list(re.finditer(amount_pattern, line))

        if len(matches) < self.MIN_AMOUNT_MATCHES:
            msg = "Could not find amount and balance in line"
            raise ValueError(msg)

        # First match is amount, second is balance
        amount_str = matches[0].group(1).replace(",", "")
        balance_str = matches[1].group(1).replace(",", "")

        amount = Decimal(amount_str)
        balance = Decimal(balance_str)

        # Parse date and time (first two parts)
        parts = line.split()
        if len(parts) < self.MIN_LINE_PARTS:
            msg = "Invalid line format"
            raise ValueError(msg)

        date_str = f"{parts[0]} {parts[1]}"
        # Parse datetime and make it timezone aware
        naive_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")  # noqa: DTZ007
        timezone_str = "Asia/Bangkok"  # Default fallback
        if config_manager:
            timezone_str = config_manager.get_timezone()
        tz = pytz.timezone(timezone_str)
        date = tz.localize(naive_date)

        # Find transaction type - it's everything between time and first amount
        time_end = line.find(parts[1]) + len(parts[1])
        amount_start = line.find(matches[0].group(1))
        transaction_type = line[time_end:amount_start].strip()

        # Parse channel and description
        channel = None
        description = ""

        # Find channel after balance
        balance_end = line.find(matches[1].group(1)) + len(matches[1].group(1))
        remaining = line[balance_end:].strip()

        if remaining:
            remaining_parts = remaining.split()
            if (
                remaining_parts
                and remaining_parts[0].isupper()
                and len(remaining_parts[0]) <= self.MAX_CHANNEL_LENGTH
            ):
                channel = remaining_parts[0]
                description = (
                    " ".join(remaining_parts[1:]) if len(remaining_parts) > 1 else ""
                )
            else:
                description = remaining

        # Determine if it's a credit or debit
        if (
            "Deposit" in transaction_type
            or "Interest" in transaction_type
            or "Credit" in transaction_type
        ):
            # Keep amount positive for credits (money coming in)
            amount = abs(amount)
        else:
            # Make amount negative for withdrawals/payments (money going out)
            amount = -abs(amount)

        return Transaction(
            date=date,
            description=description,
            amount=amount,
            balance=balance,
            transaction_type=transaction_type,
            account_number=account_config.get("account_number", "XXX-1-32483-X"),
            currency=account_config.get("currency", "THB"),
            country_code=account_config.get("country_code", "TH"),
            channel=channel,
            source_file=source_file,
            parser_name="krungsri_text",
            raw_text=line,
        )
