# API Reference

This section contains the complete API documentation for Bank Importer Thailand, automatically generated from Python docstrings.

## Overview

The Bank Importer Thailand API is organized into several main components:

- **Core**: Configuration management, processing pipeline, and database operations
- **Interfaces**: Abstract base classes for parsers and export targets
- **Models**: Data models for transactions, accounts, and sessions
- **Services**: Translation service and configuration resolution
- **Parsers**: Bank-specific and generic parsers for various file formats
- **Targets**: Export targets for CSV, YAML, and Firefly-III

## Quick Navigation

### Core Components

- [`ConfigManager`](config.md) - Configuration file management
- [`Processor`](processor.md) - Main processing pipeline
- [`DatabaseManager`](database.md) - Database operations

### Interfaces

- [`Parser`](parser.md) - Base class for bank statement parsers
- [`Target`](target.md) - Base class for export targets

### Models

- [`Transaction`](transaction.md) - Transaction data model
- [`BankAccount`](bank-account.md) - Bank account model

### Services

- [`TranslationService`](translation.md) - Translation service for transaction descriptions
- [`ConfigResolver`](config-resolver.md) - Environment variable and file-based secret resolution

## Usage Example

```python
from bank_importer import ConfigManager, Processor, DatabaseManager

# Initialize components
config_manager = ConfigManager("config.toml")
db_manager = DatabaseManager(config_manager.get_database_url())
processor = Processor(config_manager, db_manager)

# Process all accounts
for result in processor.process_accounts():
    print(f"Processed {result['account_name']}: {result['transaction_count']} transactions")
```

## Documentation Style

All API documentation is generated from Google-style docstrings in the source code. Each module, class, and function includes:

- Description of purpose and functionality
- Parameter documentation
- Return value documentation
- Usage examples where applicable
- Type hints for better IDE support
