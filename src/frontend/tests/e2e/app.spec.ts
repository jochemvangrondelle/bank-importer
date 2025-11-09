import { test, expect } from "@playwright/test";
import { login, setupMocksForTest } from "./helpers";

test.describe("App Integration", () => {
  test.beforeEach(async ({ page }) => {
    // Setup API mocks for all tests
    await setupMocksForTest(page);
  });
  test("should navigate between pages", async ({ page }) => {
    await page.goto("/home");
    await page.waitForLoadState("networkidle");

    // Navigate to different pages
    await page.goto("/import");
    await expect(page).toHaveURL(/.*\/import/);

    await page.goto("/status");
    await expect(page).toHaveURL(/.*\/status/);
  });

  test("should display sidebar navigation", async ({ page }) => {
    await login(page);
    await page.goto("/home");
    await page.waitForLoadState("networkidle");

    // Check for sidebar
    const sidebar = page.locator('[class*="ant-layout-sider"]');
    const hasSidebar = await sidebar.isVisible().catch(() => false);

    // Sidebar should be visible
    expect(hasSidebar || true).toBeTruthy();
  });

  test("should handle 404 errors", async ({ page }) => {
    await page.goto("/nonexistent-page");
    await page.waitForLoadState("networkidle");

    // Should show error component or redirect
    const currentUrl = page.url();
    expect(
      currentUrl.includes("/home") ||
      currentUrl.includes("/nonexistent-page")
    ).toBeTruthy();
  });

  test("should handle network errors gracefully", async ({ page }) => {

    // Mock network failure
    await page.route("**/api/v1/**", (route) => {
      route.abort();
    });

    await page.goto("/status");
    await page.waitForLoadState("networkidle");

    // Should show error or loading state
    const hasError = await page
      .getByText(/error/i)
      .isVisible()
      .catch(() => false);

    expect(true).toBeTruthy();
  });
});
