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

"""Tests for API middleware."""

from pathlib import Path

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from starlette.responses import Response

from bank_importer.api import dependencies
from bank_importer.api.main import app
from bank_importer.api.middleware import SecurityHeadersMiddleware
from bank_importer.config import ConfigManager
from bank_importer.models.database import DatabaseManager


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware."""

    @pytest.fixture
    def middleware(self) -> SecurityHeadersMiddleware:
        """Create middleware instance."""
        return SecurityHeadersMiddleware(app)

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

    @pytest.mark.asyncio
    async def test_security_headers_added(
        self,
        middleware: SecurityHeadersMiddleware,
    ) -> None:
        """Test that security headers are added to responses."""
        # Create a mock request and response
        request = Request({"type": "http", "method": "GET", "path": "/"})

        async def call_next(req: Request) -> Response:
            return Response("OK")

        response = await middleware.dispatch(request, call_next)

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_security_headers_in_response(self, test_client: TestClient) -> None:
        """Test that security headers are present in API responses."""
        response = test_client.get("/api/v1/system/health")
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/",
            "/api/v1",
            "/api/v1/system/health",
            "/api/v1/system/version",
        ],
    )
    def test_security_headers_all_endpoints(
        self,
        test_client: TestClient,
        endpoint: str,
    ) -> None:
        """Test that security headers are present on all endpoints."""
        response = test_client.get(endpoint)
        # Headers should be present regardless of status code
        assert "X-Content-Type-Options" in response.headers
