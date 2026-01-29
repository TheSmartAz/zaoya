import { test, expect } from './fixtures'

test.describe('UI Components', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')
  })

  test('should render button components', async ({ page }) => {
    const buttons = page.locator('button')
    await expect(buttons.first()).toBeVisible()
  })

  test('should render input components', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')
    await expect(textarea).toBeVisible()
  })

  test('should render scroll areas', async ({ page }) => {
    const scrollArea = page.locator('[data-radix-scroll-area-viewport]')
    await expect(scrollArea.first()).toBeVisible()
  })

  test('should apply proper typography', async ({ page }) => {
    // Check for Geist font being applied
    const fontFamily = await page.locator('body').evaluate(el =>
      window.getComputedStyle(el).fontFamily
    )
    expect(fontFamily).toContain('Geist')
  })

  test('should have proper color scheme', async ({ page }) => {
    // Check that CSS variables for colors are defined
    const hasColorVariables = await page.evaluate(() => {
      const styles = getComputedStyle(document.documentElement)
      return styles.getPropertyValue('--primary') !== '' ||
             styles.getPropertyValue('--background') !== ''
    })
    expect(hasColorVariables).toBeTruthy()
  })
})

test.describe('Layout Components', () => {
  test('should render Panel component', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Panels should be present
    const panels = page.locator('[class*="panel"], [class*="border"]')
    await expect(panels.first()).toBeVisible()
  })

  test('should render EditorLayout', async ({ page, isMobile }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Main layout should be visible
    const chatPanel = page.locator('#chat-panel')
    if (isMobile) {
      await expect(chatPanel).toBeAttached()
    } else {
      await expect(chatPanel).toBeVisible()
    }
  })

  test('should have responsive layout', async ({ page, isMobile }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Test different viewport sizes
    await page.setViewportSize({ width: 375, height: 667 })
    const chatPanel = page.locator('#chat-panel')
    await expect(chatPanel).toBeAttached()

    await page.setViewportSize({ width: 1920, height: 1080 })
    await expect(chatPanel).toBeVisible()
  })
})

test.describe('Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Check for headings
    const headings = page.locator('h1, h2, h3, h4, h5, h6')
    const count = await headings.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should have accessible form elements', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Textarea should have proper placeholder
    const textarea = page.getByPlaceholder('Describe what you want to create...')
    await expect(textarea).toBeVisible()

    // Buttons should be accessible via keyboard
    const button = page.locator('button').first()
    await button.focus()
    await expect(button).toBeFocused()
  })

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Tab through the interface
    await page.keyboard.press('Tab')

    // Something should be focused
    const activeElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(['BUTTON', 'TEXTAREA', 'INPUT']).toContain(activeElement)
  })
})
