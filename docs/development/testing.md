# Frontend Testing Documentation

This document covers frontend testing setup, coverage, and best practices.

## Test Coverage

### Test Files

#### 1. `auth.spec.ts` - Authentication Tests (9 tests)

- Login page display
- Password field validation
- Invalid password handling
- Successful login redirect
- Password configuration status check
- Default password hint display
- Loading state during password check
- Password input handling
- Submit button loading state

#### 2. `home.spec.ts` - Home Page Tests (6 tests)

- Home page content display
- Quick links section
- Navigation to import wizard
- Navigation to status page
- Quick links navigation
- Status information display

#### 3. `status.spec.ts` - Status Page Tests (12 tests)

- Status page display
- Summary statistics display
- Account details table
- Loading state handling
- Table columns display
- API error handling
- Sortable columns
- Pagination controls
- Date formatting
- Account details in table rows
- Summary statistics display
- Empty state handling

#### 4. `import-wizard.spec.ts` - Import Wizard Tests (19 tests)

- Import wizard page display
- Wizard steps visibility
- File upload component
- Parser selection
- Account details form
- File selection handling
- Parse button display
- Transaction table area
- Export buttons
- Step navigation
- PDF viewer area
- Form fields for account details
- Parser selection interaction
- Password input display
- Step indicators
- Form validation
- Error messages on API failure
- Transaction columns display
- Export functionality

#### 5. `navigation.spec.ts` - Navigation Tests (5 tests)

- Home page navigation
- Page-to-page navigation
- Sidebar menu navigation
- 404 error handling
- Authentication redirect

#### 6. `pdf-viewer.spec.ts` - PDF Viewer Component Tests (4 tests)

- PDF viewer rendering in import wizard
- PDF display when file uploaded
- PDF loading state
- PDF error state

#### 7. `app.spec.ts` - App Integration Tests (6 tests)

- Authentication flow
- Authentication persistence across navigation
- Logout functionality
- Sidebar navigation display
- 404 error handling
- Network error handling

**Total: 61 test cases** covering all frontend functionality.

## API Mocking

### Overview

Frontend tests use **API mocking by default** to run without requiring a real backend API. This makes tests:

- ✅ Faster (no network calls)
- ✅ More reliable (no dependency on backend state)
- ✅ Isolated (tests don't affect each other)
- ✅ CI/CD friendly (no need to start backend services)

### Auto-Generated Mocks from OpenAPI

Tests use **MSW (Mock Service Worker)** with auto-generated handlers from the OpenAPI specification (`api/openapi.yaml`). This ensures:

- Mocks stay in sync with API schema automatically
- No manual maintenance when API changes
- All endpoints automatically mocked

### Mock Setup

Most test files automatically set up API mocks in their `beforeEach` hooks:

```typescript
test.beforeEach(async ({ page }) => {
  await setupMocksForTest(page); // Sets up all API mocks
  await login(page);
  // ... rest of setup
});
```

### Customizing Mocks

To override specific endpoints in a test:

```typescript
import { server } from "./msw-handlers";
import { rest } from "msw";

test("handles custom response", async ({ page }) => {
  // Override specific endpoint
  server.use(
    rest.get("*/api/v1/status", (_req, res, ctx) => {
      return res(
        ctx.status(200),
        ctx.json({
          accounts: [
            /* custom data */
          ],
        })
      );
    })
  );

  // Your test...
});
```

### Mocked Endpoints

- **Authentication** (`/auth/login`, `/auth/status`)
- **Status** (`/status`)
- **Parsers** (`/parsers`)
- **Parse** (`/parse/file`)
- **Export** (`/parse/file/export`)

See `tests/e2e/api-mocks.ts` and `tests/e2e/openapi-to-msw.ts` for implementation details.

## Running Tests

### Prerequisites

```bash
cd src/frontend
npm install
```

### Run All Tests

```bash
npm run test:e2e
```

### Run Tests in UI Mode

```bash
npm run test:e2e:ui
```

### Run Tests in Headed Mode

```bash
npm run test:e2e:headed
```

### Run Tests in Debug Mode

```bash
npm run test:e2e:debug
```

### Run Specific Test File

```bash
npx playwright test tests/e2e/auth.spec.ts
```

## Test Configuration

Tests are configured in `playwright.config.ts`:

- Base URL: `http://localhost:3000`
- Test directory: `./tests/e2e`
- Browsers: Chromium, Firefox, WebKit
- Retries: 2 on CI, 0 locally
- Screenshots: On failure
- Trace: On first retry
- MSW setup: Automatic via `setupFiles`

## Test Helpers

### `helpers.ts`

Provides utility functions for tests:

- `login(page, password, useRealApi)` - Helper to login with a password
- `isAuthenticated(page)` - Check if user is authenticated
- `setupMocksForTest(page, config)` - Setup all API mocks

## CI/CD Integration

Tests should be run in CI/CD pipelines:

```yaml
- name: Run E2E Tests
  run: |
    cd src/frontend
    npm ci
    npm run test:e2e
```

## Best Practices

1. **Use Mocks by Default**: All tests use mocked API unless explicitly testing real API integration
2. **Test Isolation**: Each test should be independent and not rely on other tests
3. **Clear Test Names**: Use descriptive test names that explain what is being tested
4. **Wait for Elements**: Always wait for elements to be visible before interacting
5. **Error Handling**: Test both success and error scenarios
6. **Accessibility**: Test keyboard navigation and screen reader compatibility

## Troubleshooting

### Tests Fail with Network Errors

Ensure MSW is properly set up. Check `tests/e2e/msw-setup.ts` is loaded in `playwright.config.ts`.

### Tests Timeout

Increase timeout in test or check if dev server is running:

```typescript
test("my test", async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // ...
});
```

### Mocks Not Working

Verify OpenAPI spec path is correct in `openapi-to-msw.ts`:

```typescript
const specPath = join(__dirname, "../../../api/openapi.yaml");
```

## Future Enhancements

- [ ] Add unit tests for utility functions
- [ ] Add component tests with React Testing Library
- [ ] Add visual regression tests
- [ ] Add performance tests
- [ ] Add accessibility tests
- [ ] Enhance mock data generation with json-schema-faker
