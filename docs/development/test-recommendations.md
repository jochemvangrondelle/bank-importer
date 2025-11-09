# Integration and End-to-End Test Recommendations

## Overview

This document outlines recommended integration and end-to-end tests for the Bank Importer TH fullstack application. The application consists of:

- **Core**: Parsers, processors, database, translation service, export targets
- **CLI**: Command-line interface (`bank-importer` commands)
- **API**: FastAPI REST API (`/api/v1/*` endpoints)
- **Frontend**: React UI (Refine + Ant Design)

## Current Test Coverage

- ✅ Unit tests for parsers, CLI commands, API endpoints, models
- ✅ Basic frontend E2E tests (navigation, UI components)
- ❌ **Missing**: Full integration tests across components
- ❌ **Missing**: End-to-end workflows (CLI, API, Frontend)

---

## Priority 1: Critical Integration Tests

### 1.1 Full Import-Export Pipeline (Core Integration)

**Purpose**: Test the complete flow from file input to export output

**Test Scenarios**:

```python
# tests/integration/test_full_pipeline.py

@pytest.mark.integration
def test_krungsri_pdf_import_to_csv_export():
    """Test: Krungsri PDF → Parse → Database → CSV Export"""
    # 1. Import Krungsri PDF file
    # 2. Verify transactions in database
    # 3. Export to CSV
    # 4. Verify CSV contains correct transactions
    # 5. Verify export session recorded

@pytest.mark.integration
def test_scb_pdf_import_to_yaml_export():
    """Test: SCB PDF → Parse → Database → YAML Export"""
    # Similar flow for SCB bank

@pytest.mark.integration
def test_amex_csv_import_with_translation():
    """Test: Amex CSV → Parse → Translate → Database → Export"""
    # Verify Thai descriptions are translated to English

@pytest.mark.integration
def test_duplicate_detection_across_sessions():
    """Test: Import same file twice → Verify duplicates skipped"""
    # 1. Import file first time
    # 2. Import same file again
    # 3. Verify second import skips duplicates
    # 4. Verify import session tracking

@pytest.mark.integration
def test_multi_account_import_export():
    """Test: Multiple accounts → Import → Consolidated Export"""
    # 1. Import files for multiple accounts
    # 2. Export consolidated CSV
    # 3. Verify all accounts' transactions included
```

**Why Critical**: This is the core business logic - parsing bank statements and exporting transactions.

---

### 1.2 Database Integration Tests

**Purpose**: Test database operations with real SQLite database

**Test Scenarios**:

```python
# tests/integration/test_database_integration.py

@pytest.mark.integration
def test_transaction_persistence():
    """Test: Create transaction → Query → Verify persistence"""
    # Use real database, not mocks

@pytest.mark.integration
def test_import_session_lifecycle():
    """Test: Create session → Add transactions → Complete session"""
    # Verify session status transitions

@pytest.mark.integration
def test_export_session_tracking():
    """Test: Create export → Track session → Verify completion"""

@pytest.mark.integration
def test_transaction_querying_filters():
    """Test: Query transactions by account, date range, status"""
    # Verify complex queries work correctly
```

**Why Critical**: Database is the central data store - must work correctly with real data.

---

### 1.3 Parser Integration Tests

**Purpose**: Test parsers with real bank statement files

**Test Scenarios**:

```python
# tests/integration/test_parser_integration.py

@pytest.mark.integration
def test_krungsri_pdf_with_real_file():
    """Test: Parse real Krungsri PDF → Verify transactions extracted"""
    # Use actual PDF files from tests/data/

@pytest.mark.integration
def test_parser_detection_accuracy():
    """Test: Auto-detect parser for various file types"""
    # Verify correct parser selected for each bank

@pytest.mark.integration
def test_generic_csv_parser_variations():
    """Test: Parse various CSV formats → Verify flexibility"""
    # Test different CSV structures
```

**Why Critical**: Parsers are the entry point - must correctly extract transaction data.

---

## Priority 2: API Integration Tests

### 2.1 API Import-Export Workflow

**Purpose**: Test complete API workflows end-to-end

**Test Scenarios**:

