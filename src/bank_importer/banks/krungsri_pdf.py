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

"""Parser for Krungsri Bank PDF statements using pypdfium2."""

import re
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bank_importer.config import ConfigManager

import pytz

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None  # type: ignore[assignment, misc]

from bank_importer.interfaces.parser import Parser, ReconciliationTotals
from bank_importer.logging_config import log_error
from bank_importer.models.transaction import Transaction


class KrungsriPdfParser(Parser):
    """Parser for Krungsri Bank PDF statements using pypdfium2."""

    # Constants for parsing
    MIN_TRANSACTION_PARTS = 6  # Date Time Type Amount Balance Channel
    MIN_AMOUNT_MATCHES = 2  # Need at least 2 amounts (amount and balance)
    MIN_WITHDRAWAL_PARTS = 2  # Minimum parts for withdrawal check
    CHANNEL_SPLIT_PARTS = 2  # Expected parts when splitting by channel

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
        return "krungsri_pdf"

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
        return ["*.pdf"]

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for this parser."""
        return [".pdf"]

    def get_parser_description(self) -> str:
        """Get a human-readable description of this parser."""
        return "Krungsri Bank PDF Statement Parser (pypdfium2)"

    def get_parser_version(self) -> str:
        """Get the parser version."""
        return "1.0.0"

    def supports_reconciliation(self) -> bool:
        """Check if this parser supports reconciliation verification."""
        return True

    def extract_reconciliation_totals(
        self,
        file_path: Path,
        account_config: dict[str, Any],
    ) -> ReconciliationTotals | None:
        """Extract reconciliation totals from the Krungsri PDF statement."""
        password = account_config.get("password")

        if pdfium is None:
            return None

        try:
            pdf = pdfium.PdfDocument(str(file_path), password=password)
            try:
                if len(pdf) == 0:
                    return None

                # Extract text from last page
                last_page = pdf[len(pdf) - 1]
                textpage = last_page.get_textpage()
                text = textpage.get_text_range() if textpage else ""

                if not text:
                    return None

                return self._parse_reconciliation_totals(text)
            finally:
                pdf.close()
        except Exception:
            return None

    def _parse_reconciliation_totals(
        self,
        last_page_text: str,
    ) -> ReconciliationTotals | None:
        """Parse reconciliation totals from Krungsri PDF last page text."""
        lines = last_page_text.split("\n")

        # Find totals lines
        withdrawal_total_line = None
        deposit_total_line = None

        for line in lines:
            if "Total Withdrawal" in line:
                withdrawal_total_line = line
            if "Total Deposit" in line:
                deposit_total_line = line

        if not withdrawal_total_line or not deposit_total_line:
            return None

        # Parse expected totals from PDF
        # Format: "Total Withdrawal 352 items 1,490,601.79 - -"
        withdrawal_match = re.search(
            r"Total Withdrawal\s+(\d+)\s+items\s+([\d,]+\.\d{2})",
            withdrawal_total_line,
        )
        deposit_match = re.search(
            r"Total Deposit\s+(\d+)\s+items\s+([\d,]+\.\d{2})",
            deposit_total_line,
        )

        if not withdrawal_match or not deposit_match:
            return None

        return ReconciliationTotals(
            debit_count=int(withdrawal_match.group(1)),
            debit_total=Decimal(withdrawal_match.group(2).replace(",", "")),
            credit_count=int(deposit_match.group(1)),
            credit_total=Decimal(deposit_match.group(2).replace(",", "")),
        )

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        # Check if file exists and is a file (not directory)
        if not file_path.exists():
            msg = f"File does not exist: {file_path}"
            raise ValueError(msg)
        if not file_path.is_file():
            msg = f"Path is not a file: {file_path}"
            raise ValueError(msg)

        # Check file extension
        # For can_parse, we'll just check if it's a PDF file
        # The actual password validation will happen in parse_file
        return file_path.suffix.lower() == ".pdf"

    def parse_file(
        self,
        file_path: Path,
        account_config: dict[str, Any],
        config_manager: "ConfigManager | None" = None,
    ) -> Iterator[Transaction]:
        """Parse Krungsri PDF statement and yield Transaction objects.

        Password is optional. If the PDF is password-protected and no password
        is provided, an error will be raised. If password is provided but incorrect,
        an error will be raised.
        """
        # Get password from account configuration (optional)
        password = account_config.get("password")

        if pdfium is None:
            msg = "pypdfium2 is required for PDF parsing. Install with: pip install pypdfium2"
            raise ImportError(msg)

        try:
            # Open PDF with pypdfium2
            pdf = pdfium.PdfDocument(str(file_path), password=password)

            try:
                # Verify it's a Krungsri PDF by checking content
                if len(pdf) == 0:
                    msg = "PDF file has no pages"
                    raise ValueError(msg)

                # Extract text from first page to check for Krungsri indicators
                first_page = pdf[0]
                textpage = first_page.get_textpage()
                text = textpage.get_text_range() if textpage else ""

                # Look for Krungsri-specific indicators
                krungsri_indicators = [
                    "Bank of Ayudhya",
                    "Krungsri",
                    "Statement of Savings Account",
                    "XXX-1-32483-X",  # Account number pattern
                ]

                if not any(indicator in text for indicator in krungsri_indicators):
                    msg = "PDF file does not appear to be a Krungsri bank statement"
                    raise ValueError(
                        msg,
                    )

                # Collect all transactions first for reconciliation
                all_transactions = []

                # Process all pages
                for page_num in range(len(pdf)):
                    page = pdf[page_num]
                    # Extract text from the page
                    textpage = page.get_textpage()
                    text = textpage.get_text_range() if textpage else ""
                    if not text:
                        continue

                    # Parse transactions from the text
                    page_transactions = list(
                        self._parse_transactions_from_text(
                            text,
                            account_config,
                            file_path,
                        ),
                    )
                    all_transactions.extend(page_transactions)

                # Extract and verify totals from last page
                # Note: Krungsri totals may include transactions outside the statement period,
                # so reconciliation is performed but failures are logged as warnings rather than errors
                expected_totals = self.extract_reconciliation_totals(
                    file_path,
                    account_config,
                )

                if expected_totals:
                    try:
                        self.verify_reconciliation(
                            all_transactions,
                            expected_totals,
                            file_path,
                        )
                    except ValueError as e:
                        # Log reconciliation failure but don't fail parsing
                        # This allows parsing to continue even if totals don't match exactly
                        # (e.g., if PDF includes transactions outside the statement period)
                        log_error(f"Reconciliation warning (parsing continues): {e}")

                # Yield all transactions
                yield from all_transactions
            finally:
                pdf.close()

        except ValueError:
            # Re-raise ValueError as-is (these are our own error messages)
            raise
        except Exception as e:
            # Check for password/encryption related errors
            error_str = str(e).lower()
            if (
                "password" in error_str
                or "encrypted" in error_str
                or "authenticate" in error_str
                or "incorrect password" in error_str
            ):
                if not password:
                    msg = (
                        f"PDF file {file_path} appears to be password-protected. "
                        f"Please add 'password' field to account configuration."
                    )
                else:
                    msg = (
                        f"Incorrect password for PDF file {file_path}. "
                        f"Please check the password in account configuration."
                    )
                raise ValueError(msg) from None
            msg = f"Error parsing PDF file {file_path}: {e}"
            raise ValueError(msg) from e

    def _parse_transactions_from_text(
        self,
        text: str,
        account_config: dict[str, Any],
        file_path: Path,
    ) -> Iterator[Transaction]:
        """Parse transactions from extracted text."""
        # Split text into lines
        lines = text.split("\n")

        # Find the transaction section
        transaction_lines = []
        in_transaction_section = False

        for line in lines:
            # Look for the start of transaction data (header might be split across lines)
            if "Date/Time Transaction" in line or "Outstanding Balance" in line:
                in_transaction_section = True
                continue

            # Skip page headers and other non-transaction lines
            if (
                line.startswith(
                    (
                        "Page ",
                        "Account Name",
                        "E-mail",
                        "Branch Name",
                        "Statement of",
                        "Period",
                        "1222 Rama III",
                        "Bank of Ayudhya",
                    ),
                )  # Skip footer
            ):
                continue

            if (
                in_transaction_section
                and line.strip()
                and self._is_transaction_line(line)
            ):
                transaction_lines.append(line)

        # Parse each transaction line
        for line in transaction_lines:
            try:
                transaction = self._parse_transaction_line(
                    line,
                    account_config,
                    file_path,
                )
                if transaction:
                    yield transaction
            except Exception as e:
                # Log parsing errors but continue with other transactions
                log_error(f"Error parsing transaction line '{line}': {e}")
                continue

    def _is_transaction_line(self, line: str) -> bool:
        """Check if a line contains transaction data."""
        # Transaction lines should have date/time pattern at the start
        date_pattern = r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}"
        return bool(re.match(date_pattern, line.strip()))

    def _parse_transaction_line(
        self,
        line: str,
        account_config: dict[str, Any],
        file_path: Path,
    ) -> Transaction | None:
        """Parse a single transaction line."""
        # Remove extra whitespace and normalize
        line = line.strip()

        # Split the line into parts
        # Format: Date/Time Transaction Type Amount Balance Channel Description
        parts = line.split()

        # Need at least 6 parts: Date Time Type Amount Balance Channel
        if len(parts) < self.MIN_TRANSACTION_PARTS:
            return None

        try:
            # Extract date and time
            date_str = f"{parts[0]} {parts[1]}"
            # Parse datetime and make it timezone aware
            naive_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")  # noqa: DTZ007
            timezone_str = "Asia/Bangkok"  # Default fallback
            tz = pytz.timezone(timezone_str)
            date = tz.localize(naive_date)

            # Find the amounts in the line
            # Look for patterns like "5,000.00" or "1,577.18"
            amount_pattern = r"[\d,]+\.\d{2}"
            amounts = re.findall(amount_pattern, line)

            if len(amounts) < self.MIN_AMOUNT_MATCHES:
                return None

            # Format: Date/Time Transaction Type Amount OldBalance NewBalance Channel Description
            # amounts[0] = transaction amount, amounts[1] = old balance, amounts[2] = new balance
            amount_str = amounts[0].replace(",", "")
            # Use the last amount as the new balance (current balance after transaction)
            balance_str = amounts[-1].replace(",", "")

            amount = Decimal(amount_str)
            balance = Decimal(balance_str)

            # Determine if this is a withdrawal or deposit based on transaction type
            # Look for the transaction type (between time and first amount)
            time_end = line.find(parts[1]) + len(parts[1])
            amount_start = line.find(amounts[0])
            transaction_type_part = line[time_end:amount_start].strip()

            # Determine if it's a withdrawal or deposit
            if (
                "Withdrawal" in transaction_type_part
                or "Withd" in transaction_type_part
            ):
                amount = -abs(amount)  # Make it negative for withdrawal
            elif "Deposit" in transaction_type_part:
                amount = abs(amount)  # Keep it positive for deposit
            else:
                # Default to negative (withdrawal) for other types
                amount = -abs(amount)

            # Determine transaction type from the description
            transaction_type = self._determine_transaction_type(line)

            # Extract description (everything after the balance)
            # Find where the balance ends and extract the rest
            balance_end = line.find(balance_str) + len(balance_str)
            description_part = line[balance_end:].strip()

            # Extract channel and description
            # For Tax transactions, there's no additional description
            if "Tax" in line:
                channel, description = None, ""
            elif "Interest" in line:
                # For Interest transactions, clean up the description
                channel, description = None, ""
            else:
                # Split description into channel and description
                channel, description = self._extract_channel_and_description(
                    description_part,
                )

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
                channel=channel,
                raw_text=line,
                source_file=str(file_path),
                parser_name="krungsri_pdf",
            )

        except (ValueError, IndexError) as e:
            log_error(f"Error parsing transaction line: {line} - {e}")
            return None

    def _determine_transaction_type(self, line: str) -> str:
        """Determine transaction type from the line content."""
        line_lower = line.lower()

        # Check for more specific transaction types first
        if "interest" in line_lower:
            return "interest"
        if "tax" in line_lower:
            return "tax"
        if "bill payment" in line_lower:
            return "bill_payment"
        if "backdate" in line_lower:
            return "backdate"
        if "withdrawal" in line_lower or "withd" in line_lower:
            return "withdrawal"
        if "transfer" in line_lower:
            return "transfer"
        if "spending" in line_lower:
            return "spending"
        if "payment" in line_lower:
            return "payment"
        if "deposit" in line_lower:
            return "deposit"
        return "other"

    def _is_withdrawal(self, line: str) -> bool:
        """Check if a transaction line represents a withdrawal."""
        # Find transaction type - it's everything between time and first amount
        parts = line.split()
        if len(parts) < self.MIN_WITHDRAWAL_PARTS:
            return False

        # Find the first amount in the line
        amount_pattern = r"[\d,]+\.\d{2}"
        matches = list(re.finditer(amount_pattern, line))
        if not matches:
            return False

        time_end = line.find(parts[1]) + len(parts[1])
        amount_start = line.find(matches[0].group(0))
        transaction_type = line[time_end:amount_start].strip()

        # Determine if it's a credit or debit (same logic as text parser)
        return not ("Deposit" in transaction_type or "Interest" in transaction_type)

    def _extract_channel_and_description(
        self,
        description_part: str,
    ) -> tuple[str | None, str]:
        """Extract channel and description from the description part."""
        if not description_part:
            return None, ""

        # Common channels in Krungsri statements
        channels = ["MOBILE", "ATM", "BRANCH", "POS", "ACH"]

        # Find the first channel in the description
        for channel in channels:
            if channel in description_part:
                # Split at the channel
                parts = description_part.split(channel, 1)
                if len(parts) == self.CHANNEL_SPLIT_PARTS:
                    return channel, parts[1].strip()
                return channel, description_part

        # If no specific channel found, return the whole description
        return None, description_part.strip()
