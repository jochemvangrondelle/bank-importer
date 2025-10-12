"""Generic JSON parser for transaction data."""

import json
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..interfaces.parser import Parser
from ..models.transaction import Transaction


class GenericJsonParser(Parser):
    """Generic parser for JSON files containing transaction data."""

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
        return "generic_json"

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
        return ["*.json", "*.jsonl"]

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for this parser."""
        return [".json", ".jsonl"]

    def get_parser_description(self) -> str:
        """Get a human-readable description of this parser."""
        return "Generic JSON parser for transaction data"

    def get_parser_version(self) -> str:
        """Get the parser version."""
        return "1.0.0"

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in [".json", ".jsonl"]

    def parse_file(
        self, file_path: Path, account_config: dict[str, Any]
    ) -> Iterator[Transaction]:
        """Parse JSON file and yield Transaction objects."""
        try:
            with open(file_path, encoding="utf-8") as file:
                content = file.read().strip()

                if file_path.suffix.lower() == ".jsonl":
                    # JSON Lines format - one JSON object per line
                    for line_num, line in enumerate(content.split("\n"), start=1):
                        if line.strip():
                            try:
                                data = json.loads(line.strip())
                                transaction = self._parse_transaction(
                                    data, account_config, file_path, line_num
                                )
                                if transaction:
                                    yield transaction
                            except json.JSONDecodeError as e:
                                print(
                                    f"Error parsing JSON line {line_num} in {file_path}: {e}"
                                )
                                continue
                else:
                    # Regular JSON format
                    try:
                        data = json.loads(content)

                        # Handle different JSON structures
                        if isinstance(data, list):
                            # Array of transactions
                            for i, item in enumerate(data):
                                transaction = self._parse_transaction(
                                    item, account_config, file_path, i + 1
                                )
                                if transaction:
                                    yield transaction
                        elif isinstance(data, dict):
                            # Single transaction or object with transactions
                            if "transactions" in data:
                                # Object with transactions array
                                transactions = data["transactions"]
                                if isinstance(transactions, list):
                                    for i, item in enumerate(transactions):
                                        transaction = self._parse_transaction(
                                            item, account_config, file_path, i + 1
                                        )
                                        if transaction:
                                            yield transaction
                            else:
                                # Single transaction object
                                transaction = self._parse_transaction(
                                    data, account_config, file_path, 1
                                )
                                if transaction:
                                    yield transaction
                        else:
                            raise TypeError("Unexpected JSON structure")

                    except json.JSONDecodeError as e:
                        raise ValueError("Invalid JSON") from e

        except Exception as e:
            raise ValueError("Error parsing JSON file") from e

    def _parse_transaction(
        self,
        data: dict[str, Any],
        account_config: dict[str, Any],
        file_path: Path,
        item_num: int,
    ) -> Transaction | None:
        """Parse a single transaction from JSON data."""
        try:
            # Extract values with flexible field mapping
            field_mapping = self._create_field_mapping(data.keys())

            # Extract mapped values
            extracted_data = {}
            for field, json_key in field_mapping.items():
                value = data.get(json_key)
                if value is not None:
                    extracted_data[field] = value

            # Parse required fields
            date = self._parse_date(extracted_data.get("date"))
            if not date:
                return None

            amount = self._parse_amount(extracted_data.get("amount"))
            if amount is None:
                return None

            balance = self._parse_amount(extracted_data.get("balance"))
            if balance is None:
                return None

            # Determine transaction type
            transaction_type = extracted_data.get("transaction_type")
            if not transaction_type:
                transaction_type = "withdrawal" if amount < 0 else "deposit"

            # Create transaction object
            return Transaction(
                date=date,
                description=extracted_data.get("description", "Unknown transaction"),
                amount=amount,
                balance=balance,
                transaction_type=transaction_type,
                account_number=extracted_data.get("account_number")
                or account_config.get("account_number", ""),
                currency=extracted_data.get("currency")
                or account_config.get("currency", "THB"),
                country_code=extracted_data.get("country_code")
                or account_config.get("country_code", "TH"),
                channel=extracted_data.get("channel"),
                reference=extracted_data.get("reference"),
                file_path=str(file_path),
                raw_text=str(data),
                raw_json=json.dumps(data),
                parser_name="generic_json",
            )

        except Exception as e:
            print(f"Error parsing transaction {item_num}: {e}")
            return None

    def _create_field_mapping(self, keys: list[str]) -> dict[str, str]:
        """Create mapping from JSON keys to transaction fields."""
        # Normalize keys (lowercase, remove spaces, special chars)
        normalized_keys = {}
        for key in keys:
            if key:
                normalized = (
                    key.lower().replace(" ", "").replace("_", "").replace("-", "")
                )
                normalized_keys[normalized] = key

        # Define possible mappings for each transaction field
        field_mappings = {
            "date": [
                "date",
                "transactiondate",
                "txdate",
                "datetime",
                "time",
                "timestamp",
            ],
            "description": [
                "description",
                "desc",
                "memo",
                "note",
                "details",
                "narration",
                "comment",
            ],
            "amount": ["amount", "amt", "value", "sum", "total", "transactionamount"],
            "balance": [
                "balance",
                "bal",
                "runningbalance",
                "accountbalance",
                "newbalance",
            ],
            "transaction_type": [
                "type",
                "transactiontype",
                "txntype",
                "category",
                "transactiontype",
            ],
            "account_number": [
                "account",
                "accountnumber",
                "accno",
                "accountid",
                "accountnumber",
            ],
            "currency": ["currency", "curr", "ccy", "currencycode"],
            "country_code": ["country", "countrycode", "cc", "country"],
            "channel": ["channel", "method", "source", "medium", "paymentmethod"],
            "reference": [
                "reference",
                "ref",
                "id",
                "transactionid",
                "txid",
                "reference",
            ],
        }

        # Create the actual mapping
        mapping = {}
        for field, possible_names in field_mappings.items():
            for name in possible_names:
                if name in normalized_keys:
                    mapping[field] = normalized_keys[name]
                    break

        return mapping

    def _parse_date(self, date_value: Any) -> datetime | None:
        """Parse date value into datetime object."""
        if not date_value:
            return None

        # If it's already a datetime object
        if isinstance(date_value, datetime):
            return date_value

        # Convert to string
        date_str = str(date_value).strip()

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
            "%Y-%m-%dT%H:%M:%SZ",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_amount(self, amount_value: Any) -> Decimal | None:
        """Parse amount value into Decimal object."""
        if amount_value is None:
            return None

        # If it's already a Decimal or number
        if isinstance(amount_value, int | float | Decimal):
            return Decimal(str(amount_value))

        # Convert to string and clean
        amount_str = str(amount_value).strip()

        # Remove currency symbols and other non-numeric characters except . and -
        import re

        cleaned = re.sub(r"[^\d.-]", "", amount_str)

        if not cleaned:
            return None

        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None
