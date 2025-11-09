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

"""FastAPI application main module."""

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from bank_importer import __version__
from bank_importer.api.config import settings
from bank_importer.api.middleware import SecurityHeadersMiddleware
from bank_importer.telemetry import initialize_telemetry

# Initialize OpenTelemetry before creating FastAPI app
initialize_telemetry()

# Initialize Sentry SDK before creating FastAPI app (only if DSN is configured)
if settings.sentry_dsn:
    init_kwargs: dict[str, str | bool | float] = {
        "dsn": settings.sentry_dsn,
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        "send_default_pii": settings.sentry_send_default_pii,
        # Enable sending logs to Sentry
        "enable_logs": settings.sentry_enable_logs,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        "traces_sample_rate": settings.sentry_traces_sample_rate,
        # Set profile_session_sample_rate to 1.0 to profile 100%
        # of profile sessions.
        "profile_session_sample_rate": settings.sentry_profile_session_sample_rate,
    }
    # Add profile_lifecycle if configured
    if settings.sentry_profile_lifecycle:
        init_kwargs["profile_lifecycle"] = settings.sentry_profile_lifecycle
    _ = sentry_sdk.init(**init_kwargs)  # type: ignore[arg-type]

# Import FastAPI instrumentation after telemetry is initialized
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:
    FastAPIInstrumentor = None  # type: ignore[assignment, misc]
from bank_importer.api.routers import (
    auth,
    config,
    database,
    export,
    import_,
    parse,
    parsers,
    status,
    system,
    transactions,
    translation,
)

# Create FastAPI app
app = FastAPI(
    title="Bank Importer TH API",
    description=(
        "RESTful API for Bank Importer TH - A Python application to import bank statements "
        "and export transactions to various targets."
    ),
    version=__version__,
    openapi_url=settings.OPENAPI_URL,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add security headers
app.add_middleware(SecurityHeadersMiddleware)

# Instrument FastAPI with OpenTelemetry
if FastAPIInstrumentor is not None:
    FastAPIInstrumentor.instrument_app(app)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": str(exc),
            "details": None,
        },
    )


# Include routers
# Public endpoints (no auth required)
app.include_router(
    system.router,
    prefix=f"{settings.API_PREFIX}/system",
    tags=["System"],
)
app.include_router(
    parsers.router,
    prefix=f"{settings.API_PREFIX}/parsers",
    tags=["Parsers"],
)
app.include_router(
    auth.router,
    prefix=f"{settings.API_PREFIX}/auth",
    tags=["Authentication"],
)

# Protected endpoints (require authentication)
app.include_router(
    config.router,
    prefix=f"{settings.API_PREFIX}/config",
    tags=["Configuration"],
)
app.include_router(parse.router, prefix=f"{settings.API_PREFIX}/parse", tags=["Parse"])
app.include_router(
    import_.router,
    prefix=f"{settings.API_PREFIX}/import",
    tags=["Import"],
)
app.include_router(
    transactions.router,
    prefix=f"{settings.API_PREFIX}/transactions",
    tags=["Import"],
)
app.include_router(
    export.router,
    prefix=f"{settings.API_PREFIX}/export",
    tags=["Export"],
)
app.include_router(
    translation.router,
    prefix=f"{settings.API_PREFIX}/translation",
    tags=["Translation"],
)
app.include_router(
    status.router,
    prefix=f"{settings.API_PREFIX}/status",
    tags=["Status"],
)
app.include_router(
    database.router,
    prefix=f"{settings.API_PREFIX}/database",
    tags=["Database"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Bank Importer TH API",
        "version": __version__,
        "docs": settings.DOCS_URL,
        "redoc": settings.REDOC_URL,
        "openapi": settings.OPENAPI_URL,
    }


@app.get(settings.API_PREFIX)
async def api_root() -> dict[str, str]:
    """API root endpoint."""
    return {
        "message": "Bank Importer TH API v1",
        "version": __version__,
        "docs": settings.DOCS_URL,
        "redoc": settings.REDOC_URL,
        "openapi": settings.OPENAPI_URL,
    }