```python
# tests/integration/api/test_api_import_export.py

@pytest.mark.integration
@pytest.mark.api
def test_api_import_file_sync():
    """Test: POST /import/file → Verify transactions created"""
    # 1. Upload file via API
    # 2. Verify response contains transactions
    # 3. Verify database updated
    # 4. Verify import session created

@pytest.mark.integration
@pytest.mark.api
def test_api_import_async_job():
    """Test: POST /import/files → Check job status → Verify completion"""
    # 1. Start async import job
    # 2. Poll job status
    # 3. Verify completion
    # 4. Verify transactions imported

@pytest.mark.integration
@pytest.mark.api
def test_api_export_download():
    """Test: POST /export → GET /export/sessions/{id}/download"""
    # 1. Create export job
    # 2. Wait for completion
    # 3. Download export file
    # 4. Verify file content

@pytest.mark.integration
@pytest.mark.api
def test_api_transaction_filtering():
    """Test: GET /transactions with filters"""
    # Test query parameters: account, date range, status
```

**Why Critical**: API is the primary interface for frontend and external integrations.

---

### 2.2 API Authentication & Authorization

**Purpose**: Test security endpoints

**Test Scenarios**:

```python
# tests/integration/api/test_api_auth.py

@pytest.mark.integration
@pytest.mark.api
def test_api_authentication_flow():
    """Test: Login → Get token → Access protected endpoints"""
    # Verify JWT authentication works

@pytest.mark.integration
@pytest.mark.api
def test_api_unauthenticated_access():
    """Test: Access protected endpoints without auth → Verify 401"""
```

**Why Critical**: Security is essential - must verify authentication works correctly.

---

### 2.3 API Configuration Management

**Purpose**: Test config CRUD operations

**Test Scenarios**:

```python
# tests/integration/api/test_api_config.py

@pytest.mark.integration
@pytest.mark.api
def test_api_account_crud():
    """Test: Create → Read → Update → Delete account"""
    # Verify account config persistence

@pytest.mark.integration
@pytest.mark.api
def test_api_target_configuration():
    """Test: Configure export targets via API"""
```

---

## Priority 3: CLI Integration Tests

### 3.1 CLI Import-Export Workflow

**Purpose**: Test CLI commands with real files and database

**Test Scenarios**:

```python
# tests/integration/cli/test_cli_integration.py

@pytest.mark.integration
@pytest.mark.cli
def test_cli_import_files_command():
    """Test: `bank-importer import-files` → Verify transactions imported"""
    # Run actual CLI command, verify results

@pytest.mark.integration
@pytest.mark.cli
def test_cli_export_multi_command():
    """Test: `bank-importer export-multi` → Verify files exported"""
    # Run CLI command, verify output files created

@pytest.mark.integration
@pytest.mark.cli
def test_cli_status_command():
    """Test: `bank-importer status` → Verify correct status displayed"""
    # Verify status reflects actual database state

@pytest.mark.integration
@pytest.mark.cli
def test_cli_full_workflow():
    """Test: Import → Status → Export → Verify consistency"""
    # Complete workflow via CLI
```

**Why Critical**: CLI is a primary user interface - must work correctly end-to-end.

---

## Priority 4: Frontend-Backend E2E Tests

### 4.1 Complete User Workflows

**Purpose**: Test full user journeys through the UI

**Test Scenarios**:

```typescript
// src/frontend/tests/e2e/full-workflow.spec.ts

test("Complete import workflow via UI", async ({ page }) => {
  // 1. Login
  // 2. Navigate to Import Wizard
  // 3. Upload bank statement file
  // 4. Select parser
  // 5. Configure account
  // 6. Parse file
  // 7. Review transactions
  // 8. Export to CSV
  // 9. Download export file
  // 10. Verify file downloaded correctly
});

test("Status dashboard reflects actual data", async ({ page }) => {
  // 1. Import transactions via API/CLI
  // 2. Navigate to Status page
  // 3. Verify statistics displayed correctly
  // 4. Verify account status accurate
});

test("Configuration management via UI", async ({ page }) => {
  // 1. Create account via UI
  // 2. Update account config
  // 3. Delete account
  // 4. Verify changes persisted
});
```

**Why Critical**: Frontend is the user-facing interface - must work correctly with backend.

---

### 4.2 API-Frontend Integration

**Purpose**: Test frontend correctly calls API endpoints

**Test Scenarios**:

```typescript
// src/frontend/tests/e2e/api-integration.spec.ts

test("Frontend API calls work correctly", async ({ page }) => {
  // 1. Monitor network requests
  // 2. Perform UI actions
  // 3. Verify correct API endpoints called
  // 4. Verify request/response handling
});
```

---

