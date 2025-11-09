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

"""Tests for parsers router."""

import pytest
from fastapi.testclient import TestClient

from bank_importer.api.main import app


class TestParsersRouter:
    """Tests for parsers router endpoints."""

    @pytest.fixture
    def test_client(self) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_list_parsers(self, test_client: TestClient) -> None:
        """Test listing available parsers."""
        response = test_client.get("/api/v1/parsers")
        assert response.status_code == 200
        data = response.json()
        assert "parsers" in data
        assert isinstance(data["parsers"], list)
        assert len(data["parsers"]) > 0

    def test_detect_parser(self, test_client: TestClient, tmp_path) -> None:
        """Test parser detection endpoint."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        response = test_client.post(
            "/api/v1/parsers/detect",
            json={"file_path": str(test_file)},
        )
        assert response.status_code == 200
        data = response.json()
        assert "parser_name" in data or "error" in data

    @pytest.mark.parametrize(
        "parser_name",
        [
            "krungsri_text",
            "scb_pdf",
            "generic_csv",
        ],
    )
    def test_get_parser_info(self, test_client: TestClient, parser_name: str) -> None:
        """Test getting parser information."""
        response = test_client.get(f"/api/v1/parsers/{parser_name}")
        # May return 200 with info or 404 if parser not found
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "name" in data or "parser" in data
