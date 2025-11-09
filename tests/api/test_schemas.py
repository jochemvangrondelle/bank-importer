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

"""Tests for API schemas."""

from pathlib import Path

import pytest

from bank_importer.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SetPasswordRequest,
    SetPasswordResponse,
)
from bank_importer.api.schemas.common import (
    ErrorResponse,
    HealthResponse,
    VersionResponse,
)
from bank_importer.api.schemas.config import (
    AccountConfigResponse,
    TargetConfigResponse,
)
from bank_importer.models.config_models import AccountConfig, TargetConfig


class TestAuthSchemas:
    """Tests for authentication schemas."""

    @pytest.mark.parametrize(
        "password",
        [
            "test_password",
            "secure_password_123",
            "a" * 100,  # Long password
        ],
    )
    def test_login_request(self, password: str) -> None:
        """Test LoginRequest schema."""
        request = LoginRequest(password=password)
        assert request.password == password

    @pytest.mark.parametrize(
        ("access_token", "token_type"),
        [
            ("token123", "bearer"),
            ("long_token_string", "Bearer"),
        ],
    )
    def test_login_response(self, access_token: str, token_type: str) -> None:
        """Test LoginResponse schema."""
        response = LoginResponse(access_token=access_token, token_type=token_type)
        assert response.access_token == access_token
        assert response.token_type == token_type

    @pytest.mark.parametrize(
        "password",
        [
            "new_password_123",
            "test_password_456",
            "secure_pass_789",
        ],
    )
    def test_set_password_request(self, password: str) -> None:
        """Test SetPasswordRequest schema."""
        request = SetPasswordRequest(password=password, confirm_password=password)
        assert request.password == password
        assert request.confirm_password == password
        assert len(request.password) >= 8  # Minimum length requirement

    def test_set_password_response(self) -> None:
        """Test SetPasswordResponse schema."""
        response = SetPasswordResponse(message="Password set", password_configured=True)
        assert response.message == "Password set"
        assert response.password_configured is True


class TestCommonSchemas:
    """Tests for common schemas."""

    @pytest.mark.parametrize(
        ("status", "version"),
        [
            ("healthy", "1.0.0"),
            ("degraded", None),
            ("unhealthy", "2.0.0"),
        ],
    )
    def test_health_response(self, status: str, version: str | None) -> None:
        """Test HealthResponse schema."""
        response = HealthResponse(status=status, version=version)
        assert response.status == status
        assert response.timestamp is not None
        assert response.version == version

    @pytest.mark.parametrize(
        ("version", "build_date", "git_commit"),
        [
            ("1.0.0", None, None),
            ("2.0.0", None, None),
            ("1.2.3", None, None),
        ],
    )
    def test_version_response(
        self,
        version: str,
        build_date: str | None,
        git_commit: str | None,
    ) -> None:
        """Test VersionResponse schema."""
        from datetime import datetime

        build_date_obj = datetime.fromisoformat(build_date) if build_date else None
        response = VersionResponse(
            version=version,
            build_date=build_date_obj,
            git_commit=git_commit,
        )
        assert response.version == version
        assert response.build_date == build_date_obj
        assert response.git_commit == git_commit

    @pytest.mark.parametrize(
        ("error", "message", "details"),
        [
            ("NotFound", "Resource not found", None),
            ("ValidationError", "Invalid input", {"field": "name"}),
            ("InternalError", "Server error", None),
        ],
    )
    def test_error_response(
        self,
        error: str,
        message: str,
        details: dict | None,
    ) -> None:
        """Test ErrorResponse schema."""
        response = ErrorResponse(error=error, message=message, details=details)
        assert response.error == error
        assert response.message == message
        assert response.details == details


