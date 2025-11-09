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

"""Pytest fixtures for API integration tests."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from bank_importer.api.main import app
from bank_importer.config import ConfigManager
from bank_importer.models.database import DatabaseManager


@pytest.fixture
def api_test_client(
    integration_config_manager: ConfigManager,
    integration_db_manager: DatabaseManager,
    integration_processor: Any,
) -> TestClient:
    """Create a test client with overridden dependencies."""
    from bank_importer.api import dependencies

    # Override dependencies to use test database and config
    app.dependency_overrides[dependencies.get_config_manager] = (
        lambda: integration_config_manager
    )
    app.dependency_overrides[dependencies.get_db_manager] = (
        lambda: integration_db_manager
    )
    app.dependency_overrides[dependencies.get_processor] = lambda: integration_processor

    client = TestClient(app)
    yield client

    # Clean up overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def api_auth_token(
    api_test_client: TestClient,
    integration_config_manager: ConfigManager,
) -> str:
    """Get authentication token for API tests."""
    # Set a test password if not already set
    test_password = "test_api_password_123"

    # Try to set password (may fail if already set, that's ok)
    try:
        api_test_client.post(
            "/api/v1/auth/set-password",
            json={
                "password": test_password,
                "confirm_password": test_password,
            },
        )
    except Exception:
        pass  # Password may already be set

    # Login to get token
    response = api_test_client.post(
        "/api/v1/auth/login",
        json={"password": test_password},
    )

    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", "")

    # If login fails, try with default password
    response = api_test_client.post(
        "/api/v1/auth/login",
        json={"password": "admin"},
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token", "")

    # Return empty token if auth is not required
    return ""


@pytest.fixture
def authenticated_client(
    api_test_client: TestClient,
    api_auth_token: str,
) -> TestClient:
    """Create an authenticated test client."""
    # Set default headers for authentication
    api_test_client.headers.update(
        {
            "Authorization": f"Bearer {api_auth_token}" if api_auth_token else "",
        },
    )
    return api_test_client
