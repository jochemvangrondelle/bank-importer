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

"""Tests for status router endpoints."""

from datetime import UTC, datetime
from decimal import Decimal
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


class TestStatusRouter:
    """Tests for status router endpoints."""

    @pytest.fixture
    def test_client(self, tmp_path: Path) -> TestClient:
        """Create a test client with test database."""
        # Create a test config with accounts
        config_path = tmp_path / "config.toml"
        db_path = tmp_path / "test.db"
        config_path.write_text(
            f"""
[database]
url = "duckdb:///{db_path}"

[[accounts]]
name = "test_account"
parser = "krungsri_text"
account_number = "123-456-789"
account_name = "Test Account"
bank_name = "Test Bank"
currency = "THB"
country_code = "TH"
""",
        )
        config_manager = ConfigManager(config_path)
        db_manager = DatabaseManager(f"duckdb:///{db_path}")

        # Override dependencies
        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )
        app.dependency_overrides[dependencies.get_db_manager] = lambda: db_manager
        app.dependency_overrides[require_auth] = lambda: {}

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_get_status_empty(self, test_client: TestClient) -> None:
        """Test getting status with no data."""
        response = test_client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "summary" in data
        assert "import_sessions" in data
        assert len(data["accounts"]) == 1
        assert data["summary"]["total_accounts"] == 1
        assert data["summary"]["total_transactions"] == 0

    def test_get_status_with_data(self, test_client: TestClient) -> None:
        """Test getting status with data."""
        # Get db_manager from overrides
        db_manager = app.dependency_overrides[dependencies.get_db_manager]()

        # Add a transaction
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

        response = test_client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["total_transactions"] == 1
        assert data["summary"]["total_import_sessions"] == 1
        assert data["summary"]["completed_sessions"] == 1
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["account_name"] == "test_account"

    def test_get_account_status(self, test_client: TestClient) -> None:
        """Test getting account status."""
        response = test_client.get("/api/v1/status/accounts")
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "summary" in data
        assert len(data["accounts"]) == 1

    def test_get_account_status_by_name(self, test_client: TestClient) -> None:
        """Test getting account status by name."""
        response = test_client.get("/api/v1/status/accounts/test_account")
        assert response.status_code == 200
        data = response.json()
        assert data["account_name"] == "test_account"
        assert data["bank_name"] == "Test Bank"
        assert data["account_number"] == "123-456-789"
        assert data["transaction_count"] == 0

    def test_get_account_status_by_name_not_found(
        self,
        test_client: TestClient,
    ) -> None:
        """Test getting account status for non-existent account."""
        response = test_client.get("/api/v1/status/accounts/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
