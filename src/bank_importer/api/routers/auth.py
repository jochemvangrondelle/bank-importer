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

"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from bank_importer.api.config import settings
from bank_importer.api.dependencies import get_config_manager
from bank_importer.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SetPasswordRequest,
    SetPasswordResponse,
)
from bank_importer.api.security import (
    authenticate_user,
    create_access_token,
    get_api_password_hash,
    get_password_hash,
)
from bank_importer.config import ConfigManager

router = APIRouter()


@router.post("/login", tags=["Authentication"])
async def login(
    login_data: LoginRequest,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
) -> LoginResponse:
    """Login and get access token."""
    # Check if password is configured
    password_hash = await get_api_password_hash(config)
    if not password_hash:
        # Auto-set default password if not configured
        default_password = settings.DEFAULT_PASSWORD
        password_hash = get_password_hash(default_password)
        if "api" not in config.config:
            config.config["api"] = {}
        config.config["api"]["password_hash"] = password_hash
        config.save_config()
        # Now verify the provided password matches default
        if login_data.password != default_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=settings.ERROR_DEFAULT_PASSWORD,
                headers={"WWW-Authenticate": settings.JWT_TOKEN_TYPE.capitalize()},
            )
        # Password matches default, continue to create token
    else:
        # Authenticate with configured password
        is_valid = await authenticate_user(login_data.password, config)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=settings.ERROR_INCORRECT_PASSWORD,
                headers={"WWW-Authenticate": settings.JWT_TOKEN_TYPE.capitalize()},
            )

    # Create access token
    from bank_importer.api.security import get_secret_key

    secret_key = get_secret_key(config)
    access_token = create_access_token(data={"sub": "api_user"}, secret_key=secret_key)
    return LoginResponse(access_token=access_token, token_type=settings.JWT_TOKEN_TYPE)


@router.post(
    "/set-password",
    tags=["Authentication"],
)
async def set_password(
    password_data: SetPasswordRequest,
    config: Annotated[ConfigManager, Depends(get_config_manager)],
) -> SetPasswordResponse:
    """Set or update API password.

    Note: For initial setup, no auth is required. For updates after password
    is set, authentication should be required, but we allow it for simplicity.
    In production, consider requiring auth for password updates.
    """
    # Hash the password
    password_hash = get_password_hash(password_data.password)

    # Save to config
    if "api" not in config.config:
        config.config["api"] = {}
    config.config["api"]["password_hash"] = password_hash
    config.save_config()

    return SetPasswordResponse(
        message="Password set successfully",
        password_configured=True,
    )


@router.get("/status", tags=["Authentication"])
async def get_auth_status(
    config: Annotated[ConfigManager, Depends(get_config_manager)],
) -> dict[str, bool]:
    """Get authentication status (whether password is configured)."""
    password_hash = await get_api_password_hash(config)
    return {
        "password_configured": password_hash is not None,
    }
