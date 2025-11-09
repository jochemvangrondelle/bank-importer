# Quick Start Guide

Get up and running with Bank Importer Thailand in minutes.

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/jochemvangrondelle/bank-importer.git
cd bank-importer

# Install with CLI support
uv sync --group cli
```

### Using Docker

```bash
docker pull ghcr.io/jochemvangrondelle/bank-importer:stable
```

## Initial Setup

1. **Initialize configuration**:

```bash
uv run bank-importer init
```

This creates a `config.toml` file in your current directory.

2. **Configure your bank account**:

Edit `config.toml` and add your bank account details:

```toml
[accounts.my-account]
name = "My Bank Account"
bank_name = "Krungsri"
account_number = "XXX-1-12345-X"
currency = "THB"
parser = "krungsri_pdf"
file_path = "data/raw/krungsri"
password = "your-pdf-password"
```

3. **Place your bank statements**:

Place your bank statement files in the directory specified in `file_path` (e.g., `data/raw/krungsri/`).

## Basic Usage

### Import Bank Statements

```bash
# Process all accounts
uv run bank-importer run

# Process specific account
uv run bank-importer run --account my-account
```

### Export Transactions

```bash
# Export to CSV (for Firefly-III)
uv run bank-importer export --target csv

# Export to YAML (for analysis)
uv run bank-importer export --target yaml

# Export with multiple files (per source file + consolidated)
uv run bank-importer export-multi --target csv
```

### Check Status

```bash
# View import/export status
uv run bank-importer status

# View coverage analysis
uv run bank-importer coverage
```

## Next Steps

- Read the [Installation Guide](installation.md) for detailed setup instructions
- Check the [Configuration Guide](configuration.md) for advanced configuration
- See [User Guides](../user-guides/firefly-import.md) for importing into Firefly-III
