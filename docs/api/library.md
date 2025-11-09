# Library API

The `bank-importer` library provides a clean, consistent API for parsing, importing, and exporting bank transactions. This API is designed to work seamlessly across three usage modes:

1. **CLI**: Command-line interface for interactive use
2. **API**: REST API endpoints for programmatic access
3. **Library**: Direct Python function calls for integration

All three modes use the same underlying library functions, ensuring consistency and reliability.

## Installation

```bash
# Core library
uv sync

# With CLI support
uv sync --group cli

# With API support
uv sync --group api

# With translation support
uv sync --group translate

# With Firefly-III target support
uv sync --group firefly

# Everything
uv sync --group all
```

## Module Reference

::: bank_importer.library

## Quick Start Example

```python
from bank_importer import (
    parse_file,
    import_file,
    export_transactions,
    detect_parser,
    ConfigManager,
    DatabaseManager,
)

# Parse a file without database operations
account_config = {
    "name": "my_account",
    "account_number": "1234567890",
    "account_name": "My Account",
    "bank_name": "Krungsri",
    "currency": "THB",
    "country_code": "TH",
}

transactions = list(parse_file("statement.pdf", "krungsri_pdf", account_config))
print(f"Parsed {len(transactions)} transactions")

# Import and store in database
config = ConfigManager("config.toml")
db = DatabaseManager(config.get_database_url())
result = import_file(
    "statement.pdf",
    account_config=account_config,
    config_manager=config,
    db_manager=db,
)
print(f"Imported {len(result['transactions'])} new transactions")

# Export to CSV
export_result = export_transactions(transactions, "csv", output_dir="exports/")
print(f"Exported to {export_result.output_file}")
```

## Core Concepts

### Parsing vs Importing

- **Parsing** (`parse_file`): Pure function that reads a file and returns transactions. No side effects, no database operations.
- **Importing** (`import_file`): Parses a file AND stores transactions in the database. Includes translation, duplicate detection, and session tracking.

### Account Configuration

Account configuration is a dictionary with the following structure:

```python
account_config = {
    "name": "unique_account_identifier",  # Required
    "account_number": "1234567890",        # Required
    "account_name": "Display Name",        # Required
    "bank_name": "Bank Name",              # Required
    "currency": "THB",                     # Required (ISO 4217 code)
    "country_code": "TH",                  # Required (ISO 3166-1 alpha-2)
    "parser": "krungsri_pdf",              # Optional (auto-detected if not provided)
    "file_path": "data/in",                # Optional
    "file_pattern": "*.pdf",                # Optional
    "password": "pdf_password",                 # Optional (for password-protected PDFs)
    "translation": {                       # Optional
        "enabled": True,
        "use_term_mapping": True,
        "use_api_translation": True,
    },
}
```

## Consistency Across Usage Modes

The library API ensures that the same operations work identically across CLI, API, and library usage:

| Operation           | CLI                          | API                      | Library                 |
| ------------------- | ---------------------------- | ------------------------ | ----------------------- |
| Parse file          | `bank-importer import`       | `POST /api/import/files` | `parse_file()`          |
| Import file         | `bank-importer import`       | `POST /api/import/files` | `import_file()`         |
| Export transactions | `bank-importer export`       | `POST /api/export`       | `export_transactions()` |
| Detect parser       | `bank-importer list-parsers` | `GET /api/parsers`       | `detect_parser()`       |

All three modes use the same underlying library functions, ensuring consistent behavior and results.

## Error Handling

All library functions raise `ValueError` for invalid inputs or configuration errors. Database and file system errors may raise other exceptions (e.g., `IOError`, `DatabaseError`).

```python
try:
    transactions = list(parse_file("statement.pdf", "invalid_parser", account_config))
except ValueError as e:
    print(f"Error: {e}")
```

## Best Practices

1. **Use `parse_file()` for analysis**: When you only need to read and analyze transactions without storing them.

2. **Use `import_file()` for persistence**: When you need to store transactions in the database for later use.

3. **Auto-detect parsers**: Use `auto_detect=True` to automatically detect the correct parser for each file.

4. **Handle duplicates**: The `import_file()` function automatically handles duplicate detection. Use `reprocess_existing=True` to override.

5. **Configure translation**: Set up translation in your account configuration if you need automatic translation of transaction descriptions.

6. **Check available targets**: Use `list_targets()` to see which export targets are available (some may require optional dependencies).

## See Also

- [CLI Documentation](../getting-started/quick-start.md)
- [API Documentation](./index.md)
- [Configuration Guide](../getting-started/configuration.md)
- [Parser Documentation](./parsers.md)
