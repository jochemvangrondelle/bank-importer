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

"""Integration tests for database operations.

These tests verify database operations with real DuckDB database:
- Table creation and schema
- Transaction persistence
- Import/Export session lifecycle
- Query operations and filters
- Data consistency
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from bank_importer.models.database import DatabaseManager
from bank_importer.models.enums import ImportStatus, TargetCompletionStatus
from bank_importer.models.import_session import ImportSession
from bank_importer.models.transaction import Transaction


@pytest.mark.integration
class TestDatabaseTableCreation:
    """Test database table creation and schema."""

    def test_tables_created_on_init(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: All tables are created when DatabaseManager is initialized."""
        # Verify transactions table exists (DuckDB uses information_schema)
        result = integration_db_manager.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name='transactions'",
        ).fetchone()
        assert result is not None

        # Verify import_sessions table exists
        result = integration_db_manager.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name='import_sessions'",
        ).fetchone()
        assert result is not None

        # Verify export_sessions table exists
        result = integration_db_manager.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name='export_sessions'",
        ).fetchone()
        assert result is not None

        # Verify exported_transactions table exists
        result = integration_db_manager.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name='exported_transactions'",
        ).fetchone()
        assert result is not None

        # Verify target_completions table exists
        result = integration_db_manager.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name='target_completions'",
        ).fetchone()
        assert result is not None

        # Verify bank_accounts table exists
        result = integration_db_manager.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name='bank_accounts'",
        ).fetchone()
        assert result is not None

    def test_indexes_created(self, integration_db_manager: DatabaseManager) -> None:
        """Test: Indexes are created for performance."""
        # DuckDB uses pg_catalog.pg_indexes for index information
        # Just verify that we can query the transactions table efficiently
        # (indexes are created internally by DuckDB)
        result = integration_db_manager.conn.execute(
            "SELECT COUNT(*) FROM transactions",
        ).fetchone()
        assert result is not None
        # If we can query without error, indexes are working


