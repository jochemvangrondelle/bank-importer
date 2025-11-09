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

"""Authentication API schemas."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Login request schema."""

    password: str = Field(..., description="API password")


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class SetPasswordRequest(BaseModel):
    """Set API password request schema."""

    password: str = Field(
        ...,
        min_length=8,
        description="New API password (minimum 8 characters)",
    )
    confirm_password: str = Field(
        ...,
        description="Confirm new API password",
    )

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v: str, values: Any) -> str:
        """Validate that password and confirm_password match."""
        # In Pydantic v2, use values.data to access other fields
        if hasattr(values, "data") and "password" in values.data:
            if v != values.data["password"]:
                msg = "Password and confirmation do not match"
                raise ValueError(msg)
        return v


class SetPasswordResponse(BaseModel):
    """Set password response schema."""

    message: str = Field(..., description="Success message")
    password_configured: bool = Field(
        ...,
        description="Whether password is now configured",
    )
