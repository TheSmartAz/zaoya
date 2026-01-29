import { test, expect } from './fixtures'

test.describe('Zustand Stores', () => {
  test('chatStore should initialize with empty state', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Empty chat state should show the welcome message
    await expect(page.getByText('What do you want to create?')).toBeVisible()
  })

  test('chatStore should add messages', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    const textarea = page.getByPlaceholder('Describe what you want to create...')
    const message = 'Test message for store'

    await textarea.fill(message)
    await textarea.press('Enter')

    // Message should be visible in the DOM (store state reflected)
    await expect(page.getByText(message)).toBeVisible()
  })

  test('chatStore should maintain loading state', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    const textarea = page.getByPlaceholder('Describe what you want to create...')

    await textarea.fill('Loading test')
    await textarea.press('Enter')

    // After loading completes, input should be enabled
    await page.waitForTimeout(200)
    await expect(textarea).toBeEnabled()
  })

  test('projectStore should create project on mount', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Project creation should trigger the editor UI
    await expect(page.getByText('My Landing Page')).toBeVisible()
  })

  test('projectStore should maintain project state', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // The project name should be visible in the UI
    await expect(page.getByText('My Landing Page')).toBeVisible()

    // Refresh the page and check state persists (if persistence is implemented)
    // For now, just verify initial state
    await page.reload()
    await expect(page.getByText('My Landing Page')).toBeVisible()
  })
})

test.describe('Store Interactions', () => {
  test('chatStore and projectStore should work together', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Both stores should be initialized
    await expect(page.getByText('My Landing Page')).toBeVisible() // projectStore
    await expect(page.getByText('What do you want to create?')).toBeVisible() // chatStore
  })

  test('stores should update UI reactively', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    const textarea = page.getByPlaceholder('Describe what you want to create...')

    // Initial state
    await expect(page.getByText('What do you want to create?')).toBeVisible()

    // After action, state should update
    await textarea.fill('State update test')
    await textarea.press('Enter')

    // UI should reflect new state
    await expect(page.getByText('State update test')).toBeVisible()
    await expect(page.getByText('What do you want to create?')).not.toBeVisible()
  })
})
