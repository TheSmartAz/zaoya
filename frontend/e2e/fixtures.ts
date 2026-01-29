import { test as base } from '@playwright/test'

const PROJECT_ID = '79c5e15f-e29b-419a-a101-55e932515ea6'
const NOW = new Date().toISOString()

const project = {
  id: PROJECT_ID,
  name: 'My Landing Page',
  status: 'draft',
  notification_enabled: false,
  created_at: NOW,
  updated_at: NOW,
}

const pages = [
  {
    id: 'page-1',
    project_id: PROJECT_ID,
    name: 'Home',
    slug: 'home',
    path: '/',
    is_home: true,
    content: {},
    design_system: {},
    sort_order: 0,
    created_at: NOW,
    updated_at: NOW,
  },
]

const buildPlan = {
  id: 'build-1',
  project_id: PROJECT_ID,
  created_at: NOW,
  pages: [
    {
      id: 'home',
      name: 'Home',
      path: '/',
      is_main: true,
      task_count: 2,
    },
  ],
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
      status: 'pending',
      page_id: 'home',
    },
    {
      id: 'task-home-validate',
      name: 'Home: HTML 验证',
      category: 'validation',
      status: 'pending',
      page_id: 'home',
    },
    {
      id: 'task-final',
      name: '最终检查',
      category: 'finalization',
      status: 'pending',
    },
  ],
  total_tasks: 4,
  completed_tasks: 1,
  failed_tasks: 0,
  estimated_duration_ms: 8000,
  actual_duration_ms: null,
  started_at: NOW,
  completed_at: null,
  status: 'running',
}

export type TestOptions = {
  // Add custom test options here if needed
}

export const test = base.extend<TestOptions>({
  page: async ({ page }, use) => {
    await page.addInitScript(() => {
      window.localStorage.clear()
      window.sessionStorage.clear()
    })

    await page.route('**/api/**', async (route) => {
      const request = route.request()
      const url = new URL(request.url())
      const method = request.method()
      const path = url.pathname.replace(/\/+$/, '')

      const json = (payload: unknown, status = 200) =>
        route.fulfill({
          status,
          contentType: 'application/json',
          headers: { 'Access-Control-Allow-Origin': '*' },
          body: JSON.stringify(payload),
        })

      if (method === 'OPTIONS') {
        return route.fulfill({
          status: 204,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PATCH,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
          },
          body: '',
        })
      }

      if (path.endsWith('/api/projects') && method === 'GET') {
        return json([project])
      }

      if (path.endsWith(`/api/projects/${PROJECT_ID}`) && method === 'GET') {
        return json(project)
      }

      if (path.endsWith(`/api/projects/${PROJECT_ID}/pages`) && method === 'GET') {
        return json(pages)
      }

      if (path.endsWith(`/api/projects/${PROJECT_ID}/pages`) && method === 'POST') {
        return json({
          ...pages[0],
          id: 'page-2',
          name: 'New Page',
          slug: 'new-page',
          path: '/new-page',
          is_home: false,
          sort_order: 1,
        })
      }

      if (path.endsWith(`/api/projects/${PROJECT_ID}/product-doc`) && method === 'GET') {
        return route.fulfill({ status: 404, body: '' })
      }

      if (path.endsWith(`/api/projects/${PROJECT_ID}/product-doc/edit`) && method === 'POST') {
        return json({ handled: false })
      }

      if (path.endsWith(`/api/projects/${PROJECT_ID}/build/start`) && method === 'POST') {
        return json({ build_id: 'build-1' })
      }

      if (path.endsWith('/api/build/build-1/abort') && method === 'POST') {
        return json({
          build_id: 'build-1',
          project_id: PROJECT_ID,
          phase: 'aborted',
          current_task_id: null,
          build_graph: null,
          last_patch: null,
          last_validation: null,
          last_checks: null,
          last_review: null,
          token_usage: null,
          agent_usage: null,
          last_agent_usage: null,
          history: [],
        })
      }

      if (path.endsWith('/api/build/build-1') && method === 'GET') {
        return json({
          build_id: 'build-1',
          project_id: PROJECT_ID,
          phase: 'planning',
          current_task_id: null,
          build_graph: null,
          last_patch: null,
          last_validation: null,
          last_checks: null,
          last_review: null,
          history: [],
        })
      }

      if (path.endsWith('/api/build/build-1/plan') && method === 'GET') {
        return json(buildPlan)
      }

      if (path.endsWith(`/api/projects/${PROJECT_ID}/chat`) && method === 'POST') {
        const payload = {
          state: {
            brief: {},
            build_plan: {
              pages: [{ id: 'page_0', name: 'Home', path: '/' }],
              design_system: {},
              features: [],
            },
            product_document: null,
          },
          orchestrator: {
            mode: 'finish',
            next_action: {
              type: 'finish',
              plan: {
                pages: [{ id: 'page_0', name: 'Home', path: '/' }],
                design_system: {},
                features: [],
              },
              product_document: null,
              brief: {},
            },
          },
        }
        const body = `data: ${JSON.stringify(payload)}\n\ndata: [DONE]\n\n`
        return route.fulfill({
          status: 200,
          contentType: 'text/event-stream',
          headers: { 'Access-Control-Allow-Origin': '*' },
          body,
        })
      }

      if (path.endsWith('/api/chat') && method === 'POST') {
        const body =
          'data: {"choices":[{"delta":{"content":"OK"}}]}\n\n' +
          'data: [DONE]\n\n'
        return route.fulfill({
          status: 200,
          contentType: 'text/event-stream',
          headers: { 'Access-Control-Allow-Origin': '*' },
          body,
        })
      }

      return json({})
    })

    await use(page)
  },
})
export const expect = test.expect
