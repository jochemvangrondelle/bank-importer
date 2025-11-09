# Architecture and Import Boundaries

This document describes the architectural boundaries and import rules for the `bank-importer` package.

## Package Structure

The package is organized into three independent layers:

```
bank_importer/
├── (core)           # Core library - models, processors, parsers, targets
├── cli/             # CLI layer - command-line interface
└── api/             # API layer - FastAPI REST API
```

## Import Rules

### Core Package

**Location**: All modules in `src/bank_importer/` except `cli/` and `api/`

**Rules**:

- ✅ Can import from standard library and third-party packages
- ✅ Can import from other core modules
- ❌ **MUST NOT** import from `bank_importer.cli`
- ❌ **MUST NOT** import from `bank_importer.api`

**Rationale**: Core must remain independent and reusable without CLI or API dependencies.

### CLI Package

**Location**: `src/bank_importer/cli/`

**Rules**:

- ✅ Can import from standard library and third-party packages (typer, rich)
- ✅ Can import from core: `from bank_importer import ...`
- ✅ Can import from other CLI modules: `from bank_importer.cli import ...`
- ✅ **SHOULD** use library functions from `bank_importer.library` where possible
- ❌ **MUST NOT** import from `bank_importer.api`

**Rationale**: CLI is a thin layer that orchestrates core functionality. It should reuse library functions to avoid code duplication.

### API Package

**Location**: `src/bank_importer/api/`

**Rules**:

- ✅ Can import from standard library and third-party packages (fastapi, etc.)
- ✅ Can import from core: `from bank_importer import ...`
- ✅ Can import from other API modules: `from bank_importer.api import ...`
- ✅ **SHOULD** use library functions from `bank_importer.library` where possible
- ❌ **MUST NOT** import from `bank_importer.cli`

**Rationale**: API is a thin layer that orchestrates core functionality. It should reuse library functions to avoid code duplication.

## Enforcement

### Import Linter

We use [import-linter](https://github.com/seddonym/import-linter) to enforce these rules. Configuration is in `.importlinter`.

Run checks:

```bash
uv run lintlinter .importlinter
```

### Architectural Tests

Tests in `tests/test_architecture.py` verify import boundaries at runtime:

```bash
uv run pytest tests/test_architecture.py -v
```

### Ruff Configuration

Ruff is configured to enforce import style and detect potential issues:

```bash
uv run ruff check src/ --select I
```

## Library Functions

The `bank_importer.library` module provides unified functions that should be used by both CLI and API:

- `parse_file()` - Parse a file without database operations
- `import_file()` - Parse and store in database
- `export_transactions()` - Export transactions to targets
- `detect_parser()` - Auto-detect parser for a file
- `get_parser()` - Get parser instance by name
- `list_parsers()` - List all available parsers
- `list_targets()` - List all available targets

### Example: Using Library Functions

**❌ Bad - Duplicating logic in CLI:**

```python
# In cli/commands/import_files.py
def import_files(...):
    # Directly using Processor, duplicating logic
    processor = Processor()
    processor.process_account(...)
```

**✅ Good - Using library functions:**

```python
# In cli/commands/import_files.py
from bank_importer.library import import_file

def import_files(...):
    # Reusing library function
    result = import_file(
        file_path,
        account_config=account_config,
        config_manager=config,
        db_manager=db,
    )
```

## Benefits

1. **Reusability**: Core logic is written once and reused by CLI and API
2. **Consistency**: Same behavior across CLI, API, and library usage
3. **Testability**: Core functions can be tested independently
4. **Maintainability**: Changes to core logic automatically benefit all interfaces
5. **No Circular Dependencies**: Clear dependency hierarchy prevents import cycles

## Migration Guide

If you find code duplication between CLI and API:

1. **Identify the common logic** - What do both CLI and API do the same way?
2. **Move to library** - Create or use a function in `bank_importer.library`
3. **Update CLI** - Replace CLI implementation with library function call
4. **Update API** - Replace API implementation with library function call
5. **Run tests** - Verify all tests still pass
6. **Check imports** - Run `uv run lintlinter .importlinter` to verify boundaries

## See Also

- [Library API Documentation](../api/library.md) - Complete library function reference
- [Package Structure](../getting-started/installation.md) - Installation and structure overview
