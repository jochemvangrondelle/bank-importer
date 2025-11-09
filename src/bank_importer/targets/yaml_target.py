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

"""YAML target for exporting transactions in human-readable format."""

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from bank_importer.interfaces.target import Target, TargetResult
from bank_importer.models.config_models import ExportConfig
from bank_importer.models.transaction import Transaction
from bank_importer.translation_terms.opposing_account_patterns import (
    extract_opposing_account,
)


class YamlTarget(Target):
    """YAML target for exporting transactions in human-readable format."""

    def __init__(self, output_dir: str = "data/out") -> None:
        """Initialize YAML target.

        Args:
            output_dir: Directory to write YAML files to

        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_name(self) -> str:
        """Return the target name."""
        return "yaml"

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
        self,
        transactions: list[Transaction],
        config: ExportConfig | dict[str, Any],
    ) -> TargetResult:
        """Export transactions to YAML format.

        Args:
            transactions: List of transactions to export
            config: YAML export configuration

        Returns:
            Export result with metadata

        """
        if not transactions:
            return TargetResult(
                target_name=self.get_name(),
                success=True,
                exported_count=0,
                skipped_count=0,
                error_count=0,
                output_file=None,
                error_message=None,
                metadata={"message": "No transactions to export"},
            )

        # Convert config to dict if it's ExportConfig
        if isinstance(config, ExportConfig):
            config_dict = config.model_dump(mode="python")
        else:
            config_dict = config

        # Generate output filename
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        export_type = config_dict.get("export_type", "unknown")
        account_ref = config_dict.get("account_reference", "unknown")
        original_filename = config_dict.get("original_filename", "")
        bank_type = config_dict.get("bank_type", "")

        # Determine filename based on export type
        if export_type == "all_consolidated":
            filename = f"all-transactions_{timestamp}.yaml"
        elif export_type == "bank_consolidated":
            filename = f"{bank_type}-all_{timestamp}.yaml"
        elif export_type == "source_file":
            if original_filename:
                # Use original filename if available
                filename = f"{original_filename}_{timestamp}.yaml"
            else:
                # Clean up source file name for filename
                source_file = config.get("source_file", "unknown")
                clean_source = self._clean_filename(source_file)
                filename = f"{clean_source}_{timestamp}.yaml"
        else:
            filename = f"{account_ref}_{timestamp}.yaml"

        # Use custom output directory if specified
        output_dir = Path(config_dict.get("output_dir", self.output_dir))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename

        exported_count = 0
        error_count = 0

        try:
            # Convert transactions to YAML-serializable format
            yaml_data = self._transactions_to_yaml_data(transactions, config_dict)

            # Write YAML file with nice formatting
            with output_path.open("w", encoding="utf-8") as yamlfile:
                yaml.dump(
                    yaml_data,
                    yamlfile,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                    indent=2,
                    width=120,
                )
                # Count successfully exported transactions
                exported_count = len(transactions)

            # Generate summary file
            if export_type == "all_consolidated":
                summary_filename = f"summary_all-transactions_{timestamp}.yaml"
            elif export_type == "bank_consolidated":
                summary_filename = f"summary_{bank_type}-all_{timestamp}.yaml"
            elif export_type == "source_file":
                source_file = config.get("source_file", "unknown")
                clean_source = self._clean_filename(source_file)
                summary_filename = f"summary_{clean_source}_{timestamp}.yaml"
            else:
                summary_filename = f"summary_{account_ref}_{timestamp}.yaml"

            summary_path = output_dir / summary_filename
            self._generate_summary(summary_path, transactions, config_dict)

            return TargetResult(
                target_name=self.get_name(),
                success=True,
                exported_count=exported_count,
                skipped_count=0,
                error_count=error_count,
                output_file=str(output_path),
                error_message=None,
                metadata={
                    "filename": filename,
                    "summary_filename": summary_filename,
                    "account_reference": account_ref
                    if export_type not in {"all_consolidated", "bank_consolidated"}
                    else "all_accounts",
                    "total_transactions": len(transactions),
                    "date_range": self._get_date_range(transactions),
                    "amount_summary": self._get_amount_summary(transactions),
                },
            )

        except Exception as e:
            return TargetResult(
                target_name=self.get_name(),
                success=False,
                exported_count=0,
                skipped_count=0,
                error_count=len(transactions),
                output_file=None,
                error_message=str(e),
            )

    def _transactions_to_yaml_data(
        self,
        transactions: list[Transaction],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert transactions to YAML-serializable data structure."""
        # Get account details from config
        account_name = config.get("account_name", "")
        account_number = config.get("account_number", "")
        bank_name = config.get("bank_name", "")

        # Group transactions by month for better organization
        transactions_by_month: dict[str, list[dict[str, Any]]] = {}

        for transaction in transactions:
            # Get month key
            month_key = transaction.date.strftime("%Y-%m")

            if month_key not in transactions_by_month:
                transactions_by_month[month_key] = []

            # Convert transaction to dict
            transaction_dict = self._transaction_to_dict(transaction, config)
            transactions_by_month[month_key].append(transaction_dict)

        # Create the main YAML structure
        return {
            "export_info": {
                "exported_at": datetime.now(UTC).isoformat(),
                "account_name": account_name,
                "account_number": account_number,
                "bank_name": bank_name,
                "total_transactions": len(transactions),
                "date_range": self._get_date_range(transactions),
                "amount_summary": self._get_amount_summary(transactions),
            },
            "transactions": transactions_by_month,
        }

    def _transaction_to_dict(
        self,
        transaction: Transaction,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert a transaction to a dictionary for YAML export."""
        # Get account details from config
        account_config = config.get("account_config", {})
        account_name = account_config.get("name", config.get("account_name", ""))
        account_iban = account_config.get(
            "iban",
            account_config.get("account_number", config.get("account_number", "")),
        )
        account_number = transaction.account_number or account_config.get(
            "account_number",
            "",
        )

        # Format description: translated description with original in brackets if different
        if (
            transaction.translated_description
            and transaction.translated_description != transaction.description.strip()
        ):
            description = f"{transaction.translated_description} ({transaction.description.strip()})"
        else:
            description = transaction.description.strip()

        # Handle special cases for opposing account
        opposing_name, opposing_number = self._determine_opposing_account(
            transaction,
            description,
        )

        # Format amount (positive for income, negative for expense)
        amount = transaction.amount
        if transaction.transaction_type.lower() in ["debit", "withdrawal", "payment"]:
            amount = -abs(amount)
        elif transaction.transaction_type.lower() in ["credit", "deposit", "receipt"]:
            amount = abs(amount)

        # Create transaction dict with organized sections
        transaction_dict = {
            "id": transaction.id,
            "date": transaction.date.strftime("%Y-%m-%d"),
            "time": transaction.date.strftime("%H:%M:%S") if transaction.date else None,
            "description": {
                "translated": transaction.translated_description or "",
                "original": transaction.description.strip(),
                "formatted": description,
            },
            "amount": {
                "value": float(amount),
                "currency": transaction.currency,
                "formatted": f"{amount:.2f} {transaction.currency}",
            },
            "type": transaction.transaction_type,
            "category": transaction.category,
            "subcategory": transaction.subcategory,
            "channel": transaction.channel,
            "reference": transaction.reference,
            "balance": {
                "current": float(transaction.balance) if transaction.balance else None,
                "old": float(transaction.old_balance)
                if transaction.old_balance
                else None,
                "new": float(transaction.new_balance)
                if transaction.new_balance
                else None,
                "change": float(transaction.balance_change)
                if transaction.balance_change
                else None,
            },
            "dates": {
                "transaction": transaction.transaction_date.strftime("%Y-%m-%d")
                if transaction.transaction_date
                else None,
                "value": transaction.value_date.strftime("%Y-%m-%d")
                if transaction.value_date
                else None,
                "posting": transaction.posting_date.strftime("%Y-%m-%d")
                if transaction.posting_date
                else None,
                "booking": transaction.effective_date.strftime("%Y-%m-%d")
                if transaction.effective_date
                else None,
            },
            "foreign_currency": {
                "amount": float(transaction.foreign_amount)
                if transaction.foreign_amount
                else None,
                "currency": transaction.foreign_currency,
                "exchange_rate": float(transaction.exchange_rate)
                if transaction.exchange_rate
                else None,
            },
            "fees_and_taxes": {
                "fees": float(transaction.fees) if transaction.fees else None,
                "interest": float(transaction.interest)
                if transaction.interest
                else None,
                "tax": float(transaction.tax) if transaction.tax else None,
            },
            "account": {
                "name": account_name,
                "iban": account_iban,
                "number": account_number,
                "bank_name": account_config.get(
                    "bank_name",
                    config.get("bank_name", ""),
                ),
                "branch_name": account_config.get(
                    "branch_name",
                    config.get("branch_name", ""),
                ),
                "country_code": account_config.get(
                    "country_code",
                    config.get("country_code", ""),
                ),
            },
            "opposing_account": {
                "name": opposing_name,
                "number": opposing_number,
            },
            "metadata": {
                "memo": transaction.memo,
                "check_number": transaction.check_number,
                "tags": self._generate_tags(transaction),
                "parser": transaction.parser_name,
                "source_file": transaction.source_file,
                "external_id": "",  # Keep empty unless we have a unique ID from import
                "internal_reference": transaction.unique_id
                or transaction.reference
                or "",
            },
        }

        # Remove None values for cleaner output
        return self._remove_none_values(transaction_dict)

    def _generate_tags(self, transaction: Transaction) -> list[str]:
        """Generate tags for the transaction."""
        tags = ["imported", transaction.parser_name or "unknown"]
        if transaction.transaction_type:
            tags.append(transaction.transaction_type.lower())
        if transaction.channel:
            tags.append(transaction.channel.lower())
        if transaction.category:
            tags.append(transaction.category.lower())
        return tags

    def _determine_opposing_account(
        self,
        transaction: Transaction,
        description: str,
    ) -> tuple[str, str]:
        """Determine opposing account name and number based on transaction characteristics.

        Special cases:
        1. Krungsri transactions with "From Card No." and POS channel -> "UNKNOWN"
        2. ATM/Cash withdrawals -> "Cash - {CURRENCY}"
        3. Cash deposits (BRANCH category or round amounts) -> "Cash - {CURRENCY}"
        4. Otherwise use pattern extraction
        """
        # Case 1: Krungsri transactions with "From Card No." and POS channel
        if (
            transaction.parser_name == "krungsri_pdf"
            and (
                "From Card No." in transaction.description
                or "From Card No." in description
            )
            and transaction.channel
            and transaction.channel.upper() == "POS"
        ):
            return "UNKNOWN", ""

        # Case 2: ATM/Cash withdrawals
        if (transaction.channel and transaction.channel.upper() in ["ATM", "CDM"]) or (
            transaction.transaction_type
            and transaction.transaction_type.lower()
            in ["withdrawal", "cash withdrawal"]
        ):
            currency = transaction.currency or "THB"
            return f"Cash - {currency}", ""

        # Case 3: Cash deposits (BRANCH category or round amounts)
        if (
            transaction.category and transaction.category.upper() == "BRANCH"
        ) or self._is_likely_cash_deposit(transaction):
            currency = transaction.currency or "THB"
            return f"Cash - {currency}", ""

        # Case 4: Use pattern extraction
        return extract_opposing_account(description)

    def _is_likely_cash_deposit(self, transaction: Transaction) -> bool:
        """Check if transaction is likely a cash deposit based on amount patterns."""
        if not transaction.amount:
            return False

        amount = float(transaction.amount)

        # Check for round amounts (common in cash deposits)
        if amount > 0 and amount % 1000 == 0:  # Round to nearest 1000
            return True

        # Check for common cash deposit amounts
        common_amounts = [500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]
        return amount in common_amounts

    def _generate_external_id(self, transaction: Transaction) -> str:
        """Generate external ID for the transaction."""
        # Strategy 1: Check if reference looks like a unique transaction ID
        if transaction.reference and self._looks_like_transaction_id(
            transaction.reference,
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

    def _looks_like_transaction_id(self, reference: str) -> bool:
        """Check if a reference string looks like a unique transaction ID."""
        if not reference or len(reference) < 5 or len(reference) > 50:
            return False

        # Check if it contains only alphanumeric and common separators
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
        return all(pattern not in reference_lower for pattern in generic_patterns)

    def _remove_none_values(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively remove None values from dictionary."""
        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                cleaned_value = self._remove_none_values(value)
                if cleaned_value:  # Only add if not empty
                    result[key] = cleaned_value
            elif value is not None:
                # Special handling for description fields - preserve empty strings
                if (
                    key in ["translated", "original", "formatted"] and value == ""
                ) or value != "":
                    result[key] = value

        return result

    def _get_date_range(self, transactions: list[Transaction]) -> dict[str, str | None]:
        """Get the date range of transactions."""
        if not transactions:
            return {"start": None, "end": None}

        dates = [t.date for t in transactions]
        return {
            "start": min(dates).strftime("%Y-%m-%d"),
            "end": max(dates).strftime("%Y-%m-%d"),
        }

    def _get_amount_summary(self, transactions: list[Transaction]) -> dict[str, float]:
        """Get summary of transaction amounts."""
        if not transactions:
            return {"total_income": 0.0, "total_expenses": 0.0, "net": 0.0}

        total_income = 0.0
        total_expenses = 0.0

        for transaction in transactions:
            amount = float(transaction.amount)
            if amount > 0:
                total_income += amount
            else:
                total_expenses += abs(amount)

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net": total_income - total_expenses,
        }

    def _generate_summary(
        self,
        summary_path: Path,
        transactions: list[Transaction],
        config: dict[str, Any],
    ) -> None:
        """Generate a summary YAML file with statistics."""
        if not transactions:
            return

        # Group by transaction type
        by_type = {}
        by_channel = {}
        by_category = {}

        for transaction in transactions:
            # By type
            t_type = transaction.transaction_type or "unknown"
            if t_type not in by_type:
                by_type[t_type] = {"count": 0, "total_amount": 0.0}
            by_type[t_type]["count"] += 1
            by_type[t_type]["total_amount"] += float(transaction.amount)

            # By channel
            channel = transaction.channel or "unknown"
            if channel not in by_channel:
                by_channel[channel] = {"count": 0, "total_amount": 0.0}
            by_channel[channel]["count"] += 1
            by_channel[channel]["total_amount"] += float(transaction.amount)

            # By category
            category = transaction.category or "unknown"
            if category not in by_category:
                by_category[category] = {"count": 0, "total_amount": 0.0}
            by_category[category]["count"] += 1
            by_category[category]["total_amount"] += float(transaction.amount)

        summary_data = {
            "export_summary": {
                "exported_at": datetime.now(UTC).isoformat(),
                "account_name": config.get("account_name", ""),
                "account_number": config.get("account_number", ""),
                "total_transactions": len(transactions),
                "date_range": self._get_date_range(transactions),
                "amount_summary": self._get_amount_summary(transactions),
            },
            "statistics": {
                "by_transaction_type": by_type,
                "by_channel": by_channel,
                "by_category": by_category,
            },
            "top_transactions": {
                "highest_amount": self._get_top_transaction(transactions, "highest"),
                "lowest_amount": self._get_top_transaction(transactions, "lowest"),
                "recent_transactions": self._get_recent_transactions(transactions, 10),
            },
        }

        # Write summary file
        with summary_path.open("w", encoding="utf-8") as f:
            yaml.dump(
                summary_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
                width=120,
            )

    def _get_top_transaction(
        self,
        transactions: list[Transaction],
        which: str,
    ) -> dict[str, Any]:
        """Get the transaction with highest or lowest amount."""
        if not transactions:
            return {}

        if which == "highest":
            transaction = max(transactions, key=lambda t: float(t.amount))
        else:  # lowest
            transaction = min(transactions, key=lambda t: float(t.amount))

        return {
            "date": transaction.date.strftime("%Y-%m-%d"),
            "description": transaction.description,
            "amount": float(transaction.amount),
            "type": transaction.transaction_type,
            "channel": transaction.channel,
        }

    def _get_recent_transactions(
        self,
        transactions: list[Transaction],
        count: int,
    ) -> list[dict[str, Any]]:
        """Get the most recent transactions."""
        sorted_transactions = sorted(transactions, key=lambda t: t.date, reverse=True)
        recent = sorted_transactions[:count]

        return [
            {
                "date": t.date.strftime("%Y-%m-%d"),
                "description": t.description,
                "amount": float(t.amount),
                "type": t.transaction_type,
            }
            for t in recent
        ]
