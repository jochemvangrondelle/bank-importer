"""Parser for SCB (Siam Commercial Bank) PDF statements."""

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


class ScbPdfParser(Parser):
    """Parser for SCB PDF bank statements."""

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        if file_path.suffix.lower() != ".pdf":
            return False

        # For can_parse, we'll just check if it's a PDF file
        # The actual password validation will happen in parse_file
        return True

    def parse_file(
        self, file_path: Path, account_config: dict[str, Any], config_manager=None
    ) -> Iterator[Transaction]:
        """Parse SCB PDF statement and yield Transaction objects."""
        # Get password from account configuration
        password = account_config.get("password")

        if not password:
            raise ValueError(
                f"Password is required for PDF file {file_path}. Please add 'password' field to account configuration."
            )

        try:
            with pdfplumber.open(file_path, password=password) as pdf:
                # Verify it's an SCB PDF by checking content
                if len(pdf.pages) == 0:
                    raise ValueError(f"PDF file {file_path} has no pages")

                # Extract text from first page to check for SCB indicators
                first_page = pdf.pages[0]
                text = first_page.extract_text()

                # Look for SCB-specific indicators
                scb_indicators = [
                    "ACCOUNT STATEMENT WITH NOTES",
                    "SCB",
                    "Siam Commercial Bank",
                    "042-289064-1",  # Account number pattern
                ]

                if not any(indicator in text for indicator in scb_indicators):
                    raise ValueError(
                        f"PDF file {file_path} does not appear to be an SCB bank statement"
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
            raise ValueError(f"Error parsing PDF file {file_path}: {e}") from e

    def _parse_transactions_from_text(
        self, text: str, account_config: dict[str, Any], file_path: Path
    ) -> Iterator[Transaction]:
        """Parse transactions from extracted text."""
        # Split text into lines
        lines = text.split("\n")

        # Find the transaction section
        transaction_lines = []
        in_transaction_section = False
        current_transaction = {}

        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Look for the start of transaction data
            if "Date/Time Code/Channel Debit Credit Balance Description/Note" in line:
                in_transaction_section = True
                continue

            # Skip page headers and other non-transaction lines
            if (
                line.startswith("ACCOUNT STATEMENT")
                or line.startswith("รายการเดินบัญชี")
                or line.startswith("Account No.")
                or line.startswith("เลขที่บัญชี")
                or line.startswith("MISTER")
                or line.startswith("www.scb.co.th")
                or line.startswith("SCB Call Center")
                or line.startswith("ฝ่ายบริการลูกค้า")
                or line.startswith("Total amount")
                or line.startswith("Total items")
                or line.startswith("ยอดเงินคงเหลือยกมา")
                or line.startswith("Balance brought forward")
            ):
                continue

            if in_transaction_section:
                # Check if this is a transaction line (starts with date pattern)
                date_pattern = r"^\d{2}/\d{2}/\d{2}"
                if re.match(date_pattern, line):
                    # This is a date line with description
                    # Format: DD/MM/YY DESC : Description
                    parts = line.split(" DESC :", 1)
                    if len(parts) == 2:
                        date_part = parts[0].strip()
                        description = parts[1].strip()

                        # Parse the date
                        try:
                            # SCB uses DD/MM/YY format, convert to full year
                            day, month, year = date_part.split("/")
                            # Assume 20xx for years
                            full_year = f"20{year}"
                            # Parse as naive datetime first, then make it timezone aware
                            naive_date = datetime.strptime(
                                f"{day}/{month}/{full_year}", "%d/%m/%Y"
                            )
                            timezone_str = "Asia/Bangkok"  # Default fallback
                            tz = pytz.timezone(timezone_str)
                            date = tz.localize(naive_date)
                        except ValueError:
                            continue

                        # Look for the next line which should contain the transaction details
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            # Parse transaction details line
                            # Format: CODE/CHANNEL AMOUNT BALANCE
                            details = self._parse_transaction_details_new(next_line)
                            if details:
                                # Look for time in the next line
                                time = None
                                if i + 2 < len(lines):
                                    time_line = lines[i + 2].strip()
                                    if re.match(r"^\d{2}:\d{2}$", time_line):
                                        time = time_line

                                # Create transaction object
                                transaction = self._create_transaction(
                                    {
                                        "date": date,
                                        "description": description,
                                        "time": time,
                                        "debit": details.get("debit"),
                                        "credit": details.get("credit"),
                                        "balance": details.get("balance"),
                                        "channel": details.get("channel"),
                                    },
                                    account_config,
                                    file_path,
                                )
                                if transaction:
                                    yield transaction

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

    def _parse_transaction_details(self, line: str) -> dict[str, Any] | None:
        """Parse transaction details line."""
        # Format: Code/Channel Debit Credit Balance
        # Examples: X2/ENET 216.00 202,426.33
        #          FE/ENET 199.00 202,227.33
        #          X2/ENET 99,999.89 102,227.44

        # Split by whitespace
        parts = line.split()
        if len(parts) < 2:
            return None

        # First part is usually the channel code
        channel = parts[0]

        # Look for amounts (numbers with optional commas and decimals)
        amounts = []
        for part in parts[1:]:
            # Remove commas and check if it's a number
            clean_part = part.replace(",", "")
            if re.match(r"^\d+\.?\d*$", clean_part):
                amounts.append(Decimal(clean_part))

        if len(amounts) < 2:
            return None

        # In SCB format, we have: Debit Credit Balance
        # If there are 3 amounts, they are: Debit Credit Balance
        # If there are 2 amounts, they are: Credit Balance (no debit)
        if len(amounts) == 3:
            debit, credit, balance = amounts
        elif len(amounts) == 2:
            debit = None
            credit, balance = amounts
        else:
            return None

        return {
            "channel": channel,
            "debit": debit,
            "credit": credit,
            "balance": balance,
        }

    def _parse_transaction_details_new(self, line: str) -> dict[str, Any] | None:
        """Parse transaction details line in the correct SCB format (CODE/CHANNEL AMOUNT BALANCE)."""
        # Format: CODE/CHANNEL AMOUNT BALANCE
        # Examples: X2/ENET 411.95 26,409.44
        #          FE/ENET 199.00 25,206.44
        #          X2/ENET 9,997.45 15,208.99

        # Split by whitespace
        parts = line.split()
        if len(parts) < 3:  # Need at least CODE/CHANNEL AMOUNT BALANCE
            return None

        # Extract channel, amount, and balance
        channel_part = parts[0]
        amount_part = parts[1]
        balance_part = parts[2]

        # Parse channel (format: CODE/CHANNEL)
        channel_match = re.match(r"^[A-Z0-9]{1,2}/\w+$", channel_part)
        if not channel_match:
            return None
        channel = channel_part

        # Parse amount (numbers with optional commas and decimals)
        clean_amount = amount_part.replace(",", "")
        if not re.match(r"^\d+\.?\d*$", clean_amount):
            return None
        amount = Decimal(clean_amount)

        # Parse balance (numbers with optional commas and decimals)
        clean_balance = balance_part.replace(",", "")
        if not re.match(r"^\d+\.?\d*$", clean_balance):
            return None
        balance = Decimal(clean_balance)

        # In SCB format, the amount shown is typically the debit amount (withdrawal)
        # We'll determine if it's a debit or credit based on the transaction type
        # For now, assume it's a debit (withdrawal) - the _create_transaction method will handle this
        debit = amount
        credit = None

        return {
            "channel": channel,
            "debit": debit,
            "credit": credit,
            "balance": balance,
        }

    def _create_transaction(
        self,
        transaction_data: dict[str, Any],
        account_config: dict[str, Any],
        file_path: Path,
    ) -> Transaction | None:
        """Create a Transaction object from parsed data."""
        try:
            # Get the amount from the transaction details
            amount = transaction_data.get("debit") or transaction_data.get("credit")
            if amount is None:
                return None

            # Determine transaction type based on the amount and description
            # In SCB format, positive amounts are usually debits (withdrawals)
            # We need to determine if this is a withdrawal or deposit
            description = transaction_data.get("description", "").lower()

            # Look for keywords that indicate withdrawal vs deposit
            withdrawal_keywords = [
                "withdrawal",
                "payment",
                "purchase",
                "transfer out",
                "debit",
            ]
            deposit_keywords = [
                "deposit",
                "credit",
                "transfer in",
                "refund",
                "interest",
            ]

            is_withdrawal = any(
                keyword in description for keyword in withdrawal_keywords
            )
            is_deposit = any(keyword in description for keyword in deposit_keywords)

            # If we can't determine from description, assume it's a withdrawal (positive amount)
            if not is_withdrawal and not is_deposit:
                is_withdrawal = True  # Default assumption

            if is_withdrawal:
                amount = -abs(amount)  # Make it negative for withdrawal
                transaction_type = "withdrawal"
            else:
                amount = abs(amount)  # Keep it positive for deposit
                transaction_type = "deposit"

            # Balance is required
            balance = transaction_data.get("balance")
            if balance is None:
                return None

            # Create transaction
            return Transaction(
                date=transaction_data["date"],
                description=transaction_data["description"],
                amount=amount,
                balance=balance,
                currency=account_config.get("currency", "THB"),
                transaction_type=transaction_type,
                account_number=account_config.get("account_number", ""),
                account_name=account_config.get("account_name", ""),
                bank_name=account_config.get("bank_name", "SCB"),
                branch_name=account_config.get("branch_name", ""),
                channel=transaction_data.get("channel"),
                reference=account_config.get("reference", ""),
                source_file=str(file_path),
                country_code=account_config.get("country_code", "TH"),
                parser_name="scb_pdf",
            )
        except Exception as e:
            print(f"Error creating transaction: {e}")
            return None

    def _parse_transaction_line(
        self, line: str, account_config: dict[str, Any], file_path: Path
    ) -> Transaction | None:
        """Parse a single transaction line (legacy method, not used in new implementation)."""
        # This method is kept for compatibility but not used in the new implementation
        return None
