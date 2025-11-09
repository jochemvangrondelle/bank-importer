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

"""Tests for security and authentication utilities."""

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from bank_importer.api.security import (
    authenticate_user,
    create_access_token,
    get_api_password_hash,
    get_current_user,
    get_password_hash,
    get_secret_key,
    require_auth,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    @pytest.mark.parametrize(
        "password",
        [
            "test_password",
            "secure_password_123",
            "a" * 72,  # Maximum bcrypt length (72 bytes)
            "short",  # Short password
        ],
    )
    def test_get_password_hash(self, password: str) -> None:
        """Test password hashing."""
        hash_value = get_password_hash(password)
        assert isinstance(hash_value, str)
        assert len(hash_value) > 0
        assert hash_value != password  # Should be hashed

    @pytest.mark.parametrize(
        "password",
        [
            "test_password",
            "secure_password_123",
            "another_password",
        ],
    )
    def test_verify_password(self, password: str) -> None:
        """Test password verification."""
        hash_value = get_password_hash(password)
        assert verify_password(password, hash_value) is True
        assert verify_password("wrong_password", hash_value) is False

    def test_verify_password_different_hashes(self) -> None:
        """Test that same password produces different hashes."""
        password = "test_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # Hashes should be different (due to salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_get_password_hash_long_password_truncation(self) -> None:
        """Test that passwords longer than 72 bytes are truncated."""
        # Create a password longer than 72 bytes (72 bytes = 72 ASCII chars)
        long_password = "a" * 100
        hash_value = get_password_hash(long_password)
        # Should hash successfully (truncated to 72 bytes)
        assert isinstance(hash_value, str)
        assert len(hash_value) > 0

    def test_verify_password_long_password_truncation(self) -> None:
        """Test that passwords longer than 72 bytes are truncated during verification."""
        # Create a password longer than 72 bytes
        long_password = "a" * 100
        hash_value = get_password_hash(long_password)
        # Should verify successfully (truncated to 72 bytes)
        assert verify_password(long_password, hash_value) is True


class TestJWTToken:
    """Tests for JWT token functions."""

    @pytest.mark.parametrize(
        "data",
        [
            {"user_id": "123", "username": "test"},
            {"sub": "user@example.com"},
            {"role": "admin", "permissions": ["read", "write"]},
        ],
    )
    def test_create_access_token(self, data: dict) -> None:
        """Test creating access token."""
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self) -> None:
        """Test creating access token with custom expiry."""
        data = {"user_id": "123"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires_delta)
        assert isinstance(token, str)

    def test_verify_token(self) -> None:
        """Test verifying token."""
        data = {"user_id": "123", "username": "test"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["user_id"] == "123"
        assert payload["username"] == "test"
        assert "exp" in payload

    def test_verify_token_invalid(self) -> None:
        """Test verifying invalid token."""
        with pytest.raises(Exception):  # Should raise HTTPException or JWTError
            verify_token("invalid_token_string")

    @pytest.mark.parametrize(
        ("env_key", "config_key", "expected_source"),
        [
            ("test_key", None, "env"),
            (None, "config_key", "config"),
            (None, None, "default"),
        ],
    )
    def test_get_secret_key(
        self,
        env_key: str | None,
        config_key: str | None,
        expected_source: str,
    ) -> None:
        """Test getting secret key from various sources."""
        # Patch settings instance to simulate environment variable
        with patch("bank_importer.api.security.settings") as mock_settings:
            # Set up mock settings to return env_key if provided
            if env_key:
                mock_settings.jwt_secret_key = env_key
                mock_settings.get_jwt_secret_key.return_value = env_key
            else:
                # Use default value
                default_value = "bank-importer-secret-key-change-in-production"
                mock_settings.jwt_secret_key = default_value
                if config_key:
                    # Mock get_jwt_secret_key to check config
                    def get_jwt_secret_key(config: Any) -> str:
                        if config:
                            api_config = config.config.get("api", {})
                            if isinstance(api_config, dict):
                                jwt_secret = api_config.get("jwt_secret_key")
                                if jwt_secret:
                                    return jwt_secret
                        return default_value

                    mock_settings.get_jwt_secret_key.side_effect = get_jwt_secret_key
                else:
                    mock_settings.get_jwt_secret_key.return_value = default_value

            with patch(
                "bank_importer.api.security.ConfigManager",
            ) as mock_config_class:
                if config_key:
                    mock_config = Mock()
                    mock_config.config = {"api": {"jwt_secret_key": config_key}}
                    mock_config_class.return_value = mock_config
                    result = get_secret_key(mock_config)
                    if env_key:
                        assert result == env_key  # Env takes precedence
                    else:
                        assert result == config_key
                else:
                    result = get_secret_key(None)
                    if env_key:
                        assert result == env_key
                    else:
                        # Should return default
                        assert isinstance(result, str)
                        assert len(result) > 0


class TestAPIAuthentication:
    """Tests for API authentication functions."""

    @pytest.mark.asyncio
    async def test_get_api_password_hash_with_hash(self) -> None:
        """Test get_api_password_hash returns hash when configured."""
        mock_config = Mock()
        mock_config.config = {"api": {"password_hash": "test_hash"}}
        result = await get_api_password_hash(mock_config)
        assert result == "test_hash"

    @pytest.mark.asyncio
    async def test_get_api_password_hash_no_hash(self) -> None:
        """Test get_api_password_hash returns None when not configured."""
        mock_config = Mock()
        mock_config.config = {"api": {}}
        result = await get_api_password_hash(mock_config)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_api_password_hash_no_api_config(self) -> None:
        """Test get_api_password_hash returns None when no api config."""
        mock_config = Mock()
        mock_config.config = {}
        result = await get_api_password_hash(mock_config)
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_no_password_hash(self) -> None:
        """Test authenticate_user returns True when no password hash configured."""
        mock_config = Mock()
        mock_config.config = {"api": {}}
        with patch(
            "bank_importer.api.security.get_api_password_hash",
            new_callable=AsyncMock,
        ) as mock_get_hash:
            mock_get_hash.return_value = None
            result = await authenticate_user("any_password", mock_config)
            assert result is True

    @pytest.mark.asyncio
    async def test_authenticate_user_with_password_hash(self) -> None:
        """Test authenticate_user verifies password when hash is configured."""
        mock_config = Mock()
        mock_config.config = {
            "api": {"password_hash": get_password_hash("correct_password")},
        }
        with patch(
            "bank_importer.api.security.get_api_password_hash",
            new_callable=AsyncMock,
        ) as mock_get_hash:
            mock_get_hash.return_value = get_password_hash("correct_password")
            result = await authenticate_user("correct_password", mock_config)
            assert result is True
            result = await authenticate_user("wrong_password", mock_config)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_current_user(self) -> None:
        """Test get_current_user extracts token from credentials."""
        mock_credentials = Mock()
        mock_credentials.credentials = create_access_token({"user_id": "123"})
        result = await get_current_user(mock_credentials)
        assert result["user_id"] == "123"

    @pytest.mark.asyncio
    async def test_require_auth_no_password_hash(self) -> None:
        """Test require_auth allows access when no password hash configured."""
        mock_config = Mock()
        mock_config.config = {"api": {}}
        with patch(
            "bank_importer.api.security.get_api_password_hash",
            new_callable=AsyncMock,
        ) as mock_get_hash:
            mock_get_hash.return_value = None
            result = await require_auth(None, mock_config)
            assert result["authenticated"] is True
            assert "No password configured" in result["message"]

    @pytest.mark.asyncio
    async def test_require_auth_no_credentials(self) -> None:
        """Test require_auth raises error when no credentials provided but password is set."""
        from fastapi import HTTPException

        mock_config = Mock()
        mock_config.config = {"api": {"password_hash": get_password_hash("test")}}
        with patch(
            "bank_importer.api.security.get_api_password_hash",
            new_callable=AsyncMock,
        ) as mock_get_hash:
            mock_get_hash.return_value = get_password_hash("test")
            with pytest.raises(HTTPException) as exc_info:
                await require_auth(None, mock_config)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_auth_with_valid_token(self) -> None:
        """Test require_auth succeeds with valid token."""
        mock_config = Mock()
        mock_config.config = {"api": {"password_hash": get_password_hash("test")}}
        mock_credentials = Mock()
        mock_credentials.credentials = create_access_token({"user_id": "123"})
        with patch(
            "bank_importer.api.security.get_api_password_hash",
            new_callable=AsyncMock,
        ) as mock_get_hash:
            mock_get_hash.return_value = get_password_hash("test")
            result = await require_auth(mock_credentials, mock_config)
            assert result["user_id"] == "123"