class TestConfigSchemas:
    """Tests for configuration schemas."""

    def test_translation_settings_hide_api_key(self) -> None:
        """Test hide_api_key method on TranslationSettings."""
        from bank_importer.api.schemas.config import TranslationSettings

        # Test hide_api_key returns None (hides API key in responses)
        # The method always returns None regardless of input
        result = TranslationSettings.hide_api_key("test_key")
        assert result is None
        result = TranslationSettings.hide_api_key(None)
        assert result is None
        # Test with empty string
        result = TranslationSettings.hide_api_key("")
        assert result is None

    def test_account_config_response_from_account_config(self) -> None:
        """Test AccountConfigResponse.from_account_config."""
        account = AccountConfig(
            name="test_account",
            parser="krungsri_pdf",
            file_path=Path("/test/file.pdf"),
            file_pattern="*.pdf",
            account_number="123-456-789",
            account_name="Test User",
            bank_name="Test Bank",
            currency="THB",
            country_code="TH",
            reference="test_ref",
            translation={"enabled": True},
        )
        response = AccountConfigResponse.from_account_config(account)
        assert response.name == "test_account"
        assert response.parser == "krungsri_pdf"
        assert response.file_path == "/test/file.pdf"
        assert response.account_number == "123-456-789"

    def test_account_config_response_from_dict(self) -> None:
        """Test AccountConfigResponse.from_dict."""
        account_dict = {
            "name": "test_account",
            "parser": "krungsri_pdf",
            "file_path": Path("/test/file.pdf"),
            "file_pattern": "*.pdf",
            "password": "secret",  # Should be removed
            "password_file": "secret.txt",  # Should be removed
        }
        # from_dict creates a copy and modifies it
        response = AccountConfigResponse.from_dict(account_dict)
        assert response.name == "test_account"
        assert response.parser == "krungsri_pdf"
        assert response.file_path == "/test/file.pdf"
        # Password fields should not be in response
        assert not hasattr(response, "password")
        assert not hasattr(response, "password_file")

    def test_target_config_response_from_target_config(self) -> None:
        """Test TargetConfigResponse.from_target_config."""
        target = TargetConfig(
            name="csv",
            enabled=True,
            output_dir=Path("/test/output"),
            config={"delimiter": ","},
        )
        response = TargetConfigResponse.from_target_config(target)
        assert response.name == "csv"
        assert response.enabled is True
        assert response.output_dir == "/test/output"
        assert response.config == {"delimiter": ","}

    def test_target_config_response_from_dict_with_csv_config(self) -> None:
        """Test TargetConfigResponse.from_dict with csv_config."""
        target_dict = {
            "name": "csv",
            "enabled": True,
            "csv_config": {"delimiter": ","},
        }
        response = TargetConfigResponse.from_dict(target_dict)
        assert response.name == "csv"
        assert response.config == {"delimiter": ","}
        # Original dict is not modified (from_dict works on a copy)
        assert "csv_config" in target_dict
        # Response should have config, not csv_config
        assert response.config == {"delimiter": ","}

    def test_target_config_response_from_dict_with_yaml_config(self) -> None:
        """Test TargetConfigResponse.from_dict with yaml_config."""
        target_dict = {
            "name": "yaml",
            "enabled": True,
            "yaml_config": {"indent": 2},
        }
        response = TargetConfigResponse.from_dict(target_dict)
        assert response.name == "yaml"
        assert response.config == {"indent": 2}
        # Original dict is not modified (from_dict works on a copy)
        assert "yaml_config" in target_dict
        # Response should have config, not yaml_config
        assert response.config == {"indent": 2}

    def test_target_config_response_from_dict_with_firefly_config(self) -> None:
        """Test TargetConfigResponse.from_dict with firefly_config."""
        target_dict = {
            "name": "firefly",
            "enabled": True,
            "firefly_config": {"api_url": "https://api.firefly.example.com"},
        }
        response = TargetConfigResponse.from_dict(target_dict)
        assert response.name == "firefly"
        assert response.config == {"api_url": "https://api.firefly.example.com"}
        # Original dict is not modified (from_dict works on a copy)
        assert "firefly_config" in target_dict
        # Response should have config, not firefly_config
        assert response.config == {"api_url": "https://api.firefly.example.com"}

    def test_target_config_response_from_dict_with_path_output_dir(self) -> None:
        """Test TargetConfigResponse.from_dict with Path output_dir."""
        target_dict = {
            "name": "csv",
            "enabled": True,
            "output_dir": Path("/test/output"),
        }
        response = TargetConfigResponse.from_dict(target_dict)
        assert response.output_dir == "/test/output"
