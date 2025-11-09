# Package Restructuring Plan

## Goal

Separate the package into three independent groups:

1. **Core/Library** - Base functionality (models, interfaces, processors, etc.)
2. **CLI** - Command-line interface (optional)
3. **API** - FastAPI REST API (optional)

Users can install:

- `bank-importer` or `bank-importer[core]` - Just the library
- `bank-importer[cli]` - Library + CLI
- `bank-importer[api]` - Library + API
- `bank-importer[cli,api]` - Everything

## Current Structure

```
src/bank_importer/
├── __init__.py
├── __main__.py
├── cli_main.py              # CLI entry point
├── cli_parameters.py        # CLI-specific
├── cli_utils.py             # CLI-specific
├── logging_config.py        # Shared (used by CLI and core)
├── version.py               # Shared
├── config.py                # Core
├── config_resolver.py       # Core
├── processor.py             # Core
├── parser_detector.py       # Core
├── target_manager.py        # Core
├── translation_service.py   # Core
├── models/                  # Core
├── interfaces/              # Core
├── banks/                   # Core
├── targets/                 # Core
├── translation_terms/       # Core
├── cli/                     # CLI package
│   ├── commands/
│   └── ...
└── api/                     # API package
    ├── routers/
    ├── schemas/
    └── ...
```

## Proposed Structure

```
src/bank_importer/
├── __init__.py              # Core exports only
├── __main__.py              # Optional CLI entry point (if CLI installed)
├── models/                  # Core
├── interfaces/              # Core
├── banks/                   # Core
├── targets/                 # Core
├── translation_terms/       # Core
├── config.py                # Core
├── config_resolver.py       # Core
├── processor.py             # Core
├── parser_detector.py       # Core
├── target_manager.py        # Core
├── translation_service.py   # Core
├── logging_config.py        # Core (used by CLI/API but part of core)
├── version.py               # Core
├── cli/                     # CLI package (optional)
│   ├── __init__.py
│   ├── main.py              # CLI entry point (moved from cli_main.py)
│   ├── parameters.py        # CLI-specific (moved from cli_parameters.py)
│   ├── utils.py             # CLI-specific (moved from cli_utils.py)
│   └── commands/
│       └── ...
└── api/                     # API package (optional)
    ├── __init__.py
    ├── main.py
    ├── routers/
    ├── schemas/
    └── ...
```

## Dependency Groups

### Core Dependencies (always installed)

- sqlmodel
- pydantic
- toml
- pdfplumber
- pyyaml
- pytz
- deep-translator
- google-trans
- googletrans
- firefly-iii-api-client
- uv-dynamic-versioning

### CLI Dependencies (only with [cli])

- typer
- rich

### API Dependencies (only with [api])

- fastapi
- uvicorn[standard]
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart

## Implementation Steps

### Step 1: Update pyproject.toml

1. Move CLI dependencies to `[project.optional-dependencies.cli]`
2. Move API dependencies to `[project.optional-dependencies.api]`
3. Keep core dependencies in `[project.dependencies]`
4. Update `[project.scripts]` to point to `bank_importer.cli.main:app`
5. Add optional entry points for API

### Step 2: Reorganize CLI Package

1. Move `cli_main.py` → `cli/main.py`
2. Move `cli_parameters.py` → `cli/parameters.py`
3. Move `cli_utils.py` → `cli/utils.py`
4. Update all imports in CLI commands
5. Update `__main__.py` to conditionally import CLI

### Step 3: Ensure API Package Independence

1. Verify API imports only from core
2. Add conditional imports for API-only dependencies
3. Update API entry points

### Step 4: Update Core Package

1. Ensure `__init__.py` only exports core functionality
2. No CLI or API imports in core
3. Keep shared utilities (logging_config, version) in core

### Step 5: Update Tests

1. Update all test imports
2. Ensure tests can run with just core installed
3. Add conditional test markers for CLI/API tests

### Step 6: Update Documentation

1. Update README.md with installation instructions
2. Update API documentation
3. Update any other docs

### Step 7: Verify

1. Install with just core - verify imports work
2. Install with CLI - verify CLI works
3. Install with API - verify API works
4. Install with both - verify everything works
5. Run all tests

## Import Strategy

### Core Package

- All core modules import from `bank_importer.*` (same package)
- No conditional imports needed

### CLI Package

- CLI imports from core: `from bank_importer import ...`
- CLI-specific code in `cli/` package
- Conditional imports for CLI-only dependencies (typer, rich)

### API Package

- API imports from core: `from bank_importer import ...`
- API-specific code in `api/` package
- Conditional imports for API-only dependencies (fastapi, etc.)

## Entry Points

### CLI Entry Point

```python
# pyproject.toml
[project.scripts]
bank-importer = "bank_importer.cli.main:app"
```

### API Entry Point (optional)

```python
# Can be run via: python -m bank_importer.api.run
# Or: uvicorn bank_importer.api.main:app
```

### Core Library Usage

```python
from bank_importer import ConfigManager, Processor
# No CLI or API dependencies needed
```

## Testing Strategy

1. **Core Tests**: Should work with just core installed
2. **CLI Tests**: Mark with `@pytest.mark.cli`, skip if CLI not installed
3. **API Tests**: Mark with `@pytest.mark.api`, skip if API not installed

## Migration Notes

- All existing imports from `bank_importer.*` continue to work for core
- CLI imports change from `bank_importer.cli_main` to `bank_importer.cli.main`
- API imports remain the same
- Tests need to be updated to new import paths
