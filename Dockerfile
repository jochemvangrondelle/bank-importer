# Multi-stage build for smaller image size
FROM python:3.12-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy uv configuration files
COPY pyproject.toml uv.lock ./

# Copy source code and submodules
COPY src/ ./src/

# Install dependencies and application
RUN uv sync --frozen --no-dev && uv pip install -e .

# Production stage
FROM python:3.12-slim as production

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY --from=builder /app/src /app/src
COPY config-example.toml ./

# Create data directories
RUN mkdir -p /app/data/in /app/data/out /app/logs && \
    chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set version from package
ARG VERSION
ENV APP_VERSION=${VERSION:-$(python -c "from bank_importer_th import __version__; print(__version__)")}

# Set default volumes
VOLUME ["/app/data/in", "/app/data/out", "/app/logs"]

# Set default working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD bank-importer-th --version || exit 1

# Default command
ENTRYPOINT ["bank-importer-th"]

# Default arguments (show help)
CMD ["--help"] 