import { test, expect } from '@playwright/test';

test('home renders dashboard', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Patient Registration System')).toBeVisible();
});
