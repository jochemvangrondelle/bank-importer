# Use Python slim image
FROM python:3.12-slim

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy uv configuration files
COPY pyproject.toml uv.lock ./

# Copy source code and submodules
COPY src/ ./src/
COPY config-example.toml ./

# Install dependencies and application
RUN uv sync --frozen && uv pip install -e .

# Create data directories
RUN mkdir -p /app/data/in /app/data/out /app/logs && \
    chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set version from package
ARG VERSION
ENV APP_VERSION=${VERSION:-$(uv run python -c "from bank_importer_th import __version__; print(__version__)")}

# Set default volumes
VOLUME ["/app/data/in", "/app/data/out", "/app/logs"]

# Set default working directory
WORKDIR /app

# Default command
ENTRYPOINT ["bank-importer-th"]

# Default arguments (show help)
CMD ["--help"] 