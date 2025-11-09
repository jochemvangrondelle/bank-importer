# Integration Tests

This directory contains integration tests for the full import-export pipeline.

## Structure

Integration tests are organized by parser, with each parser having its own test file:

- `base.py` - Base class with common test functionality
- `test_krungsri_pdf.py` - Krungsri PDF parser integration tests
- `test_krungsri_text.py` - Krungsri text parser integration tests
- `test_scb_pdf.py` - SCB PDF parser integration tests
- `test_amex_th_csv.py` - Amex Thailand CSV parser integration tests
- `test_generic_csv.py` - Generic CSV parser integration tests

## Adding a New Parser Integration Test

To add integration tests for a new parser:

1. Create a new test file: `test_<parser_name>.py`
2. Inherit from `BaseParserIntegrationTest`
3. Implement required properties:
   - `parser_name` - The parser name (e.g., "my_parser")
   - `test_file_name` - Test file name in `tests/data/`
4. Optionally override:
   - `create_account_config()` - For parser-specific account config
   - `validate_imported_transactions()` - For parser-specific validations

Example:

```python
from .base import BaseParserIntegrationTest

class TestMyParserIntegration(BaseParserIntegrationTest):
    @property
    def parser_name(self) -> str:
        return "my_parser"

    @property
    def test_file_name(self) -> str:
        return "my_parser_sample.pdf"
```

## Running Integration Tests

### Run all integration tests:
```bash
pytest tests/integration/ -v -m integration
```

### Run integration tests with coverage:
```bash
pytest tests/integration/ -v -m integration --cov=src/bank_importer --cov-report=term-missing
```

### Run integration tests for a specific parser:
```bash
pytest tests/integration/test_krungsri_pdf.py -v
```

### Using poethepoet:
```bash
# Run integration tests
uv run poe test-integration

# Run with coverage
uv run poe test-integration-cov
```

## Test Coverage

Integration tests track coverage separately from unit tests:

- **Unit test coverage**: `pytest tests/ -m 'not integration' --cov=...`
- **Integration test coverage**: `pytest tests/integration/ -m integration --cov=...`

This allows you to:
1. See which code paths are covered by integration tests vs unit tests
2. Ensure critical paths are tested end-to-end
3. Identify gaps in integration test coverage

## What Integration Tests Cover

Each parser integration test includes:

1. **Full Import-Export Pipeline (CSV)**: Import file → Database → Export CSV → Validate
2. **Full Import-Export Pipeline (YAML)**: Import file → Database → Export YAML → Validate
3. **Duplicate Detection**: Import same file twice → Verify duplicates skipped
4. **Import Session Tracking**: Verify import sessions are properly tracked in database

## Test Data

Test files are located in `tests/data/`:
- `krungsri_valid.pdf` - Krungsri PDF test file
- `krungsri_valid.txt` - Krungsri text test file
- `scb_valid.pdf` - SCB PDF test file
- `amex_sample.csv` - Amex CSV test file
- `generic_valid.csv` - Generic CSV test file

## Fixtures

Integration tests use fixtures from `conftest.py`:
- `integration_db_manager` - Temporary database for each test
- `integration_config_manager` - Temporary config for each test
- `integration_processor` - Processor instance with test database/config
- `integration_target_manager` - Target manager for exports
- `test_data_dir` - Path to test data directory
- `output_dir` - Temporary output directory

## Notes

- Integration tests use **real databases** (SQLite) - not mocks
- Each test is **isolated** - uses temporary database and config
- Tests are **slower** than unit tests - they exercise the full pipeline
- Tests require **test data files** to exist in `tests/data/`
