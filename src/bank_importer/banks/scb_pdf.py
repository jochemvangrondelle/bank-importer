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

"""Parser for SCB (Siam Commercial Bank) PDF statements using pypdfium2."""

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


class ScbPdfParser(Parser):
    """Parser for SCB PDF bank statements using pypdfium2."""

    # Constants for parsing
    DESC_SPLIT_PARTS = 2  # Expected parts when splitting by " DESC :"
    MIN_LINE_PARTS = 2  # Minimum parts in a line
    MIN_AMOUNT_MATCHES = 2  # Need at least 2 amounts (credit and balance)
    THREE_AMOUNTS = 3  # Three amounts: Debit Credit Balance
    MIN_TRANSACTION_PARTS = 3  # Need at least CODE/CHANNEL AMOUNT BALANCE

    def get_bank_type(self) -> str:
        """Get the bank type identifier for this parser."""
        return "scb"

    def get_export_config(self) -> dict[str, Any]:
        """Get export configuration specific to this parser."""
        return {
            "bank_name": "Siam Commercial Bank",
            "default_account_name": "SCB Savings Account",
            "default_account_number": "012-3-45678-9",
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
        return "Siam Commercial Bank PDF Statement Parser (pypdfium2)"

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
        """Extract reconciliation totals from the SCB PDF statement."""
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
        """Parse reconciliation totals from SCB PDF last page text.

        SCB format:
        Total amount
        Total items
        37,296.58 0.00    (debit total, credit total)
        27 0              (debit count, credit count)
        """
        lines = last_page_text.split("\n")

        # Find totals section - look for line with both "Total amount" and "Total items"
        # or find them separately
        total_amount_line_idx = None
        total_items_line_idx = None

        for i, line in enumerate(lines):
            if "Total amount" in line:
                total_amount_line_idx = i
            if "Total items" in line:
                total_items_line_idx = i

        if total_amount_line_idx is None or total_items_line_idx is None:
            return None

        # The amounts and counts are typically on the lines after "Total items"
        # Format: amounts on one line, counts on next line
        amounts_line = None
        counts_line = None

        # Look for amounts line (contains two decimal numbers)
        start_idx = max(total_amount_line_idx, total_items_line_idx) + 1
        for i in range(start_idx, min(start_idx + 5, len(lines))):
            line = lines[i].strip()
            # Check if line contains two decimal numbers (amounts)
            amounts = re.findall(r"[\d,]+\.\d{2}", line)
            if len(amounts) >= 2:
                amounts_line = line
                # Counts should be on the next line
                if i + 1 < len(lines):
                    counts_line = lines[i + 1].strip()
                break

        if not amounts_line or not counts_line:
            return None

        # Parse amounts (remove commas, convert to Decimal)
        amounts = [
            Decimal(a.replace(",", ""))
            for a in re.findall(r"[\d,]+\.\d{2}", amounts_line)
        ]
        # Parse counts (integers only, no commas in counts)
        counts = [
            int(c)
            for c in re.findall(r"^\d+$", counts_line.split()[0])
            + re.findall(r"^\d+$", counts_line.split()[1])
            if c.isdigit()
        ]

        # Alternative: parse counts from the counts_line directly
        if not counts:
            count_parts = counts_line.split()
            counts = [int(p) for p in count_parts if p.isdigit()]

        if len(amounts) < 2 or len(counts) < 2:
            return None

        return ReconciliationTotals(
            debit_count=counts[0],
            debit_total=amounts[0],
            credit_count=counts[1],
            credit_total=amounts[1],
        )

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        # For can_parse, we'll just check if it's a PDF file
        # The actual password validation will happen in parse_file
        return file_path.suffix.lower() == ".pdf"

    def parse_file(
        self,
        file_path: Path,
        account_config: dict[str, Any],
        config_manager: "ConfigManager | None" = None,
    ) -> Iterator[Transaction]:
        """Parse SCB PDF statement and yield Transaction objects.

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
                # Verify it's an SCB PDF by checking content
                if len(pdf) == 0:
                    msg = f"PDF file {file_path} has no pages"
                    raise ValueError(msg)

                # Extract text from first page to check for SCB indicators
                first_page = pdf[0]
                textpage = first_page.get_textpage()
                text = textpage.get_text_range() if textpage else ""

                # Look for SCB-specific indicators
                scb_indicators = [
                    "ACCOUNT STATEMENT WITH NOTES",
                    "SCB",
                    "Siam Commercial Bank",
                    "012-345678-9",  # Account number pattern
                ]

                if not any(indicator in text for indicator in scb_indicators):
                    msg = f"PDF file {file_path} does not appear to be an SCB bank statement"
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
                expected_totals = self.extract_reconciliation_totals(
                    file_path,
                    account_config,
                )

                if expected_totals:
                    self.verify_reconciliation(
                        all_transactions,
                        expected_totals,
                        file_path,
                    )

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
            if line.startswith(
                (
                    "ACCOUNT STATEMENT",
                    "รายการเดินบัญชี",
                    "Account No.",
                    "เลขที่บัญชี",
                    "MISTER",
                    "www.scb.co.th",
                    "SCB Call Center",
                    "ฝ่ายบริการลูกค้า",
                    "Total amount",
                    "Total items",
                    "ยอดเงินคงเหลือยกมา",
                    "Balance brought forward",
                    "NOTE :",
                ),
            ):
                continue

            if in_transaction_section:
                # Check if this is a transaction line (starts with date pattern)
                date_pattern = r"^\d{2}/\d{2}/\d{2}"
                if re.match(date_pattern, line):
                    # This is a date line
                    # Format: DD/MM/YY or DD/MM/YY DESC : Description
                    date_part = line.split(" DESC :", 1)[0].strip()
                    description_from_date = ""
                    if " DESC :" in line:
                        description_from_date = line.split(" DESC :", 1)[1].strip()

                    # Parse the date
                    try:
                        # SCB uses DD/MM/YY format, convert to full year
                        day, month, year = date_part.split("/")
                        # Assume 20xx for years
                        full_year = f"20{year}"
                        # Parse datetime and make it timezone aware
                        naive_date = datetime.strptime(  # noqa: DTZ007
                            f"{day}/{month}/{full_year}",
                            "%d/%m/%Y",
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
                        # Format: TIME CODE/CHANNEL AMOUNT BALANCE DESCRIPTION
                        # or: CODE/CHANNEL AMOUNT BALANCE DESCRIPTION
                        details = self._parse_transaction_details_with_description(
                            next_line,
                        )
                        if details:
                            # Use description from details line, or fall back to date line
                            description = details.get(
                                "description",
                                description_from_date,
                            )

                            # Look for time in details or next line
                            time = details.get("time")
                            if not time and i + 2 < len(lines):
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
        if len(parts) < self.MIN_LINE_PARTS:
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

        if len(amounts) < self.MIN_AMOUNT_MATCHES:
            return None

        # In SCB format, we have: Debit Credit Balance
        # If there are 3 amounts, they are: Debit Credit Balance
        # If there are 2 amounts, they are: Credit Balance (no debit)
        if len(amounts) == self.THREE_AMOUNTS:
            debit, credit, balance = amounts
        elif len(amounts) == self.MIN_AMOUNT_MATCHES:
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
        if (
            len(parts) < self.MIN_TRANSACTION_PARTS
        ):  # Need at least CODE/CHANNEL AMOUNT BALANCE
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

    def _parse_transaction_details_with_description(
        self,
        line: str,
    ) -> dict[str, Any] | None:
        """Parse transaction details line with description (TIME CODE/CHANNEL AMOUNT BALANCE DESCRIPTION)."""
        # Format: TIME CODE/CHANNEL AMOUNT BALANCE DESCRIPTION
        # Examples: 13:55 X2/ENET 470.80 53,253.17 จ่ายบิล Prime Burger
        #          or: X2/ENET 470.80 53,253.17 Description

        parts = line.split()
        if len(parts) < self.MIN_TRANSACTION_PARTS:
            return None

        # Check if first part is time (HH:MM format)
        time = None
        start_idx = 0
        if re.match(r"^\d{2}:\d{2}$", parts[0]):
            time = parts[0]
            start_idx = 1

        # Need at least CODE/CHANNEL AMOUNT BALANCE after time
        if len(parts) < start_idx + self.MIN_TRANSACTION_PARTS:
            return None

        channel_part = parts[start_idx]
        amount_part = parts[start_idx + 1]
        balance_part = parts[start_idx + 2]
        description = (
            " ".join(parts[start_idx + 3 :]) if len(parts) > start_idx + 3 else ""
        )

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

        return {
            "channel": channel,
            "raw_amount": amount,
            "balance": balance,
            "description": description,
            "time": time,
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
            # Note: X2 in SCB is used for electronic payments (debits), not credits
            income_channels = [
                "X1",
                "IN",
            ]  # Transfer in, deposit (X2 removed - it's used for debits)
            expense_channels = [
                "X2",  # Electronic payment/debit in SCB
                "FE",
                "WD",
                "PAY",
                "ATM",
                "CDM",
                "C2",  # Cash withdrawal
            ]  # Fee, withdrawal, payment

            is_income = False
            is_expense = False

            # Check description keywords first (more reliable)
            description_lower = description.lower()
            for keyword in income_keywords:
                if keyword in description_lower:
                    is_income = True
                    break

            for keyword in expense_keywords:
                if keyword in description_lower:
                    is_expense = True
                    break

            # Check channel codes only if description didn't provide classification
            if not is_income and not is_expense:
                # Check expense channels first (X2 is common for debits)
                for channel_code in expense_channels:
                    if channel.startswith(channel_code):
                        is_expense = True
                        break

                # Then check income channels
                if not is_expense:
                    for channel_code in income_channels:
                        if channel.startswith(channel_code):
                            is_income = True
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
            log_error(f"Error creating transaction: {e}")
            return None

    def _parse_transaction_line(
        self,
        line: str,
        account_config: dict[str, Any],
        file_path: Path,
    ) -> Transaction | None:
        """Parse a single transaction line (legacy method, not used in new implementation)."""
        # This method is kept for compatibility but not used in the new implementation
        return None