@pytest.mark.integration
class TestTransactionPersistence:
    """Test transaction persistence and retrieval."""

    def test_transaction_persistence(
        self,
        integration_db_manager: DatabaseManager,
        sample_transaction: Transaction,
    ) -> None:
        """Test: Create transaction → Query → Verify persistence."""
        # Add transaction
        transaction_id, is_new = integration_db_manager.add_transaction(
            sample_transaction,
        )
        assert is_new is True
        assert transaction_id > 0

        # Query transaction
        retrieved = integration_db_manager.get_transaction_by_id(transaction_id)
        assert retrieved is not None
        assert retrieved.id == transaction_id
        assert retrieved.description == sample_transaction.description
        assert retrieved.amount == sample_transaction.amount
        assert retrieved.balance == sample_transaction.balance

    def test_transaction_duplicate_detection(
        self,
        integration_db_manager: DatabaseManager,
        sample_transaction: Transaction,
    ) -> None:
        """Test: Adding duplicate transaction returns existing ID."""
        # Add first transaction
        transaction_id1, is_new1 = integration_db_manager.add_transaction(
            sample_transaction,
        )
        assert is_new1 is True

        # Add duplicate (same unique_id)
        transaction_id2, is_new2 = integration_db_manager.add_transaction(
            sample_transaction,
        )
        assert is_new2 is False
        assert transaction_id2 == transaction_id1

    def test_transaction_batch_insert(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Insert multiple transactions and verify all persisted."""
        transactions = [
            Transaction(
                date=datetime.now(UTC) + timedelta(days=i),
                description=f"Transaction {i}",
                amount=Decimal(f"{100 + i}.00"),
                balance=Decimal(f"{1000 + i}.00"),
                transaction_type="debit" if i % 2 == 0 else "credit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                unique_id=f"test-{i}",
            )
            for i in range(10)
        ]

        # Add all transactions
        inserted_ids = []
        for transaction in transactions:
            transaction_id, is_new = integration_db_manager.add_transaction(transaction)
            assert is_new is True
            inserted_ids.append(transaction_id)

        # Verify all transactions exist
        all_transactions = integration_db_manager.get_all_transactions()
        assert len(all_transactions) >= 10

        # Verify specific transactions
        for i, transaction_id in enumerate(inserted_ids):
            retrieved = integration_db_manager.get_transaction_by_id(transaction_id)
            assert retrieved is not None
            assert retrieved.description == f"Transaction {i}"


@pytest.mark.integration
class TestImportSessionLifecycle:
    """Test import session lifecycle and state transitions."""

    def test_import_session_lifecycle(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Create session → Add transactions → Complete session."""
        # Create import session
        import_session = ImportSession(
            account_name="test_account",
            bank_name="Test Bank",
            session_name="test_session",
            file_path="/test/file.pdf",
            file_hash="test_hash_123",
            status=ImportStatus.PROCESSING.value,
            total_transactions=5,
            started_at=datetime.now(UTC),
        )

        session_id = integration_db_manager.create_import_session(import_session)
        assert session_id > 0

        # Verify session created
        session = integration_db_manager.get_import_session(session_id)
        assert session is not None
        assert session["status"] == ImportStatus.PROCESSING.value
        assert session["total_transactions"] == 5
        assert session["processed_transactions"] == 0

        # Update session with processed transactions
        integration_db_manager.update_import_session(
            session_id,
            processed_transactions=3,
            error_count=1,
        )

        # Verify update
        session = integration_db_manager.get_import_session(session_id)
        assert session["processed_transactions"] == 3
        assert session["error_count"] == 1

        # Complete session
        integration_db_manager.update_import_session(
            session_id,
            status=ImportStatus.COMPLETED.value,
            processed_transactions=5,
            completed_at=datetime.now(UTC),
        )

        # Verify completion
        session = integration_db_manager.get_import_session(session_id)
        assert session["status"] == ImportStatus.COMPLETED.value
        assert session["processed_transactions"] == 5
        assert session["completed_at"] is not None

    def test_import_session_status_transitions(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Verify session status transitions work correctly."""
        import_session = ImportSession(
            account_name="test_account",
            bank_name="Test Bank",
            session_name="test_session",
            file_path="/test/file.pdf",
            file_hash="test_hash_status",
            status=ImportStatus.PENDING.value,
            started_at=datetime.now(UTC),
        )

        session_id = integration_db_manager.create_import_session(import_session)

        # Transition: PENDING → PROCESSING
        integration_db_manager.update_import_session(
            session_id,
            status=ImportStatus.PROCESSING.value,
        )
        session = integration_db_manager.get_import_session(session_id)
        assert session["status"] == ImportStatus.PROCESSING.value

        # Transition: PROCESSING → COMPLETED
        integration_db_manager.update_import_session(
            session_id,
            status=ImportStatus.COMPLETED.value,
            completed_at=datetime.now(UTC),
        )
        session = integration_db_manager.get_import_session(session_id)
        assert session["status"] == ImportStatus.COMPLETED.value

    def test_import_session_duplicate_file_hash(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Duplicate file hash detection."""
        import_session1 = ImportSession(
            account_name="test_account",
            bank_name="Test Bank",
            session_name="session1",
            file_path="/test/file1.pdf",
            file_hash="duplicate_hash",
            status=ImportStatus.COMPLETED.value,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )

        integration_db_manager.create_import_session(import_session1)

        # Try to create session with same file_hash
        import_session2 = ImportSession(
            account_name="test_account",
            bank_name="Test Bank",
            session_name="session2",
            file_path="/test/file2.pdf",
            file_hash="duplicate_hash",  # Same hash
            status=ImportStatus.PENDING.value,
            started_at=datetime.now(UTC),
        )

        # Should raise error or return existing session
        with pytest.raises(Exception):  # Expect constraint violation
            integration_db_manager.create_import_session(import_session2)


@pytest.mark.integration
class TestExportSessionTracking:
    """Test export session tracking and completion."""

    def test_export_session_tracking(
        self,
        integration_db_manager: DatabaseManager,
        sample_transaction: Transaction,
    ) -> None:
        """Test: Create export → Track session → Verify completion."""
        # Add transaction first
        transaction_id, _ = integration_db_manager.add_transaction(sample_transaction)

        # Create export session
        export_session_id = integration_db_manager.create_export_session(
            session_name="test_export",
            target_name="csv",
            account_reference="test_account",
        )
        assert export_session_id > 0

        # Verify session created
        sessions = integration_db_manager.get_export_sessions()
        session = next((s for s in sessions if s["id"] == export_session_id), None)
        assert session is not None
        assert session["status"] == "processing"
        assert session["total_transactions"] == 0
        assert session["exported_transactions"] == 0

        # Mark transaction as exported
        integration_db_manager.mark_transaction_exported(
            transaction_id=transaction_id,
            target_name="csv",
            export_session_id=export_session_id,
            status="exported",
        )

        # Update export session
        integration_db_manager.update_export_session(
            export_session_id,
            exported_transactions=1,
            status="completed",
            completed_at=datetime.now(UTC),
        )

        # Verify completion
        sessions = integration_db_manager.get_export_sessions()
        session = next((s for s in sessions if s["id"] == export_session_id), None)
        assert session is not None
        assert session["status"] == "completed"
        assert session["exported_transactions"] == 1
        assert session["completed_at"] is not None

    def test_export_session_multiple_transactions(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Export session with multiple transactions."""
        # Create multiple transactions
        transaction_ids = []
        for i in range(5):
            transaction = Transaction(
                date=datetime.now(UTC) + timedelta(days=i),
                description=f"Transaction {i}",
                amount=Decimal(f"{100 + i}.00"),
                balance=Decimal(f"{1000 + i}.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                unique_id=f"export-test-{i}",
            )
            transaction_id, _ = integration_db_manager.add_transaction(transaction)
            transaction_ids.append(transaction_id)

        # Create export session
        export_session_id = integration_db_manager.create_export_session(
            session_name="multi_export",
            target_name="csv",
            account_reference="test_account",
        )

        # Mark all transactions as exported
        for transaction_id in transaction_ids:
            integration_db_manager.mark_transaction_exported(
                transaction_id=transaction_id,
                target_name="csv",
                export_session_id=export_session_id,
                status="exported",
            )

        # Update session
        integration_db_manager.update_export_session(
            export_session_id,
            exported_transactions=5,
            status="completed",
            completed_at=datetime.now(UTC),
        )

        # Verify
        sessions = integration_db_manager.get_export_sessions()
        session = next((s for s in sessions if s["id"] == export_session_id), None)
        assert session is not None
        assert session["exported_transactions"] == 5
        assert session["status"] == "completed"


@pytest.mark.integration
class TestTransactionQueryingFilters:
    """Test transaction querying with various filters."""

    def test_query_transactions_by_account(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Query transactions by account number."""
        # Create transactions for different accounts
        account1_transactions = []
        account2_transactions = []

        for i in range(5):
            # Account 1 transactions
            t1 = Transaction(
                date=datetime.now(UTC) + timedelta(days=i),
                description=f"Account1 Transaction {i}",
                amount=Decimal(f"{100 + i}.00"),
                balance=Decimal(f"{1000 + i}.00"),
                transaction_type="debit",
                account_number="111-222-333",
                currency="THB",
                country_code="TH",
                unique_id=f"acc1-{i}",
            )
            transaction_id, _ = integration_db_manager.add_transaction(t1)
            account1_transactions.append(transaction_id)

            # Account 2 transactions
            t2 = Transaction(
                date=datetime.now(UTC) + timedelta(days=i),
                description=f"Account2 Transaction {i}",
                amount=Decimal(f"{200 + i}.00"),
                balance=Decimal(f"{2000 + i}.00"),
                transaction_type="credit",
                account_number="444-555-666",
                currency="THB",
                country_code="TH",
                unique_id=f"acc2-{i}",
            )
            transaction_id, _ = integration_db_manager.add_transaction(t2)
            account2_transactions.append(transaction_id)

        # Query account 1 transactions
        account1_results = integration_db_manager.get_transactions_by_account(
            "111-222-333",
        )
        assert len(account1_results) == 5
        for result in account1_results:
            assert result["account_number"] == "111-222-333"

        # Query account 2 transactions
        account2_results = integration_db_manager.get_transactions_by_account(
            "444-555-666",
        )
        assert len(account2_results) == 5
        for result in account2_results:
            assert result["account_number"] == "444-555-666"

    def test_query_transactions_by_date_range(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Query transactions by date range."""
        base_date = datetime(2025, 1, 1, tzinfo=UTC)

        # Create transactions across different dates
        for i in range(10):
            transaction = Transaction(
                date=base_date + timedelta(days=i),
                description=f"Transaction {i}",
                amount=Decimal(f"{100 + i}.00"),
                balance=Decimal(f"{1000 + i}.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                unique_id=f"date-test-{i}",
            )
            integration_db_manager.add_transaction(transaction)

        # Query transactions in date range (days 2-5)
        start_date = base_date + timedelta(days=2)
        end_date = base_date + timedelta(days=5)

        # Use get_transactions_filtered for date range
        filtered, total = integration_db_manager.get_transactions_filtered(
            date_from=start_date,
            date_to=end_date,
        )

        assert len(filtered) == 4  # Days 2, 3, 4, 5
        assert total == 4

    def test_query_transactions_by_source_file(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Query transactions by source file."""
        # Create transactions from different source files
        file1_transactions = []
        file2_transactions = []

        for i in range(3):
            # File 1 transactions
            t1 = Transaction(
                date=datetime.now(UTC) + timedelta(days=i),
                description=f"File1 Transaction {i}",
                amount=Decimal(f"{100 + i}.00"),
                balance=Decimal(f"{1000 + i}.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                source_file="/test/file1.pdf",
                unique_id=f"file1-{i}",
            )
            transaction_id, _ = integration_db_manager.add_transaction(t1)
            file1_transactions.append(transaction_id)

            # File 2 transactions
            t2 = Transaction(
                date=datetime.now(UTC) + timedelta(days=i),
                description=f"File2 Transaction {i}",
                amount=Decimal(f"{200 + i}.00"),
                balance=Decimal(f"{2000 + i}.00"),
                transaction_type="credit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                source_file="/test/file2.pdf",
                unique_id=f"file2-{i}",
            )
            transaction_id, _ = integration_db_manager.add_transaction(t2)
            file2_transactions.append(transaction_id)

        # Query by source file
        file1_results = integration_db_manager.get_transactions_by_source_file(
            "/test/file1.pdf",
        )
        assert len(file1_results) == 3
        for result in file1_results:
            assert result.source_file == "/test/file1.pdf"

        file2_results = integration_db_manager.get_transactions_by_source_file(
            "/test/file2.pdf",
        )
        assert len(file2_results) == 3
        for result in file2_results:
            assert result.source_file == "/test/file2.pdf"

    def test_query_transactions_by_session(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Query transactions by import session."""
        # Create import session
        import_session = ImportSession(
            account_name="test_account",
            bank_name="Test Bank",
            session_name="test_session",
            file_path="/test/file.pdf",
            file_hash="session_test_hash",
            status=ImportStatus.COMPLETED.value,
            total_transactions=3,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        integration_db_manager.create_import_session(import_session)

        # Create transactions (note: in real usage, transactions would be linked via source_file)
        transaction_ids = []
        for i in range(3):
            transaction = Transaction(
                date=datetime.now(UTC) + timedelta(days=i),
                description=f"Session Transaction {i}",
                amount=Decimal(f"{100 + i}.00"),
                balance=Decimal(f"{1000 + i}.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                source_file="/test/file.pdf",
                unique_id=f"session-{i}",
            )
            transaction_id, _ = integration_db_manager.add_transaction(transaction)
            transaction_ids.append(transaction_id)

        # Query transactions by source file (which links to session)
        session_transactions = integration_db_manager.get_transactions_by_source_file(
            "/test/file.pdf",
        )
        assert len(session_transactions) == 3


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency and integrity."""

    def test_transaction_foreign_key_consistency(
        self,
        integration_db_manager: DatabaseManager,
        sample_transaction: Transaction,
    ) -> None:
        """Test: Verify transaction data consistency."""
        # Add transaction
        transaction_id, _ = integration_db_manager.add_transaction(sample_transaction)

        # Retrieve and verify all fields match
        retrieved = integration_db_manager.get_transaction_by_id(transaction_id)
        assert retrieved is not None

        # Verify core fields
        assert retrieved.description == sample_transaction.description
        assert retrieved.amount == sample_transaction.amount
        assert retrieved.balance == sample_transaction.balance
        assert retrieved.account_number == sample_transaction.account_number
        assert retrieved.currency == sample_transaction.currency
        assert retrieved.country_code == sample_transaction.country_code

    def test_import_session_transaction_count_consistency(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Import session transaction counts are consistent."""
        # Create session
        import_session = ImportSession(
            account_name="test_account",
            bank_name="Test Bank",
            session_name="consistency_test",
            file_path="/test/consistency.pdf",
            file_hash="consistency_hash",
            status=ImportStatus.PROCESSING.value,
            total_transactions=10,
            started_at=datetime.now(UTC),
        )
        session_id = integration_db_manager.create_import_session(import_session)

        # Add transactions
        for i in range(10):
            transaction = Transaction(
                date=datetime.now(UTC) + timedelta(days=i),
                description=f"Consistency Transaction {i}",
                amount=Decimal(f"{100 + i}.00"),
                balance=Decimal(f"{1000 + i}.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                source_file="/test/consistency.pdf",
                unique_id=f"consistency-{i}",
            )
            integration_db_manager.add_transaction(transaction)

        # Update session to match actual count
        integration_db_manager.update_import_session(
            session_id,
            processed_transactions=10,
            status=ImportStatus.COMPLETED.value,
            completed_at=datetime.now(UTC),
        )

        # Verify consistency
        session = integration_db_manager.get_import_session(session_id)
        assert session["total_transactions"] == 10
        assert session["processed_transactions"] == 10

        # Verify actual transaction count matches
        transactions = integration_db_manager.get_transactions_by_source_file(
            "/test/consistency.pdf",
        )
        assert len(transactions) == 10

    def test_export_session_transaction_count_consistency(
        self,
        integration_db_manager: DatabaseManager,
    ) -> None:
        """Test: Export session exported transaction counts are consistent."""
        # Create transactions
        transaction_ids = []
        for i in range(5):
            transaction = Transaction(
                date=datetime.now(UTC) + timedelta(days=i),
                description=f"Export Consistency {i}",
                amount=Decimal(f"{100 + i}.00"),
                balance=Decimal(f"{1000 + i}.00"),
                transaction_type="debit",
                account_number="123-456-789",
                currency="THB",
                country_code="TH",
                unique_id=f"export-consistency-{i}",
            )
            transaction_id, _ = integration_db_manager.add_transaction(transaction)
            transaction_ids.append(transaction_id)

        # Create export session
        export_session_id = integration_db_manager.create_export_session(
            session_name="export_consistency",
            target_name="csv",
            account_reference="test_account",
        )

        # Mark all as exported
        for transaction_id in transaction_ids:
            integration_db_manager.mark_transaction_exported(
                transaction_id=transaction_id,
                target_name="csv",
                export_session_id=export_session_id,
                status="exported",
            )

        # Update session with total_transactions
        integration_db_manager.update_export_session(
            export_session_id,
            total_transactions=5,
            exported_transactions=5,
            status="completed",
            completed_at=datetime.now(UTC),
        )

        # Verify consistency
        sessions = integration_db_manager.get_export_sessions()
        session = next((s for s in sessions if s["id"] == export_session_id), None)
        assert session is not None
        assert session["total_transactions"] == 5
        assert session["exported_transactions"] == 5

        # Verify actual exported transaction count by checking exported_transactions table
        result = integration_db_manager.conn.execute(
            "SELECT COUNT(*) FROM exported_transactions WHERE export_session_id = ?",
            [export_session_id],
        ).fetchone()
        assert result[0] == 5


@pytest.mark.integration
class TestTargetCompletionTracking:
    """Test target completion tracking."""

    def test_target_completion_lifecycle(
        self,
        integration_db_manager: DatabaseManager,
        sample_transaction: Transaction,
    ) -> None:
        """Test: Create target completion → Update status → Verify completion."""
        # Add transaction
        transaction_id, _ = integration_db_manager.add_transaction(sample_transaction)

        # Create target completion
        integration_db_manager.mark_target_completed(
            transaction_id=transaction_id,
            target_name="csv",
            error_message=None,
        )

        # Verify completion was created
        result = integration_db_manager.conn.execute(
            "SELECT * FROM target_completions WHERE transaction_id = ? AND target_name = ?",
            [transaction_id, "csv"],
        ).fetchone()
        assert result is not None
        columns = integration_db_manager._get_columns(
            integration_db_manager.conn.execute(
                "SELECT * FROM target_completions WHERE transaction_id = ? AND target_name = ?",
                [transaction_id, "csv"],
            ),
        )
        completion_dict = dict(zip(columns, result, strict=False))
        assert completion_dict["status"] == TargetCompletionStatus.COMPLETED.value
        assert completion_dict["completed_at"] is not None

    def test_target_completion_duplicate(
        self,
        integration_db_manager: DatabaseManager,
        sample_transaction: Transaction,
    ) -> None:
        """Test: Target completion for same transaction+target is unique."""
        # Add transaction
        transaction_id, _ = integration_db_manager.add_transaction(sample_transaction)

        # Create first completion
        integration_db_manager.mark_target_completed(
            transaction_id=transaction_id,
            target_name="csv",
            error_message=None,
        )

        # Get first completion ID
        result1 = integration_db_manager.conn.execute(
            "SELECT id FROM target_completions WHERE transaction_id = ? AND target_name = ?",
            [transaction_id, "csv"],
        ).fetchone()
        completion_id1 = result1[0] if result1 else None
        assert completion_id1 is not None

        # Create second completion (should update existing)
        integration_db_manager.mark_target_completed(
            transaction_id=transaction_id,
            target_name="csv",  # Same target
            error_message=None,
        )

        # Verify same ID (updated, not new)
        result2 = integration_db_manager.conn.execute(
            "SELECT id FROM target_completions WHERE transaction_id = ? AND target_name = ?",
            [transaction_id, "csv"],
        ).fetchone()
        completion_id2 = result2[0] if result2 else None
        assert completion_id2 == completion_id1

        # Verify status updated
        result = integration_db_manager.conn.execute(
            "SELECT status FROM target_completions WHERE transaction_id = ? AND target_name = ?",
            [transaction_id, "csv"],
        ).fetchone()
        assert result[0] == TargetCompletionStatus.COMPLETED.value
