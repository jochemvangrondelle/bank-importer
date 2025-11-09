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

"""Sentry SDK configuration settings using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SentrySettings(BaseSettings):
    """Sentry SDK configuration settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="SENTRY_",
        case_sensitive=False,
        extra="ignore",
    )

    # Sentry DSN (required - set via SENTRY_DSN environment variable)
    dsn: str | None = Field(
        default=None,
        description="Sentry DSN for error tracking (set via SENTRY_DSN env var)",
    )

    # Sentry configuration options
    send_default_pii: bool = Field(
        default=True,
        description="Send default PII (request headers and IP) to Sentry",
    )
    enable_logs: bool = Field(
        default=True,
        description="Enable sending logs to Sentry",
    )
    traces_sample_rate: float = Field(
        default=1.0,
        description="Sample rate for transaction tracing (0.0 to 1.0)",
    )
    profile_session_sample_rate: float = Field(
        default=1.0,
        description="Sample rate for profiling sessions (0.0 to 1.0)",
    )


# Singleton instance - loads from environment variables automatically
sentry_settings = SentrySettings()
