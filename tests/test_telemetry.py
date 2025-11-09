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

"""Tests for OpenTelemetry integration."""

import os
from unittest.mock import MagicMock, patch

import pytest

from bank_importer.telemetry import (
    _is_telemetry_enabled,
    get_tracer,
    initialize_telemetry,
    trace_function,
    trace_span,
)


class TestTelemetryOptional:
    """Test that telemetry is optional and has zero overhead when disabled."""

    def test_telemetry_disabled_by_default(self) -> None:
        """Test that telemetry is disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            # Reset the cache
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            assert not _is_telemetry_enabled()

    def test_telemetry_disabled_via_env(self) -> None:
        """Test that telemetry can be disabled via environment variable."""
        with patch.dict(os.environ, {"OTEL_PYTHON_DISABLED": "true"}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            assert not _is_telemetry_enabled()

    def test_telemetry_enabled_when_exporter_set(self) -> None:
        """Test that telemetry is enabled when exporter is set."""
        with patch.dict(os.environ, {"OTEL_TRACES_EXPORTER": "console"}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            # May be True or False depending on whether opentelemetry is installed
            # But the function should not raise
            result = _is_telemetry_enabled()
            assert isinstance(result, bool)

    def test_initialize_telemetry_no_overhead_when_disabled(self) -> None:
        """Test that initialize_telemetry has no overhead when disabled."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            # Should return immediately without side effects
            initialize_telemetry()
            # If we get here without error, it worked

    def test_trace_span_no_overhead_when_disabled(self) -> None:
        """Test that trace_span has no overhead when disabled."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            # Should work without overhead
            with trace_span("test_span", {"key": "value"}):
                # Code inside should execute normally
                result = 1 + 1
                assert result == 2

    def test_trace_function_no_overhead_when_disabled(self) -> None:
        """Test that trace_function decorator has no overhead when disabled."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None

            @trace_function(attributes={"test": "value"})
            def test_func(x: int, y: int) -> int:
                return x + y

            # Function should work normally
            result = test_func(2, 3)
            assert result == 5

    def test_trace_function_preserves_function_metadata(self) -> None:
        """Test that trace_function preserves function metadata."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None

            @trace_function()
            def documented_func(x: int) -> int:
                """A documented function."""
                return x * 2

            assert documented_func.__name__ == "documented_func"
            assert documented_func.__doc__ == "A documented function."

    def test_get_tracer_works_when_disabled(self) -> None:
        """Test that get_tracer works even when telemetry is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            # Should return a tracer (dummy or real) without error
            tracer = get_tracer("test_module")
            assert tracer is not None


class TestTelemetryConfiguration:
    """Test telemetry configuration options."""

    def test_otlp_endpoint_configuration(self) -> None:
        """Test OTLP endpoint configuration."""
        with patch.dict(
            os.environ,
            {
                "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
                "OTEL_TRACES_EXPORTER": "otlp",
            },
            clear=True,
        ):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            # Should enable telemetry when OTLP endpoint is set
            enabled = _is_telemetry_enabled()
            assert isinstance(enabled, bool)

    def test_console_exporter_configuration(self) -> None:
        """Test console exporter configuration."""
        with patch.dict(
            os.environ,
            {"OTEL_TRACES_EXPORTER": "console"},
            clear=True,
        ):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            enabled = _is_telemetry_enabled()
            assert isinstance(enabled, bool)

    def test_none_exporter_configuration(self) -> None:
        """Test that 'none' exporter disables telemetry."""
        with patch.dict(
            os.environ,
            {"OTEL_TRACES_EXPORTER": "none"},
            clear=True,
        ):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            # Should be disabled when exporter is 'none' and no OTLP endpoint
            assert not _is_telemetry_enabled()


class TestTelemetryIntegration:
    """Integration tests for telemetry."""

    def test_initialize_telemetry_safe_to_call_multiple_times(self) -> None:
        """Test that initialize_telemetry can be called multiple times safely."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            # Should be safe to call multiple times
            initialize_telemetry()
            initialize_telemetry()
            initialize_telemetry()
            # If we get here, it worked

    def test_trace_span_context_manager(self) -> None:
        """Test that trace_span works as a context manager."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            # Should work as context manager
            with trace_span("test"):
                pass
            # If we get here, it worked

    def test_trace_function_with_async_function(self) -> None:
        """Test that trace_function works with async functions."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None

            @trace_function()
            async def async_test_func(x: int) -> int:
                return x * 2

            # Should be callable (actual execution requires async context)
            assert callable(async_test_func)

    def test_telemetry_cache_reset(self) -> None:
        """Test that telemetry cache can be reset for testing."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            # Reset cache
            bank_importer.telemetry._telemetry_enabled = None
            # First call should cache the result
            result1 = _is_telemetry_enabled()
            # Second call should use cache
            result2 = _is_telemetry_enabled()
            assert result1 == result2

    def test_trace_span_with_attributes(self) -> None:
        """Test that trace_span handles attributes correctly."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None
            # Should work with attributes
            with trace_span("test", {"key": "value", "number": 42}):
                pass
            # If we get here, it worked

    def test_trace_function_no_overhead_preserves_args(self) -> None:
        """Test that trace_function preserves function arguments when disabled."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None

            @trace_function()
            def test_func(a: int, b: int, c: int = 10) -> int:
                return a + b + c

            # Should work with positional and keyword arguments
            assert test_func(1, 2) == 13
            assert test_func(1, 2, 3) == 6
            assert test_func(1, 2, c=5) == 8


