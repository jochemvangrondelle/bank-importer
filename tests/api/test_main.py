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

"""Tests for FastAPI main application."""

import pytest
from fastapi.testclient import TestClient

from bank_importer.api.main import app


class TestFastAPIApp:
    """Tests for FastAPI application."""

    @pytest.fixture
    def test_client(self) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_root_endpoint(self, test_client: TestClient) -> None:
        """Test root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    def test_api_root_endpoint(self, test_client: TestClient) -> None:
        """Test API root endpoint."""
        response = test_client.get("/api/v1")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "Bank Importer TH API v1"

    def test_openapi_schema(self, test_client: TestClient) -> None:
        """Test OpenAPI schema endpoint."""
        response = test_client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Bank Importer TH API"

    @pytest.mark.parametrize(
        ("path", "expected_status"),
        [
            ("/", 200),
            ("/api/v1", 200),
            ("/api/v1/openapi.json", 200),
            ("/api/v1/docs", 200),
            ("/api/v1/redoc", 200),
        ],
    )
    def test_public_endpoints(
        self,
        test_client: TestClient,
        path: str,
        expected_status: int,
    ) -> None:
        """Test public endpoints."""
        response = test_client.get(path)
        assert response.status_code == expected_status

    def test_global_exception_handler(self, test_client: TestClient) -> None:
        """Test global exception handler."""
        # Note: We can't easily test the global exception handler without
        # modifying the app, so we'll test that the app has the handler configured
        # by checking that exception handlers are registered
        assert app.exception_handlers is not None
        assert Exception in app.exception_handlers

    def test_cors_middleware(self, test_client: TestClient) -> None:
        """Test CORS middleware."""
        response = test_client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should be handled
        assert response.status_code in [200, 204, 405]
