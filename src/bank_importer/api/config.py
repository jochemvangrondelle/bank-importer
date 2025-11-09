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

"""API configuration settings using pydantic-settings."""

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from bank_importer.config import ConfigManager


class APISettings(BaseSettings):
    """API configuration settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="API_",
        case_sensitive=False,
        extra="ignore",
    )

    # Server settings
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind to",
        alias="API_HOST",
    )
    port: int = Field(
        default=8000,
        description="Port to bind to",
        alias="API_PORT",
    )

    # API path prefix
    api_prefix: str = Field(
        default="/api/v1",
        description="API path prefix",
    )

    # JWT settings
    jwt_secret_key: str = Field(
        default="bank-importer-secret-key-change-in-production",
        description="JWT secret key (use JWT_SECRET_KEY env var or api.jwt_secret_key in config)",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30 * 24 * 60,  # 30 days
        description="JWT access token expiration in minutes",
    )
    jwt_token_type: str = Field(
        default="bearer",
        description="JWT token type",
    )

    # Authentication settings
    default_password: str = Field(
        default="admin",
        description="Default password for initial setup",
    )
    password_config_key: str = Field(
        default="jwt_secret_key",
        description="Config key for JWT secret key in config file",
    )

    # CORS settings
    cors_allow_origins: str | list[str] = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins (can be string or list)",
        alias="CORS_ORIGINS",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS",
    )
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed HTTP methods for CORS",
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed HTTP headers for CORS",
    )

    # API documentation paths
    openapi_url: str = Field(
        default="/api/v1/openapi.json",
        description="OpenAPI JSON URL",
    )
    docs_url: str = Field(
        default="/api/v1/docs",
        description="Swagger UI docs URL",
    )
    redoc_url: str = Field(
        default="/api/v1/redoc",
        description="ReDoc URL",
    )

    # Sentry settings
    sentry_dsn: str | None = Field(
        default=None,
        description="Sentry DSN for API error tracking (set via API_SENTRY_DSN or SENTRY_DSN env var)",
        alias="SENTRY_DSN",
    )
    sentry_send_default_pii: bool = Field(
        default=True,
        description="Send default PII (request headers and IP) to Sentry",
        alias="SENTRY_SEND_DEFAULT_PII",
    )
    sentry_enable_logs: bool = Field(
        default=True,
        description="Enable sending logs to Sentry",
        alias="SENTRY_ENABLE_LOGS",
    )
    sentry_traces_sample_rate: float = Field(
        default=1.0,
        description="Sample rate for transaction tracing (0.0 to 1.0)",
        alias="SENTRY_TRACES_SAMPLE_RATE",
    )
    sentry_profile_session_sample_rate: float = Field(
        default=1.0,
        description="Sample rate for profiling sessions (0.0 to 1.0)",
        alias="SENTRY_PROFILE_SESSION_SAMPLE_RATE",
    )
    sentry_profile_lifecycle: str | None = Field(
        default="trace",
        description="Profile lifecycle mode ('trace' to auto-profile active transactions)",
        alias="SENTRY_PROFILE_LIFECYCLE",
    )

    # Error messages
    error_not_authenticated: str = Field(
        default="Not authenticated. Please login first at /api/v1/auth/login",
        description="Error message for unauthenticated requests",
    )
    error_incorrect_password: str = Field(
        default="Incorrect password",
        description="Error message for incorrect password",
    )
    error_default_password: str = Field(
        default="Incorrect password. Default password is 'admin'.",
        description="Error message for incorrect default password",
    )
    error_could_not_validate: str = Field(
        default="Could not validate credentials",
        description="Error message for invalid token",
    )
    error_password_not_configured: str = Field(
        default="API password not configured. Please set a password first.",
        description="Error message when password is not configured",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str] | Any) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",")]
        return ["*"]

    @field_validator("port", mode="before")
    @classmethod
    def parse_port(cls, v: Any) -> int:
        """Parse port from string or int."""
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return 8000
        return 8000

    def get_jwt_secret_key(self, config: ConfigManager | None = None) -> str:
        """Get JWT secret key from config or environment.

        Priority:
        1. Environment variable (JWT_SECRET_KEY)
        2. Config file (api.jwt_secret_key)
        3. Default from settings (not secure for production!)
        """
        # Check environment variable first (already loaded by pydantic-settings)
        # If jwt_secret_key was set via env var, it will differ from default
        default_value = APISettings.model_fields["jwt_secret_key"].default
        if self.jwt_secret_key != default_value:
            return self.jwt_secret_key

        # Check config file
        if config:
            api_config = config.config.get("api", {})
            if isinstance(api_config, dict):
                jwt_secret = api_config.get(self.password_config_key)
                if jwt_secret and isinstance(jwt_secret, str):
                    return str(jwt_secret)

        # Fallback to default (not secure for production!)
        return self.jwt_secret_key

    def get_cors_origins(self) -> list[str]:
        """Get CORS allowed origins."""
        # pydantic-settings may return str or list[str] depending on how it was set
        cors_value = self.cors_allow_origins
        if isinstance(cors_value, list):
            return cors_value
        # Type checker knows cors_allow_origins can be str
        assert isinstance(cors_value, str), (
            "cors_allow_origins must be str or list[str]"
        )
        return self.parse_cors_origins(cors_value)

    def get_api_host(self) -> str:
        """Get API host."""
        return self.host

    def get_api_port(self) -> int:
        """Get API port."""
        return self.port

    # Legacy properties for backward compatibility
    # Note: Property names use UPPERCASE for backward compatibility
    @property
    def DEFAULT_HOST(self) -> str:
        """Legacy property for backward compatibility."""
        return self.host

    # Legacy properties for backward compatibility
    # Note: Property names use UPPERCASE for backward compatibility
    @property
    def DEFAULT_PORT(self) -> int:
        """Legacy property for backward compatibility."""
        return self.port

    @property
    def API_PREFIX(self) -> str:
        """Legacy property for backward compatibility."""
        return self.api_prefix

    @property
    def JWT_SECRET_KEY_DEFAULT(self) -> str:
        """Legacy property for backward compatibility."""
        return self.jwt_secret_key

    @property
    def JWT_ALGORITHM(self) -> str:
        """Legacy property for backward compatibility."""
        return self.jwt_algorithm

    @property
    def JWT_ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """Legacy property for backward compatibility."""
        return self.jwt_access_token_expire_minutes

    @property
    def JWT_TOKEN_TYPE(self) -> str:
        """Legacy property for backward compatibility."""
        return self.jwt_token_type

    @property
    def DEFAULT_PASSWORD(self) -> str:
        """Legacy property for backward compatibility."""
        return self.default_password

    @property
    def PASSWORD_ENV_VAR(self) -> str:
        """Legacy property for backward compatibility."""
        return "JWT_SECRET_KEY"

    @property
    def PASSWORD_CONFIG_KEY(self) -> str:
        """Legacy property for backward compatibility."""
        return self.password_config_key

    @property
    def CORS_ALLOW_ORIGINS(self) -> list[str]:
        """Legacy property for backward compatibility."""
        return self.get_cors_origins()

    @property
    def CORS_ALLOW_CREDENTIALS(self) -> bool:
        """Legacy property for backward compatibility."""
        return self.cors_allow_credentials

    @property
    def CORS_ALLOW_METHODS(self) -> list[str]:
        """Legacy property for backward compatibility."""
        return self.cors_allow_methods

    @property
    def CORS_ALLOW_HEADERS(self) -> list[str]:
        """Legacy property for backward compatibility."""
        return self.cors_allow_headers

    @property
    def OPENAPI_URL(self) -> str:
        """Legacy property for backward compatibility."""
        return self.openapi_url

    @property
    def DOCS_URL(self) -> str:
        """Legacy property for backward compatibility."""
        return self.docs_url

    @property
    def REDOC_URL(self) -> str:
        """Legacy property for backward compatibility."""
        return self.redoc_url

    @property
    def ERROR_NOT_AUTHENTICATED(self) -> str:
        """Legacy property for backward compatibility."""
        return self.error_not_authenticated

    @property
    def ERROR_INCORRECT_PASSWORD(self) -> str:
        """Legacy property for backward compatibility."""
        return self.error_incorrect_password

    @property
    def ERROR_DEFAULT_PASSWORD(self) -> str:
        """Legacy property for backward compatibility."""
        return self.error_default_password

    @property
    def ERROR_COULD_NOT_VALIDATE(self) -> str:
        """Legacy property for backward compatibility."""
        return self.error_could_not_validate

    @property
    def ERROR_PASSWORD_NOT_CONFIGURED(self) -> str:
        """Legacy property for backward compatibility."""
        return self.error_password_not_configured


# Singleton instance - loads from environment variables automatically
settings = APISettings()