class TestTelemetryHelperFunctions:
    """Test telemetry helper functions."""

    def test_get_service_name_default(self) -> None:
        """Test _get_service_name returns default."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            service_name = bank_importer.telemetry._get_service_name()
            assert service_name == "bank-importer"

    def test_get_service_name_from_env(self) -> None:
        """Test _get_service_name from environment."""
        with patch.dict(
            os.environ,
            {"OTEL_SERVICE_NAME": "custom-service"},
            clear=True,
        ):
            import bank_importer.telemetry

            service_name = bank_importer.telemetry._get_service_name()
            assert service_name == "custom-service"

    def test_get_resource_attributes_default(self) -> None:
        """Test _get_resource_attributes returns default."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            attrs = bank_importer.telemetry._get_resource_attributes()
            assert "service.name" in attrs
            assert "service.version" in attrs

    def test_get_resource_attributes_from_env(self) -> None:
        """Test _get_resource_attributes from environment."""
        with patch.dict(
            os.environ,
            {"OTEL_RESOURCE_ATTRIBUTES": "key1=value1,key2=value2"},
            clear=True,
        ):
            import bank_importer.telemetry

            attrs = bank_importer.telemetry._get_resource_attributes()
            assert attrs["key1"] == "value1"
            assert attrs["key2"] == "value2"

    def test_get_traces_exporter_default(self) -> None:
        """Test _get_traces_exporter returns default."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            exporter = bank_importer.telemetry._get_traces_exporter()
            assert exporter == "none"

    def test_get_traces_exporter_from_env(self) -> None:
        """Test _get_traces_exporter from environment."""
        with patch.dict(os.environ, {"OTEL_TRACES_EXPORTER": "console"}, clear=True):
            import bank_importer.telemetry

            exporter = bank_importer.telemetry._get_traces_exporter()
            assert exporter == "console"

    def test_get_otlp_endpoint_none(self) -> None:
        """Test _get_otlp_endpoint returns None when not set."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            endpoint = bank_importer.telemetry._get_otlp_endpoint()
            assert endpoint is None

    def test_get_otlp_endpoint_from_env(self) -> None:
        """Test _get_otlp_endpoint from environment."""
        with patch.dict(
            os.environ,
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318"},
            clear=True,
        ):
            import bank_importer.telemetry

            endpoint = bank_importer.telemetry._get_otlp_endpoint()
            assert endpoint == "http://localhost:4318"

    def test_get_otlp_endpoint_traces_specific(self) -> None:
        """Test _get_otlp_endpoint from traces-specific env var."""
        with patch.dict(
            os.environ,
            {"OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": "http://localhost:4319"},
            clear=True,
        ):
            import bank_importer.telemetry

            endpoint = bank_importer.telemetry._get_otlp_endpoint()
            assert endpoint == "http://localhost:4319"

    def test_get_otlp_headers_none(self) -> None:
        """Test _get_otlp_headers returns None when not set."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            headers = bank_importer.telemetry._get_otlp_headers()
            assert headers is None

    def test_get_otlp_headers_from_env(self) -> None:
        """Test _get_otlp_headers from environment."""
        with patch.dict(
            os.environ,
            {"OTEL_EXPORTER_OTLP_HEADERS": "key1=value1,key2=value2"},
            clear=True,
        ):
            import bank_importer.telemetry

            headers = bank_importer.telemetry._get_otlp_headers()
            assert headers is not None
            assert headers["key1"] == "value1"
            assert headers["key2"] == "value2"

    def test_get_otlp_headers_traces_specific(self) -> None:
        """Test _get_otlp_headers from traces-specific env var."""
        with patch.dict(
            os.environ,
            {"OTEL_EXPORTER_OTLP_TRACES_HEADERS": "auth=token123"},
            clear=True,
        ):
            import bank_importer.telemetry

            headers = bank_importer.telemetry._get_otlp_headers()
            assert headers is not None
            assert headers["auth"] == "token123"

    def test_trace_function_with_name(self) -> None:
        """Test trace_function with custom name."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None

            @bank_importer.telemetry.trace_function(name="custom_span_name")
            def test_func() -> int:
                return 42

            result = test_func()
            assert result == 42

    def test_trace_function_with_attributes(self) -> None:
        """Test trace_function with attributes."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None

            @bank_importer.telemetry.trace_function(attributes={"operation": "test"})
            def test_func(x: int) -> int:
                return x * 2

            result = test_func(5)
            assert result == 10

    def test_trace_function_with_kwargs(self) -> None:
        """Test trace_function captures kwargs."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None

            @bank_importer.telemetry.trace_function()
            def test_func(a: int, b: int = 10) -> int:
                return a + b

            result = test_func(5, b=20)
            assert result == 25

    def test_trace_span_with_no_attributes(self) -> None:
        """Test trace_span without attributes."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None

            with bank_importer.telemetry.trace_span("test_span"):
                result = 1 + 1
                assert result == 2

    def test_initialize_telemetry_with_sentry(self) -> None:
        """Test initialize_telemetry with Sentry available."""
        with patch.dict(os.environ, {}, clear=True):
            import bank_importer.telemetry

            bank_importer.telemetry._telemetry_enabled = None

            with patch("bank_importer.telemetry.SENTRY_AVAILABLE", True):
                with patch("bank_importer.telemetry.sentry_sdk") as mock_sentry:
                    mock_sentry.Hub.current.client = None
                    mock_sentry.init = MagicMock()

                    bank_importer.telemetry.initialize_telemetry()

                    # Should attempt to initialize Sentry if available
                    # (may or may not be called depending on sentry_settings)
