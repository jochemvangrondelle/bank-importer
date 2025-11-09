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

"""Tests for config router endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bank_importer.api import dependencies
from bank_importer.api.main import app
from bank_importer.api.security import require_auth
from bank_importer.config import ConfigManager


class TestConfigRouter:
    """Tests for config router endpoints."""

    @pytest.fixture
    def test_client(self, tmp_path: Path) -> TestClient:
        """Create a test client with test config."""
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            """
[database]
url = "duckdb:///:memory:"

[app]
timezone = "Asia/Bangkok"

[output]
output_dir = "data/out"

[translation]
enable_translation = true
default_source_language = "th"
default_target_language = "en"

[[accounts]]
name = "test_account"
parser = "krungsri_text"
file_path = "data/in/test"
account_number = "123-456-789"
account_name = "Test Account"
bank_name = "Test Bank"
currency = "THB"
country_code = "TH"

[[targets]]
name = "csv"
enabled = true
""",
        )
        config_manager = ConfigManager(config_path)

        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )
        app.dependency_overrides[require_auth] = lambda: {}

        client = TestClient(app)
        yield client

        app.dependency_overrides.clear()

    def test_get_config(self, test_client: TestClient) -> None:
        """Test getting full configuration."""
        response = test_client.get("/api/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "database" in data
        assert "output" in data
        assert "translation" in data
        assert "accounts" in data
        assert "targets" in data
        assert data["app"]["timezone"] == "Asia/Bangkok"
        assert len(data["accounts"]) == 1
        assert len(data["targets"]) == 1

    def test_update_config_not_implemented(self, test_client: TestClient) -> None:
        """Test updating full configuration (not implemented)."""
        response = test_client.put(
            "/api/v1/config",
            json={},
        )
        assert response.status_code == 501
        data = response.json()
        assert "detail" in data

    def test_get_settings(self, test_client: TestClient) -> None:
        """Test getting settings."""
        response = test_client.get("/api/v1/config/settings")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "database" in data
        assert "output" in data
        assert "translation" in data

    def test_update_settings_not_implemented(self, test_client: TestClient) -> None:
        """Test updating settings (not implemented)."""
        response = test_client.patch(
            "/api/v1/config/settings",
            json={
                "app": {"timezone": "UTC"},
            },
        )
        assert response.status_code == 501
        data = response.json()
        assert "detail" in data

    def test_get_accounts(self, test_client: TestClient) -> None:
        """Test getting all accounts."""
        response = test_client.get("/api/v1/config/accounts")
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["name"] == "test_account"

    def test_get_account_by_name(self, test_client: TestClient) -> None:
        """Test getting account by name."""
        response = test_client.get("/api/v1/config/accounts/test_account")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_account"
        assert data["bank_name"] == "Test Bank"

    def test_get_account_by_name_not_found(self, test_client: TestClient) -> None:
        """Test getting non-existent account."""
        response = test_client.get("/api/v1/config/accounts/nonexistent")
        assert response.status_code == 404

    def test_get_targets(self, test_client: TestClient) -> None:
        """Test getting all targets."""
        response = test_client.get("/api/v1/config/targets")
        assert response.status_code == 200
        data = response.json()
        assert "targets" in data
        assert len(data["targets"]) == 1
        assert data["targets"][0]["name"] == "csv"

    def test_get_target_by_name(self, test_client: TestClient) -> None:
        """Test getting target by name."""
        response = test_client.get("/api/v1/config/targets/csv")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "csv"
        assert data["enabled"] is True

    def test_get_target_by_name_not_found(self, test_client: TestClient) -> None:
        """Test getting non-existent target."""
        response = test_client.get("/api/v1/config/targets/nonexistent")
        assert response.status_code == 404
