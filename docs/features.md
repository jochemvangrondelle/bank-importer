# Features

Bank Importer Thailand provides a comprehensive solution for importing and exporting bank transactions from various Thai banks and formats.

## Core Capabilities

### 🏦 Multi-Bank Support

- **Krungsri Bank**: PDF and text statement parsing
- **Siam Commercial Bank (SCB)**: PDF statement parsing
- **American Express Thailand**: CSV statement parsing with foreign currency support
- **Generic Parsers**: CSV, JSON, and fixed-width file support for any bank

### 📊 Flexible Export Formats

- **CSV**: Optimized for Firefly-III import with comprehensive metadata
- **YAML**: Human-readable format for analysis and review
- **Firefly-III**: Direct integration (optional dependency)

### 🌐 Translation Service

- Automatic Thai-to-English translation
- Financial terms mapping
- Google Translate API integration (optional)
- Translation caching for performance

### 🔧 Advanced Features

- **Duplicate Detection**: File-level and transaction-level deduplication
- **Unique ID Generation**: Prevents duplicate imports across sessions
- **Comprehensive Metadata**: Tracks source files, parsers, and import sessions
- **Flexible Configuration**: TOML-based configuration with account management
- **Multiple Usage Modes**: CLI, API, and library usage

## Usage Modes

### 1. Command-Line Interface (CLI)

Easy-to-use commands for interactive use:

```bash
# Initialize configuration
bank-importer init

# Import bank statements
bank-importer import data/in/

# Export to CSV
bank-importer export --target csv

# Full pipeline
bank-importer run --account my-account
```

### 2. REST API

RESTful API for programmatic access and web integration:

```bash
# Start API server
bank-importer-api

# Import files via API
curl -X POST http://localhost:8000/api/v1/import/files \
  -H "Content-Type: application/json" \
  -d '{"account_name": "my-account"}'
```

### 3. Python Library

Direct Python function calls for integration:

```python
from bank_importer import parse_file, import_file, export_transactions

# Parse a file
transactions = list(parse_file("statement.pdf", "krungsri_pdf", account_config))

# Import to database
result = import_file("statement.pdf", account_config=account_config, ...)

# Export to CSV
export_result = export_transactions(transactions, "csv")
```

## Architecture Highlights

- **Modular Design**: Pluggable parsers and targets
- **Database Integration**: SQLite-based transaction storage
- **Session Tracking**: Import and export session management
- **Error Handling**: Comprehensive error reporting and logging
- **Type Safety**: Full type hints and type checking

## Supported File Formats

### Input Formats

- **PDF**: Password-protected and unprotected PDF statements
- **CSV**: Comma, semicolon, tab, or pipe-delimited
- **JSON**: Standard JSON and JSON Lines formats
- **Fixed-Width**: Columnar text files

### Output Formats

- **CSV**: Firefly-III compatible with metadata
- **YAML**: Structured data format
- **Import Configs**: Auto-generated configuration files

## Performance Features

- **Translation Caching**: Reduces API calls and improves speed
- **Batch Processing**: Efficient handling of multiple files
- **Incremental Imports**: Skip already-processed files
- **Duplicate Prevention**: Fast duplicate detection using database indexes

## Security Features

- **Password Protection**: Support for password-protected PDFs
- **Secure Configuration**: Sensitive data handling in configuration
- **API Authentication**: Optional authentication for REST API
- **Error Sanitization**: Safe error messages without exposing sensitive data

## Extensibility

- **Custom Parsers**: Easy to add new bank parsers
- **Custom Targets**: Simple interface for new export formats
- **Plugin Architecture**: Modular and extensible design
- **Configuration Hooks**: Flexible configuration system
