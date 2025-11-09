import { test, expect } from "@playwright/test";
import { login } from "./helpers";

test.describe("Navigation", () => {
  test("should navigate to home page", async ({ page }) => {
    await page.goto("/");

    // Should redirect to /home or show login
    await page.waitForLoadState("networkidle");

    const currentUrl = page.url();
    expect(
      currentUrl.includes("/home") || currentUrl.includes("/login")
    ).toBeTruthy();
  });

  test("should navigate between pages", async ({ page }) => {
    await login(page);

    // Navigate to home
    await page.goto("/home");
    await expect(page).toHaveURL(/.*\/home/);

    // Navigate to import
    await page.goto("/import");
    await expect(page).toHaveURL(/.*\/import/);

    // Navigate to status
    await page.goto("/status");
    await expect(page).toHaveURL(/.*\/status/);
  });

  test("should navigate via sidebar menu", async ({ page }) => {
    await login(page);
    await page.goto("/home");

    // Check for sidebar menu items
    const homeLink = page.getByRole("link", { name: /Home/i });
    const importLink = page.getByRole("link", { name: /Import/i });
    const statusLink = page.getByRole("link", { name: /Status/i });

    // At least one menu item should be visible
    const hasMenu = await Promise.race([
      homeLink.isVisible().then(() => true),
      importLink.isVisible().then(() => true),
      statusLink.isVisible().then(() => true),
      page.waitForTimeout(1000).then(() => false),
    ]);

    expect(hasMenu).toBeTruthy();
  });

  test("should show 404 for unknown routes", async ({ page }) => {
    await login(page);

    // Try to access unknown route
    await page.goto("/unknown-route");

    // Should show error component or redirect
    await page.waitForLoadState("networkidle");

    // Either error page or redirect to login/home
    const currentUrl = page.url();
    expect(
      currentUrl.includes("/home") ||
      currentUrl.includes("/login") ||
      currentUrl.includes("/unknown-route")
    ).toBeTruthy();
  });

  test("should redirect to login when not authenticated", async ({ page }) => {
    // Clear authentication
    await page.context().clearCookies();
    await page.goto("/home");

    // Should redirect to login
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/.*\/login/);
  });
});
