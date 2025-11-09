# Bank Importer Thailand

[![CI](https://github.com/jochemvangrondelle/bank-importer/actions/workflows/ci.yml/badge.svg)](https://github.com/jochemvangrondelle/bank-importer/actions/workflows/ci.yml)
[![Release](https://github.com/jochemvangrondelle/bank-importer/actions/workflows/release.yml/badge.svg)](https://github.com/jochemvangrondelle/bank-importer/actions/workflows/release.yml)
[![License: PolyForm-Noncommercial-1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-blue.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg)](https://hub.docker.com/)

A Python application that parses Thai bank export PDFs and exports transactions to CSV format suitable for import into Firefly-III or other. The application is designed to support alternative export formats and other parsers, with contributions welcome.

## Data Flow Architecture

```mermaid
graph TD
    %% Configuration
    A[config.toml<br/>Bank Account Configs] --> B[Configuration Manager]

    %% Input Files
    C[Bank Statement Files<br/>- Krungsri PDF<br/>- SCB PDF<br/>- Generic CSV/JSON] --> D[File Scanner]

    %% Processing Pipeline
    B --> E[Parser Selection]
    D --> E
    E --> F[PDF/Text Parsers<br/>- Krungsri Parser<br/>- SCB Parser<br/>- Generic Parsers]

    %% Database Layer
    F --> G[Transaction Extraction]
    G --> H[Database Manager<br/>SQLite Storage]
    H --> I[Import Sessions<br/>Transaction Records]

    %% Translation Layer
    I --> J[Translation Service<br/>- Term Mapping<br/>- Google Translate API<br/>- Caching]

    %% Export Layer
    J --> K[Target Manager]
    K --> L[Export Targets<br/>- CSV Target<br/>- YAML Target]

    %% Output
    L --> M[Export Files<br/>- CSV for Firefly-III<br/>- YAML for Analysis<br/>- Import Configs]

    %% Styling
    classDef config fill:#e1f5fe
    classDef input fill:#f3e5f5
    classDef process fill:#e8f5e8
    classDef storage fill:#fff3e0
    classDef output fill:#fce4ec

    class A,B config
    class C,D input
    class E,F,G,J,K,L process
    class H,I storage
    class M output
```

## Overview

This application is specifically designed for Thai bank statements but built with extensibility in mind. It currently supports:

- **Krungsri Bank** (PDF and text formats)
- **Siam Commercial Bank (SCB)** (PDF format)
- **American Express Thailand** (CSV format)
- **Generic parsers** for CSV, JSON, and fixed-width formats

The application exports to CSV format optimized for Firefly-III's import system, but is intentionally designed without a direct Firefly-III target to rely on Firefly's own robust importer.

## Features

### 🏦 **Supported Banks**

- **Krungsri Bank**: PDF and text statement parsing
- **Siam Commercial Bank (SCB)**: PDF statement parsing
- **American Express Thailand**: CSV statement parsing with foreign currency support
- **Generic parsers**: CSV, JSON, and fixed-width file support

### 📊 **Export Formats**

- **CSV**: Optimized for Firefly-III import with comprehensive transaction data
- **YAML**: Human-readable format for data validation and analysis
- **Import configurations**: Auto-generated Firefly-III import configs

### 🌐 **Translation Support**

- **Thai to English translation**: Automatic translation of transaction descriptions
- **Financial terms mapping**: Pre-defined Thai financial terminology
- **Google Translate integration**: Full sentence translation for complex descriptions
- **Translation caching**: Persistent cache to avoid repeated API calls

### 🔧 **Advanced Features**

- **Duplicate detection**: Prevents importing the same transaction multiple times
- **External ID generation**: Unique identifiers for transaction tracking
- **Comprehensive metadata**: Balance information, transaction types, channels
- **Flexible configuration**: Easy setup for multiple accounts and banks

## Quick Start

### Installation

#### Option 1: Local Installation (Recommended for Users)

```bash
# Clone the repository
git clone https://github.com/jochemvangrondelle/bank-importer.git
cd bank-importer

# Install core only
uv sync

# Install with CLI
uv sync --group cli

# Install with API
uv sync --group api

# Install with both
uv sync --group cli --group api
```

#### Option 2: Local Installation (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/jochemvangrondelle/bank-importer.git
cd bank-importer

# Install dependencies
uv sync

# Copy and configure the example configuration
cp config-example.toml config.toml
# Edit config.toml with your account details
```

#### Option 3: Docker Installation (Recommended for Production)

##### Quick Start with Pre-built Images

```bash
# Pull stable release from Docker Hub (pending stable release :-))
# docker pull jochemvangrondelle/bank-importer:stable

# Pull latest prerelease for testing
docker pull jochemvangrondelle/bank-importer:latest

# Run the container with help
docker run --rm jochemvangrondelle/bank-importer:stable --help

# Run with actual commands (mount your data directories)
docker run --rm \
  -v $(pwd)/data/in:/app/data/in:ro \
  -v $(pwd)/data/out:/app/data/out \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config.toml:/app/config.toml:ro \
  jochemvangrondelle/bank-importer:stable \
  bank-importer import-files data/in/
```

##### Using Docker Compose (Recommended)

```bash
# Uses pre-built image from Docker Hub by default
docker-compose run --rm bank-importer --help

# Run actual commands
docker-compose run --rm api cli import-files data/in/
docker-compose run --rm api cli export-multi --target csv
docker-compose run --rm api cli status

# Build locally when needed
docker-compose build
docker-compose up --build
```

##### Building Docker Images Locally

```bash
# Build for local platform (AMD64/ARM64)
make docker-build

# Build for multiple platforms (AMD64 + ARM64)
make docker-build-multi

# Build and push to Docker Hub
make docker-build-push

# Build for specific platform
make docker-build-arm64          # ARM64 only
make docker-build-amd64          # AMD64 only

# Using the build script directly
./scripts/docker-build.sh --local                    # Local build
./scripts/docker-build.sh --multi-platform --push    # Multi-platform + push
./scripts/docker-build.sh --platform linux/arm64     # Specific platform
```

##### Docker Image Tags

- **`stable`** - Production-ready stable releases (recommended for production)
- **`latest`** - Latest prerelease versions (for testing)
- **`v1.2.3`** - Specific version tags

##### Volume Mounts

The Docker container expects these volume mounts:

- **`/app/data/in`** - Input directory (bank statements) - read-only
- **`/app/data/out`** - Output directory (exports) - read-write
- **`/app/logs`** - Logs directory - read-write
- **`/app/config.toml`** - Configuration file - read-only

##### Environment Variables

- **`APP_VERSION`** - Application version (auto-detected from package)

##### Smart Entrypoint

The container includes a smart entrypoint that handles various command patterns:

```bash
# These all work the same way:
docker run --rm <image> --help
docker run --rm <image> bank-importer --help
docker run --rm <image> import-files data/in/
docker run --rm <image> bank-importer import-files data/in/
```

##### Docker Image Optimization

The Docker image is optimized for production use:

- **Multi-stage build** with shared base layer for maximum efficiency
- **uv-based** Python package management for faster builds and smaller images
- **Python 3.13** with optimized runtime
- **Non-root user** (appuser) for security
- **Health check** included for container monitoring
- **Cross-platform support** (AMD64/ARM64) via Docker Buildx
- **Smart layer caching** for faster rebuilds

**Image layers:**

- **Base stage**: Common runtime dependencies (`libmagic1`), user setup, working directory
- **Builder stage**: Build dependencies (`build-essential`), application building
- **Production stage**: Runtime-only, minimal footprint

### Basic Usage

#### Local Installation (Python CLI)

```bash
# Using uv run (traditional way)
uv run python -m bank_importer import-files data/in/
uv run python -m bank_importer export-multi
uv run python -m bank_importer status

# Using direct script (new way)
bank-importer import-files data/in/
bank-importer export-multi
bank-importer status
```

#### Docker Usage

```bash
# Using docker run
docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/config.toml:/app/config.toml bank-importer import-files data/in/
docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/config.toml:/app/config.toml bank-importer export-multi
docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/config.toml:/app/config.toml bank-importer status

# Using docker-compose (recommended)
docker-compose run --rm bank-importer import-files data/in/
docker-compose run --rm bank-importer export-multi
docker-compose run --rm bank-importer status
```

### Docker Support

The application is containerized for easy deployment and consistent environments across different systems.

### Docker Features

- **Multi-stage build**: Optimized for size and security
- **Non-root user**: Runs as `appuser` for security
- **Volume mounts**: Easy data persistence and configuration
- **Timezone support**: Configurable timezone via `config.toml`
- **PDF processing**: Includes all necessary system dependencies

### Docker Usage

#### Quick Start with Docker Compose

```bash
# Build the image
docker-compose build

# Import bank statements
docker-compose run --rm bank-importer import-files data/in/

# Export to CSV
docker-compose run --rm bank-importer export-multi

# Check status
docker-compose run --rm bank-importer status
```

#### Manual Docker Commands

```bash
# Build the image
docker build -t bank-importer .

# Run with volume mounts
docker run --rm \
  -v $(pwd)/data/in:/app/data/in:ro \
  -v $(pwd)/data/out:/app/data/out \
  -v $(pwd)/config.toml:/app/config.toml:ro \
  bank-importer import-files data/in/

# Export transactions
docker run --rm \
  -v $(pwd)/data/in:/app/data/in:ro \
  -v $(pwd)/data/out:/app/data/out \
  -v $(pwd)/config.toml:/app/config.toml:ro \
  bank-importer export-multi
```

#### Docker Volume Structure

```
your-project/
├── data/
│   ├── in/          # Bank statement files (read-only)
│   └── out/         # Generated exports (read-write)
├── config.toml      # Configuration file (read-only)
├── logs/            # Application logs (optional)
└── docker-compose.yml
```

#### Environment Variables

The Docker container supports the following environment variables:

- `PYTHONPATH`: Python path (automatically set)
- `PATH`: Includes local bin directory

**Note**: Timezone is now configured in `config.toml` under the `[app]` section instead of using the `TZ` environment variable.

#### Security Considerations

- Runs as non-root user (`appuser`)
- Read-only mounts for input files and configuration
- Minimal base image (Python slim)
- No persistent secrets in image

## Configuration

Edit `config.toml` with your account details:

### Application Settings

```toml
[app]
# Default timezone for all date/time operations
timezone = "Asia/Bangkok"
```

### Account Configuration

```toml
[[accounts]]
name           = "krungsri_main"
parser         = "krungsri_pdf"
file_pattern   = "*.pdf"
file_path      = "data/in/Krungsri"
account_number = "YOUR_ACCOUNT_NUMBER"
account_name   = "YOUR_NAME"
bank_name      = "Krungsri Bank"
password       = "YOUR_PASSWORD"

[[accounts]]
name           = "amex_th_csv"
parser         = "amex_th_csv"
file_pattern   = "*.csv"
file_path      = "data/in/amex_th"
account_number = "XXXX-XXXXXX-43002"
account_name   = "TH - CC AMEX (Billed / Uncharged)"
bank_name      = "American Express Thailand"
currency       = "THB"
country_code   = "TH"
```

## Project Structure

```
bank-importer/
├── src/bank_importer/
│   ├── banks/           # Bank-specific parsers
│   ├── targets/         # Export format handlers
│   ├── translation_terms/ # Thai financial terms
│   └── models/          # Data models
├── data/in/             # Bank statement files
├── data/out/            # Generated exports
├── config.toml          # Configuration (not in repo)
├── config-example.toml  # Example configuration
├── Dockerfile           # Docker container definition
├── docker-compose.yml   # Docker Compose configuration
├── .dockerignore        # Docker build exclusions
└── README.md
```

## Entry Points

The application provides multiple ways to run:

### Script Entry Point

After installation, you can run the application directly:

```bash
# Direct script execution
bank-importer --help
bank-importer import-files data/in/
bank-importer export-multi
```

### Module Entry Point

Traditional Python module execution:

```bash
# Module execution
uv run python -m bank_importer --help
uv run python -m bank_importer import-files data/in/
```

### Docker Entry Point

Containerized execution:

```bash
# Docker execution
docker run --rm bank-importer --help
docker-compose run --rm bank-importer import-files data/in/
```

## Supported Banks

### Krungsri Bank

- **Formats**: PDF and text statements
- **Features**: Password-protected PDF support
- **File patterns**: `*.pdf`, `*.txt`

### Siam Commercial Bank (SCB)

- **Formats**: PDF statements
- **Features**: Monthly statement parsing
- **File patterns**: `*AcctSt_*.pdf`

### American Express Thailand

- **Formats**: CSV statements
- **Features**:
  - Foreign currency transaction support with conversion rates
  - Country code detection in merchant names (e.g., "SHOPEETH" → "SHOPEE TH")
  - Amount normalization (expenses negative, repayments positive)
  - Unique ID generation using AMEX reference numbers
  - Comprehensive transaction metadata preservation
- **File patterns**: `*.csv`
- **Account configuration**: Requires `account_name`, `account_number`, `currency`, and `country_code`

### Generic Parsers

- **CSV**: Flexible CSV import with header detection
- **JSON**: JSON transaction data import
- **Fixed-width**: Legacy bank statement formats

## Export Formats

### CSV Export

Optimized for Firefly-III import with:

- Comprehensive transaction metadata
- Thai to English translation
- Duplicate detection
- Import configuration files

### YAML Export

Human-readable format for:

- Data validation
- Transaction analysis
- Debugging and development

## Translation Features

The application includes sophisticated Thai to English translation:

- **Financial terms mapping**: Pre-defined Thai banking terminology
- **Google Translate integration**: Full sentence translation
- **Smart caching**: Persistent translation cache
- **Fallback handling**: Original text preserved if translation fails

## Contributing

Contributions are welcome! The project is designed for extensibility:

### Adding New Banks

1. Create a new parser in `src/bank_importer/banks/`
2. Implement the `Parser` interface
3. Add configuration examples
4. Update documentation

### Adding New Export Formats

1. Create a new target in `src/bank_importer/targets/`
2. Implement the `Target` interface
3. Add configuration options
4. Update documentation

### Translation Improvements

- Add new Thai financial terms to `translation_terms/thai_terms.py`
- Improve translation logic in `translation_service.py`
- Add support for additional languages

## Development

### Setup Development Environment

```bash
# Install development dependencies and pre-commit hooks
make dev-setup

# Run all development checks (matches CI)
make dev-check

# Run pre-commit hooks on staged files
make pre-commit

# Or run individual commands
uv run pytest
uv run mypy src/
uv run ruff check src/
uv run ruff format src/
```

For detailed pre-commit setup, see [Pre-commit Setup Documentation](../development/pre-commit-setup.md).

### Release Process

This project uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) for automated versioning and releases based on conventional commits.

#### Commit Convention

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```bash
# Examples
feat: add support for new bank format
fix: resolve PDF parsing issue
docs: update installation instructions
chore: update dependencies
```

#### Branch Strategy

- **`develop`**: Latest merged changes, continuous integration, publishes prerelease versions
- **`main`**: Production releases, publishes stable versions

#### Making a Release

```bash
# Interactive commit using commitizen
make commit

# Manual release (if needed)
make release

# Check current version
make version
```

#### Pre-commit Hooks

Pre-commit hooks enforce:

- **Conventional commit message format** (validated before commit)
- **Code formatting** (ruff format)
- **Linting** (ruff check, mypy)
- **Tests** (pytest)
- **File validation** (YAML, JSON, TOML)
- **Security checks** (bandit, detect-secrets)

For detailed setup, see [Pre-commit Setup Documentation](../development/pre-commit-setup.md).
For changelog generation, see [Changelog Guide](../operations/changelog-guide.md).

### Docker Development

```bash
# Build development image
docker build -t bank-importer:dev .

# Run with development volumes
docker run --rm -it \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config.toml:/app/config.toml \
  bank-importer:dev bash

# Test Docker build
docker build -t bank-importer:test .
docker run --rm bank-importer:test --help
```

### Publishing to Docker Hub

To publish the Docker image to Docker Hub:

```bash
# Build with proper tags
docker build -t yourusername/bank-importer:latest .
docker build -t yourusername/bank-importer:v0.0.1 .

# Push to Docker Hub
docker push yourusername/bank-importer:latest
docker push yourusername/bank-importer:v0.0.1
```

### Docker Best Practices

- **Multi-stage builds**: Reduces final image size
- **Non-root user**: Improves security
- **Volume mounts**: Keeps data persistent
- **Read-only mounts**: Protects input files
- **Environment variables**: Configurable behavior

### Project Architecture

The application follows a modular architecture:

- **Parsers**: Bank-specific transaction parsing
- **Targets**: Export format handlers
- **Models**: Data structures and database models
- **Translation**: Thai to English translation service
- **CLI**: Command-line interface for user interaction

## Security

### 🔒 **Security Considerations**

- **No sensitive data storage**: The application does not store bank credentials or sensitive financial information
- **Local processing**: All data processing happens locally on your machine
- **Optional API keys**: Google Translate API key is optional and only used for translation
- **Docker security**: Runs as non-root user with minimal permissions

### 🛡️ **Best Practices**

- Keep your `config.toml` file secure and never commit it to version control
- Use strong passwords for password-protected PDF files
- Regularly update dependencies for security patches
- Review exported data before importing into financial management systems

## Support

For issues, feature requests, or contributions:

- Open an issue on [GitHub Issues](https://github.com/jochemvangrondelle/bank-importer/issues)
- Submit a pull request on [GitHub Pull Requests](https://github.com/jochemvangrondelle/bank-importer/pulls)
- Check the [documentation index](../index.md) for comprehensive guides

## Version Management

The project uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) for automated version management based on [Conventional Commits](https://www.conventionalcommits.org/).

### 🔢 **Version Information**

```bash
# Show current version
bank-importer version

# Show version via Makefile
make version
```

For detailed version management information, see [Version Management Documentation](../development/version-management.md).

### 🚀 **Automated Releases**

The project includes GitHub Actions workflows for automated releases:

- **CI Workflow** (`.github/workflows/ci.yml`): Runs tests and builds on every push
- **Release Workflow** (`.github/workflows/release.yml`): Creates releases and Docker images on version tags

See [Release Process Documentation](../development/release-process.md) for details.

### 🐳 **Docker Version Tags**

Docker images are automatically tagged with version numbers:

```bash
# Build with version tag
make docker-build

# Push to registry
make docker-push

# Complete release process
make release
```

### 📋 **Version Files**

- **`pyproject.toml`**: Package version for distribution (single source of truth, managed by semantic-release)
- **`src/bank_importer/__init__.py`**: Python package version (read from package metadata)

For more details, see [Version Management Documentation](../development/version-management.md) and [Release Process Documentation](../development/release-process.md).

## Recent Enhancements

### 🐳 **Docker Support**

- **Universal Docker image**: Multi-stage build optimized for size and security
- **Non-root execution**: Runs as `appuser` for enhanced security
- **Volume mounts**: Easy data persistence and configuration management
- **Docker Compose**: Simplified deployment with `docker-compose.yml`

### 📦 **Script Entry Points**

- **Direct script execution**: `bank-importer` command after installation
- **Module execution**: Traditional `uv run python -m bank_importer`
- **Docker execution**: Containerized `docker run bank-importer`

### 📊 **Enhanced Documentation**

- **Mermaid data flow diagram**: Visual representation of the application architecture
- **Comprehensive Docker guide**: Complete setup and usage instructions
- **Multiple installation options**: Local development vs. production deployment

### 🔧 **Development Improvements**

- **Docker development environment**: Easy setup for contributors
- **Publishing guidelines**: Instructions for Docker Hub distribution
- **Best practices**: Security and performance recommendations

### 💳 **American Express Thailand Support**

- **CSV parser**: Full support for AMEX Thailand CSV statement format
- **Foreign currency handling**: Automatic conversion rates and original currency preservation
- **Smart merchant formatting**: Country code detection (e.g., "SHOPEETH" → "SHOPEE TH")
- **Amount normalization**: Consistent expense/income direction across all banks
- **Unique ID generation**: Uses AMEX reference numbers for duplicate prevention
- **Comprehensive testing**: Full test suite with anonymized sample data

---

**Note**: This project is in active development. While functional for supported banks, it may have bugs or missing features. Contributions and feedback are highly appreciated! Please test thoroughly with your specific bank statements before using in production.