## Priority 5: Cross-Component Integration

### 5.1 CLI-API Consistency

**Purpose**: Verify CLI and API produce same results

**Test Scenarios**:

```python
# tests/integration/test_cli_api_consistency.py

@pytest.mark.integration
def test_cli_and_api_same_import_results():
    """Test: Import via CLI vs API → Verify same transactions"""
    # 1. Import file via CLI
    # 2. Import same file via API
    # 3. Verify identical transactions created

@pytest.mark.integration
def test_cli_and_api_same_export_results():
    """Test: Export via CLI vs API → Verify same output"""
    # Compare export files from CLI and API
```

**Why Critical**: Users may use both interfaces - must be consistent.

---

### 5.2 Library Function Integration

**Purpose**: Test `bank_importer.library` functions used by CLI/API

**Test Scenarios**:

```python
# tests/integration/test_library_integration.py

@pytest.mark.integration
def test_library_import_file():
    """Test: library.import_file() → Verify complete workflow"""
    # Test library function directly

@pytest.mark.integration
def test_library_export_transactions():
    """Test: library.export_transactions() → Verify export"""
```

**Why Critical**: Library functions are shared by CLI and API - must work correctly.

---

## Priority 6: Error Handling & Edge Cases

### 6.1 Error Scenarios

**Test Scenarios**:

```python
# tests/integration/test_error_handling.py

@pytest.mark.integration
def test_invalid_file_handling():
    """Test: Invalid file → Verify graceful error handling"""

@pytest.mark.integration
def test_missing_config_handling():
    """Test: Missing account config → Verify appropriate error"""

@pytest.mark.integration
def test_database_error_recovery():
    """Test: Database errors → Verify proper error messages"""
```

---

### 6.2 Edge Cases

**Test Scenarios**:

```python
# tests/integration/test_edge_cases.py

@pytest.mark.integration
def test_empty_file_handling():
    """Test: Empty statement file → Verify no errors"""

@pytest.mark.integration
def test_large_file_handling():
    """Test: Large statement file → Verify performance acceptable"""

@pytest.mark.integration
def test_special_characters_in_transactions():
    """Test: Special characters in descriptions → Verify encoding"""
```

---

## Test Infrastructure Recommendations

### Test Data Management

1. **Create test fixtures** for bank statement files:

   - `tests/fixtures/bank_statements/` - Real statement files
   - `tests/fixtures/configs/` - Test configuration files

2. **Database fixtures**:

   - Use temporary databases for each test
   - Clean up after each test

3. **Test isolation**:
   - Each integration test should be independent
   - Use pytest fixtures for setup/teardown

### Test Execution

1. **Mark tests appropriately**:

   ```python
   @pytest.mark.integration
   @pytest.mark.api
   @pytest.mark.cli
   @pytest.mark.slow  # For long-running tests
   ```

2. **Separate test suites**:

   ```bash
   # Run only integration tests
   pytest -m integration

   # Run only API integration tests
   pytest -m "integration and api"

   # Run only fast tests
   pytest -m "not slow"
   ```

3. **CI/CD integration**:
   - Run unit tests on every commit
   - Run integration tests on PRs
   - Run full E2E tests on main branch

### Docker-based Testing

Consider using Docker Compose for integration tests:

```yaml
# tests/docker-compose.test.yml
services:
  test-db:
    image: sqlite:latest # Or use PostgreSQL for more realistic testing
    # ...

  test-api:
    build: .
    depends_on: [test-db]
    # ...
```

---

## Implementation Priority

1. **Phase 1** (Critical): Full import-export pipeline tests
2. **Phase 2** (High): API integration tests
3. **Phase 3** (High): CLI integration tests
4. **Phase 4** (Medium): Frontend-Backend E2E tests
5. **Phase 5** (Medium): Cross-component consistency tests
6. **Phase 6** (Low): Error handling and edge cases

---

## Metrics & Coverage Goals

- **Integration test coverage**: Target 80%+ of critical paths
- **E2E test coverage**: All major user workflows
- **Test execution time**: Keep integration tests under 5 minutes
- **Test reliability**: 99%+ pass rate (flaky tests are worse than no tests)

---

## Notes

- Start with **Priority 1** tests - they validate core functionality
- Use **real files and databases** for integration tests (not mocks)
- Keep tests **fast and isolated** - use fixtures for setup
- **Document test data** - explain what each test file represents
- **Maintain test data** - update when bank statement formats change
