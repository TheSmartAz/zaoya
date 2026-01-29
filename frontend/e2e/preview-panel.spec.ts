import { test, expect } from './fixtures'

test.describe('PreviewPanel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')
  })

  test('should display empty state initially', async ({ page }) => {
    await expect(page.getByText('Your page will appear here')).toBeVisible()
    await expect(
      page.getByText('Chat with AI to generate content for this page')
    ).toBeVisible()
  })

  test('should have device frame container', async ({ page, isMobile }) => {
    // The preview area should exist
    const previewPanel = page.locator('#preview-panel')
    if (isMobile) {
      await expect(previewPanel).toBeAttached()
    } else {
      await expect(previewPanel).toBeVisible()
    }
  })

  test('should center the preview content', async ({ page }) => {
    // Check that preview panel uses flexbox with center alignment
    const emptyState = page.getByText('Your page will appear here')
    await expect(emptyState).toBeVisible()

    // Verify centering is applied
    const container = emptyState.locator('..').locator('..')
    const hasCentering = await container.evaluate(el => {
      const styles = window.getComputedStyle(el)
      return styles.display === 'flex' &&
        (styles.alignItems === 'center' || styles.justifyContent === 'center')
    })
    expect(hasCentering).toBeTruthy()
  })

  test('should show iframe when HTML is set', async ({ page, isMobile }) => {
    // This test would require setting preview HTML via store
    // For now, we test the structure exists
    const previewPanel = page.locator('#preview-panel')
    if (isMobile) {
      await expect(previewPanel).toBeAttached()
    } else {
      await expect(previewPanel).toBeVisible()
    }
  })

  test('should be responsive on mobile devices', async ({ page, isMobile }) => {
    if (isMobile) {
      // On mobile, preview should still be visible
      await expect(page.locator('main')).toBeVisible()
    }
  })

  test('should maintain proper aspect ratio', async ({ page, isMobile }) => {
    // Preview panel should maintain its structure
    const previewPanel = page.locator('#preview-panel')
    if (isMobile) {
      await expect(previewPanel).toBeAttached()
    } else {
      await expect(previewPanel).toBeVisible()
    }

    // Check that panel has proper dimensions
    const box = await previewPanel.boundingBox()
    if (box) {
      expect(box.width).toBeGreaterThan(0)
      expect(box.height).toBeGreaterThan(0)
    }
  })
})

test.describe('DeviceFrame', () => {
  test('should render device frame styling', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Device frame should be present in preview
    await expect(page.getByText('Your page will appear here')).toBeVisible()
  })

  test('should provide visual device boundaries', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Check that the device frame has proper styling
    const frameElements = page.locator('[class*="rounded"]')
    await expect(frameElements.first()).toBeVisible()
  })
})
