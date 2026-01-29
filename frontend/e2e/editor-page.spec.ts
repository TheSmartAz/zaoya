import { test, expect } from './fixtures'

test.describe('EditorPage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')
  })

  test('should render the editor page', async ({ page, isMobile }) => {
    // Check that the main editor layout is visible
    const chatPanel = page.locator('#chat-panel')
    if (isMobile) {
      await expect(chatPanel).toBeAttached()
    } else {
      await expect(chatPanel).toBeVisible()
    }
  })

  test('should display the project name', async ({ page }) => {
    // The default project name is "My Landing Page"
    await expect(page.getByText('My Landing Page')).toBeVisible()
  })

  test('should have ChatPanel and PreviewPanel', async ({ page }) => {
    // Chat panel should be visible
    await expect(page.getByText('What do you want to create?')).toBeVisible()

    // Preview panel should show empty state
    await expect(page.getByText('Your page will appear here')).toBeVisible()
  })

  test('should create a project on mount', async ({ page }) => {
    // The project should be created automatically
    // Verify by checking for the chat interface which only appears when project exists
    await expect(page.getByPlaceholder('Describe what you want to create...')).toBeVisible()
  })

  test('should have proper layout structure', async ({ page, isMobile }) => {
    // Check for responsive layout
    const mainContent = page.locator('main')
    if (!isMobile) {
      await expect(mainContent).toBeVisible()
    }

    // Chat panel should be on the left
    const chatPanel = page.locator('#chat-panel')
    if (isMobile) {
      await expect(chatPanel).toBeAttached()
    } else {
      await expect(chatPanel).toBeVisible()
    }

    // Preview panel should take remaining space
    const previewPanel = page.locator('#preview-panel')
    if (isMobile) {
      await expect(previewPanel).toBeAttached()
    } else {
      await expect(previewPanel).toBeVisible()
    }
  })
})
