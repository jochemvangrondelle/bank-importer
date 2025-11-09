import { Page } from "@playwright/test";
import { setupApiMocks } from "./api-mocks";

/**
 * Helper function to navigate to home page (no auth needed).
 * Uses mocked API by default unless useRealApi is true.
 */
export async function login(
  page: Page,
  password: string = "admin",
  useRealApi: boolean = false,
): Promise<void> {
  // Setup API mocks if not using real API
  if (!useRealApi) {
    await setupApiMocks(page);
  }

  // Navigate directly to home (no login required)
  await page.goto("/home");
  await page.waitForLoadState("networkidle");
}

/**
 * Setup all API mocks for a test.
 * Call this in beforeEach if you want all tests to use mocks.
 */
export async function setupMocksForTest(
  page: Page,
  config?: Parameters<typeof setupApiMocks>[1],
): Promise<void> {
  await setupApiMocks(page, config);
}
