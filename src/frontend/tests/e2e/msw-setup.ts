/**
 * MSW setup for Playwright tests.
 *
 * This file configures MSW to intercept API calls during tests.
 */

import { beforeAll, afterEach, afterAll } from "@playwright/test";
import { server } from "./msw-handlers";

// Start server before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: "warn" });
});

// Reset handlers after each test (for test isolation)
afterEach(() => {
  server.resetHandlers();
});

// Clean up after all tests
afterAll(() => {
  server.close();
});
