"""Firefly-III target for exporting transactions directly to Firefly-III API."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..interfaces.target import Target
from ..models.transaction import Transaction


class FireflyTarget(Target):
    """Firefly-III target for exporting transactions directly to Firefly-III API."""

    def __init__(self, output_dir: str = "data/out"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def get_name(self) -> str:
        return "firefly"

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
        Export transactions to Firefly-III compatible CSV format with enhanced tags.

        Args:
            transactions: List of transactions to export
            config: Firefly-III export configuration

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
            filename = f"firefly-all-transactions_{timestamp}.csv"
        elif export_type == "bank_consolidated":
            filename = f"firefly-{bank_type}-all_{timestamp}.csv"
        elif export_type == "source_file":
            if original_filename:
                # Use original filename if available
                filename = f"firefly-{original_filename}_{timestamp}.csv"
            else:
                # Clean up source file name for filename
                source_file = config.get("source_file", "unknown")
                clean_source = self._clean_filename(source_file)
                filename = f"firefly-{clean_source}_{timestamp}.csv"
        else:
            filename = f"firefly-{account_ref}_{timestamp}.csv"

        # Use custom output directory if specified
        output_dir = Path(config.get("output_dir", self.output_dir))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        # Firefly-III CSV format with enhanced tags
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
        """Convert a transaction to CSV row format with enhanced tags."""

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

        # Format amount details
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

        # Create enhanced tags with transaction type
        tags_parts: list[str] = ["imported", transaction.parser_name or "unknown"]

        # Add transaction type to tags (this is the key enhancement)
        if transaction.transaction_type:
            tags_parts.append(transaction.transaction_type.lower())

        # Add other tags based on configuration
        firefly_config = config.get("firefly_config", {})

        if firefly_config.get("include_channel_tag", True) and transaction.channel:
            tags_parts.append(transaction.channel.lower())

        if firefly_config.get("include_category_tag", True) and transaction.category:
            tags_parts.append(transaction.category.lower())

        # Add default tags
        default_tags = firefly_config.get(
            "default_tags", ["imported", "bank-importer-th"]
        )
        tags_parts.extend(default_tags)

        # Remove duplicates and join
        unique_tags = list(dict.fromkeys(tags_parts))
        tags = ",".join(unique_tags)

        # Generate external ID for duplicate detection
        external_id = self._generate_external_id(transaction, config)

        # Extract Amex-specific fields from raw_json if available
        amex_fields: dict[str, str] = {}
        if transaction.raw_json and isinstance(transaction.raw_json, dict):
            amex_fields = {
                "card_member": transaction.raw_json.get("card_member", ""),
                "appears_on_statement": transaction.raw_json.get(
                    "appears_on_statement", ""
                ),
                "address": transaction.raw_json.get("address", ""),
                "city_state": transaction.raw_json.get("city_state", ""),
                "zip_code": transaction.raw_json.get("zip_code", ""),
                "extended_details": transaction.raw_json.get("extended_details", ""),
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

        # Get bank information
        bank_name = account_config.get("bank_name", "")
        branch_name = account_config.get("branch_name", "")
        country_code = account_config.get("country_code", "")

        # Generate internal reference
        internal_reference = transaction.unique_id or transaction.reference or ""

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

    def _extract_opposing_account(self, description: str) -> tuple[str, str]:
        """Extract opposing account information from description."""
        # Simple extraction - can be enhanced based on specific bank formats
        opposing_name = ""
        opposing_number = ""

        # Look for common patterns
        if " to " in description.lower():
            parts = description.split(" to ", 1)
            if len(parts) > 1:
                opposing_name = parts[1].strip()
        elif " from " in description.lower():
            parts = description.split(" from ", 1)
            if len(parts) > 1:
                opposing_name = parts[1].strip()

        return opposing_name, opposing_number

    def _generate_external_id(
        self, transaction: Transaction, config: dict[str, Any]
    ) -> str:
        """Generate external ID for duplicate detection."""
        firefly_config = config.get("firefly_config", {})
        external_id_format = firefly_config.get(
            "external_id_format", "{account_number}_{date}_{transaction_id}"
        )

        account_number = transaction.account_number or ""
        date_str = transaction.date.strftime("%Y%m%d")
        transaction_id = transaction.unique_id or str(transaction.id or "")

        return external_id_format.format(
            account_number=account_number, date=date_str, transaction_id=transaction_id
        )

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
                "tags-comma",  # tags (enhanced with transaction type)
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
            "do_mapping": [False] * 58,  # No automatic mapping
            "mapping": [],
            "duplicate_detection_method": "classic",
            "ignore_duplicate_lines": True,
            "ignore_duplicate_transactions": True,
            "unique_column_index": 42,  # external_id column
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
            "conversion": False,
        }

        # Write configuration file
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(import_config, f, indent=2, ensure_ascii=False)
