import { test, expect } from '@playwright/test';

test.describe('Qognition - App Shell and Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the root of the application before each test
    await page.goto('/');
  });

  test('Happy Path: should render the application header and main navigation links', async ({ page }) => {
    // Verify the main header/banner is visible
    const header = page.getByRole('banner');
    await expect(header).toBeVisible();
    await expect(header.getByText(/qognition/i)).toBeVisible();

    // Verify main navigation links are present in the header
    // Scoping to the banner is necessary as links may be duplicated in the main content
    const expectedLinks = ['Home', 'Dashboard', 'Reports'];
    for (const linkName of expectedLinks) {
      const navLink = header.getByRole('link', { name: new RegExp(linkName, 'i') });
      await expect(navLink).toBeVisible();
    }
  });

  test('Happy Path: should navigate between primary modules correctly', async ({ page }) => {
    const modules = [
      { name: 'Dashboard', path: '/dashboard' },
      { name: 'Reports', path: '/reports' }
    ];

    for (const module of modules) {
      // Click link in the banner for reliable navigation (avoiding strict mode violations)
      await page.getByRole('banner').getByRole('link', { name: new RegExp(module.name, 'i') }).click();
      
      // Verify URL change and that the main content area reflects the current module
      await expect(page).toHaveURL(new RegExp(module.path));
      await expect(page.locator('main')).toContainText(new RegExp(module.name, 'i'));
      
      // Navigate back via the Home link in the banner
      await page.getByRole('banner').getByRole('link', { name: /home/i }).click();
      await expect(page).toHaveURL(/\/$/);
    }
  });

  test('Negative Test: should display a user-friendly 404 error page for invalid routes', async ({ page }) => {
    // Access a non-existent route
    const invalidPath = '/invalid-route-' + Date.now();
    await page.goto(invalidPath);

    // Verify 404 message and heading are displayed as expected
    const errorHeading = page.getByRole('heading', { name: /404|not found/i });
    await expect(errorHeading).toBeVisible();
    await expect(page.getByText(/does not exist|could not find/i)).toBeVisible();

    // Verify ability to recover by returning to the home page via the link in main content
    const homeLink = page.getByRole('main').getByRole('link', { name: /home/i });
    await expect(homeLink).toBeVisible();
    await homeLink.click();
    await expect(page).toHaveURL('/');
  });

  test('Edge Case: should handle responsive navigation menu on mobile viewports', async ({ page }) => {
    // Set to a standard mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();

    // Look for the mobile menu toggle button in the header
    const menuButton = page.getByRole('button', { name: /menu|navigation|toggle/i });
    
    // If the mobile menu toggle is present, test its open/close functionality
    if (await menuButton.isVisible()) {
      await menuButton.click();
      const mobileNav = page.getByRole('navigation');
      await expect(mobileNav).toBeVisible();
      
      // Verify links are visible and accessible in the mobile menu
      await expect(mobileNav.getByRole('link', { name: /dashboard/i })).toBeVisible();
      
      // Close the menu and verify it is hidden
      await menuButton.click();
      await expect(mobileNav).not.toBeVisible();
    }
  });

  test('Edge Case: should maintain current route and application layout on page refresh', async ({ page }) => {
    // Navigate to the Reports module
    await page.getByRole('banner').getByRole('link', { name: /reports/i }).click();
    await expect(page).toHaveURL(/.*reports/);
    
    // Perform a hard reload to simulate a user browser refresh
    await page.reload();

    // Verify consistency of the URL and layout components after refresh
    await expect(page).toHaveURL(/.*reports/);
    await expect(page.getByRole('banner')).toBeVisible();
    await expect(page.locator('main')).toContainText(/reports/i);
  });
});