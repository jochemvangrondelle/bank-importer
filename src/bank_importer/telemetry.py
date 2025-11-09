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

"""OpenTelemetry configuration for tracing and metrics.

This module provides OpenTelemetry setup for both API and CLI usage.

Environment Variables:
    OTEL_SERVICE_NAME: Service name (default: "bank-importer")
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint URL (default: None, uses console exporter)
    OTEL_EXPORTER_OTLP_HEADERS: OTLP headers (optional)
    OTEL_RESOURCE_ATTRIBUTES: Resource attributes (key=value,key=value format)
    OTEL_TRACES_EXPORTER: Traces exporter (otlp, console, none) (default: console)
    OTEL_METRICS_EXPORTER: Metrics exporter (otlp, console, none) (default: console)
    OTEL_LOGS_EXPORTER: Logs exporter (otlp, console, none) (default: none)
    OTEL_PYTHON_DISABLED: Set to "true" to disable telemetry completely (default: false)

Note: By default, telemetry is disabled (OTEL_TRACES_EXPORTER=none) to ensure zero
overhead for CLI users. To enable, set OTEL_TRACES_EXPORTER=console or configure
an OTLP endpoint.
"""

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, TypeVar

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Console exporter is part of SDK
    try:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
    except ImportError:
        # Fallback: create a simple console exporter
        class ConsoleSpanExporter:  # type: ignore[no-redef]
            """Fallback console span exporter."""

            def export(self, spans: Any) -> None:
                """Export spans to console."""
                import json
                import sys

                for span in spans:
                    sys.stdout.write(
                        json.dumps(
                            {
                                "name": span.name,
                                "context": {
                                    "trace_id": format(span.context.trace_id, "032x"),
                                },
                                "attributes": dict(span.attributes)
                                if hasattr(span, "attributes")
                                else {},
                            },
                        )
                        + "\n",
                    )

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

    # Create dummy implementations for when OpenTelemetry is not available
    class DummySpan:
        """Dummy span that does nothing when OpenTelemetry is unavailable."""

        def set_attribute(self, key: str, value: Any) -> None:
            """No-op attribute setter."""

        def __enter__(self) -> "DummySpan":
            """Context manager entry."""
            return self

        def __exit__(self, *args: object) -> None:
            """Context manager exit."""

    class DummyTracer:
        """Dummy tracer that returns dummy spans when OpenTelemetry is unavailable."""

        def start_as_current_span(self, name: str) -> DummySpan:  # noqa: ARG002
            """Return a dummy span."""
            return DummySpan()

    class DummyTrace:
        """Dummy trace module when OpenTelemetry is unavailable."""

        @staticmethod
        def get_tracer(name: str) -> DummyTracer:  # noqa: ARG004
            """Return a dummy tracer."""
            return DummyTracer()

        @staticmethod
        def get_tracer_provider() -> None:
            """Return None for tracer provider."""
            return

        @staticmethod
        def set_tracer_provider(provider: Any) -> None:
            """No-op provider setter."""

    trace = DummyTrace()  # type: ignore[assignment]
    TracerProvider = None  # type: ignore[assignment, misc]
    Resource = None  # type: ignore[assignment, misc]
    BatchSpanProcessor = None  # type: ignore[assignment, misc]
    ConsoleSpanExporter = None  # type: ignore[assignment, misc]
    OTLPSpanExporter = None  # type: ignore[assignment, misc]

from bank_importer import __version__
from bank_importer.sentry_config import sentry_settings

try:
    import sentry_sdk

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None  # type: ignore[assignment]

F = TypeVar("F", bound=Callable[..., Any])


def _get_service_name() -> str:
    """Get service name from environment or default."""
    return os.getenv("OTEL_SERVICE_NAME", "bank-importer")


def _get_resource_attributes() -> dict[str, str]:
    """Get resource attributes from environment."""
    attrs: dict[str, str] = {
        "service.name": _get_service_name(),
        "service.version": __version__,
    }

    # Parse OTEL_RESOURCE_ATTRIBUTES if provided
    resource_attrs = os.getenv("OTEL_RESOURCE_ATTRIBUTES", "")
    if resource_attrs:
        for pair in resource_attrs.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                attrs[key.strip()] = value.strip()

    return attrs


def _get_traces_exporter() -> str:
    """Get traces exporter from environment."""
    return os.getenv("OTEL_TRACES_EXPORTER", "none")


def _get_otlp_endpoint() -> str | None:
    """Get OTLP endpoint from environment."""
    return os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    )


def _get_otlp_headers() -> dict[str, str] | None:
    """Get OTLP headers from environment."""
    headers_str = os.getenv("OTEL_EXPORTER_OTLP_HEADERS") or os.getenv(
        "OTEL_EXPORTER_OTLP_TRACES_HEADERS",
    )
    if not headers_str:
        return None

    headers: dict[str, str] = {}
    for pair in headers_str.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            headers[key.strip()] = value.strip()
    return headers


# Cache for telemetry enabled state to avoid repeated env checks
_telemetry_enabled: bool | None = None


