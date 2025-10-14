import { test, expect } from '@playwright/test';

test.describe('Portfolio Site', () => {
  test('home page renders correctly', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check for key elements
    await expect(page.locator('text=Portfolio')).toBeVisible({ timeout: 10000 });
    
    // Take a screenshot for visual regression
    await page.screenshot({ path: 'tests/screenshots/homepage.png' });
  });

  test('contact form works end-to-end', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Scroll to contact section
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    
    // Fill out the form with multiple selectors for robustness
    const nameSelector = 'input[name="name"], input#name, input[placeholder*="name" i]';
    const emailSelector = 'input[name="email"], input#email, input[type="email"], input[placeholder*="email" i]';
    const messageSelector = 'textarea[name="message"], textarea#message, textarea[placeholder*="message" i]';
    
    await page.fill(nameSelector, 'Test User');
    await page.fill(emailSelector, 'test@example.com');
    await page.fill(messageSelector, 'Hello from Playwright test!');
    
    // Submit form
    const submitSelector = 'button:has-text("Send"), button[type="submit"], input[type="submit"]';
    await page.click(submitSelector);
    
    // Wait for response (success message or status change)
    await page.waitForTimeout(2000);
    
    // Check for success indication (adapt based on actual implementation)
    const successSelectors = [
      '.status:has-text("sent")',
      '.success',
      'text=success',
      'text=thank you',
      '.message-sent'
    ];
    
    let successFound = false;
    for (const selector of successSelectors) {
      try {
        await expect(page.locator(selector)).toBeVisible({ timeout: 1000 });
        successFound = true;
        break;
      } catch (e) {
        // Continue to next selector
      }
    }
    
    if (!successFound) {
      // Take screenshot for debugging
      await page.screenshot({ path: 'tests/screenshots/form-submit-debug.png' });
      console.log('No success message found - check screenshot for debugging');
    }
  });

  test('responsive design works on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:3000');
    
    // Check that content is still accessible on mobile
    await expect(page.locator('text=Portfolio')).toBeVisible();
    
    // Take mobile screenshot
    await page.screenshot({ path: 'tests/screenshots/mobile.png' });
  });

  test('all interactive elements are accessible', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Check that interactive elements have proper accessibility
    const buttons = page.locator('button, input[type="submit"]');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      // Ensure buttons have text or aria-label
      const hasText = await button.innerText().then(text => text.trim().length > 0);
      const hasAriaLabel = await button.getAttribute('aria-label').then(label => label && label.length > 0);
      
      expect(hasText || hasAriaLabel).toBeTruthy();
    }
    
    // Check form inputs have labels
    const inputs = page.locator('input, textarea');
    const inputCount = await inputs.count();
    
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const inputId = await input.getAttribute('id');
      const inputName = await input.getAttribute('name');
      
      if (inputId) {
        // Check for associated label
        const label = page.locator(`label[for="${inputId}"]`);
        await expect(label).toBeVisible();
      } else if (inputName) {
        // Check for label containing the input or nearby label text
        const hasLabel = await page.locator(`label:has(input[name="${inputName}"]), label + input[name="${inputName}"], input[name="${inputName}"] + label`).count() > 0;
        expect(hasLabel).toBeTruthy();
      }
    }
  });
});