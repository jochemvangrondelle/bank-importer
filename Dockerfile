# Base stage with common runtime dependencies
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

# Install common runtime dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Builder stage - inherits from base and adds build dependencies
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY src/ ./src/

# Copy uv configuration files and README (needed for package metadata)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Install application in editable mode
RUN uv pip install -e .

# Copy entrypoint script and make it executable
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Production stage - inherits from base
FROM base AS production

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY --from=builder /app/src /app/src
COPY config-example.toml ./

# Copy entrypoint script from builder
COPY --from=builder /usr/local/bin/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Create data directories and set ownership
RUN mkdir -p /app/data/in /app/data/out /app/logs && \
    chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Set version from package
ARG VERSION
ENV APP_VERSION=$VERSION

# Set default volumes
VOLUME ["/app/data/in", "/app/data/out", "/app/logs"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD bank-importer-th --version || exit 1

# Default command
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
