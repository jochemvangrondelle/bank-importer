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

"""Tests for database router endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bank_importer.api import dependencies
from bank_importer.api.main import app
from bank_importer.api.security import require_auth
from bank_importer.config import ConfigManager
from bank_importer.models.database import DatabaseManager
from bank_importer.models.import_session import ImportSession
from bank_importer.models.transaction import Transaction


class TestDatabaseRouter:
    """Tests for database router endpoints."""

    @pytest.fixture
    def test_client(self, tmp_path: Path) -> TestClient:
        """Create a test client with test database."""
        # Create a test config and database
        config_path = tmp_path / "config.toml"
        db_path = tmp_path / "test.db"
        config_path.write_text(
            f"""
[database]
url = "duckdb:///{db_path}"
""",
        )
        config_manager = ConfigManager(config_path)
        db_manager = DatabaseManager(f"duckdb:///{db_path}")

        # Override dependencies to use test database and config
        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )
        app.dependency_overrides[dependencies.get_db_manager] = lambda: db_manager
        app.dependency_overrides[require_auth] = lambda: {}

        client = TestClient(app)
        yield client

        # Clean up overrides after test
        app.dependency_overrides.clear()

    def test_init_database(self, test_client: TestClient, tmp_path: Path) -> None:
        """Test database initialization."""
        response = test_client.post("/api/v1/database/init")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "database_url" in data
        assert data["message"] == "Database initialized successfully"
        assert "duckdb:///" in data["database_url"]

    def test_init_database_reset(self, test_client: TestClient, tmp_path: Path) -> None:
        """Test database initialization with reset."""
        # Create a database file first
        db_path = tmp_path / "test.db"
        DatabaseManager(f"duckdb:///{db_path}")
        # Database is initialized in __init__, just verify it exists
        assert db_path.exists() or str(db_path) == ":memory:"

        # Now reset it
        response = test_client.post("/api/v1/database/init?reset=true")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Database initialized successfully"

    def test_get_database_stats_empty(self, test_client: TestClient) -> None:
        """Test getting database statistics with empty database."""
        response = test_client.get("/api/v1/database/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_transactions" in data
        assert "total_import_sessions" in data
        assert "total_export_sessions" in data
        assert "database_size" in data
        assert "database_path" in data
        assert data["total_transactions"] == 0
        assert data["total_import_sessions"] == 0
        assert data["total_export_sessions"] == 0

    def test_get_database_stats_with_data(
        self,
        test_client: TestClient,
        tmp_path: Path,
    ) -> None:
        """Test getting database statistics with data."""
        # Add some test data
        db_path = tmp_path / "test.db"
        db_manager = DatabaseManager(f"duckdb:///{db_path}")

        # Add a transaction
        from datetime import UTC, datetime
        from decimal import Decimal

        transaction = Transaction(
            date=datetime(2024, 1, 1, tzinfo=UTC),
            description="Test transaction",
            amount=Decimal("100.00"),
            balance=Decimal("1000.00"),
            transaction_type="debit",
            account_number="123-456-789",
            currency="THB",
            country_code="TH",
            source_file="test.txt",
        )
        db_manager.add_transaction(transaction)

        # Add an import session
        import_session = ImportSession(
            file_path="test.txt",
            file_hash="abc123",
            account_name="test_account",
            bank_name="Test Bank",
            session_name="test_session",
            status="completed",
            started_at=datetime.now(UTC),
        )
        db_manager.create_import_session(import_session)

        response = test_client.get("/api/v1/database/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 1
        assert data["total_import_sessions"] == 1
        assert data["database_size"] > 0
        assert "test.db" in data["database_path"]

    def test_init_database_duckdb_colon_format(self, tmp_path: Path) -> None:
        """Test database initialization with duckdb: format."""
        config_path = tmp_path / "config.toml"
        db_path = tmp_path / "test.db"
        config_path.write_text(
            f"""
[database]
url = "duckdb:{db_path}"
""",
        )
        config_manager = ConfigManager(config_path)
        db_manager = DatabaseManager(f"duckdb:{db_path}")

        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )
        app.dependency_overrides[dependencies.get_db_manager] = lambda: db_manager
        app.dependency_overrides[require_auth] = lambda: {}

        client = TestClient(app)
        try:
            response = client.post("/api/v1/database/init?reset=true")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_database_stats_duckdb_colon_format(self, tmp_path: Path) -> None:
        """Test getting database stats with duckdb: format."""
        config_path = tmp_path / "config.toml"
        db_path = tmp_path / "test.db"
        config_path.write_text(
            f"""
[database]
url = "duckdb:{db_path}"
""",
        )
        config_manager = ConfigManager(config_path)
        db_manager = DatabaseManager(f"duckdb:{db_path}")

        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )
        app.dependency_overrides[dependencies.get_db_manager] = lambda: db_manager
        app.dependency_overrides[require_auth] = lambda: {}

        client = TestClient(app)
        try:
            response = client.get("/api/v1/database/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_transactions" in data
            assert "total_import_sessions" in data
            assert "total_export_sessions" in data
            assert "database_size" in data
            assert "database_path" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_database_stats_nonexistent_db(self, tmp_path: Path) -> None:
        """Test getting database stats when database doesn't exist."""
        config_path = tmp_path / "config.toml"
        db_path = tmp_path / "nonexistent.db"
        config_path.write_text(
            f"""
[database]
url = "duckdb:///{db_path}"
""",
        )
        config_manager = ConfigManager(config_path)
        # Don't create the database file
        db_manager = DatabaseManager(f"duckdb:///{db_path}")

        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )
        app.dependency_overrides[dependencies.get_db_manager] = lambda: db_manager
        app.dependency_overrides[require_auth] = lambda: {}

        client = TestClient(app)
        try:
            response = client.get("/api/v1/database/stats")
            assert response.status_code == 200
            data = response.json()
            # DuckDB creates a file even when empty, so size will be >= 0
            assert "database_size" in data
            assert isinstance(data["database_size"], int)
            assert data["database_size"] >= 0
            # Database path should be empty string if file doesn't exist
            assert "database_path" in data
        finally:
            app.dependency_overrides.clear()
