"""American Express Thailand CSV parser for transaction data."""

import csv
import re
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..interfaces.parser import Parser
from ..models.transaction import Transaction
from ..translation_service import get_translation_service


class AmexThCsvParser(Parser):
    """Parser for American Express Thailand CSV files."""

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        # Check if file exists and is a file (not directory)
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Check file extension
        if file_path.suffix.lower() != ".csv":
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

        # Check if this looks like an Amex CSV file
        # Expected headers: Date,Description,Card Member,Account #,Amount,Extended Details,Appears On Your Statement As,Address,City/State,Zip Code,Country,Reference,Category
        expected_headers = [
            "Date",
            "Description",
            "Card Member",
            "Account #",
            "Amount",
            "Extended Details",
            "Appears On Your Statement As",
            "Address",
            "City/State",
            "Zip Code",
            "Country",
            "Reference",
            "Category",
        ]

        # Check if the first line contains the expected headers
        first_line_lower = first_line.lower()
        header_matches = sum(
            1 for header in expected_headers if header.lower() in first_line_lower
        )

        # We need at least 8 out of 13 headers to match (allowing for minor variations)
        if header_matches < 8:
            return False

        # Check if we have at least 2 lines (header + data)
        if len(lines) < 2:
            return False

        return True

    def parse_file(
        self,
        file_path: Path,
        account_config: dict[str, Any],
        config_manager: Any = None,
    ) -> Iterator[Transaction]:
        """Parse Amex CSV file and yield Transaction objects."""
        # Validate file exists and is a file
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        try:
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
                    delimiter=",",
                    quotechar='"',
                    skipinitialspace=True,
                )

                # Validate headers
                if not reader.fieldnames:
                    raise ValueError("No headers found")

                # Process each row
                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 for header row
                    try:
                        transaction = self._parse_row(
                            row, account_config, file_path, row_num
                        )
                        if transaction:
                            yield transaction
                    except Exception as e:
                        print(f"Error parsing row {row_num}: {e}")
                        continue

        except Exception as e:
            raise ValueError(f"Error parsing Amex CSV file {file_path}: {e}") from e

    def _parse_row(
        self,
        row: dict[str, str],
        account_config: dict[str, Any],
        file_path: Path,
        row_num: int,
    ) -> Transaction | None:
        """Parse a single row from the Amex CSV file."""

        # Extract basic fields
        date_str = row.get("Date", "").strip()
        description = row.get("Description", "").strip()
        card_member = row.get("Card Member", "").strip()
        # Ignore Account # from CSV - use config account number instead
        amount_str = row.get("Amount", "").strip()
        extended_details = row.get("Extended Details", "").strip()
        appears_on_statement = row.get("Appears On Your Statement As", "").strip()
        address = row.get("Address", "").strip()
        city_state = row.get("City/State", "").strip()
        zip_code = row.get("Zip Code", "").strip()
        country = row.get("Country", "").strip()
        reference = row.get("Reference", "").strip()
        category = row.get("Category", "").strip()

        # Skip empty rows
        if not date_str or not description or not amount_str:
            return None

        # Parse date (MM/DD/YYYY format)
        try:
            date = datetime.strptime(date_str, "%m/%d/%Y")
        except ValueError:
            print(f"Warning: Invalid date format '{date_str}' in row {row_num}")
            return None

        # Parse amount
        try:
            # Remove any currency symbols and commas
            amount_clean = re.sub(r"[^\d.-]", "", amount_str)
            amount = Decimal(amount_clean)

            # AMEX reports spendings as positive and credits as negative
            # For Firefly-III import, we need expenses negative and credits positive
            # So we negate all amounts to convert from AMEX format to Firefly-III format
            amount = -amount

        except (ValueError, InvalidOperation) as e:
            print(f"Warning: Invalid amount '{amount_str}' in row {row_num}: {e}")
            return None

        # Parse foreign currency information from Extended Details
        foreign_currency, foreign_amount, exchange_rate = self._parse_foreign_currency(
            extended_details
        )

        # Determine transaction type
        transaction_type = self._determine_transaction_type(description, amount)

        # Create unique ID using reference or generate one
        unique_id = self._generate_unique_id(
            reference,
            account_config.get("account_number", "XXXX-XXXXXX-43002"),
            date,
            amount,
            description,
        )

        # Get account details from config
        account_number_clean = account_config.get("account_number", "XXXX-XXXXXX-43002")
        currency = account_config.get("currency", "THB")
        country_code = account_config.get("country_code", "TH")

        # Create description with additional context
        full_description = self._create_full_description(
            description, appears_on_statement, address, city_state, country
        )

        # Apply translation if enabled
        translated_description = None
        translation_config = account_config.get("translation", {})
        if translation_config.get("enabled", False):
            translation_service = get_translation_service(
                source_language=translation_config.get("source_language", "th"),
                target_language=translation_config.get("target_language", "en"),
                term_mappings=translation_config.get("term_mappings", {}),
            )
            translated_description = translation_service.translate_description(
                full_description,
                use_cache=translation_config.get("use_cache", True),
                use_term_mapping=translation_config.get("use_term_mapping", True),
                use_api_translation=translation_config.get("use_api_translation", True),
            )

        # Create notes with additional metadata
        notes_parts: list[str] = []
        if card_member:
            notes_parts.append(f"Card Member: {card_member}")
        if appears_on_statement and appears_on_statement != description:
            notes_parts.append(f"Statement: {appears_on_statement}")
        if address:
            notes_parts.append(f"Address: {address}")
        if city_state:
            notes_parts.append(f"Location: {city_state}")
        if zip_code:
            notes_parts.append(f"ZIP: {zip_code}")
        if country:
            notes_parts.append(f"Country: {country}")
        if category:
            notes_parts.append(f"Category: {category}")
        if extended_details:
            notes_parts.append(f"Details: {extended_details}")

        notes = " | ".join(notes_parts) if notes_parts else ""

        # Create raw data for preservation
        raw_data = {
            "date": date_str,
            "description": description,
            "card_member": card_member,
            "account_number": account_number_clean,
            "amount": amount_str,
            "extended_details": extended_details,
            "appears_on_statement": appears_on_statement,
            "address": address,
            "city_state": city_state,
            "zip_code": zip_code,
            "country": country,
            "reference": reference,
            "category": category,
        }

        transaction = Transaction(
            date=date,
            description=full_description,
            translated_description=translated_description,
            amount=amount,
            balance=Decimal("0"),  # Amex CSV doesn't provide balance
            transaction_type=transaction_type,
            account_number=account_number_clean,
            currency=currency,
            country_code=country_code,
            reference=reference,
            memo=notes,
            category=category if category else None,
            foreign_currency=foreign_currency,
            foreign_amount=foreign_amount,
            exchange_rate=exchange_rate,
            raw_text=extended_details,
            raw_json=None,  # Will be set below
            source_file=str(file_path),
            parser_name="amex_th_csv",
            unique_id=unique_id,
        )

        # Set raw JSON data
        transaction.set_raw_json_dict(raw_data)

        return transaction

    def _parse_foreign_currency(
        self, extended_details: str
    ) -> tuple[str | None, Decimal | None, Decimal | None]:
        """Parse foreign currency information from Extended Details field."""
        if not extended_details:
            return None, None, None

        # Clean up the extended details - remove newlines and normalize spaces
        cleaned_details = extended_details.replace("\n", " ").replace("\r", " ")
        cleaned_details = re.sub(r"\s+", " ", cleaned_details).strip()

        # Pattern to match currency conversion: "254.00 US DOLLAR CONVERTED TO"
        # Updated patterns to match the actual format in Amex CSV
        currency_patterns = [
            r"(\d+(?:,\d+)*\.?\d*)\s+US\s+DOLLAR\s+CONVERTED\s+TO",
            r"(\d+(?:,\d+)*\.?\d*)\s+EURO\s+CONVERTED\s+TO",
            r"(\d+(?:,\d+)*\.?\d*)\s+BAHT\s+CONVERTED\s+TO",
            r"(\d+(?:,\d+)*\.?\d*)\s+POUND\s+CONVERTED\s+TO",
            r"(\d+(?:,\d+)*\.?\d*)\s+YEN\s+CONVERTED\s+TO",
        ]

        for pattern in currency_patterns:
            match = re.search(pattern, cleaned_details, re.IGNORECASE)
            if match:
                foreign_amount_str = match.group(1).replace(",", "")

                # Determine currency based on the pattern matched
                if "US DOLLAR" in pattern:
                    foreign_currency = "USD"
                elif "EURO" in pattern:
                    foreign_currency = "EUR"
                elif "BAHT" in pattern:
                    foreign_currency = "THB"
                elif "POUND" in pattern:
                    foreign_currency = "GBP"
                elif "YEN" in pattern:
                    foreign_currency = "JPY"
                else:
                    foreign_currency = "UNKNOWN"

                try:
                    foreign_amount = Decimal(foreign_amount_str)
                    # For now, we don't have the exchange rate in the data
                    # We could calculate it if we had both amounts, but it's not provided
                    exchange_rate = None
                    return foreign_currency, foreign_amount, exchange_rate
                except (InvalidOperation, ValueError):
                    continue

        return None, None, None

    def _determine_transaction_type(self, description: str, amount: Decimal) -> str:
        """Determine the transaction type based on description and amount."""
        description_lower = description.lower()

        # Purchase transactions (negative amounts - expenses)
        if amount < 0:
            if "grab" in description_lower:
                return "transport"
            elif "spotify" in description_lower or "tidal" in description_lower:
                return "entertainment"
            elif "adobe" in description_lower or "cursor" in description_lower:
                return "software"
            elif "udemy" in description_lower:
                return "education"
            elif "apple" in description_lower:
                return "technology"
            elif "hotel" in description_lower or "agoda" in description_lower:
                return "travel"
            elif "market" in description_lower or "lotus" in description_lower:
                return "groceries"
            elif "paypal" in description_lower:
                return "online_payment"
            else:
                return "purchase"

        # Payment transactions (positive amounts - credits)
        else:
            if "payment" in description_lower:
                return "payment"
            elif "fee" in description_lower:
                return "fee"
            else:
                return "payment"

    def _generate_unique_id(
        self,
        reference: str,
        account_number: str,
        date: datetime,
        amount: Decimal,
        description: str,
    ) -> str:
        """Generate a unique ID for the transaction."""
        import hashlib

        # If we have a reference that looks like a unique ID, use it
        if reference and self._looks_like_transaction_id(reference):
            return f"{account_number}_{reference}"

        # Otherwise, create a hash-based ID
        hash_input = f"{date.strftime('%Y%m%d')}_{amount}_{description[:50]}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"{account_number}_{date.strftime('%Y%m%d')}_{hash_value}"

    def _looks_like_transaction_id(self, reference: str) -> bool:
        """Check if a reference string looks like a unique transaction ID."""
        if not reference or len(reference) < 5 or len(reference) > 50:
            return False

        # Check if it contains only alphanumeric and common separators
        if not re.match(r"^[A-Za-z0-9\-_\.\/]+$", reference):
            return False

        # Exclude common generic references
        generic_patterns = [
            "example",
            "test",
            "demo",
            "reference",
            "ref",
            "account",
            "main",
        ]

        reference_lower = reference.lower()
        for pattern in generic_patterns:
            if pattern in reference_lower:
                return False

        return True

    def _fix_country_codes_in_description(self, description: str) -> str:
        """Add space before country codes at the end of merchant names."""
        # Use the parser's configured country code
        country_code = self.get_default_country_code()

        # Check if description ends with the country code
        if description.upper().endswith(country_code):
            # Add space before the country code
            return description[: -len(country_code)] + " " + country_code

        return description

    def _create_full_description(
        self,
        description: str,
        appears_on_statement: str,
        address: str,
        city_state: str,
        country: str,
    ) -> str:
        """Create a comprehensive description with location information."""
        # Fix country codes in the description
        fixed_description = self._fix_country_codes_in_description(description)

        parts: list[str] = [fixed_description]

        # Add location information if available
        location_parts: list[str] = []
        if address:
            location_parts.append(address)
        if city_state:
            location_parts.append(city_state)
        if country:
            location_parts.append(country)

        if location_parts:
            location_str = ", ".join(location_parts)
            parts.append(f"({location_str})")

        # Add statement description if different from main description
        if appears_on_statement and appears_on_statement != description:
            # Also fix country codes in the statement description
            fixed_statement = self._fix_country_codes_in_description(
                appears_on_statement
            )
            parts.append(f"[{fixed_statement}]")

        return " ".join(parts)

    def get_bank_type(self) -> str:
        """Get the bank type identifier for this parser."""
        return "amex_th"

    def get_export_config(self) -> dict[str, Any]:
        """Get export configuration specific to this parser."""
        return {
            "bank_name": "American Express Thailand",
            "default_account_name": "TH - CC AMEX (Billed / Uncharged)",
            "default_account_number": "XXXX-XXXXXX-43002",
            "default_currency": "THB",
            "default_country_code": "TH",
            "supports_foreign_currency": True,
            "supports_translation": True,
            "translation_source_language": "en",
            "translation_target_language": "en",
        }

    def get_parser_name(self) -> str:
        """Get the parser name identifier."""
        return "amex_th_csv"

    def get_default_account_name(self) -> str:
        """Get the default account name for this parser."""
        return "TH - CC AMEX (Billed / Uncharged)"

    def get_default_account_number(self) -> str:
        """Get the default account number for this parser."""
        return "XXXX-XXXXXX-43002"

    def get_default_currency(self) -> str:
        """Get the default currency for this parser."""
        return "THB"

    def get_default_country_code(self) -> str:
        """Get the default country code for this parser."""
        return "TH"

    def get_supported_file_patterns(self) -> list[str]:
        """Get list of supported file patterns for this parser."""
        return ["*.csv"]

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for this parser."""
        return [".csv"]

    def get_parser_description(self) -> str:
        """Get a human-readable description of this parser."""
        return "American Express Thailand CSV Statement Parser"

    def get_parser_version(self) -> str:
        """Get the parser version."""
        return "1.0.0"
