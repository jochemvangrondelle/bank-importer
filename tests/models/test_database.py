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

"""Tests for database manager."""

from pathlib import Path

import pytest

from bank_importer.models.database import DatabaseManager


class TestDatabaseManager:
    """Test database manager functionality."""

    def test_init(self, tmp_path, db_manager: DatabaseManager) -> None:
        """Test database manager initialization."""
        assert db_manager.database_url.startswith("sqlite:///")
        assert db_manager.engine is not None

    def test_add_transaction_new(
        self,
        db_manager: DatabaseManager,
        sample_transaction,
    ) -> None:
        """Test adding a new transaction."""
        transaction_id, is_new = db_manager.add_transaction(sample_transaction)
        assert is_new is True
        assert transaction_id > 0

    def test_add_transaction_duplicate(
        self,
        db_manager: DatabaseManager,
        transaction_factory,
    ) -> None:
        """Test adding a duplicate transaction."""
        transaction = transaction_factory(unique_id="test123")
        # Add first transaction
        transaction_id1, is_new1 = db_manager.add_transaction(transaction)
        assert is_new1 is True

        # Try to add duplicate
        transaction2 = transaction_factory(
            date=transaction.date,
            description=transaction.description,
            amount=transaction.amount,
            balance=transaction.balance,
            transaction_type=transaction.transaction_type,
            account_number=transaction.account_number,
            currency=transaction.currency,
            country_code=transaction.country_code,
            source_file=transaction.source_file,
            unique_id=transaction.unique_id,
        )
        transaction_id2, is_new2 = db_manager.add_transaction(transaction2)
        assert is_new2 is False
        assert transaction_id2 == transaction_id1

    def test_generate_unique_id(
        self,
        db_manager: DatabaseManager,
        transaction_factory,
    ) -> None:
        """Test unique ID generation."""
        transaction = transaction_factory(description="Test")
        unique_id = db_manager._generate_unique_id(transaction)
        assert unique_id is not None
        assert len(unique_id) == 8

    @pytest.mark.parametrize(
        ("account_number", "expected_count"),
        [("123-456-789", 1), ("nonexistent", 0)],
    )
    def test_get_transactions_by_account(
        self,
        db_manager: DatabaseManager,
        transaction_factory,
        account_number: str,
        expected_count: int,
    ) -> None:
        """Test getting transactions by account."""
        if expected_count > 0:
            transaction = transaction_factory(account_number=account_number)
            db_manager.add_transaction(transaction)

        transactions = db_manager.get_transactions_by_account(account_number)
        assert len(transactions) == expected_count
        if expected_count > 0:
            assert transactions[0]["account_number"] == account_number

    def test_get_unprocessed_transactions(
        self,
        db_manager: DatabaseManager,
        sample_transaction,
    ) -> None:
        """Test getting unprocessed transactions."""
        db_manager.add_transaction(sample_transaction)

        unprocessed = db_manager.get_unprocessed_transactions("csv")
        assert len(unprocessed) == 1

    def test_mark_target_completed(
        self,
        db_manager: DatabaseManager,
        sample_transaction,
    ) -> None:
        """Test marking target as completed."""
        transaction_id, _ = db_manager.add_transaction(sample_transaction)

        db_manager.mark_target_completed(transaction_id, "csv")
        # Verify by checking unprocessed transactions
        unprocessed = db_manager.get_unprocessed_transactions("csv")
        assert len(unprocessed) == 0

    def test_mark_target_completed_with_error(
        self,
        db_manager: DatabaseManager,
        sample_transaction,
    ) -> None:
        """Test marking target as completed with error."""
        transaction_id, _ = db_manager.add_transaction(sample_transaction)

        db_manager.mark_target_completed(
            transaction_id,
            "csv",
            error_message="Test error",
        )
        # Transaction with error should still be unprocessed (error_message means it failed)
        unprocessed = db_manager.get_unprocessed_transactions("csv")
        assert len(unprocessed) == 1

    def test_create_import_session_new(
        self,
        db_manager: DatabaseManager,
        import_session_factory,
    ) -> None:
        """Test creating a new import session."""
        import_session = import_session_factory()
        session_id = db_manager.create_import_session(import_session)
        assert session_id > 0

    @pytest.mark.parametrize(
        ("initial_status", "second_status", "should_raise", "error_match"),
        [
            ("completed", "processing", True, "File already processed"),
            ("failed", "processing", False, None),  # Should update existing
            ("processing", "processing", True, "File already being processed"),
        ],
    )
    def test_create_import_session_duplicate(
        self,
        db_manager: DatabaseManager,
        import_session_factory,
        initial_status: str,
        second_status: str,
        should_raise: bool,
        error_match: str | None,
    ) -> None:
        """Test creating import session with duplicate file hash."""
        import_session1 = import_session_factory(
            file_path="test.txt",
            file_hash="abc123",
            status=initial_status,
        )
        db_manager.create_import_session(import_session1)

        import_session2 = import_session_factory(
            file_path="test2.txt",
            file_hash="abc123",
            status=second_status,
        )

        if should_raise:
            with pytest.raises(ValueError, match=error_match):
                db_manager.create_import_session(import_session2)
        else:
            # Should update existing session
            session_id2 = db_manager.create_import_session(import_session2)
            session = db_manager.get_import_session(session_id2)
            assert session is not None
            assert session["status"] == second_status

    def test_update_import_session(
        self,
        db_manager: DatabaseManager,
        import_session_factory,
    ) -> None:
        """Test updating import session."""
        import_session = import_session_factory()
        session_id = db_manager.create_import_session(import_session)

        db_manager.update_import_session(
            session_id,
            status="completed",
            total_transactions=10,
        )
        session = db_manager.get_import_session(session_id)
        assert session is not None
        assert session["status"] == "completed"
        assert session["total_transactions"] == 10

    @pytest.mark.parametrize(
        ("session_id", "expected_result"),
        [(1, True), (99999, False)],
    )
    def test_get_import_session(
        self,
        db_manager: DatabaseManager,
        import_session_factory,
        session_id: int,
        expected_result: bool,
    ) -> None:
        """Test getting import session by ID."""
        if expected_result:
            import_session = import_session_factory(file_path="test.txt")
            session_id = db_manager.create_import_session(import_session)

        session = db_manager.get_import_session(session_id)
        if expected_result:
            assert session is not None
            assert session["file_path"] == "test.txt"
        else:
            assert session is None

    def test_get_import_sessions_by_account(
        self,
        db_manager: DatabaseManager,
        import_session_factory,
    ) -> None:
        """Test getting import sessions by account."""
        import_session = import_session_factory(account_name="test_account")
        db_manager.create_import_session(import_session)

        sessions = db_manager.get_import_sessions_by_account("test_account")
        assert len(sessions) == 1
        assert sessions[0]["account_name"] == "test_account"

    @pytest.mark.parametrize(
        ("session_exists", "expected_count"),
        [(True, 1), (False, 0)],
    )
    def test_get_transactions_by_session(
        self,
        db_manager: DatabaseManager,
        import_session_factory,
        sample_transaction,
        session_exists: bool,
        expected_count: int,
    ) -> None:
        """Test getting transactions by session."""
        if session_exists:
            import_session = import_session_factory(
                file_path="test.txt",
                status="completed",
            )
            session_id = db_manager.create_import_session(import_session)
            db_manager.add_transaction(sample_transaction)
        else:
            session_id = 99999

        transactions = db_manager.get_transactions_by_session(session_id)
        assert len(transactions) == expected_count

    def test_get_import_session_by_file_hash(
        self,
        db_manager: DatabaseManager,
        import_session_factory,
    ) -> None:
        """Test getting import session by file hash."""
        import_session = import_session_factory(file_hash="abc123")
        db_manager.create_import_session(import_session)

        session = db_manager.get_import_session_by_file_hash("abc123")
        assert session is not None
        assert session["file_hash"] == "abc123"

    @pytest.mark.parametrize("status", ["pending", "processing", "completed", "failed"])
    def test_get_pending_import_sessions(
        self,
        db_manager: DatabaseManager,
        import_session_factory,
        status: str,
    ) -> None:
        """Test getting pending import sessions."""
        import_session = import_session_factory(status=status)
        db_manager.create_import_session(import_session)

        pending = db_manager.get_pending_import_sessions()
        expected_count = 1 if status == "pending" else 0
        assert len(pending) == expected_count
        if expected_count > 0:
            assert pending[0]["status"] == "pending"

    def test_create_export_session(self, db_manager: DatabaseManager) -> None:
        """Test creating export session."""
        session_id = db_manager.create_export_session(
            "test_export",
            "csv",
            "test_account",
        )
        assert session_id > 0

    def test_update_export_session(self, db_manager: DatabaseManager) -> None:
        """Test updating export session."""
        session_id = db_manager.create_export_session(
            "test_export",
            "csv",
            "test_account",
        )

        db_manager.update_export_session(
            session_id,
            status="completed",
            total_transactions=10,
            exported_transactions=8,
            skipped_transactions=2,
        )

        sessions = db_manager.get_export_sessions()
        assert len(sessions) == 1
        assert sessions[0]["status"] == "completed"
        assert sessions[0]["total_transactions"] == 10

    def test_mark_transaction_exported(
        self,
        db_manager: DatabaseManager,
        sample_transaction,
    ) -> None:
        """Test marking transaction as exported."""
        transaction_id, _ = db_manager.add_transaction(sample_transaction)

        export_session_id = db_manager.create_export_session(
            "test_export",
            "csv",
            "test_account",
        )

        exported_id = db_manager.mark_transaction_exported(
            transaction_id,
            "csv",
            export_session_id,
        )
        assert exported_id > 0

    def test_get_unexported_transactions(
        self,
        db_manager: DatabaseManager,
        sample_transaction,
    ) -> None:
        """Test getting unexported transactions."""
        db_manager.add_transaction(sample_transaction)

        unexported = db_manager.get_unexported_transactions("csv")
        assert len(unexported) == 1

    @pytest.mark.parametrize(
        ("account_number", "expected_count"),
        [("123-456-789", 1), ("different", 0)],
    )
    def test_get_unexported_transactions_with_account(
        self,
        db_manager: DatabaseManager,
        transaction_factory,
        account_number: str,
        expected_count: int,
    ) -> None:
        """Test getting unexported transactions filtered by account."""
        transaction = transaction_factory(account_number="123-456-789")
        db_manager.add_transaction(transaction)

        unexported = db_manager.get_unexported_transactions("csv", account_number)
        assert len(unexported) == expected_count

    def test_get_transactions_by_source_file(
        self,
        db_manager: DatabaseManager,
        sample_transaction,
    ) -> None:
        """Test getting transactions by source file."""
        db_manager.add_transaction(sample_transaction)

        transactions = db_manager.get_transactions_by_source_file("test.txt")
        assert len(transactions) == 1
        assert transactions[0].source_file == "test.txt"

    def test_get_all_transactions(
        self,
        db_manager: DatabaseManager,
        sample_transactions,
    ) -> None:
        """Test getting all transactions."""
        for transaction in sample_transactions:
            db_manager.add_transaction(transaction)

        all_transactions = db_manager.get_all_transactions()
        assert len(all_transactions) == len(sample_transactions)

    def test_get_unique_source_files(
        self,
        db_manager: DatabaseManager,
        transaction_factory,
    ) -> None:
        """Test getting unique source files."""
        transaction1 = transaction_factory(source_file="file1.txt")
        transaction2 = transaction_factory(source_file="file2.txt")
        db_manager.add_transaction(transaction1)
        db_manager.add_transaction(transaction2)

        source_files = db_manager.get_unique_source_files()
        assert len(source_files) == 2
        assert "file1.txt" in source_files
        assert "file2.txt" in source_files

    def test_get_export_sessions(self, db_manager: DatabaseManager) -> None:
        """Test getting export sessions."""
        db_manager.create_export_session("export1", "csv", "account1")
        db_manager.create_export_session("export2", "yaml", "account2")

        sessions = db_manager.get_export_sessions()
        assert len(sessions) == 2

    def test_get_export_sessions_filtered(self, db_manager: DatabaseManager) -> None:
        """Test getting export sessions filtered by target."""
        db_manager.create_export_session("export1", "csv", "account1")
        db_manager.create_export_session("export2", "yaml", "account2")

        csv_sessions = db_manager.get_export_sessions("csv")
        assert len(csv_sessions) == 1
        assert csv_sessions[0]["target_name"] == "csv"

    def test_clear_export_sessions(self, db_manager: DatabaseManager) -> None:
        """Test clearing export sessions."""
        db_manager.create_export_session("export1", "csv", "account1")
        db_manager.clear_export_sessions()

        sessions = db_manager.get_export_sessions()
        assert len(sessions) == 0

    @pytest.mark.parametrize(
        ("target_name", "expected"),
        [(None, True), ("csv", True), ("yaml", False)],
    )
    def test_has_source_file_been_exported(
        self,
        db_manager: DatabaseManager,
        sample_transaction,
        target_name: str | None,
        expected: bool,
    ) -> None:
        """Test checking if source file has been exported."""
        transaction_id, _ = db_manager.add_transaction(sample_transaction)

        assert (
            db_manager.has_source_file_been_exported("test.txt", target_name) is False
        )

        export_session_id = db_manager.create_export_session(
            "export1",
            "csv",
            "account1",
        )
        db_manager.mark_transaction_exported(transaction_id, "csv", export_session_id)

        assert (
            db_manager.has_source_file_been_exported("test.txt", target_name)
            is expected
        )

    @pytest.mark.parametrize(
        ("status", "expected"),
        [("completed", True), ("processing", False), ("failed", False)],
    )
    def test_has_source_file_been_imported(
        self,
        db_manager: DatabaseManager,
        import_session_factory,
        status: str,
        expected: bool,
    ) -> None:
        """Test checking if source file has been imported."""
        assert db_manager.has_source_file_been_imported("test.txt") is False

        import_session = import_session_factory(
            file_path="test.txt",
            file_hash="abc123",
            status=status,
        )
        db_manager.create_import_session(import_session)

        assert db_manager.has_source_file_been_imported("test.txt") is expected

    def test_close_connection(self, db_manager: DatabaseManager) -> None:
        """Test closing database connection."""
        # Connection should be open initially
        assert not db_manager._closed
        assert db_manager.conn is not None

        # Close the connection
        db_manager.close()

        # Connection should be closed
        assert db_manager._closed
        assert db_manager.conn is None

        # Closing again should be safe (idempotent)
        db_manager.close()
        assert db_manager._closed

    def test_context_manager(self, tmp_path: Path) -> None:
        """Test DatabaseManager as context manager."""
        db_path = tmp_path / "context_test.db"
        db_url = f"sqlite:///{db_path}"

        # Use as context manager
        with DatabaseManager(db_url) as db:
            assert not db._closed
            assert db.conn is not None
            # Perform an operation
            db._get_next_id("transactions")

        # Connection should be closed after exiting context
        assert db._closed
        assert db.conn is None

    def test_closed_connection_raises_error(self, db_manager: DatabaseManager) -> None:
        """Test that operations on closed connection raise errors."""
        # Close the connection
        db_manager.close()

        # Operations should raise RuntimeError
        with pytest.raises(RuntimeError, match="Database connection is closed"):
            db_manager._get_next_id("transactions")

        with pytest.raises(RuntimeError, match="Database connection is closed"):
            with db_manager._transaction():
                pass

    def test_connection_cleanup_on_gc(self, tmp_path: Path) -> None:
        """Test that connection is cleaned up on garbage collection."""
        db_path = tmp_path / "gc_test.db"
        db_url = f"sqlite:///{db_path}"

        # Create a DatabaseManager without using context manager
        db = DatabaseManager(db_url)
        assert not db._closed

        # Delete reference to trigger garbage collection
        del db

        # Connection should be closed (tested via __del__)

    def test_close_without_conn_attribute(self) -> None:
        """Test that close() handles case where conn attribute doesn't exist."""
        # Create a partially initialized object (simulating failed __init__)
        db = object.__new__(DatabaseManager)
        db._closed = False
        # Don't set db.conn - simulate partial initialization

        # close() should not raise AttributeError
        db.close()
        assert db._closed

    def test_del_without_conn_attribute(self) -> None:
        """Test that __del__ handles case where conn attribute doesn't exist."""
        # Create a partially initialized object (simulating failed __init__)
        db = object.__new__(DatabaseManager)
        db._closed = False
        # Don't set db.conn - simulate partial initialization

        # __del__ should not raise AttributeError
        db.__del__()
        assert db._closed

    def test_close_idempotent(self, db_manager: DatabaseManager) -> None:
        """Test that close() can be called multiple times safely."""
        # Close once
        db_manager.close()
        assert db_manager._closed

        # Close again - should be safe
        db_manager.close()
        assert db_manager._closed

    def test_init_creates_parent_directory(self, tmp_path: Path) -> None:
        """Test that __init__ creates parent directory if it doesn't exist."""
        db_dir = tmp_path / "new_dir"
        db_path = db_dir / "test.db"
        db_url = f"sqlite:///{db_path}"

        # Directory doesn't exist yet
        assert not db_dir.exists()

        # Creating DatabaseManager should create the directory
        db = DatabaseManager(db_url)
        assert db_dir.exists()
        assert (
            db_path.exists() or db_path.parent.exists()
        )  # DuckDB may create in parent

        db.close()

    def test_init_permission_error(self, tmp_path: Path) -> None:
        """Test that __init__ raises helpful error on permission issues."""
        # Create a read-only directory
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444)  # Read-only

        db_path = read_only_dir / "test.db"
        db_url = f"sqlite:///{db_path}"

        try:
            # The error will be caught when trying to create the file, not the directory
            with pytest.raises(
                RuntimeError,
                match="Cannot open database file.*Permission denied",
            ):
                DatabaseManager(db_url)
        finally:
            # Restore permissions for cleanup
            read_only_dir.chmod(0o755)

    def test_init_database_permission_error(self, tmp_path: Path) -> None:
        """Test that __init__ raises helpful error when database file is not writable."""
        # Create a read-only file
        read_only_file = tmp_path / "readonly.db"
        read_only_file.touch()
        read_only_file.chmod(0o444)  # Read-only

        db_url = f"sqlite:///{read_only_file}"

        try:
            with pytest.raises(
                RuntimeError,
                match="Cannot open database file.*Permission denied",
            ):
                DatabaseManager(db_url)
        finally:
            # Restore permissions for cleanup
            read_only_file.chmod(0o644)
