import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('accessibility checks pass', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Run axe accessibility tests
  const accessibilityScanResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa']) // WCAG 2.1 AA standards
    .analyze();
  
  // Allow some minor issues initially but fail if too many
  const violations = accessibilityScanResults.violations;
  const criticalViolations = violations.filter(v => v.impact === 'critical' || v.impact === 'serious');
  
  if (criticalViolations.length > 0) {
    console.error('Critical accessibility violations found:');
    console.error(JSON.stringify(criticalViolations, null, 2));
    throw new Error(`Found ${criticalViolations.length} critical accessibility violations`);
  }
  
  // Log minor issues for improvement
  if (violations.length > 0) {
    console.log(`Found ${violations.length} total accessibility issues (none critical)`);
    violations.forEach(violation => {
      console.log(`- ${violation.id}: ${violation.description}`);
    });
  }
  
  // Ensure we don't exceed reasonable threshold
  expect(violations.length).toBeLessThan(10);
});