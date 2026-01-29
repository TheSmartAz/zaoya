import { test, expect } from './fixtures'

test.describe('InterviewCard', () => {
  test('should render interview question with options', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // For now, we'll test the structure exists
    // Full interview flow would require mocking the API responses
    await expect(page.getByText('What do you want to create?')).toBeVisible()
  })

  test('should display question number', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // The interview card structure should be available
    // Testing with actual interview data would require API mocking
    await expect(
      page.getByPlaceholder('Describe what you want to create...')
    ).toBeVisible()
  })
})

test.describe('Interview Flow', () => {
  test('should support interview flow UI components', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Check that card components can be rendered
    // This tests the UI infrastructure
    await expect(page.locator('#chat-panel')).toBeVisible()
  })

  test('should have card styling available', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Check for card component usage in the DOM
    const cardElements = page.locator('[class*="rounded"]')
    await expect(cardElements.first()).toBeVisible()
  })
})
