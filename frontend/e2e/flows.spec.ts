import { test, expect } from './fixtures'

test.describe('Editor Page Flow', () => {
  test('should complete basic chat flow', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // 1. Initial state
    await expect(page.getByText('What do you want to create?')).toBeVisible()
    await expect(page.getByText('Your page will appear here')).toBeVisible()

    // 2. Send a message
    const textarea = page.getByPlaceholder('Describe what you want to create...')
    await textarea.fill('Create a landing page for a coffee shop')
    await textarea.press('Enter')

    // 3. User message appears
    await expect(page.getByText('Create a landing page for a coffee shop')).toBeVisible()

    // 4. Input is cleared
    await expect(textarea).toHaveValue('')
  })

  test('should handle multiple messages in conversation', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    const textarea = page.getByPlaceholder('Describe what you want to create...')

    // Send multiple messages
    const messages = [
      'I need a portfolio website',
      'For a photographer',
      'With a dark theme'
    ]

    for (const message of messages) {
      await textarea.fill(message)
      await textarea.press('Enter')
      await expect(page.getByText(message)).toBeVisible()
      await page.waitForTimeout(100)
    }

    // All messages should be visible
    for (const message of messages) {
      await expect(page.getByText(message)).toBeVisible()
    }
  })

  test('should maintain state during interaction', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Verify initial project state
    await expect(page.getByText('My Landing Page')).toBeVisible()

    // Send a message
    const textarea = page.getByPlaceholder('Describe what you want to create...')
    await textarea.fill('Test message')
    await textarea.press('Enter')

    // Project name should still be visible
    await expect(page.getByText('My Landing Page')).toBeVisible()

    // Message should be in chat
    await expect(page.getByText('Test message')).toBeVisible()
  })

  test('should handle rapid message sending', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    const textarea = page.getByPlaceholder('Describe what you want to create...')

    // Send messages rapidly
    await textarea.fill('First message')
    await textarea.press('Enter')
    await page.waitForTimeout(50)

    await textarea.fill('Second message')
    await textarea.press('Enter')
    await page.waitForTimeout(50)

    await textarea.fill('Third message')
    await textarea.press('Enter')

    // All messages should appear
    await expect(page.getByText('First message')).toBeVisible()
    await expect(page.getByText('Second message')).toBeVisible()
    await expect(page.getByText('Third message')).toBeVisible()
  })
})

test.describe('Error Handling', () => {
  test('should handle empty message gracefully', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    const textarea = page.getByPlaceholder('Describe what you want to create...')

    // Try to send whitespace-only message
    await textarea.fill('   ')
    await textarea.press('Enter')

    // Should not crash or show error
    await expect(page.locator('body')).toBeVisible()
  })

  test('should handle very long messages', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    const textarea = page.getByPlaceholder('Describe what you want to create...')

    // Type a very long message
    const longMessage = 'A'.repeat(1000)
    await textarea.fill(longMessage)
    await textarea.press('Enter')

    // Should handle without error
    await expect(page.getByText(longMessage)).toBeVisible()
  })
})

test.describe('User Interactions', () => {
  test('should allow clicking on UI elements', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Click on various interactive elements
    const buttons = page.locator('button')
    const count = await buttons.count()

    for (let i = 0; i < Math.min(count, 3); i++) {
      const button = buttons.nth(i)
      if (await button.isVisible() && await button.isEnabled()) {
        await button.click({ trial: true })
      }
    }
  })

  test('should support keyboard shortcuts', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    const textarea = page.getByPlaceholder('Describe what you want to create...')

    // Focus textarea
    await textarea.focus()
    await expect(textarea).toBeFocused()

    // Type and send with Enter
    await textarea.type('Keyboard shortcut test')
    await page.keyboard.press('Enter')

    // Message should be sent
    await expect(page.getByText('Keyboard shortcut test')).toBeVisible()
  })
})
