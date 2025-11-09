# Bank Importer Thailand

[![CI](https://github.com/jochemvangrondelle/bank-importer/actions/workflows/ci.yml/badge.svg)](https://github.com/jochemvangrondelle/bank-importer/actions/workflows/ci.yml)
[![Release](https://github.com/jochemvangrondelle/bank-importer/actions/workflows/release.yml/badge.svg)](https://github.com/jochemvangrondelle/bank-importer/actions/workflows/release.yml)
[![Documentation](https://readthedocs.org/projects/bank-importer/badge/?version=latest)](https://bank-importer.readthedocs.io/en/latest/?badge=latest)
[![Code Coverage](https://codecov.io/gh/jochemvangrondelle/bank-importer/branch/main/graph/badge.svg)](https://codecov.io/gh/jochemvangrondelle/bank-importer)
[![PyPI Version](https://img.shields.io/pypi/v/bank-importer.svg)](https://pypi.org/project/bank-importer/)
[![Python Version](https://img.shields.io/pypi/pyversions/bank-importer.svg)](https://pypi.org/project/bank-importer/)
[![License: PolyForm-Noncommercial-1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-blue.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0/)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type Check: Mypy](https://img.shields.io/badge/type%20check-mypy-blue.svg)](https://mypy.readthedocs.io/)
[![Type Check: Pyright](https://img.shields.io/badge/type%20check-pyright-blue.svg)](https://microsoft.github.io/pyright/)

A Python application that parses Thai bank export PDFs and exports transactions to CSV format suitable for import into Firefly-III or other financial management systems.

## Features

- **Multiple Bank Support**: Parses statements from Krungsri, SCB, and other Thai banks
- **Flexible Parsers**: Supports PDF, CSV, JSON, and fixed-width formats
- **Translation Service**: Automatic Thai-to-English translation with caching
- **Multiple Export Formats**: CSV for Firefly-III, YAML for analysis
- **Duplicate Prevention**: File-level and transaction-level deduplication
- **CLI Interface**: Easy-to-use command-line interface

## Quick Start

```bash
# Clone and install
git clone https://github.com/jochemvangrondelle/bank-importer.git
cd bank-importer
uv sync --group cli

# Initialize configuration
uv run bank-importer init

# Process bank statements
uv run bank-importer run --account my-account

# Export to CSV
uv run bank-importer export --target csv
```

## Documentation Structure

This documentation is organized into the following sections:

### 🚀 [Getting Started](getting-started/quick-start.md)

- [Installation](getting-started/installation.md) - Installation instructions
- [Quick Start](getting-started/quick-start.md) - Get up and running quickly
- [Configuration](getting-started/configuration.md) - Configure accounts and parsers

### 📚 [Core Library](api/library.md)

- [Library API](api/library.md) - Python library reference
- Automatic code documentation from Python docstrings
- All core classes and functions

### 🌐 [REST API](api/rest-api.md)

- [API Overview](api/rest-api.md) - REST API documentation
- [OpenAPI Specification](api/openapi.md) - Complete OpenAPI 3.1.0 spec
- Endpoint documentation

### 💻 [CLI](cli/index.md)

- [CLI Reference](cli/index.md) - Command-line interface documentation
- All available commands and options

### 📖 [Guides](getting-started/quick-start.md)

- **User Guides**: Firefly-III import, generic parsers, translation
- **Development**: Contributing, setup, release process
- **Operations**: Docker, changelog management

### 🔗 [Resources](resources.md)

- Links, discussions, and additional resources
- Community and support information

### 📝 [Release Notes](release-notes.md)

- Version history and changelog

## Links

- **GitHub**: [jochemvangrondelle/bank-importer](https://github.com/jochemvangrondelle/bank-importer)
- **Issues**: [GitHub Issues](https://github.com/jochemvangrondelle/bank-importer/issues)
- **Releases**: [GitHub Releases](https://github.com/jochemvangrondelle/bank-importer/releases)
