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

"""Security and authentication utilities."""

import types
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from bank_importer.api.dependencies import get_config_manager
from bank_importer.config import ConfigManager

# Workaround for bcrypt 5.0.0 compatibility with passlib
# bcrypt 5.0.0 doesn't have __about__ attribute that passlib expects
# Also need to patch wrap bug detection to avoid long password issues
try:
    import bcrypt

    if not hasattr(bcrypt, "__about__"):
        about_module = types.ModuleType("__about__")
        bcrypt_version = getattr(bcrypt, "__version__", "5.0.0")
        about_module.__version__ = bcrypt_version  # type: ignore[attr-defined]
        bcrypt.__about__ = about_module  # type: ignore[attr-defined]

    # Patch bcrypt.hashpw to truncate passwords longer than 72 bytes
    # This prevents errors during wrap bug detection
    original_hashpw = bcrypt.hashpw

    def patched_hashpw(password: bytes, salt: bytes) -> bytes:
        """Patched hashpw that truncates passwords longer than 72 bytes."""
        if len(password) > 72:
            password = password[:72]
        return original_hashpw(password, salt)

    bcrypt.hashpw = patched_hashpw

    # Patch passlib's wrap bug detection to avoid issues with long test passwords
    import passlib.handlers.bcrypt as bcrypt_handler

    def patched_detect_wrap_bug(_ident: bytes) -> bool:
        """Patched version that skips wrap bug detection to avoid bcrypt 72-byte limit issues."""
        # Skip detection - assume no wrap bug (bcrypt 2b doesn't have this issue)
        # This prevents passlib from trying to hash long passwords during detection
        return False

    # Patch the function directly
    bcrypt_handler.detect_wrap_bug = patched_detect_wrap_bug

    # Also patch the backend's detect_wrap_bug method if it exists
    if hasattr(bcrypt_handler, "_BcryptBackend"):
        backend_class = bcrypt_handler._BcryptBackend
        if hasattr(backend_class, "detect_wrap_bug"):
            backend_class.detect_wrap_bug = lambda _self, _ident: False
except (ImportError, AttributeError):
    pass

# Password hashing context - initialized lazily to avoid bcrypt initialization issues
_pwd_context: CryptContext | None = None


def _get_pwd_context() -> CryptContext:
    """Get password context, initializing it lazily."""
    global _pwd_context
    if _pwd_context is None:
        # Configure bcrypt to use 2b identifier to avoid wrap bug detection issues
        _pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__ident="2b",
        )
    return _pwd_context


# Import API settings
from bank_importer.api.config import settings

# HTTP Bearer token scheme
security = HTTPBearer()


def get_secret_key(config: ConfigManager | None = None) -> str:
    """Get JWT secret key from config or environment."""
    return settings.get_jwt_secret_key(config)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Note: bcrypt has a 72-byte limit. Passwords longer than 72 bytes
    are truncated to 72 bytes before verification to ensure consistent behavior.
    """
    # Truncate to 72 bytes to avoid bcrypt limitation
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, then decode back to string
        plain_password = password_bytes[:72].decode("utf-8", errors="ignore")
    result = _get_pwd_context().verify(plain_password, hashed_password)
    return bool(result)


def get_password_hash(password: str) -> str:
    """Hash a password.

    Note: bcrypt has a 72-byte limit. Passwords longer than 72 bytes
    are truncated to 72 bytes before hashing to ensure consistent behavior.
    """
    # Truncate to 72 bytes to avoid bcrypt limitation
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, then decode back to string
        password = password_bytes[:72].decode("utf-8", errors="ignore")
    result = _get_pwd_context().hash(password)
    return str(result)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    secret_key: str | None = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        )
    to_encode.update({"exp": expire})
    key = secret_key or settings.get_jwt_secret_key()
    result = jwt.encode(to_encode, key, algorithm=settings.JWT_ALGORITHM)
    return str(result)


def verify_token(token: str, secret_key: str | None = None) -> dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        key = secret_key or settings.get_jwt_secret_key()
        return jwt.decode(token, key, algorithms=[settings.JWT_ALGORITHM])
        # jwt.decode always returns dict[str, Any] at runtime
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=settings.ERROR_COULD_NOT_VALIDATE,
            headers={"WWW-Authenticate": settings.JWT_TOKEN_TYPE.capitalize()},
        )


async def get_api_password_hash(
    config: ConfigManager = Depends(get_config_manager),
) -> str | None:
    """Get the API password hash from config."""
    api_config = config.config.get("api", {})
    if isinstance(api_config, dict):
        return api_config.get("password_hash")
    return None


async def authenticate_user(
    password: str,
    config: ConfigManager = Depends(get_config_manager),
) -> bool:
    """Authenticate a user with a password."""
    password_hash = await get_api_password_hash(config)
    if not password_hash:
        # No password set - allow access (initial setup)
        return True
    return verify_password(password, password_hash)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    return verify_token(token)


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    config: ConfigManager = Depends(get_config_manager),
) -> dict[str, Any]:
    """Require authentication for protected endpoints.

    If no password is configured, allows access (for initial setup).
    Once a password is set, requires valid JWT token.
    """
    # Check if API password is configured
    password_hash = await get_api_password_hash(config)
    if not password_hash:
        # No password set - allow access (initial setup)
        return {"authenticated": True, "message": "No password configured"}

    # Require authentication
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=settings.ERROR_NOT_AUTHENTICATED,
            headers={"WWW-Authenticate": settings.JWT_TOKEN_TYPE.capitalize()},
        )

    token = credentials.credentials
    secret_key = get_secret_key(config)
    return verify_token(token, secret_key=secret_key)
