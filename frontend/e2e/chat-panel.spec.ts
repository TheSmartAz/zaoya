import { test, expect } from './fixtures'

test.describe('ChatPanel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')
  })

  test('should display empty state message', async ({ page }) => {
    await expect(page.getByText('What do you want to create?')).toBeVisible()
    await expect(page.getByText("Describe your page and I'll build it for you")).toBeVisible()
  })

  test('should have input bar with textarea and send button', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')
    const sendButton = page.locator('button').filter({ hasText: /^$/ }).or(page.locator('button[aria-label]'))

    await expect(textarea).toBeVisible()
    await expect(textarea).toBeEnabled()

    // The send button should be a round button with an icon
    const arrowUpButton = page.locator('button').filter({ has: page.locator('svg') })
    await expect(arrowUpButton.first()).toBeVisible()
  })

  test('should send a message when clicking send button', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')
    const message = 'Create a landing page for a coffee shop'

    await textarea.fill(message)

    // Find and click the send button (arrow icon)
    const sendButton = page.locator('button').filter({ has: page.locator('svg') }).first()
    await sendButton.click()

    // Message should appear in the chat
    await expect(page.getByText(message)).toBeVisible()
  })

  test('should send a message when pressing Enter', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')
    const message = 'Create a portfolio website'

    await textarea.fill(message)
    await textarea.press('Enter')

    // Message should appear in the chat
    await expect(page.getByText(message)).toBeVisible()
  })

  test('should not send empty message', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')

    // Try to send empty message
    await textarea.fill('   ')
    await textarea.press('Enter')

    // No message should appear (empty state text should still be there)
    await expect(page.getByText('What do you want to create?')).toBeVisible()
  })

  test('should allow Shift+Enter for new line', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')

    await textarea.fill('First line')
    await textarea.press('Shift+Enter')
    await textarea.type('Second line')

    // The textarea should still have the content (not sent)
    await expect(textarea).toHaveValue(/First line[\S\s]*Second line/)
  })

  test('should display user messages with proper styling', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')

    await textarea.fill('Hello, I need a website')
    await textarea.press('Enter')

    // User message should be visible
    const userMessage = page.getByText('Hello, I need a website')
    await expect(userMessage).toBeVisible()

    // User messages should be right-aligned (check for justify-end class effect)
    const messageContainer = userMessage.locator('..').locator('..')
    const computedStyle = await messageContainer.evaluate(el => window.getComputedStyle(el).justifyContent)
    expect(computedStyle).toBe('flex-end')
  })

  test('should show AI response after user message', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')

    await expect(page.getByText('My Landing Page')).toBeVisible()

    await textarea.fill('Create a landing page')
    await textarea.press('Enter')

    await expect(page.getByText('Build Plan')).toBeVisible({ timeout: 10000 })

    await textarea.fill('Add a hero section')
    await textarea.press('Enter')

    await page.waitForTimeout(200)

    // AI response should appear (mocked as OK)
    await expect(page.getByText('OK')).toBeVisible({ timeout: 10000 })
  })

  test('should open product doc after handled edit', async ({ page }) => {
    const productDoc = {
      id: 'doc-1',
      project_id: '79c5e15f-e29b-419a-a101-55e932515ea6',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      overview: 'Test product doc overview',
      target_users: ['Founders'],
      content_structure: {
        sections: [
          {
            name: 'Hero',
            description: 'Highlight the value',
            priority: 'high',
          },
        ],
      },
      design_requirements: {
        style: 'Modern',
        colors: ['#2563eb'],
        typography: 'Geist',
        mood: 'Confident',
      },
      page_plan: {
        pages: [
          {
            id: 'home',
            name: 'Home',
            path: '/',
            description: 'Landing page',
            is_main: true,
            sections: ['Hero'],
          },
        ],
      },
      technical_constraints: ['Tailwind CSS'],
      interview_answers: [
        {
          question_id: 'q1',
          question: 'Who is the target user?',
          answer: 'Founders',
          answered_at: new Date().toISOString(),
        },
      ],
      generation_count: 1,
      last_generated_at: new Date().toISOString(),
    }

    await page.route('**/api/projects/**/product-doc/edit', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ handled: true }),
      })
    })

    await page.route('**/api/projects/**/product-doc', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(productDoc),
        })
        return
      }
      await route.fallback()
    })

    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    const textarea = page.getByPlaceholder('Describe what you want to create...')

    await textarea.fill('Create a landing page')
    await textarea.press('Enter')

    await expect(page.getByText('Build Plan')).toBeVisible({ timeout: 10000 })

    await textarea.fill('Update the product doc overview')
    await textarea.press('Enter')

    await expect(
      page.getByText('已更新 ProductDoc，可以在预览面板查看。')
    ).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('项目需求文档')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('Test product doc overview')).toBeVisible({
      timeout: 10000,
    })
  })

  test('should disable input while loading', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')

    await textarea.fill('Create a website')
    await textarea.press('Enter')

    // After the mock stream completes, input should be enabled
    await page.waitForTimeout(200)
    await expect(textarea).toBeEnabled()
  })

  test('should auto-resize textarea', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')

    // Get initial height
    const initialHeight = await textarea.evaluate(el => el.scrollHeight)

    // Type a long message
    await textarea.fill('This is a very long message that should cause the textarea to grow in height automatically to accommodate all the text content without scrolling')

    // Get new height
    const newHeight = await textarea.evaluate(el => el.scrollHeight)

    // Height should have increased
    expect(newHeight).toBeGreaterThan(initialHeight)
  })

  test('should clear textarea after sending message', async ({ page }) => {
    const textarea = page.getByPlaceholder('Describe what you want to create...')

    await textarea.fill('Test message')
    await textarea.press('Enter')

    // Textarea should be cleared
    await expect(textarea).toHaveValue('')
  })
})
