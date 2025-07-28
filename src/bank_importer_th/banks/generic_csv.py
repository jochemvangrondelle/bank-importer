"""Generic CSV/TSV parser for transaction data."""

import csv
import json
import re
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict

from ..interfaces.parser import Parser
from ..models.transaction import Transaction


class GenericCsvParser(Parser):
    """Generic parser for CSV/TSV files with auto-detection of separators and quotes."""

    def get_bank_type(self) -> str:
        """Get the bank type identifier for this parser."""
        return "generic"

    def get_export_config(self) -> Dict[str, Any]:
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
        return "generic_csv"

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
        return ["*.csv", "*.tsv", "*.txt"]

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for this parser."""
        return [".csv", ".tsv", ".txt"]

    def get_parser_description(self) -> str:
        """Get a human-readable description of this parser."""
        return "Generic CSV/TSV parser with auto-detection of delimiters and formats"

    def get_parser_version(self) -> str:
        """Get the parser version."""
        return "1.0.0"

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        # Check if file exists and is a file (not directory)
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Check file extension
        if file_path.suffix.lower() not in [".csv", ".tsv", ".txt"]:
            return False

        # Try to validate CSV content
        try:
            with open(file_path, encoding="utf-8") as file:
                sample = file.read(4096)  # Read first 4KB
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding="latin-1") as file:
                    sample = file.read(4096)
            except Exception:
                return False

        # Find the first non-empty line
        lines = [line.strip() for line in sample.split("\n") if line.strip()]
        if not lines:
            return False

        first_line = lines[0]

        # Check if the first line contains common CSV delimiters
        delimiters = [",", "\t", ";", "|"]
        delimiter_found = False
        for delim in delimiters:
            if delim in first_line:
                delimiter_found = True
                break

        if not delimiter_found:
            return False

        # Check if we have at least 2 lines (header + data)
        if len(lines) < 2:
            return False

        return True

    def parse_file(
        self, file_path: Path, account_config: dict[str, Any]
    ) -> Iterator[Transaction]:
        """Parse CSV/TSV file and yield Transaction objects."""
        # Validate file exists and is a file
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        try:
            # Auto-detect delimiter and quote character
            delimiter, quotechar = self._detect_format(file_path)

            with open(file_path, encoding="utf-8") as file:
                # Try to detect encoding if UTF-8 fails
                try:
                    content = file.read()
                except UnicodeDecodeError:
                    # Try with different encoding
                    with open(file_path, encoding="latin-1") as file2:
                        content = file2.read()

                # Parse CSV content
                reader = csv.DictReader(
                    content.splitlines(),
                    delimiter=delimiter,
                    quotechar=quotechar,
                    skipinitialspace=True,
                )

                # Validate headers
                if not reader.fieldnames:
                    raise ValueError("No headers found")

                # Map headers to transaction fields
                field_mapping = self._create_field_mapping(
                    list(reader.fieldnames) if reader.fieldnames else None
                )

                # Process each row
                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 because row 1 is header
                    try:
                        transaction = self._parse_row(
                            row, field_mapping, account_config, file_path
                        )
                        if transaction:
                            yield transaction
                    except Exception as e:
                        # Log parsing error but continue with other rows
                        print(f"Error parsing row {row_num} in {file_path}: {e}")
                        continue

        except Exception as e:
            raise ValueError("Error parsing CSV file") from e

    def _detect_format(self, file_path: Path) -> tuple[str, str]:
        """Auto-detect delimiter and quote character."""
        try:
            with open(file_path, encoding="utf-8") as file:
                sample = file.read(4096)  # Read first 4KB
        except UnicodeDecodeError:
            with open(file_path, encoding="latin-1") as file:
                sample = file.read(4096)

        # Find the first non-empty line
        lines = [line.strip() for line in sample.split("\n") if line.strip()]
        if not lines:
            raise ValueError("File appears to be empty")

        first_line = lines[0]

        # Common delimiters to try
        delimiters = [",", "\t", ";", "|"]
        quote_chars = ['"', "'", ""]

        # Count occurrences of each delimiter
        delimiter_counts: dict[str, int] = {}
        for delim in delimiters:
            delimiter_counts[delim] = first_line.count(delim)

        # Choose the most common delimiter
        delimiter = max(delimiter_counts, key=lambda k: delimiter_counts[k])

        # If no clear delimiter found, default to comma
        if delimiter_counts[delimiter] == 0:
            delimiter = ","

        # Detect quote character by looking for quoted fields
        quotechar = '"'  # Default
        for quote in quote_chars:
            if quote and quote in first_line:
                # Check if quotes are used consistently
                quote_count = first_line.count(quote)
                if quote_count > 0:
                    quotechar = quote
                    break

        return delimiter, quotechar

    def _create_field_mapping(self, headers: list[str] | None) -> dict[str, str]:
        """Create mapping from CSV headers to transaction fields."""
        # Normalize headers (lowercase, remove spaces, special chars)
        normalized_headers = {}
        if headers:
            for header in headers:
                if header:
                    normalized = re.sub(r"[^\w]", "", header.lower())
                    normalized_headers[normalized] = header

        # Standard field mappings
        field_mapping = {
            # Core fields
            "date": normalized_headers.get("date", ""),
            "description": normalized_headers.get("description", ""),
            "amount": normalized_headers.get("amount", ""),
            "balance": normalized_headers.get("balance", ""),
            "transaction_type": normalized_headers.get("transactiontype", "")
            or normalized_headers.get("transaction_type", ""),
            "account_number": normalized_headers.get("accountnumber", ""),
            # Enhanced balance tracking
            "old_balance": normalized_headers.get("oldbalance", ""),
            "new_balance": normalized_headers.get("newbalance", ""),
            # Additional date fields
            "transaction_date": normalized_headers.get("transactiondate", ""),
            "value_date": normalized_headers.get("valuedate", ""),
            "posting_date": normalized_headers.get("postingdate", ""),
            "effective_date": normalized_headers.get("effectivedate", ""),
            # Account and location
            "currency": normalized_headers.get("currency", ""),
            "country_code": normalized_headers.get("countrycode", ""),
            # Transaction details
            "channel": normalized_headers.get("channel", ""),
            "reference": normalized_headers.get("reference", ""),
            "check_number": normalized_headers.get("checknumber", ""),
            "memo": normalized_headers.get("memo", ""),
            "category": normalized_headers.get("category", ""),
            "subcategory": normalized_headers.get("subcategory", ""),
            # Additional metadata
            "exchange_rate": normalized_headers.get("exchangerate", ""),
            "foreign_currency": normalized_headers.get("foreigncurrency", ""),
            "foreign_amount": normalized_headers.get("foreignamount", ""),
            "fees": normalized_headers.get("fees", ""),
            "interest": normalized_headers.get("interest", ""),
            "tax": normalized_headers.get("tax", ""),
        }

        return field_mapping

    def _parse_row(
        self,
        row: dict[str, str],
        field_mapping: dict[str, str],
        account_config: dict[str, Any],
        file_path: Path,
    ) -> Transaction:
        """Parse a single CSV row into a Transaction object."""
        # Extract basic fields with proper type handling
        date_str = str(row.get(field_mapping.get("date", ""), ""))
        description = str(row.get(field_mapping.get("description", ""), ""))
        amount_str = str(row.get(field_mapping.get("amount", ""), ""))
        balance_str = str(row.get(field_mapping.get("balance", ""), ""))

        # Enhanced balance tracking
        old_balance_str = str(row.get(field_mapping.get("old_balance", ""), ""))
        new_balance_str = str(row.get(field_mapping.get("new_balance", ""), ""))

        # Additional date fields
        transaction_date_str = str(
            row.get(field_mapping.get("transaction_date", ""), "")
        )
        value_date_str = str(row.get(field_mapping.get("value_date", ""), ""))
        posting_date_str = str(row.get(field_mapping.get("posting_date", ""), ""))
        effective_date_str = str(row.get(field_mapping.get("effective_date", ""), ""))

        # Transaction details
        transaction_type = str(row.get(field_mapping.get("transaction_type", ""), ""))
        channel = str(row.get(field_mapping.get("channel", ""), ""))
        reference = str(row.get(field_mapping.get("reference", ""), ""))
        check_number = str(row.get(field_mapping.get("check_number", ""), ""))
        memo = str(row.get(field_mapping.get("memo", ""), ""))
        category = str(row.get(field_mapping.get("category", ""), ""))
        subcategory = str(row.get(field_mapping.get("subcategory", ""), ""))

        # Additional metadata
        exchange_rate_str = str(row.get(field_mapping.get("exchange_rate", ""), ""))
        foreign_currency = str(row.get(field_mapping.get("foreign_currency", ""), ""))
        foreign_amount_str = str(row.get(field_mapping.get("foreign_amount", ""), ""))
        fees_str = str(row.get(field_mapping.get("fees", ""), ""))
        interest_str = str(row.get(field_mapping.get("interest", ""), ""))
        tax_str = str(row.get(field_mapping.get("tax", ""), ""))

        # Parse dates
        date = self._parse_date(date_str) if date_str else datetime.now()
        transaction_date = (
            self._parse_date(transaction_date_str) if transaction_date_str else None
        )
        value_date = self._parse_date(value_date_str) if value_date_str else None
        posting_date = self._parse_date(posting_date_str) if posting_date_str else None
        effective_date = (
            self._parse_date(effective_date_str) if effective_date_str else None
        )

        # Parse amounts
        amount = self._parse_amount(amount_str) if amount_str else Decimal("0")
        balance = self._parse_amount(balance_str) if balance_str else Decimal("0")
        old_balance = self._parse_amount(old_balance_str) if old_balance_str else None
        new_balance = self._parse_amount(new_balance_str) if new_balance_str else None
        exchange_rate = (
            self._parse_amount(exchange_rate_str) if exchange_rate_str else None
        )
        foreign_amount = (
            self._parse_amount(foreign_amount_str) if foreign_amount_str else None
        )
        fees = self._parse_amount(fees_str) if fees_str else None
        interest = self._parse_amount(interest_str) if interest_str else None
        tax = self._parse_amount(tax_str) if tax_str else None

        # Get currency from CSV or use default
        currency = str(
            row.get(field_mapping.get("currency", ""), "")
        ) or account_config.get("currency", "THB")

        # Infer transaction type if not provided
        if not transaction_type:
            if amount > 0:
                transaction_type = "deposit"
            else:
                transaction_type = "withdrawal"
        else:
            # Use the transaction type from CSV as-is
            transaction_type = transaction_type.lower()

        # Use new_balance if available, otherwise use balance
        final_balance = new_balance if new_balance is not None else balance

        # Skip transactions with missing required fields
        if not date or not description or amount == 0:
            return None

        return Transaction(
            date=date,
            description=description,
            amount=amount,
            balance=final_balance,
            old_balance=old_balance,
            new_balance=new_balance,
            transaction_type=transaction_type,
            account_number=account_config.get("account_number", ""),
            transaction_date=transaction_date,
            value_date=value_date,
            posting_date=posting_date,
            effective_date=effective_date,
            currency=currency,
            country_code=account_config.get("country_code", "TH"),
            channel=channel or None,
            reference=reference or None,
            check_number=check_number or None,
            memo=memo or None,
            category=category or None,
            subcategory=subcategory or None,
            exchange_rate=exchange_rate,
            foreign_currency=foreign_currency or None,
            foreign_amount=foreign_amount,
            fees=fees,
            interest=interest,
            tax=tax,
            raw_json=json.dumps(row),
            parser_name="generic_csv",
            source_file=str(file_path),
        )

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string into datetime object."""
        if not date_str:
            return None

        # Common date formats - prioritize DD/MM/YYYY over MM/DD/YYYY
        date_formats = [
            "%Y-%m-%d",  # 2024-01-01
            "%d/%m/%Y",  # 01/01/2024 (DD/MM/YYYY) - prioritize this
            "%Y/%m/%d",  # 2024/01/01
            "%d-%m-%Y",  # 01-01-2024
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            # Note: Removed MM/DD/YYYY formats to avoid conflicts with DD/MM/YYYY
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
