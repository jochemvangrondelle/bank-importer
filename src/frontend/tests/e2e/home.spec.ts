import { test, expect } from "@playwright/test";
import { login, setupMocksForTest } from "./helpers";

test.describe("Home Page", () => {
  test.beforeEach(async ({ page }) => {
    // Setup API mocks for all tests
    await setupMocksForTest(page);
    await login(page);
    await page.goto("/home");
    await page.waitForLoadState("networkidle");
  });

  test("should display home page content", async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Bank Importer TH/);

    // Check welcome message
    await expect(page.getByText(/Welcome to Bank Importer TH/)).toBeVisible();
    await expect(
      page.getByText(/A web-based interface for importing and managing bank transactions/),
    ).toBeVisible();
  });

  test("should display quick links", async ({ page }) => {
    // Check quick links section
    await expect(page.getByText("Quick Links")).toBeVisible();

    // Check import wizard link
    await expect(
      page.getByRole("link", { name: /Import Wizard/ }),
    ).toBeVisible();

    // Check status link
    await expect(
      page.getByRole("link", { name: /Status/ }),
    ).toBeVisible();
  });

  test("should navigate to import wizard", async ({ page }) => {
    // Click Start Import Wizard button
    await page.getByRole("button", { name: "Start Import Wizard" }).click();

    // Should navigate to import page
    await page.waitForURL(/.*\/import/, { timeout: 5000 });
    await expect(page).toHaveURL(/.*\/import/);
  });

  test("should navigate to status page", async ({ page }) => {
    // Click View Status button
    await page.getByRole("button", { name: "View Status" }).click();

    // Should navigate to status page
    await page.waitForURL(/.*\/status/, { timeout: 5000 });
    await expect(page).toHaveURL(/.*\/status/);
  });

  test("should navigate via quick links", async ({ page }) => {
    // Click status link in quick links
    await page.getByRole("link", { name: /Status: View account status/ }).click();

    // Should navigate to status page
    await page.waitForURL(/.*\/status/, { timeout: 5000 });
    await expect(page).toHaveURL(/.*\/status/);
  });

  test("should display status information", async ({ page }) => {
    // Check status text
    await expect(
      page.getByText(/Foundation setup complete/),
    ).toBeVisible();
  });
});
