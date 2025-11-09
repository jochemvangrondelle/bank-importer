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

"""Tests for system router."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from bank_importer.api import dependencies
from bank_importer.api.main import app
from bank_importer.config import ConfigManager
from bank_importer.models.database import DatabaseManager


class TestSystemRouter:
    """Tests for system router endpoints."""

    @pytest.fixture
    def test_client(self, tmp_path: Path) -> TestClient:
        """Create a test client with test database."""
        # Create a test config and database
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """
[database]
url = "duckdb:///:memory:"
""",
        )
        config_manager = ConfigManager(config_path)
        db_manager = DatabaseManager("duckdb:///:memory:")

        # Override dependencies to use test database and config
        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )
        app.dependency_overrides[dependencies.get_db_manager] = lambda: db_manager

        client = TestClient(app)
        yield client

        # Clean up overrides after test
        app.dependency_overrides.clear()

    def test_health_endpoint_healthy(self, test_client: TestClient) -> None:
        """Test health check endpoint when database is healthy."""
        response = test_client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_health_endpoint_database_unavailable(self, tmp_path: Path) -> None:
        """Test health check endpoint when database is unavailable."""
        # Create a test client with a mock database that raises an exception
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """
[database]
url = "duckdb:///:memory:"
""",
        )
        config_manager = ConfigManager(config_path)

        # Create a mock database manager that raises an exception
        mock_db = MagicMock(spec=DatabaseManager)
        # Mock the conn attribute and its execute method
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("Database connection failed")
        mock_db.conn = mock_conn

        # Override dependencies
        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )
        app.dependency_overrides[dependencies.get_db_manager] = lambda: mock_db

        client = TestClient(app)
        try:
            response = client.get("/api/v1/system/health")
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            assert "Database connectivity check failed" in data["detail"]
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    def test_version_endpoint(self, test_client: TestClient) -> None:
        """Test version endpoint."""
        response = test_client.get("/api/v1/system/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    @pytest.mark.parametrize(
        ("endpoint", "expected_keys"),
        [
            ("/api/v1/system/health", ["status", "timestamp", "version"]),
            ("/api/v1/system/version", ["version"]),
        ],
    )
    def test_system_endpoints(
        self,
        test_client: TestClient,
        endpoint: str,
        expected_keys: list[str],
    ) -> None:
        """Test system endpoints return expected keys."""
        response = test_client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        for key in expected_keys:
            assert key in data
