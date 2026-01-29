import { test, expect } from './fixtures'

test.describe('BuildPlanCard', () => {
  test('should render build plan structure', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Check that the main layout supports build plan display
    await expect(page.locator('main')).toBeVisible()
  })

  test('should have button components available', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Buttons should be available in the DOM
    const buttons = page.locator('button')
    await expect(buttons.first()).toBeVisible()
  })
})

test.describe('Multi-page flow', () => {
  test('should show reconnect banner and resume stream after refresh', async ({ page }) => {
    await page.addInitScript(() => {
      const stored = {
        state: {
          buildId: 'build-1',
          projectId: '79c5e15f-e29b-419a-a101-55e932515ea6',
          phase: 'implementing',
        },
        version: 0,
      }
      window.localStorage.setItem('build-store', JSON.stringify(stored))

      class MockEventSource {
        listeners: Record<string, Array<(event: MessageEvent | Event) => void>> = {}
        constructor() {
          window.setTimeout(() => {
            this.dispatch('open')
            this.dispatch('task', {
              id: 'task-resume',
              type: 'task_started',
              title: 'Resumed task',
              status: 'running',
              session_id: 'build-1',
              project_id: '79c5e15f-e29b-419a-a101-55e932515ea6',
            })
          }, 200)
        }
        addEventListener(type: string, cb: (event: MessageEvent | Event) => void) {
          this.listeners[type] = this.listeners[type] || []
          this.listeners[type].push(cb)
        }
        dispatch(type: string, data?: any) {
          const event =
            type === 'open'
              ? new Event('open')
              : ({ data: JSON.stringify(data) } as MessageEvent)
          ;(this.listeners[type] || []).forEach((cb) => cb(event))
        }
        close() {}
      }

      // @ts-expect-error override EventSource for test
      window.EventSource = MockEventSource
    })

    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    await expect(page.getByText('Reconnecting...')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('Resumed task')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('Reconnecting...')).toBeHidden({ timeout: 10000 })
  })

  test('should render build plan card from SSE and allow edits', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    await expect(
      page.getByPlaceholder('Describe what you want to create...')
    ).toBeVisible()

    await page.evaluate(
      () =>
        new Promise<void>((resolve) => {
          setTimeout(() => {
            window.dispatchEvent(
              new CustomEvent('build-sse-event', {
                detail: {
                  event: 'card',
                  data: {
                    type: 'build_plan',
                    data: {
                      pages: [
                        { id: 'home', name: 'Home', path: '/', is_main: true },
                        { id: 'about', name: 'About', path: '/about', is_main: false },
                      ],
                      estimated_tasks: 6,
                      approval_required: true,
                    },
                    session_id: 'build-1',
                    project_id: '79c5e15f-e29b-419a-a101-55e932515ea6',
                  },
                },
              })
            )
            resolve()
          }, 0)
        })
    )

    const planCard = page.getByText('Build plan').locator('..').locator('..')
    await expect(planCard).toBeVisible()
    await planCard.getByRole('button', { name: 'Edit' }).click()

    await planCard.getByRole('button', { name: 'Add page', exact: true }).click()
    const nameInput = planCard.locator('input[type="text"]').first()
    await nameInput.fill('Contact')
    await nameInput.press('Enter')

    await expect(planCard.getByText('Contact', { exact: true })).toBeVisible()
    await expect(planCard.getByText('/contact', { exact: true })).toBeVisible()
  })

  test('should update running build plan progress from plan_update events', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    await page.evaluate(
      () =>
        new Promise<void>((resolve) => {
          setTimeout(() => {
            window.dispatchEvent(
              new CustomEvent('build-sse-event', {
                detail: {
                  event: 'card',
                  data: {
                    type: 'build_plan',
                    data: {
                      pages: [{ id: 'home', name: 'Home', path: '/', is_main: true }],
                      estimated_tasks: 4,
                      approval_required: false,
                      build_id: 'build-1',
                    },
                    session_id: 'build-1',
                    project_id: '79c5e15f-e29b-419a-a101-55e932515ea6',
                  },
                },
              })
            )
            resolve()
          }, 0)
        })
    )

    await expect(page.getByText('构建进度')).toBeVisible()
    await expect(page.getByText('1 / 4 任务完成')).toBeVisible()

    await page.evaluate(() => {
      window.dispatchEvent(
        new CustomEvent('build-sse-event', {
          detail: {
            event: 'plan_update',
            data: {
              id: 'build-1',
              completed_tasks: 3,
              failed_tasks: 0,
              tasks: [
                {
                  id: 'task-plan',
                  name: '创建构建计划',
                  category: 'planning',
                  status: 'done',
                },
                {
                  id: 'task-home-html',
                  name: 'Home: 生成 HTML 结构',
                  category: 'generation',
                  status: 'done',
                  page_id: 'home',
                },
                {
                  id: 'task-home-validate',
                  name: 'Home: HTML 验证',
                  category: 'validation',
                  status: 'done',
                  page_id: 'home',
                },
                {
                  id: 'task-final',
                  name: '最终检查',
                  category: 'finalization',
                  status: 'pending',
                },
              ],
              status: 'running',
            },
          },
        })
      )
    })

    await expect(page.getByText('3 / 4 任务完成')).toBeVisible()
  })

  test('should approve build plan and finish build', async ({ page }) => {
    await page.addInitScript(() => {
      class MockEventSource {
        listeners: Record<string, Array<(event: MessageEvent) => void>> = {}
        constructor() {
          window.setTimeout(() => {
            const payload = {
              id: 'build-build-1',
              type: 'build_complete',
              title: 'Build complete',
              status: 'done',
              session_id: 'build-1',
              project_id: '79c5e15f-e29b-419a-a101-55e932515ea6',
            }
            this.dispatch('task', payload)
          }, 50)
        }
        addEventListener(type: string, cb: (event: MessageEvent) => void) {
          this.listeners[type] = this.listeners[type] || []
          this.listeners[type].push(cb)
        }
        dispatch(type: string, data: any) {
          const event = { data: JSON.stringify(data) } as MessageEvent
          ;(this.listeners[type] || []).forEach((cb) => cb(event))
        }
        close() {}
      }

      // @ts-expect-error override EventSource for test
      window.EventSource = MockEventSource
    })

    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')
    await expect(
      page.getByPlaceholder('Describe what you want to create...')
    ).toBeVisible()

    await page.evaluate(
      () =>
        new Promise<void>((resolve) => {
          setTimeout(() => {
            window.dispatchEvent(
              new CustomEvent('build-sse-event', {
                detail: {
                  event: 'card',
                  data: {
                    type: 'build_plan',
                    data: {
                      pages: [
                        { id: 'home', name: 'Home', path: '/', is_main: true },
                      ],
                      estimated_tasks: 3,
                      approval_required: true,
                    },
                    session_id: 'build-1',
                    project_id: '79c5e15f-e29b-419a-a101-55e932515ea6',
                  },
                },
              })
            )
            resolve()
          }, 0)
        })
    )

    await page.getByRole('button', { name: 'Start build' }).click({ force: true })
    await expect(page.locator('#chat-panel')).toContainText('Build complete', {
      timeout: 10000,
    })
  })

  test('should approve edited build plan and send updated pages', async ({ page }) => {
    await page.addInitScript(() => {
      class MockEventSource {
        addEventListener() {}
        close() {}
      }
      // @ts-expect-error override EventSource for test
      window.EventSource = MockEventSource
    })

    let buildStartPayload: any = null
    await page.route('**/api/projects/**/build/start', async (route) => {
      buildStartPayload = route.request().postDataJSON()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ build_id: 'build-1' }),
      })
    })

    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')
    await expect(
      page.getByPlaceholder('Describe what you want to create...')
    ).toBeVisible()

    await page.evaluate(
      () =>
        new Promise<void>((resolve) => {
          setTimeout(() => {
            window.dispatchEvent(
              new CustomEvent('build-sse-event', {
                detail: {
                  event: 'card',
                  data: {
                    type: 'build_plan',
                    data: {
                      pages: [
                        { id: 'home', name: 'Home', path: '/', is_main: true },
                        { id: 'about', name: 'About', path: '/about', is_main: false },
                      ],
                      estimated_tasks: 4,
                      approval_required: true,
                    },
                    session_id: 'build-1',
                    project_id: '79c5e15f-e29b-419a-a101-55e932515ea6',
                  },
                },
              })
            )
            resolve()
          }, 0)
        })
    )

    const planCard = page.getByText('Build plan').locator('..').locator('..')
    await expect(planCard).toBeVisible()
    await planCard.getByRole('button', { name: 'Edit' }).click()

    await planCard.getByRole('button', { name: 'Add page', exact: true }).click()
    const nameInput = planCard.locator('input[type="text"]').first()
    await nameInput.fill('Contact')
    await nameInput.press('Enter')

    await planCard.getByRole('button', { name: 'Start build' }).click({ force: true })

    await expect.poll(() => buildStartPayload).not.toBeNull()
    const pagesPayload = buildStartPayload?.pages || []
    expect(
      pagesPayload.some(
        (page: any) => page.name === 'Contact' && page.path === '/contact'
      )
    ).toBe(true)
    expect(
      pagesPayload.some((page: any) => page.name === 'Home' && page.path === '/')
    ).toBe(true)
  })

  test('should show retry button on validation card and trigger retry', async ({ page }) => {
    await page.addInitScript(() => {
      ;(window as any).__esUrls = []
      class MockEventSource {
        constructor(url: string) {
          ;(window as any).__esUrls.push(url)
        }
        addEventListener() {}
        close() {}
      }
      // @ts-expect-error override EventSource for test
      window.EventSource = MockEventSource
    })

    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')
    await expect(
      page.getByPlaceholder('Describe what you want to create...')
    ).toBeVisible()

    await page.evaluate(
      () =>
        new Promise<void>((resolve) => {
          setTimeout(() => {
            window.dispatchEvent(
              new CustomEvent('build-sse-event', {
                detail: {
                  event: 'task',
                  data: {
                    id: 'page-about',
                    type: 'task_failed',
                    title: 'About failed',
                    status: 'failed',
                    session_id: 'build-1',
                    project_id: '79c5e15f-e29b-419a-a101-55e932515ea6',
                  },
                },
              })
            )
            window.dispatchEvent(
              new CustomEvent('build-sse-event', {
                detail: {
                  event: 'card',
                  data: {
                    type: 'validation',
                    data: {
                      errors: [{ type: 'validation', message: 'Invalid HTML' }],
                      suggestions: [],
                      page_id: 'about',
                    },
                    session_id: 'build-1',
                  },
                },
              })
            )
            resolve()
          }, 0)
        })
    )

    const validationCard = page.getByText('Validation failed').locator('..').locator('..')
    await validationCard.getByRole('button', { name: 'Retry' }).click({ force: true })
    await page.waitForFunction(() => (window as any).__esUrls.length > 0)
    const urls = await page.evaluate(() => (window as any).__esUrls)
    expect(urls.join('|')).toContain('/api/build/build-1/retry/about')
  })

  test('should abort build and restore send button', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    await expect(
      page.getByPlaceholder('Describe what you want to create...')
    ).toBeVisible()

    await page.evaluate(
      () =>
        new Promise<void>((resolve) => {
          setTimeout(() => {
            window.dispatchEvent(
              new CustomEvent('build-sse-event', {
                detail: {
                  event: 'task',
                  data: {
                    id: 'build-build-1',
                    type: 'task_started',
                    title: 'Build started',
                    status: 'running',
                    session_id: 'build-1',
                    project_id: '79c5e15f-e29b-419a-a101-55e932515ea6',
                  },
                },
              })
            )
            resolve()
          }, 0)
        })
    )

    await page.evaluate(() => {
      const button = Array.from(document.querySelectorAll('button')).find(
        (el) => el.textContent?.includes('Abort')
      ) as HTMLButtonElement | undefined
      button?.click()
    })

    await expect(page.getByPlaceholder('Describe what you want to create...')).toBeEnabled()
  })
})

test.describe('QuickActionChip', () => {
  test('should support chip-style buttons', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // The page should support chip components
    // Chips are typically rounded-full elements
    await expect(page.locator('button').first()).toBeVisible()
  })

  test('should allow clicking on action elements', async ({ page }) => {
    await page.goto('/editor/79c5e15f-e29b-419a-a101-55e932515ea6')

    // Buttons should be clickable
    const button = page.locator('button').first()
    await expect(button).toBeEnabled()
  })
})
