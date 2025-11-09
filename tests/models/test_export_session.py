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

"""Tests for export session models."""

from bank_importer.models.enums import ExportedTransactionStatus, ExportStatus
from bank_importer.models.export_session import ExportedTransaction, ExportSession


class TestExportSession:
    """Test ExportSession model."""

    def test_status_enum_valid_value(self) -> None:
        """Test status_enum property with valid enum value."""
        session = ExportSession(
            session_name="test",
            target_name="csv",
            account_reference="acc1",
            status="completed",
        )
        assert session.status_enum == ExportStatus.COMPLETED

    def test_status_enum_invalid_value_fallback(self) -> None:
        """Test status_enum property with invalid value falls back to PROCESSING."""
        session = ExportSession(
            session_name="test",
            target_name="csv",
            account_reference="acc1",
            status="invalid_status",
        )
        assert session.status_enum == ExportStatus.PROCESSING

    def test_status_enum_setter(self) -> None:
        """Test status_enum setter."""
        session = ExportSession(
            session_name="test",
            target_name="csv",
            account_reference="acc1",
        )
        session.status_enum = ExportStatus.COMPLETED
        assert session.status == "completed"


class TestExportedTransaction:
    """Test ExportedTransaction model."""

    def test_status_enum_valid_value(self) -> None:
        """Test status_enum property with valid enum value."""
        transaction = ExportedTransaction(
            transaction_id=1,
            target_name="csv",
            export_session_id=1,
            status="exported",
        )
        assert transaction.status_enum == ExportedTransactionStatus.EXPORTED

    def test_status_enum_invalid_value_fallback(self) -> None:
        """Test status_enum property with invalid value falls back to EXPORTED."""
        transaction = ExportedTransaction(
            transaction_id=1,
            target_name="csv",
            export_session_id=1,
            status="invalid_status",
        )
        assert transaction.status_enum == ExportedTransactionStatus.EXPORTED

    def test_status_enum_setter(self) -> None:
        """Test status_enum setter."""
        transaction = ExportedTransaction(
            transaction_id=1,
            target_name="csv",
            export_session_id=1,
        )
        transaction.status_enum = ExportedTransactionStatus.FAILED
        assert transaction.status == "failed"
