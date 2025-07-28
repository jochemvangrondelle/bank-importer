"""Parser for Krungsri Bank PDF statements."""

import re
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pdfplumber
import pytz

from ..interfaces.parser import Parser
from ..models.transaction import Transaction


class KrungsriPdfParser(Parser):
    """Parser for Krungsri Bank PDF statements."""

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        # Check if file exists and is a file (not directory)
        if not file_path.exists():
            raise ValueError(f"File does not exist: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Check file extension
        if file_path.suffix.lower() != ".pdf":
            return False

        # For can_parse, we'll just check if it's a PDF file
        # The actual password validation will happen in parse_file
        return True

    def parse_file(
        self, file_path: Path, account_config: dict[str, Any], config_manager=None
    ) -> Iterator[Transaction]:
        """Parse Krungsri PDF statement and yield Transaction objects."""
        # Get password from account configuration
        password = account_config.get("password")

        if not password:
            raise ValueError(
                f"Password is required for PDF file {file_path}. Please add 'password' field to account configuration."
            )

        try:
            with pdfplumber.open(file_path, password=password) as pdf:
                # Verify it's a Krungsri PDF by checking content
                if len(pdf.pages) == 0:
                    raise ValueError("PDF file has no pages")

                # Extract text from first page to check for Krungsri indicators
                first_page = pdf.pages[0]
                text = first_page.extract_text()

                # Look for Krungsri-specific indicators
                krungsri_indicators = [
                    "Bank of Ayudhya",
                    "Krungsri",
                    "Statement of Savings Account",
                    "XXX-1-32483-X",  # Account number pattern
                ]

                if not any(indicator in text for indicator in krungsri_indicators):
                    raise ValueError(
                        "PDF file does not appear to be a Krungsri bank statement"
                    )

                # Process all pages
                for page in pdf.pages:
                    # Extract text from the page
                    text = page.extract_text()
                    if not text:
                        continue

                    # Parse transactions from the text
                    yield from self._parse_transactions_from_text(
                        text, account_config, file_path
                    )

        except Exception as e:
            if (
                "password" in str(e).lower()
                or "encrypted" in str(e).lower()
                or "PDFPasswordIncorrect" in str(e)
                or "PdfminerException" in str(e)
            ):
                raise ValueError(
                    f"Incorrect password for PDF file {file_path}. Please check the password in account configuration."
                ) from None
            raise ValueError("Error parsing PDF file") from e

    def _parse_transactions_from_text(
        self, text: str, account_config: dict[str, Any], file_path: Path
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
                line.startswith("Page ")
                or line.startswith("Account Name")
                or line.startswith("E-mail")
                or line.startswith("Branch Name")
                or line.startswith("Statement of")
                or line.startswith("Period")
                or line.startswith("1222 Rama III")  # Skip footer
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
                    line, account_config, file_path
                )
                if transaction:
                    yield transaction
            except Exception as e:
                # Log parsing errors but continue with other transactions
                print(f"Error parsing transaction line '{line}': {e}")
                continue

    def _is_transaction_line(self, line: str) -> bool:
        """Check if a line contains transaction data."""
        # Transaction lines should have date/time pattern at the start
        date_pattern = r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}"
        return bool(re.match(date_pattern, line.strip()))

    def _parse_transaction_line(
        self, line: str, account_config: dict[str, Any], file_path: Path
    ) -> Transaction | None:
        """Parse a single transaction line."""
        # Remove extra whitespace and normalize
        line = line.strip()

        # Split the line into parts
        # Format: Date/Time Transaction Withdrawal/Deposit Outstanding Balance Channel Description
        parts = line.split()

        # Tax transactions have only 5 parts, others have 6+
        if len(parts) < 5:
            return None

        try:
            # Extract date and time
            date_str = f"{parts[0]} {parts[1]}"
            # Parse as naive datetime first, then make it timezone aware
            naive_date = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            timezone_str = "Asia/Bangkok"  # Default fallback
            tz = pytz.timezone(timezone_str)
            date = tz.localize(naive_date)

            # Find the amount and balance
            # Look for patterns like "5,000.00" or "1,577.18"
            amount_pattern = r"[\d,]+\.\d{2}"
            amounts = re.findall(amount_pattern, line)

            if len(amounts) < 2:
                return None

            # First amount is the transaction amount, second is the balance
            amount_str = amounts[0].replace(",", "")
            balance_str = amounts[1].replace(",", "")

            amount = Decimal(amount_str)
            balance = Decimal(balance_str)

            # Make withdrawals negative (same logic as text parser)
            if self._is_withdrawal(line):
                amount = -amount

            # Determine transaction type from the description
            transaction_type = self._determine_transaction_type(line)

            # Extract description (everything after the balance)
            # Find where the balance ends and extract the rest
            balance_end = line.find(balance_str) + len(balance_str)
            description_part = line[balance_end:].strip()

            # For Tax transactions, there's no additional description
            if "Tax" in line:
                channel, description = None, ""
            elif "Interest" in line:
                # For Interest transactions, clean up the description
                channel, description = None, ""
            else:
                # Split description into channel and description
                channel, description = self._extract_channel_and_description(
                    description_part
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
            print(f"Error parsing transaction line: {line} - {e}")
            return None

    def _determine_transaction_type(self, line: str) -> str:
        """Determine transaction type from the line content."""
        line_lower = line.lower()

        # Check for more specific transaction types first
        if "interest" in line_lower:
            return "interest"
        elif "tax" in line_lower:
            return "tax"
        elif "bill payment" in line_lower:
            return "bill_payment"
        elif "backdate" in line_lower:
            return "backdate"
        elif "withdrawal" in line_lower or "withd" in line_lower:
            return "withdrawal"
        elif "transfer" in line_lower:
            return "transfer"
        elif "spending" in line_lower:
            return "spending"
        elif "payment" in line_lower:
            return "payment"
        elif "deposit" in line_lower:
            return "deposit"
        else:
            return "other"

    def _is_withdrawal(self, line: str) -> bool:
        """Check if a transaction line represents a withdrawal."""
        # Find transaction type - it's everything between time and first amount
        parts = line.split()
        if len(parts) < 2:
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
        self, description_part: str
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
                if len(parts) == 2:
                    return channel, parts[1].strip()
                else:
                    return channel, description_part

        # If no specific channel found, return the whole description
        return None, description_part.strip()
