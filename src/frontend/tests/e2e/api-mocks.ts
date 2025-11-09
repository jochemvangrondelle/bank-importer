import { Page } from "@playwright/test";

/**
 * API mock responses for testing without a real backend.
 */

export interface MockConfig {
  mockStatus?: boolean;
  mockParsers?: boolean;
  mockParse?: boolean;
}

/**
 * Setup API mocks for all endpoints.
 */
export async function setupApiMocks(
  page: Page,
  config: MockConfig = {}
): Promise<void> {
  const { mockStatus = true, mockParsers = true, mockParse = true } = config;

  // Mock status endpoint
  if (mockStatus) {
    await page.route("**/api/v1/status", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          accounts: [
            {
              account_name: "Test Account",
              bank_name: "Test Bank",
              account_number: "1234567890",
              parser: "krungsri",
              transaction_count: 42,
              last_import: new Date().toISOString(),
              date_range: {
                min_date: "2024-01-01T00:00:00Z",
                max_date: "2024-12-31T23:59:59Z",
              },
            },
            {
              account_name: "Another Account",
              bank_name: "Another Bank",
              account_number: "0987654321",
              parser: "scb",
              transaction_count: 15,
              last_import: null,
              date_range: {
                min_date: null,
                max_date: null,
              },
            },
          ],
          summary: {
            total_accounts: 2,
            total_transactions: 57,
            total_import_sessions: 5,
            completed_sessions: 4,
            failed_sessions: 1,
          },
          import_sessions: [],
        }),
      });
    });
  }

  // Mock parsers endpoint
  if (mockParsers) {
    await page.route("**/api/v1/parsers", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          parsers: [
            {
              name: "krungsri",
              bank_type: "Krungsri",
              supported_extensions: [".pdf"],
              description: "Krungsri Bank parser",
            },
            {
              name: "scb",
              bank_type: "SCB",
              supported_extensions: [".pdf", ".csv"],
              description: "Siam Commercial Bank parser",
            },
          ],
        }),
      });
    });
  }

  // Mock parse endpoint
  if (mockParse) {
    await page.route("**/api/v1/parse/file", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          transactions: [
            {
              id: 1,
              date: "2024-01-15",
              description: "Test Transaction 1",
              translated_description: "Test Transaction 1",
              amount: 1000.0,
              balance: 5000.0,
              transaction_type: "debit",
              currency: "THB",
              account_number: "1234567890",
            },
            {
              id: 2,
              date: "2024-01-16",
              description: "Test Transaction 2",
              translated_description: "Test Transaction 2",
              amount: -500.0,
              balance: 4500.0,
              transaction_type: "credit",
              currency: "THB",
              account_number: "1234567890",
            },
          ],
          parser_name: "krungsri",
          total_transactions: 2,
        }),
      });
    });
  }

  // Mock export endpoint
  await page.route("**/api/v1/parse/file/export", (route) => {
    route.fulfill({
      status: 200,
      contentType: "text/csv",
      headers: {
        "Content-Disposition": 'attachment; filename="export.csv"',
      },
      body: "date,description,amount\n2024-01-15,Test Transaction 1,1000.0",
    });
  });
}

/**
 * Setup API mocks for error scenarios.
 */
export async function setupErrorMocks(page: Page): Promise<void> {
  await page.route("**/api/v1/**", (route) => {
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({
        detail: "Internal server error",
      }),
    });
  });
}

/**
 * Setup API mocks for network failures.
 */
export async function setupNetworkFailureMocks(page: Page): Promise<void> {
  await page.route("**/api/v1/**", (route) => {
    route.abort();
  });
}

/**
 * Clear all API mocks.
 */
export async function clearApiMocks(page: Page): Promise<void> {
  await page.unroute("**/api/v1/**");
}
