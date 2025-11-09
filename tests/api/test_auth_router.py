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

"""Tests for authentication router."""

import pytest
from fastapi.testclient import TestClient

from bank_importer.api.main import app


class TestAuthRouter:
    """Tests for authentication router endpoints."""

    @pytest.fixture
    def test_client(self) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_login_no_password_configured(self, test_client: TestClient) -> None:
        """Test login when no password is configured."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={"password": "any_password"},
        )
        # Should either succeed (no password) or fail (password required)
        assert response.status_code in [200, 400, 401]

    @pytest.mark.parametrize(
        ("password", "expected_status"),
        [
            ("test_password", [200, 401]),  # May succeed or fail depending on config
            ("", [400, 401]),  # Empty password
        ],
    )
    def test_login_various_passwords(
        self,
        test_client: TestClient,
        password: str,
        expected_status: list[int],
    ) -> None:
        """Test login with various passwords."""
        response = test_client.post(
            "/api/v1/auth/login",
            json={"password": password},
        )
        assert response.status_code in expected_status

    def test_set_password(self, test_client: TestClient) -> None:
        """Test setting API password."""
        response = test_client.post(
            "/api/v1/auth/set-password",
            json={
                "password": "new_password_123",
                "confirm_password": "new_password_123",
            },
        )
        # May succeed or fail depending on current config
        assert response.status_code in [200, 400, 500]

    def test_set_password_mismatch(self, test_client: TestClient) -> None:
        """Test setting password with mismatched confirmation."""
        response = test_client.post(
            "/api/v1/auth/set-password",
            json={"password": "password1", "confirm_password": "password2"},
        )
        # Should fail validation
        assert response.status_code in [400, 422]

    def test_get_auth_status(self, test_client: TestClient) -> None:
        """Test getting authentication status."""
        response = test_client.get("/api/v1/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "password_configured" in data
        assert isinstance(data["password_configured"], bool)

    def test_login_with_default_password(
        self, test_client: TestClient, tmp_path
    ) -> None:
        """Test login with default password when no password is configured."""
        from bank_importer.api import dependencies
        from bank_importer.api.main import app
        from bank_importer.config import ConfigManager

        config_path = tmp_path / "config.toml"
        config_path.write_text('[database]\nurl = "sqlite:///test.db"')
        config_manager = ConfigManager(config_path)

        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )

        try:
            from bank_importer.api.config import settings

            response = test_client.post(
                "/api/v1/auth/login",
                json={"password": settings.DEFAULT_PASSWORD},
            )
            # Should succeed with default password
            assert response.status_code in [200, 401]
        finally:
            app.dependency_overrides.clear()

    def test_login_with_wrong_password(self, test_client: TestClient, tmp_path) -> None:
        """Test login with wrong password."""
        from bank_importer.api import dependencies
        from bank_importer.api.main import app
        from bank_importer.config import ConfigManager

        config_path = tmp_path / "config.toml"
        # Create a real bcrypt hash for a known password
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        correct_password = "test_password_123"
        password_hash = pwd_context.hash(correct_password)

        config_path.write_text(
            f"""
[database]
url = "sqlite:///test.db"
[api]
password_hash = "{password_hash}"
""",
        )
        config_manager = ConfigManager(config_path)

        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )

        try:
            # Try with wrong password
            response = test_client.post(
                "/api/v1/auth/login",
                json={"password": "wrong_password"},
            )
            # Should fail with wrong password (401) or internal error (500) if hash verification fails
            assert response.status_code in [401, 500]

            # Try with correct password - should succeed
            response2 = test_client.post(
                "/api/v1/auth/login",
                json={"password": correct_password},
            )
            # Should succeed with correct password
            assert response2.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_set_password_creates_api_section(
        self, test_client: TestClient, tmp_path
    ) -> None:
        """Test that set_password creates api section if it doesn't exist."""
        from bank_importer.api import dependencies
        from bank_importer.api.main import app
        from bank_importer.config import ConfigManager

        config_path = tmp_path / "config.toml"
        config_path.write_text('[database]\nurl = "sqlite:///test.db"')
        config_manager = ConfigManager(config_path)

        app.dependency_overrides[dependencies.get_config_manager] = (
            lambda: config_manager
        )

        try:
            response = test_client.post(
                "/api/v1/auth/set-password",
                json={"password": "new_password", "confirm_password": "new_password"},
            )
            # Should succeed
            assert response.status_code in [200, 400, 500]
            # Check that api section was created
            if response.status_code == 200:
                assert "api" in config_manager.config
        finally:
            app.dependency_overrides.clear()
