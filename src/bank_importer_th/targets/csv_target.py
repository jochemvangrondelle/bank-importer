"""CSV target for exporting transactions to Firefly-III compatible format."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..interfaces.target import Target
from ..models.transaction import Transaction


class CsvTarget(Target):
    """CSV target for exporting transactions to Firefly-III compatible format."""

    def __init__(self, output_dir: str = "data/out"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def get_name(self) -> str:
        return "csv"

    def _clean_filename(self, filename: str) -> str:
        """Clean filename for use in output filename."""
        # Remove path and extension
        clean_name = Path(filename).stem
        # Replace problematic characters
        clean_name = clean_name.replace(" ", "_").replace("-", "_")
        clean_name = "".join(c for c in clean_name if c.isalnum() or c in "_-")
        # Limit length
        if len(clean_name) > 30:
            clean_name = clean_name[:30]
        return clean_name

    def export_transactions(
        self, transactions: list[Transaction], config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Export transactions to CSV format compatible with Firefly-III.

        Args:
            transactions: List of transactions to export
            config: CSV export configuration

        Returns:
            Export result with metadata
        """
        if not transactions:
            return {
                "target_name": self.get_name(),
                "success": True,
                "exported_count": 0,
                "skipped_count": 0,
                "error_count": 0,
                "metadata": {"message": "No transactions to export"},
            }

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_type = config.get("export_type", "unknown")
        account_ref = config.get("account_reference", "unknown")
        original_filename = config.get("original_filename", "")
        bank_type = config.get("bank_type", "")

        # Determine filename based on export type
        if export_type == "all_consolidated":
            filename = f"all-transactions_{timestamp}.csv"
        elif export_type == "bank_consolidated":
            filename = f"{bank_type}-all_{timestamp}.csv"
        elif export_type == "source_file":
            if original_filename:
                # Use original filename if available
                filename = f"{original_filename}_{timestamp}.csv"
            else:
                # Clean up source file name for filename
                source_file = config.get("source_file", "unknown")
                clean_source = self._clean_filename(source_file)
                filename = f"{clean_source}_{timestamp}.csv"
        else:
            filename = f"{account_ref}_{timestamp}.csv"

        # Use custom output directory if specified
        output_dir = Path(config.get("output_dir", self.output_dir))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        # Firefly-III CSV format with maximum context for easy classification
        fieldnames = [
            # Core transaction data
            "date",
            "description",
            "amount",
            "currency",
            # Account information
            "account_name",
            "account_iban",
            "account_number",
            "account_bic",
            # Opposing account information
            "opposing_name",
            "opposing_iban",
            "opposing_number",
            "opposing_bic",
            # Classification fields
            "category_name",
            "budget_name",
            "bill_name",
            "subscription_name",
            # Transaction metadata
            "transaction_type",
            "channel",
            "reference",
            "check_number",
            "memo",
            "subcategory",
            # Amount details
            "amount_foreign",
            "foreign_currency",
            "exchange_rate",
            "fees",
            "interest",
            "tax",
            # Date metadata
            "date_transaction",
            "date_value",
            "date_posting",
            "date_booking",
            "date_process",
            "date_due",
            "date_invoice",
            "date_payment",
            "date_interest",
            # Balance information
            "balance",
            "balance_old",
            "balance_new",
            "balance_change",
            # Additional metadata
            "tags",
            "notes",
            "external_id",
            "internal_reference",
            # Bank-specific information
            "bank_name",
            "branch_name",
            "country_code",
            "parser_name",
            "source_file",
            # Raw data preservation
            "raw_text",
            "raw_json",
            # Amex-specific fields
            "card_member",
            "appears_on_statement",
            "address",
            "city_state",
            "zip_code",
            "extended_details",
        ]

        exported_count = 0
        error_count = 0

        try:
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for transaction in transactions:
                    try:
                        row = self._transaction_to_csv_row(transaction, config)
                        writer.writerow(row)
                        exported_count += 1
                    except Exception as e:
                        error_count += 1
                        # Log error but continue with other transactions
                        print(f"Error exporting transaction {transaction.id}: {e}")

            # Generate Firefly-III import configuration
            config_filename = filename.replace(".csv", "_config.json")
            config_path = output_dir / config_filename
            self._generate_import_config(config_path, config, len(transactions))

            return {
                "target_name": self.get_name(),
                "success": True,
                "exported_count": exported_count,
                "skipped_count": 0,
                "error_count": error_count,
                "output_file": str(output_path),
                "metadata": {
                    "filename": filename,
                    "config_filename": config_filename,
                    "account_reference": account_ref,
                    "total_transactions": len(transactions),
                },
            }

        except Exception as e:
            return {
                "target_name": self.get_name(),
                "success": False,
                "exported_count": 0,
                "skipped_count": 0,
                "error_count": len(transactions),
                "error_message": str(e),
            }

    def _transaction_to_csv_row(
        self, transaction: Transaction, config: dict[str, Any]
    ) -> dict[str, str]:
        """Convert a transaction to CSV row format."""

        # Format date for Firefly-III (YYYY-MM-DD)
        date_str = transaction.date.strftime("%Y-%m-%d")

        # Format amount (positive for income, negative for expense)
        amount = transaction.amount
        if transaction.transaction_type.lower() in ["debit", "withdrawal", "payment"]:
            amount = -abs(amount)
        elif transaction.transaction_type.lower() in ["credit", "deposit", "receipt"]:
            amount = abs(amount)

        amount_str = f"{amount:.2f}"

        # Get account details from config
        account_config = config.get("account_config", {})
        account_name = account_config.get("name", config.get("account_name", ""))
        account_iban = account_config.get(
            "iban",
            account_config.get("account_number", config.get("account_number", "")),
        )
        account_number = transaction.account_number or account_config.get(
            "account_number", ""
        )

        # Extract opposing account information from description
        opposing_name, opposing_number = self._extract_opposing_account(
            transaction.description
        )

        # Use pre-translated description if available, otherwise use original
        if transaction.translated_description:
            description = f"{transaction.translated_description} ({transaction.description.strip()})"
        else:
            description = transaction.description.strip()

        if len(description) > 100:
            description = description[:97] + "..."

        # Extract additional account details from config
        bank_name = account_config.get("bank_name", config.get("bank_name", ""))
        branch_name = account_config.get("branch_name", config.get("branch_name", ""))
        country_code = account_config.get(
            "country_code", config.get("country_code", "")
        )

        # Format balance information
        balance_str = f"{transaction.balance:.2f}" if transaction.balance else ""
        balance_old_str = (
            f"{transaction.old_balance:.2f}" if transaction.old_balance else ""
        )
        balance_new_str = (
            f"{transaction.new_balance:.2f}" if transaction.new_balance else ""
        )
        balance_change_str = (
            f"{transaction.balance_change:.2f}" if transaction.balance_change else ""
        )

        # Format date fields
        date_transaction_str = (
            transaction.transaction_date.strftime("%Y-%m-%d")
            if transaction.transaction_date
            else ""
        )
        date_value_str = (
            transaction.value_date.strftime("%Y-%m-%d")
            if transaction.value_date
            else ""
        )
        date_posting_str = (
            transaction.posting_date.strftime("%Y-%m-%d")
            if transaction.posting_date
            else ""
        )
        date_booking_str = (
            transaction.effective_date.strftime("%Y-%m-%d")
            if transaction.effective_date
            else ""
        )

        # Format amount fields
        amount_foreign_str = (
            f"{transaction.foreign_amount:.2f}" if transaction.foreign_amount else ""
        )
        exchange_rate_str = (
            f"{transaction.exchange_rate:.6f}" if transaction.exchange_rate else ""
        )
        fees_str = f"{transaction.fees:.2f}" if transaction.fees else ""
        interest_str = f"{transaction.interest:.2f}" if transaction.interest else ""
        tax_str = f"{transaction.tax:.2f}" if transaction.tax else ""

        # Create comprehensive notes with all available metadata
        notes_parts: list[str] = []
        if transaction.balance:
            notes_parts.append(f"Balance: {transaction.balance:.2f}")
        if transaction.transaction_type:
            notes_parts.append(f"Type: {transaction.transaction_type}")
        if transaction.channel:
            notes_parts.append(f"Channel: {transaction.channel}")
        if transaction.reference:
            notes_parts.append(f"Ref: {transaction.reference}")
        if transaction.check_number:
            notes_parts.append(f"Check: {transaction.check_number}")
        if transaction.memo:
            notes_parts.append(f"Memo: {transaction.memo}")
        if transaction.category:
            notes_parts.append(f"Category: {transaction.category}")
        if transaction.subcategory:
            notes_parts.append(f"Subcategory: {transaction.subcategory}")
        if transaction.raw_text:
            notes_parts.append(f"Raw: {transaction.raw_text[:200]}...")

        notes = " | ".join(notes_parts) if notes_parts else ""

        # Create enhanced tags
        tags_parts: list[str] = ["imported", transaction.parser_name or "unknown"]
        if transaction.transaction_type:
            tags_parts.append(transaction.transaction_type.lower())
        if transaction.channel:
            tags_parts.append(transaction.channel.lower())
        if transaction.category:
            tags_parts.append(transaction.category.lower())
        tags = ",".join(tags_parts)

        # Extract Amex-specific fields from raw_json if available
        amex_fields: dict[str, str] = {}
        if transaction.raw_json and isinstance(transaction.raw_json, dict):
            import typing

            raw_json_dict = typing.cast(dict[str, Any], transaction.raw_json)
            amex_fields = {
                "card_member": str(raw_json_dict.get("card_member", "")),
                "appears_on_statement": str(
                    raw_json_dict.get("appears_on_statement", "")
                ),
                "address": str(raw_json_dict.get("address", "")),
                "city_state": str(raw_json_dict.get("city_state", "")),
                "zip_code": str(raw_json_dict.get("zip_code", "")),
                "extended_details": str(raw_json_dict.get("extended_details", "")),
            }
        else:
            amex_fields = {
                "card_member": "",
                "appears_on_statement": "",
                "address": "",
                "city_state": "",
                "zip_code": "",
                "extended_details": "",
            }

        # External ID logic
        external_id = ""
        if transaction.reference and self._looks_like_transaction_id(
            transaction.reference
        ):
            external_id = transaction.reference
        # Always use our unique_id as internal_reference
        internal_reference = transaction.unique_id or ""

        return {
            # Core transaction data
            "date": date_str,
            "description": description,
            "amount": amount_str,
            "currency": transaction.currency,
            # Account information
            "account_name": account_name,
            "account_iban": account_iban,
            "account_number": account_number,
            "account_bic": "",
            # Opposing account information
            "opposing_name": opposing_name,
            "opposing_iban": "",
            "opposing_number": opposing_number,
            "opposing_bic": "",
            # Classification fields
            "category_name": transaction.category or "",
            "budget_name": "",
            "bill_name": "",
            "subscription_name": "",
            # Transaction metadata
            "transaction_type": transaction.transaction_type or "",
            "channel": transaction.channel or "",
            "reference": transaction.reference or "",
            "check_number": transaction.check_number or "",
            "memo": transaction.memo or "",
            "subcategory": transaction.subcategory or "",
            # Amount details
            "amount_foreign": amount_foreign_str,
            "foreign_currency": transaction.foreign_currency or "",
            "exchange_rate": exchange_rate_str,
            "fees": fees_str,
            "interest": interest_str,
            "tax": tax_str,
            # Date metadata
            "date_transaction": date_transaction_str,
            "date_value": date_value_str,
            "date_posting": date_posting_str,
            "date_booking": date_booking_str,
            "date_process": "",
            "date_due": "",
            "date_invoice": "",
            "date_payment": "",
            "date_interest": "",
            # Balance information
            "balance": balance_str,
            "balance_old": balance_old_str,
            "balance_new": balance_new_str,
            "balance_change": balance_change_str,
            # Additional metadata
            "tags": tags,
            "notes": notes,
            "external_id": external_id,
            "internal_reference": internal_reference,
            # Bank-specific information
            "bank_name": bank_name,
            "branch_name": branch_name,
            "country_code": country_code,
            "parser_name": transaction.parser_name or "",
            "source_file": transaction.source_file or "",
            # Raw data preservation
            "raw_text": transaction.raw_text or "",
            "raw_json": str(transaction.raw_json) if transaction.raw_json else "",
            # Amex-specific fields
            "card_member": amex_fields["card_member"],
            "appears_on_statement": amex_fields["appears_on_statement"],
            "address": amex_fields["address"],
            "city_state": amex_fields["city_state"],
            "zip_code": amex_fields["zip_code"],
            "extended_details": amex_fields["extended_details"],
        }

    def _generate_import_config(
        self, config_path: Path, account_config: dict[str, Any], transaction_count: int
    ) -> None:
        """Generate Firefly-III import configuration file."""

        # Create optimized import configuration
        import_config = {
            "version": 3,
            "source": "bank-importer-th",
            "created_at": datetime.now().isoformat(),
            "date": "Y-m-d",
            "default_account": 0,  # User needs to set this in Firefly-III
            "delimiter": "comma",
            "headers": True,
            "rules": True,
            "skip_form": False,
            "add_import_tag": True,
            "specifics": ["AppendHash"],
            "roles": [
                # Core transaction data (0-3)
                "date_transaction",  # date
                "description",  # description
                "amount",  # amount (normalized by parser)
                "currency-code",  # currency
                # Account information (4-7)
                "account-name",  # account_name
                "account-iban",  # account_iban
                "account-number",  # account_number
                "account-bic",  # account_bic
                # Opposing account information (8-11)
                "opposing-name",  # opposing_name
                "opposing-iban",  # opposing_iban
                "opposing-number",  # opposing_number
                "opposing-bic",  # opposing_bic
                # Classification fields (12-15)
                "category-name",  # category_name
                "budget-name",  # budget_name
                "bill-name",  # bill_name
                "bill-name",  # subscription_name
                # Transaction metadata (16-21)
                "note",  # transaction_type
                "note",  # channel
                "internal_reference",  # reference
                "note",  # check_number
                "note",  # memo
                "note",  # subcategory
                # Amount details (22-27)
                "amount_foreign",  # amount_foreign
                "foreign-currency-code",  # foreign_currency
                "note",  # exchange_rate
                "note",  # fees
                "note",  # interest
                "note",  # tax
                # Date metadata (28-37)
                "date_transaction",  # date_transaction
                "date_transaction",  # date_value
                "date_transaction",  # date_posting
                "date_transaction",  # date_booking
                "note",  # date_process
                "note",  # date_due
                "note",  # date_invoice
                "note",  # date_payment
                "note",  # date_interest
                # Balance information (38-41)
                "note",  # balance
                "note",  # balance_old
                "note",  # balance_new
                "note",  # balance_change
                # Additional metadata (42-45)
                "tags-comma",  # tags
                "note",  # notes
                "external-id",  # external_id
                "internal_reference",  # internal_reference
                # Bank-specific information (46-50)
                "note",  # bank_name
                "note",  # branch_name
                "note",  # country_code
                "note",  # parser_name
                "note",  # source_file
                # Raw data preservation (51-52)
                "note",  # raw_text
                "note",  # raw_json
                # Amex-specific fields (53-58)
                "note",  # card_member
                "note",  # appears_on_statement
                "note",  # address
                "note",  # city_state
                "note",  # zip_code
                "note",  # extended_details
            ],
            "do_mapping": {
                # Core transaction data (0-3)
                "0": False,  # date_transaction
                "1": False,  # description
                "2": False,  # amount
                "3": True,  # currency-code
                # Account information (4-7)
                "4": True,  # account-name
                "5": True,  # account-iban
                "6": True,  # account-number
                "7": False,  # account-bic
                # Opposing account information (8-11)
                "8": True,  # opposing-name
                "9": True,  # opposing-iban
                "10": True,  # opposing-number
                "11": False,  # opposing-bic
                # Classification fields (12-15)
                "12": True,  # category-name
                "13": True,  # budget-name
                "14": True,  # bill-name
                "15": True,  # subscription_name
                # Transaction metadata (16-21) - all stored in notes
                "16": False,  # transaction_type
                "17": False,  # channel
                "18": True,  # reference
                "19": False,  # check_number
                "20": False,  # memo
                "21": False,  # subcategory
                # Amount details (22-27)
                "22": True,  # amount_foreign
                "23": True,  # foreign-currency-code
                "24": False,  # exchange_rate
                "25": False,  # fees
                "26": False,  # interest
                "27": False,  # tax
                # Date metadata (28-37) - most stored in notes
                "28": False,  # date_transaction
                "29": False,  # date_value
                "30": False,  # date_posting
                "31": False,  # date_booking
                "32": False,  # date_process
                "33": False,  # date_due
                "34": False,  # date_invoice
                "35": False,  # date_payment
                "36": False,  # date_interest
                # Balance information (38-41) - all stored in notes
                "38": False,  # balance
                "39": False,  # balance_old
                "40": False,  # balance_new
                "41": False,  # balance_change
                # Additional metadata (42-45)
                "42": False,  # tags-space
                "43": False,  # notes
                "44": False,  # external-id
                "45": True,  # internal_reference
                # Bank-specific information (46-50) - all stored in notes
                "46": False,  # bank_name
                "47": False,  # branch_name
                "48": False,  # country_code
                "49": False,  # parser_name
                "50": False,  # source_file
                # Raw data preservation (51-52) - all stored in notes
                "51": False,  # raw_text
                "52": False,  # raw_json
                # Amex-specific fields (53-58) - all stored in notes
                "53": False,  # card_member
                "54": False,  # appears_on_statement
                "55": False,  # address
                "56": False,  # city_state
                "57": False,  # zip_code
                "58": False,  # extended_details
            },
            "mapping": {
                "3": {  # currency-code
                    "THB": "THB"
                },
                "4": {  # account-name
                    account_config.get("account_name", ""): account_config.get(
                        "account_name", ""
                    )
                },
                "5": {  # account-iban
                    account_config.get("account_number", ""): account_config.get(
                        "account_number", ""
                    )
                },
                "6": {  # account-number
                    account_config.get("account_number", ""): account_config.get(
                        "account_number", ""
                    )
                },
                "8": {  # opposing-name
                    "": ""
                },
                "9": {  # opposing-iban
                    "": ""
                },
                "10": {  # opposing-number
                    "": ""
                },
                "12": {  # category-name
                    "": ""
                },
                "13": {  # budget-name
                    "": ""
                },
                "14": {  # bill-name
                    "": ""
                },
                "15": {  # subscription_name
                    "": ""
                },
                "18": {  # reference
                    "": ""
                },
                "22": {  # amount_foreign
                    "": ""
                },
                "23": {  # foreign-currency-code
                    "": ""
                },
                "45": {  # internal_reference
                    "": ""
                },
            },
            "duplicate_detection_method": "classic",
            "ignore_duplicate_lines": True,
            "ignore_duplicate_transactions": True,
            "unique_column_index": 44,  # external_id column (new position)
            "unique_column_type": "external-id",
            "flow": "csv",
            "identifier": "0",
            "connection": "0",
            "ignore_spectre_categories": False,
            "map_all_data": False,
            "accounts": [],
            "date_range": "all",
            "date_range_number": 30,
            "date_range_unit": "d",
            "date_not_before": "",
            "date_not_after": "",
            "nordigen_country": "",
            "nordigen_bank": "",
            "nordigen_requisitions": [],
            "conversion": True,
        }

        # Write configuration file
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(import_config, f, indent=2, ensure_ascii=False)

    def _generate_external_id(self, transaction: Transaction) -> str:
        """
        Generate a unique external ID for the transaction.

        Strategy:
        1. Use bank-provided reference if it looks like a unique ID
        2. Use channel + date + amount hash if channel is available
        3. Fall back to account + date + database ID (current method)
        """
        import hashlib

        # Strategy 1: Check if reference looks like a unique transaction ID
        if transaction.reference and self._looks_like_transaction_id(
            transaction.reference
        ):
            return f"{transaction.account_number}_{transaction.reference}"

        # Strategy 2: Use channel + date + amount hash (for banks with channel codes)
        if transaction.channel and transaction.channel.strip():
            # Create a hash of date + amount + description for uniqueness
            hash_input = f"{transaction.date.strftime('%Y%m%d')}_{transaction.amount}_{transaction.description[:50]}"
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            return f"{transaction.account_number}_{transaction.channel}_{transaction.date.strftime('%Y%m%d')}_{hash_value}"

        # Strategy 3: Fall back to current method (account + date + database ID)
        return f"{transaction.account_number}_{transaction.date.strftime('%Y%m%d')}_{transaction.id}"

    def _extract_opposing_account(self, description: str) -> tuple[str, str]:
        """
        Extract opposing account name and number from transaction description.

        Patterns to recognize:
        - "Transfer to BBL x9551 MR VASAN NARDVIRIY"
        - "Transfer to TTB x1863 PREEYANUT PAN"
        - "Transfer to KBANK x1234 JOHN DOE"
        - "Bill Payment HARNG CENTRAL DEPARTMENT STORE L"
        - "จ่ายบิล HARNG CENTRAL DEPARTMENT STORE L"
        """
        import re

        if not description:
            return "", ""

        # Pattern for bank transfers with account numbers
        # Matches: "Transfer to [BANK] x[ACCOUNT_NUMBER] [NAME]"
        transfer_pattern = r"Transfer to (\w+)\s+x(\d+)\s+(.+)"
        match = re.search(transfer_pattern, description, re.IGNORECASE)

        if match:
            bank_name = match.group(1)
            account_number = match.group(2)
            person_name = match.group(3).strip()

            # Combine bank and person name for opposing_name
            opposing_name = f"{bank_name} {person_name}"
            return opposing_name, account_number

        # Pattern for other bank transfers
        # Matches: "Transfer to [BANK] [ACCOUNT_NUMBER] [NAME]"
        other_pattern = r"Transfer to (\w+)\s+(\d+)\s+(.+)"
        match = re.search(other_pattern, description, re.IGNORECASE)

        if match:
            bank_name = match.group(1)
            account_number = match.group(2)
            person_name = match.group(3).strip()

            opposing_name = f"{bank_name} {person_name}"
            return opposing_name, account_number

        # Pattern for bill payments and other financial transactions
        # Remove common financial terms and extract merchant/store name
        financial_terms = [
            r"Bill Payment\s+",
            r"จ่ายบิล\s+",
            r"Payment\s+",
            r"Payment to\s+",
            r"โอนเงิน\s+",
            r"Transfer\s+",
            r"Withdrawal\s+",
            r"ถอนเงิน\s+",
            r"Deposit\s+",
            r"ฝากเงิน\s+",
            r"Credit\s+",
            r"Debit\s+",
            r"ATM\s+",
            r"POS\s+",
            r"CDM\s+",
            r"IB\s+",  # Internet Banking
            r"Mobile Banking\s+",
            r"Online Banking\s+",
            r"QR\s+",
            r"QR Payment\s+",
            r"QR Code\s+",
            r"Cash Withdrawal\s+",
            r"Cash Deposit\s+",
            r"Fund Transfer\s+",
            r"Interbank Transfer\s+",
            r"Domestic Transfer\s+",
            r"International Transfer\s+",
        ]

        cleaned_description = description.strip()
        for term in financial_terms:
            cleaned_description = re.sub(
                term, "", cleaned_description, flags=re.IGNORECASE
            )

            # Special pattern for K+ shop transactions
        # Matches: "K+ shop (MERCHANT_NAME)" or "K+ shop (MERCHANT_NAME)"
        k_shop_pattern = r"K\+\s*shop\s*\(([^)]+)\)"
        k_shop_match = re.search(k_shop_pattern, cleaned_description, re.IGNORECASE)
        if k_shop_match:
            merchant_name = k_shop_match.group(1).strip()
            return merchant_name, ""

        # Pattern for bank transfers with person names
        # Matches: "BAY MR.SOURAV DAS" -> extracts "MR.SOURAV DAS"
        bank_person_pattern = r"(\w+)\s+(MR\.|MRS\.|MS\.|DR\.|PROF\.|SIR\.|MADAM\.|MR\s|MRS\s|MS\s|DR\s|PROF\s|SIR\s|MADAM\s)(.+)"
        bank_person_match = re.search(
            bank_person_pattern, cleaned_description, re.IGNORECASE
        )
        if bank_person_match:
            title = bank_person_match.group(2).strip()
            person_name = bank_person_match.group(3).strip()

            # Clean up person name by removing common suffixes
            person_name = re.sub(
                r"\s+From\s+Acc.*$", "", person_name, flags=re.IGNORECASE
            )
            person_name = re.sub(
                r"\s+To\s+Acc.*$", "", person_name, flags=re.IGNORECASE
            )
            person_name = re.sub(r"\s+Account.*$", "", person_name, flags=re.IGNORECASE)
            person_name = re.sub(r"\s+Acc.*$", "", person_name, flags=re.IGNORECASE)

            # Combine title and person name for opposing_name
            opposing_name = f"{title}{person_name}"
            return opposing_name, ""

        # If we have meaningful content left after removing financial terms
        if cleaned_description and len(cleaned_description.strip()) > 3:
            merchant_name = cleaned_description.strip()
            return merchant_name, ""

        return "", ""

    def _looks_like_transaction_id(self, reference: str) -> bool:
        """
        Check if a reference string looks like a unique transaction ID.

        Criteria:
        - Contains only alphanumeric characters and common separators
        - Has reasonable length (5-50 characters)
        - Doesn't look like a generic reference
        """
        if not reference or len(reference) < 5 or len(reference) > 50:
            return False

        # Check if it contains only alphanumeric and common separators
        import re

        if not re.match(r"^[A-Za-z0-9\-_\.\/]+$", reference):
            return False

        # Exclude common generic references
        generic_patterns = [
            "scb_main",
            "krungsri_main",
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
