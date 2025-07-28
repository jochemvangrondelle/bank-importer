"""Parser for SCB (Siam Commercial Bank) PDF statements."""

import re
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

import pdfplumber
import pytz

from ..interfaces.parser import Parser
from ..models.transaction import Transaction


class ScbPdfParser(Parser):
    """Parser for SCB PDF bank statements."""

    def get_bank_type(self) -> str:
        """Get the bank type identifier for this parser."""
        return "scb"

    def get_export_config(self) -> Dict[str, Any]:
        """Get export configuration specific to this parser."""
        return {
            "bank_name": "Siam Commercial Bank",
            "default_account_name": "SCB Savings Account",
            "default_account_number": "042-2-89064-1",
            "default_currency": "THB",
            "default_country_code": "TH",
            "supports_foreign_currency": False,
            "supports_translation": True,
            "translation_source_language": "TH",
            "translation_target_language": "en",
        }

    def get_parser_name(self) -> str:
        """Get the parser name identifier."""
        return "scb_pdf"

    def get_default_account_name(self) -> str:
        """Get the default account name for this parser."""
        return "SCB Savings Account"

    def get_default_account_number(self) -> str:
        """Get the default account number for this parser."""
        return "042-2-89064-1"

    def get_default_currency(self) -> str:
        """Get the default currency for this parser."""
        return "THB"

    def get_default_country_code(self) -> str:
        """Get the default country code for this parser."""
        return "TH"

    def get_supported_file_patterns(self) -> list[str]:
        """Get list of supported file patterns for this parser."""
        return ["*AcctSt_*.pdf"]

    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions for this parser."""
        return [".pdf"]

    def get_parser_description(self) -> str:
        """Get a human-readable description of this parser."""
        return "Siam Commercial Bank PDF Statement Parser"

    def get_parser_version(self) -> str:
        """Get the parser version."""
        return "1.0.0"

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
        in_transaction_section = False

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
                or line.startswith("NOTE :")
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
                                        "raw_amount": details.get("raw_amount"),
                                        "balance": details.get("balance"),
                                        "channel": details.get("channel"),
                                    },
                                    account_config,
                                    file_path,
                                )
                                if transaction:
                                    yield transaction

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

        # In SCB format, we need to determine if this is a debit or credit
        # We'll store the raw amount and let _create_transaction determine the classification
        # based on the transaction description and channel
        return {
            "channel": channel,
            "raw_amount": amount,
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
            # Get the raw amount and balance from the transaction details
            raw_amount = transaction_data.get("raw_amount")
            balance = transaction_data.get("balance")
            description = transaction_data.get("description", "")
            channel = transaction_data.get("channel", "")

            if balance is None or raw_amount is None:
                return None

            # Determine if this is income or expense based on description and channel
            # Income indicators: "Received transfer", "From the deposit system", "Credit", etc.
            # Expense indicators: "Withdrawal", "Payment", "Debit", etc.

            # Check for income indicators in description
            income_keywords = [
                "received transfer",
                "รับโอนจาก",
                "from the deposit system",
                "จากระบบเงินฝาก",
                "credit",
                "deposit",
                "transfer in",
                "mcl",  # MCL transactions are typically deposits
            ]

            # Check for expense indicators in description
            expense_keywords = [
                "withdrawal",
                "payment",
                "debit",
                "purchase",
                "transfer out",
                "withdraw",
                "pay",
                "spend",
                "จ่ายบิล",  # Bill payment in Thai
                "top-up",
                "terminal",
                "atm",
                "cdm",
                "transfer to",  # Transfer to other accounts
                "promptpay",  # PromptPay transfers
                "income from work",  # Income from work transfers
            ]

            # Check channel codes for income/expense classification
            income_channels = ["X1", "X2", "IN"]  # Transfer in, deposit
            expense_channels = [
                "FE",
                "WD",
                "PAY",
                "ATM",
                "CDM",
            ]  # Fee, withdrawal, payment

            is_income = False
            is_expense = False

            # Check description keywords
            description_lower = description.lower()
            for keyword in income_keywords:
                if keyword in description_lower:
                    is_income = True
                    break

            for keyword in expense_keywords:
                if keyword in description_lower:
                    is_expense = True
                    break

            # Check channel codes
            if not is_income and not is_expense:
                for channel_code in income_channels:
                    if channel.startswith(channel_code):
                        is_income = True
                        break

                for channel_code in expense_channels:
                    if channel.startswith(channel_code):
                        is_expense = True
                        break

            # Determine amount and transaction type
            if is_income:
                amount = raw_amount  # Income is positive
                transaction_type = "deposit"
            elif is_expense:
                amount = -raw_amount  # Expense is negative
                transaction_type = "withdrawal"
            else:
                # Default to expense if we can't determine
                amount = -raw_amount
                transaction_type = "withdrawal"

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
                channel=channel,
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
