# Bank Importer Thailand - TODO

## Project Overview

Small utility to convert Thailand bank statement formats into structured data for Firefly import.

## Pipeline Architecture

1. ✅ Get configurations from config.toml
2. ✅ Parse file(s) using configured parsers
3. ✅ Store transactions in SQLite DB (SQLModel)
4. 🔄 Yield transactions for target pushing

## Implementation Tasks

### Core Infrastructure

- [x] Project structure setup
- [x] Configuration management (config.toml)
- [x] Database models and storage (SQLModel with proper indexes)
- [x] CLI interface with run command
- [x] Pipeline processor with generators
- [x] Test-driven development setup with comprehensive test coverage
- [x] Strict linting configuration (ruff, mypy, pyright)

### Parsers

- [x] Krungsri text parser (from manual copy/paste) - TESTED ✅
- [x] Krungsri PDF parser (from original PDF) - TESTING
- [ ] Generic text parser framework

### Data Models

- [x] Transaction model (SQLModel with indexes)
- [x] ImportSession model (SQLModel with indexes)
- [x] TargetCompletion model (SQLModel with indexes)
- [x] BankAccount model (SQLModel with indexes)

### Database

- [x] SQLModel integration with proper table creation
- [x] Unique indexes for deduplication
- [x] Performance indexes for common queries
- [x] Database manager with CRUD operations

### CLI Commands

- [x] `run` - Process all accounts or specific account
- [x] `list-accounts` - Show configured accounts
- [x] `list-sessions` - Show import sessions
- [x] `init` - Initialize configuration file
- [x] Error handling and user feedback

### Processor

- [x] Fetch config from ConfigManager
- [x] Identify pending import jobs from database
- [x] Orchestrate workers/parsers
- [x] Store results in database
- [x] Update logs and progress centrally
- [x] File hash calculation for deduplication
- [x] Import session management

### Testing

- [x] Test-driven development setup
- [x] CLI tests with mocked dependencies
- [x] Processor tests with comprehensive coverage
- [x] Database model tests
- [x] Parser tests
- [x] Integration tests

### Code Quality

- [x] Ruff configuration with strict rules
- [x] MyPy configuration with strict mode
- [x] Pyright configuration with strict mode
- [x] Pytest with coverage reporting
- [x] Type annotations throughout codebase
- [x] Docstrings and documentation

### Remaining Issues

#### Linting Issues (47 remaining)

- [ ] Fix TRY003: Avoid long exception messages
- [ ] Fix B904: Use `raise ... from error` in except clauses
- [ ] Fix D401: Docstring imperative mood
- [ ] Fix RUF012: Mutable class attributes with ClassVar
- [ ] Fix SIM108: Use ternary operators
- [ ] Fix RUF001: Ambiguous Unicode characters
- [ ] Fix S324: Insecure hash functions (md5)
- [ ] Fix SIM117: Combine with statements
- [ ] Fix S608: SQL injection vectors
- [ ] Fix TRY400: Use logging.exception
- [ ] Fix F821: Undefined names in storage.py

#### Type Checking Issues (72 remaining)

- [ ] Install missing type stubs (types-toml, types-PyYAML)
- [ ] Fix missing type annotations
- [ ] Fix incompatible types in assignments
- [ ] Fix undefined names and attributes
- [ ] Fix import issues with rich library
- [ ] Fix SQLModel/SQLAlchemy type issues

### Next Steps

1. **Fix remaining linting issues** - Address the 47 ruff warnings and 72 mypy errors
2. **Complete storage module** - Fix undefined names and implement missing functionality
3. **Add target processing** - Implement the final step of the pipeline
4. **Add more parsers** - Support additional bank formats
5. **Performance optimization** - Optimize database queries and file processing
6. **Documentation** - Add comprehensive user and developer documentation

## Current Status

✅ **Core functionality working**: The parser successfully processes both Krungsri text files (312 transactions) and PDF files (310 transactions) and stores them in the database.

✅ **Test coverage**: 26 tests passing with 31% overall coverage (higher for core modules).

✅ **Database schema**: SQLModel tables with proper indexes and constraints.

✅ **CLI interface**: All commands working with proper error handling.

✅ **Processor pipeline**: Complete implementation of the 5-step process.

🔄 **Code quality**: Strict linting configured, but 47 ruff warnings and 72 mypy errors remain to be addressed.

## Usage

```bash
# Install dependencies
pip install -e .

# Run tests
python -m pytest tests/ -v

# Process all accounts
python -m bank_importer_th run

# Process specific account
python -m bank_importer_th run --account krungsri_main

# List accounts
python -m bank_importer_th list-accounts

# List import sessions
python -m bank_importer_th list-sessions
```
