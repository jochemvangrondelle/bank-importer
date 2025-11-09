# Builder stage - install dependencies and build
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Install git for git-based dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Enable bytecode compilation for better performance
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Disable Python downloads, use system interpreter across both images
ENV UV_PYTHON_DOWNLOADS=0

# Set working directory
WORKDIR /app

# Build argument for dependency groups (default: all)
ARG DEPENDENCY_GROUPS=all

# Install dependencies based on groups using cache mounts for better performance
# First, install dependencies without the project for optimal layer caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    if [ "$DEPENDENCY_GROUPS" = "all" ]; then \
        uv sync --locked --no-install-project --no-dev --group all; \
    else \
        # Parse groups and install them (avoid duplicate installs) \
        GROUPS=$(echo "$DEPENDENCY_GROUPS" | tr ',' ' ' | tr ' ' '\n' | sort -u | tr '\n' ' '); \
        uv sync --locked --no-install-project --no-dev $(for group in $GROUPS; do echo "--group $group"; done); \
    fi

# Copy the rest of the project source code and install it
# Installing separately from dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$DEPENDENCY_GROUPS" = "all" ]; then \
        uv sync --locked --no-dev --group all; \
    else \
        # Parse groups and install them (avoid duplicate installs) \
        GROUPS=$(echo "$DEPENDENCY_GROUPS" | tr ',' ' ' | tr ' ' '\n' | sort -u | tr '\n' ' '); \
        uv sync --locked --no-dev $(for group in $GROUPS; do echo "--group $group"; done); \
    fi

# Generate OpenAPI specification (only if API group is included)
RUN if echo "$DEPENDENCY_GROUPS" | grep -q "api" || [ "$DEPENDENCY_GROUPS" = "all" ]; then \
        /app/.venv/bin/python scripts/generate_openapi.py api/openapi.yaml || \
        (echo "Warning: Failed to generate OpenAPI spec (API may not be available)" && exit 0); \
    fi

# Production stage - minimal runtime image
FROM python:3.13-slim-bookworm AS production

# Install only runtime dependencies (no build tools)
# curl is included for healthcheck (lightweight, standard practice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Create app user (non-root, generic UID - not bound to specific UID)
# Using system user without specific UID allows Openshift and other platforms
# to use random UIDs while still working correctly
RUN groupadd --system appuser \
    && useradd --system --gid appuser --create-home appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder (owned by root for immutability)
COPY --from=builder /app/.venv /app/.venv

# Copy only necessary application files (owned by root for immutability)
COPY --from=builder /app/src /app/src
COPY config-example.toml ./

# Copy entrypoint script (owned by root, executable but not writable)
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

# Set version from build arg (passed from GitHub Actions)
ARG VERSION=0.0.0

# Extract version from package metadata if VERSION not provided, and create version file
# Use /tmp for version file to allow any UID to write
RUN if [ "$VERSION" = "0.0.0" ]; then \
      EXTRACTED_VERSION=$(/app/.venv/bin/python -c "import importlib.metadata; print(importlib.metadata.version('bank-importer'))" 2>/dev/null || echo "0.0.0"); \
      echo "$EXTRACTED_VERSION" > /tmp/.version; \
      echo "Extracted version: $EXTRACTED_VERSION"; \
    else \
      echo "$VERSION" > /tmp/.version; \
      echo "Using provided version: $VERSION"; \
    fi

# Create data directories with world-writable permissions (for any UID)
# Use /tmp for temporary data to allow any UID to write
RUN mkdir -p /app/data/in /app/data/out /app/logs /app/data \
    && chmod 755 /app/data/in /app/data/out /app/logs /app/data \
    && chmod 644 /app/config-example.toml

# Set version environment variable (read from file at runtime)
# Use /tmp for temporary data to support any UID
ENV APP_VERSION_FILE=/tmp/.version \
    APP_TMP_DATA=/tmp \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Expose only the API port (documentation purposes)
EXPOSE 8000

# Add version label (using build arg)
LABEL org.opencontainers.image.title="Bank Importer" \
      org.opencontainers.image.description="A Python application that parses Thai bank export PDFs and exports transactions to CSV format suitable for import into Firefly-III" \
      org.opencontainers.image.licenses="PolyForm-Noncommercial-1.0.0" \
      org.opencontainers.image.version="${VERSION}"

# Switch to app user (non-root, generic UID)
USER appuser

# Set default volumes
VOLUME ["/app/data/in", "/app/data/out", "/app/logs"]

# Health check - check API health endpoint using portable curl command
# Falls back to CLI version check if API unavailable
# Uses shell form to allow environment variable expansion
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD sh -c "curl -f http://localhost:${API_PORT:-8000}/api/v1/system/health >/dev/null 2>&1 || bank-importer --version >/dev/null 2>&1 || exit 1"

# Default command - launch FastAPI server
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["api"]