def _is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled (cached)."""
    global _telemetry_enabled
    if _telemetry_enabled is None:
        if (
            not OPENTELEMETRY_AVAILABLE
            or os.getenv("OTEL_PYTHON_DISABLED", "").lower() == "true"
            or (_get_traces_exporter() == "none" and not _get_otlp_endpoint())
        ):
            _telemetry_enabled = False
        else:
            _telemetry_enabled = True
    return _telemetry_enabled


def _setup_tracer_provider() -> None:
    """Set up OpenTelemetry tracer provider."""
    if not _is_telemetry_enabled():
        return

    # Check if already configured
    current_provider = trace.get_tracer_provider()
    if TracerProvider is not None and isinstance(current_provider, TracerProvider):
        return

    if Resource is None or TracerProvider is None or BatchSpanProcessor is None:
        return

    resource = Resource.create(_get_resource_attributes())
    tracer_provider = TracerProvider(resource=resource)

    # Add span processors based on exporter configuration
    exporter_type = _get_traces_exporter()

    if exporter_type == "otlp" or (exporter_type == "none" and _get_otlp_endpoint()):
        # Use OTLP exporter
        otlp_endpoint = _get_otlp_endpoint()
        if otlp_endpoint and OTLPSpanExporter is not None:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                headers=_get_otlp_headers(),
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        elif exporter_type != "none" and ConsoleSpanExporter is not None:
            # Fallback to console if OTLP endpoint not configured
            console_exporter = ConsoleSpanExporter()
            tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
    elif exporter_type == "console" and ConsoleSpanExporter is not None:
        # Use console exporter
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
    # else: exporter_type == "none", no exporter added

    trace.set_tracer_provider(tracer_provider)


def initialize_telemetry() -> None:
    """Initialize OpenTelemetry tracing and Sentry SDK.

    This should be called early in the application lifecycle, before any
    instrumented code is executed. Safe to call multiple times.

    When telemetry is disabled (default), this function returns immediately
    with zero overhead.
    """
    # Initialize Sentry SDK for general Python usage (only if not already initialized)
    if SENTRY_AVAILABLE and sentry_sdk is not None and sentry_settings.dsn:
        try:
            # Check if Sentry is already initialized (e.g., by API-specific initialization)
            if sentry_sdk.Hub.current.client is None:
                _ = sentry_sdk.init(
                    dsn=sentry_settings.dsn,
                    # Add data like request headers and IP for users,
                    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
                    send_default_pii=sentry_settings.send_default_pii,
                    # Enable sending logs to Sentry
                    enable_logs=sentry_settings.enable_logs,
                    # Set traces_sample_rate to 1.0 to capture 100%
                    # of transactions for tracing.
                    traces_sample_rate=sentry_settings.traces_sample_rate,
                    # Set profile_session_sample_rate to 1.0 to profile 100%
                    # of profile sessions.
                    profile_session_sample_rate=sentry_settings.profile_session_sample_rate,
                )
        except Exception:
            # Silently fail if Sentry initialization fails (e.g., network issues)
            pass

    if not _is_telemetry_enabled():
        return

    _setup_tracer_provider()


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance for the given name.

    Args:
        name: Tracer name (typically __name__ of the module)

    Returns:
        Tracer instance

    """
    return trace.get_tracer(name)


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[trace.Span]:
    """Context manager for creating a trace span.

    Args:
        name: Span name
        attributes: Optional span attributes

    Yields:
        Span instance

    Example:
        >>> with trace_span("parse_file", {"file": "statement.pdf"}):
        ...     # Your code here
        ...     pass

    """
    # Early return if telemetry is disabled - zero overhead
    if not _is_telemetry_enabled():
        # Return a dummy span that does nothing
        if not OPENTELEMETRY_AVAILABLE:
            yield DummySpan()  # type: ignore[return-value, misc]
        else:
            # OpenTelemetry is available but disabled - create a no-op span
            class NoOpSpan:
                """No-op span when telemetry is disabled."""

                def set_attribute(self, key: str, value: Any) -> None:
                    """No-op attribute setter."""

                def __enter__(self) -> "NoOpSpan":
                    """Context manager entry."""
                    return self

                def __exit__(self, *args: object) -> None:
                    """Context manager exit."""

            yield NoOpSpan()  # type: ignore[return-value, misc]
        return

    tracer = get_tracer(__name__)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        yield span


def trace_function(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """Decorator for tracing a function.

    Args:
        name: Optional span name (defaults to function name)
        attributes: Optional span attributes

    Returns:
        Decorator function

    Example:
        >>> @trace_function(attributes={"operation": "import"})
        ... def import_file(path: str):
        ...     pass

    """
    # Early check - if telemetry is disabled, return a no-op decorator
    if not _is_telemetry_enabled():

        def noop_decorator(func: F) -> F:
            return func

        return noop_decorator

    def decorator(func: F) -> F:
        import inspect
        from functools import wraps

        span_name = name or func.__name__
        tracer = get_tracer(func.__module__)
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Double-check at runtime (in case env changed)
                if not _is_telemetry_enabled():
                    return await func(*args, **kwargs)
                with tracer.start_as_current_span(span_name) as span:
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, str(value))
                    if args:
                        span.set_attribute("function.args_count", len(args))
                    if kwargs:
                        for key, value in kwargs.items():
                            if isinstance(value, (str, int, float, bool)):
                                span.set_attribute(f"function.{key}", value)
                    return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Double-check at runtime (in case env changed)
            if not _is_telemetry_enabled():
                return func(*args, **kwargs)
            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))
                if args:
                    span.set_attribute("function.args_count", len(args))
                if kwargs:
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(f"function.{key}", value)
                return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
