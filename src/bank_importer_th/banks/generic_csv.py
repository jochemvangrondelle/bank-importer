"""Generic CSV/TSV parser for transaction data."""

import csv
import json
import re
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..interfaces.parser import Parser
from ..models.transaction import Transaction


class GenericCsvParser(Parser):
    """Generic parser for CSV/TSV files with auto-detection of separators and quotes."""

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in [".csv", ".tsv", ".txt"]

    def parse_file(self, file_path: Path, account_config: dict[str, Any]) -> Iterator[Transaction]:
        """Parse CSV/TSV file and yield Transaction objects."""
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
                    content.splitlines(), delimiter=delimiter, quotechar=quotechar, skipinitialspace=True
                )

                # Validate headers
                if not reader.fieldnames:
                    raise ValueError("No headers found")

                # Map headers to transaction fields
                field_mapping = self._create_field_mapping(list(reader.fieldnames) if reader.fieldnames else None)

                # Process each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
                    try:
                        transaction = self._parse_row(row, field_mapping, account_config, file_path, row_num)
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
        delimiter_counts = {}
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
                if quote_count > 0 and quote_count % 2 == 0:
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

        # Define possible mappings for each transaction field
        field_mappings = {
            "date": ["date", "transactiondate", "txdate", "datetime", "time"],
            "description": ["description", "desc", "memo", "note", "details", "narration"],
            "amount": ["amount", "amt", "value", "sum", "total"],
            "balance": ["balance", "bal", "runningbalance", "accountbalance"],
            "transaction_type": ["type", "transactiontype", "txntype", "category"],
            "account_number": ["account", "accountnumber", "accno", "accountid"],
            "currency": ["currency", "curr", "ccy"],
            "country_code": ["country", "countrycode", "cc"],
            "channel": ["channel", "method", "source", "medium"],
            "reference": ["reference", "ref", "id", "transactionid", "txid"],
        }

        # Create the actual mapping
        mapping = {}
        for field, possible_names in field_mappings.items():
            for name in possible_names:
                if name in normalized_headers:
                    mapping[field] = normalized_headers[name]
                    break

        return mapping

    def _parse_row(
        self,
        row: dict[str, str],
        field_mapping: dict[str, str],
        account_config: dict[str, Any],
        file_path: Path,
        row_num: int,
    ) -> Transaction | None:
        """Parse a single CSV row into a Transaction object."""
        try:
            # Extract values using field mapping
            data = {}
            for field, csv_header in field_mapping.items():
                value = row.get(csv_header, "").strip()
                if value:
                    data[field] = value

            # Parse date
            date = self._parse_date(data.get("date"), account_config)
            if not date:
                return None

            # Parse amount
            amount = self._parse_amount(data.get("amount"))
            if amount is None:
                return None

            # Parse balance
            balance = self._parse_amount(data.get("balance"))
            if balance is None:
                return None

            # Determine transaction type if not provided
            transaction_type = data.get("transaction_type")
            if not transaction_type:
                transaction_type = "withdrawal" if amount < 0 else "deposit"

            # Create transaction object
            return Transaction(
                date=date,
                description=data.get("description", "Unknown transaction"),
                amount=amount,
                balance=balance,
                transaction_type=transaction_type,
                account_number=data.get("account_number") or account_config.get("account_number", ""),
                currency=data.get("currency") or account_config.get("currency", "THB"),
                country_code=data.get("country_code") or account_config.get("country_code", "TH"),
                channel=data.get("channel"),
                reference=data.get("reference"),
                file_path=str(file_path),
                raw_text=str(row),
                raw_json=json.dumps(row),
                parser_name="generic_csv",
            )

        except Exception as e:
            print(f"Error parsing row {row_num}: {e}")
            return None

    def _parse_date(self, date_str: str | None, account_config: dict[str, Any]) -> datetime | None:
        """Parse date string into datetime object."""
        if not date_str:
            return None

        # Common date formats to try
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        # If no format matches, try to extract date from string
        try:
            # Try to find a date pattern in the string
            date_patterns = [
                r"(\d{4}-\d{2}-\d{2})",
                r"(\d{2}/\d{2}/\d{4})",
                r"(\d{2}-\d{2}-\d{4})",
            ]

            for pattern in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    date_part = match.group(1)
                    for fmt in date_formats[:6]:  # Only try basic date formats
                        try:
                            return datetime.strptime(date_part, fmt)
                        except ValueError:
                            continue
        except Exception:
            pass

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
