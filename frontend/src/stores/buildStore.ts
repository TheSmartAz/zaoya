import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { BuildPlanCardData, BuildPlanPage, LiveTaskMessage } from '@/types/chat'
import type { BuildPlan } from '@/types/buildPlan'
import { useProjectStore } from './projectStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export type BuildPhase =
  | 'planning'
  | 'implementing'
  | 'verifying'
  | 'reviewing'
  | 'iterating'
  | 'ready'
  | 'aborted'
  | 'error'

export type TaskStatus = 'todo' | 'doing' | 'done' | 'blocked'

export type ReviewDecision = 'approve' | 'request_changes'

export interface Task {
  id: string
  title: string
  goal: string
  acceptance: string[]
  depends_on: string[]
  files_expected: string[]
  status: TaskStatus
  created_at: string
  completed_at?: string
}

export interface BuildGraph {
  tasks: Task[]
  notes: string
  created_at: string
}

export interface PatchSet {
  id: string
  task_id: string
  diff: string
  touched_files: string[]
  notes: string
  created_at: string
}

export interface ValidationReport {
  ok: boolean
  errors: string[]
  warnings: string[]
  js_valid: boolean
}

export interface CheckReport {
  ok: boolean
  typecheck_ok: boolean
  lint_ok: boolean
  unit_ok: boolean
  logs: string
}

export interface ReviewReport {
  decision: ReviewDecision
  reasons: string[]
  required_fixes: string[]
}

export interface BuildHistoryEvent {
  ts: string
  phase: BuildPhase
  action: string
  details: Record<string, unknown>
}

export interface BuildSeed {
  brief: Record<string, unknown>
  build_plan?: Record<string, unknown> | null
  product_doc?: Record<string, unknown> | null
}

interface BuildApiResponse {
  build_id: string
  project_id: string
  phase: BuildPhase
  current_task_id: string | null
  build_graph: BuildGraph | null
  last_patch: PatchSet | null
  last_validation: ValidationReport | null
  last_checks: CheckReport | null
  last_review: ReviewReport | null
  history: BuildHistoryEvent[]
}

export interface BuildState {
  buildId: string | null
  projectId: string | null

  phase: BuildPhase | null
  currentTaskId: string | null

  buildGraph: BuildGraph | null
  lastPatch: PatchSet | null
  lastValidation: ValidationReport | null
  lastChecks: CheckReport | null
  lastReview: ReviewReport | null
  history: BuildHistoryEvent[]

  isBuilding: boolean
  streamStatus: 'idle' | 'connected' | 'reconnecting' | 'error'
  streamError: string | null
  isLoading: boolean
  isStepping: boolean
  error: string | null

  startBuild: (projectId: string, seed: BuildSeed) => Promise<void>
  stepBuild: (userMessage?: string) => Promise<void>
  abortBuild: () => Promise<void>
  revertPatch: () => Promise<void>
  loadBuild: () => Promise<void>
  checkPublishReady: () => Promise<boolean>
  resetBuild: () => void

  setBuildComplete: () => void
  setStreamStatus: (status: BuildState['streamStatus']) => void
  setStreamError: (error: string | null) => void
  hydrateLiveTasksFromState: () => void

  liveTasks: LiveTaskMessage[]
  addLiveTask: (task: LiveTaskMessage) => void
  updateLiveTask: (taskId: string, updates: Partial<LiveTaskMessage>) => void
  removeLiveTask: (taskId: string) => void
  clearLiveTasks: () => void
  handleTaskEvent: (event: any) => void
  handleCardEvent: (event: any) => void
  handlePreviewUpdate: (event: any) => void
  handlePlanUpdate: (data: Partial<BuildPlan>) => void

  pendingBuildPlan: { plan: BuildPlanCardData; sourceTaskId: string } | null
  setPendingBuildPlan: (plan: BuildPlanCardData | null, sourceTaskId?: string) => void
  approveBuildPlan: (pages: BuildPlanPage[]) => Promise<void>
  dismissBuildPlan: (taskId: string) => void
  retryBuildPage: (taskId: string) => void
}

const isActivePhase = (phase: BuildPhase | null) =>
  Boolean(phase && !['ready', 'aborted', 'error'].includes(phase))

const applyBuildState = (set: (state: Partial<BuildState>) => void, state: BuildApiResponse) => {
  set({
    buildId: state.build_id,
    projectId: state.project_id,
    phase: state.phase,
    currentTaskId: state.current_task_id,
    buildGraph: state.build_graph,
    lastPatch: state.last_patch,
    lastValidation: state.last_validation,
    lastChecks: state.last_checks,
    lastReview: state.last_review,
    history: state.history,
    isBuilding: isActivePhase(state.phase),
  })
}

export const useBuildStore = create<BuildState>()(
  persist(
    (set, get) => ({
      buildId: null,
      projectId: null,
      phase: null,
      currentTaskId: null,
      buildGraph: null,
      lastPatch: null,
      lastValidation: null,
      lastChecks: null,
      lastReview: null,
      history: [],
      isBuilding: false,
      streamStatus: 'idle',
      streamError: null,
      isLoading: false,
      isStepping: false,
      error: null,
      liveTasks: [],
      pendingBuildPlan: null,

      async startBuild(projectId: string, seed: BuildSeed) {
        set({ isLoading: true, error: null, liveTasks: [], isBuilding: true })

        try {
          const response = await fetch(`${API_BASE_URL}/api/build/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: projectId, seed }),
          })

          if (!response.ok) {
            throw new Error(`Failed to start build: ${response.statusText}`)
          }

          const state = (await response.json()) as BuildApiResponse
          applyBuildState(set, state)
          set({ isLoading: false, streamStatus: 'connected', streamError: null })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Unknown error',
            isLoading: false,
            isBuilding: false,
          })
        }
      },

      async stepBuild(userMessage?: string) {
        const { buildId } = get()
        if (!buildId) return

        set({ isStepping: true, error: null })

        try {
          const response = await fetch(`${API_BASE_URL}/api/build/step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              build_id: buildId,
              user_message: userMessage,
            }),
          })

          if (!response.ok) {
            throw new Error(`Failed to step build: ${response.statusText}`)
          }

          const state = (await response.json()) as BuildApiResponse
          applyBuildState(set, state)
          set({ isStepping: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Unknown error',
            isStepping: false,
          })
        }
      },

      async abortBuild() {
        const { buildId } = get()
        if (!buildId) return

        set({ isLoading: true, error: null })

        try {
          const response = await fetch(`${API_BASE_URL}/api/build/${buildId}/abort`, {
            method: 'POST',
          })

          if (!response.ok) {
            throw new Error(`Failed to abort build: ${response.statusText}`)
          }

          const state = (await response.json()) as BuildApiResponse
          applyBuildState(set, state)
          set({
            isLoading: false,
            isBuilding: false,
            streamStatus: 'idle',
            streamError: null,
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Unknown error',
            isLoading: false,
            isBuilding: false,
          })
        }
      },

      async revertPatch() {
        const { buildId, projectId } = get()
        if (!buildId || !projectId) return

        set({ isLoading: true, error: null })

        try {
          const listResponse = await fetch(
            `${API_BASE_URL}/api/projects/${projectId}/snapshots`
          )

          if (!listResponse.ok) {
            throw new Error(`Failed to load snapshots: ${listResponse.statusText}`)
          }

          const snapshots = (await listResponse.json()) as Array<{ id: string }>
          const latest = snapshots[0]

          if (!latest) {
            set({ isLoading: false, error: 'No snapshots available to restore' })
            return
          }

          const restoreResponse = await fetch(
            `${API_BASE_URL}/api/projects/${projectId}/snapshots/${latest.id}/restore`,
            { method: 'POST' }
          )

          if (!restoreResponse.ok) {
            throw new Error(`Failed to restore snapshot: ${restoreResponse.statusText}`)
          }

          const stateResponse = await fetch(`${API_BASE_URL}/api/build/${buildId}`)
          if (stateResponse.ok) {
            const state = (await stateResponse.json()) as BuildApiResponse
            applyBuildState(set, state)
          }

          set({ isLoading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to revert patch',
            isLoading: false,
          })
        }
      },

      async loadBuild() {
        const { buildId } = get()
        if (!buildId) return

        set({ isLoading: true, error: null })

        try {
          const response = await fetch(`${API_BASE_URL}/api/build/${buildId}`)
          if (!response.ok) {
            if (response.status === 404 || response.status === 403) {
              get().resetBuild()
              return
            }
            throw new Error(`Failed to load build: ${response.statusText}`)
          }

          const state = (await response.json()) as BuildApiResponse
          applyBuildState(set, state)
          get().hydrateLiveTasksFromState()
          set({ isLoading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to load build',
            isLoading: false,
          })
        }
      },

      async checkPublishReady() {
        const { buildId } = get()
        if (!buildId) return false

        try {
          const response = await fetch(`${API_BASE_URL}/api/build/${buildId}/can-publish`)
          if (response.ok) {
            const result = (await response.json()) as { can_publish: boolean }
            return result.can_publish
          }
        } catch {
          return true
        }

        return false
      },

      resetBuild() {
        set({
          buildId: null,
          projectId: null,
          phase: null,
          currentTaskId: null,
          buildGraph: null,
          lastPatch: null,
          lastValidation: null,
          lastChecks: null,
          lastReview: null,
          history: [],
          isBuilding: false,
          streamStatus: 'idle',
          streamError: null,
          isLoading: false,
          isStepping: false,
          error: null,
          liveTasks: [],
          pendingBuildPlan: null,
        })
      },

      setBuildComplete() {
        set({ isBuilding: false, streamStatus: 'idle', streamError: null })
      },

      setStreamStatus(status) {
        set({ streamStatus: status })
      },

      setStreamError(error) {
        set({ streamError: error })
      },

      hydrateLiveTasksFromState() {
        const { buildGraph, buildId } = get()
        if (!buildGraph) return
        const tasks = buildGraph.tasks
          .filter((task) => task.status !== 'todo')
          .map((task) => {
            const status =
              task.status === 'done'
                ? 'done'
                : task.status === 'blocked'
                  ? 'failed'
                  : 'running'
            const type =
              task.status === 'done'
                ? 'task_done'
                : task.status === 'blocked'
                  ? 'task_failed'
                  : 'task_started'
            return {
              id: task.id,
              type,
              title: task.title,
              status,
              timestamp: Date.now(),
              session_id: buildId || 'unknown',
            } as LiveTaskMessage
          })
        set({ liveTasks: tasks })
      },

      addLiveTask(task) {
        set((state) => ({
          liveTasks: [...state.liveTasks, task],
        }))
      },

      updateLiveTask(taskId, updates) {
        set((state) => ({
          liveTasks: state.liveTasks.map((task) =>
            task.id === taskId ? { ...task, ...updates } : task
          ),
        }))
      },

      removeLiveTask(taskId) {
        set((state) => ({
          liveTasks: state.liveTasks.filter((task) => task.id !== taskId),
        }))
      },

      clearLiveTasks() {
        set({ liveTasks: [] })
      },

      handleTaskEvent(event) {
        const { liveTasks } = get()
        const existing = liveTasks.find((task) => task.id === event.id)
        const normalizedStatus =
          event.status || (event.type === 'build_complete' ? 'done' : 'running')
        const normalizedTitle =
          event.title || (event.type === 'build_complete' ? 'Build complete' : '')
        const currentBuildId = get().buildId
        if (event.session_id && currentBuildId && event.session_id !== currentBuildId) {
          get().clearLiveTasks()
        }
        if (!get().buildId && event.session_id) {
          set({
            buildId: event.session_id,
            projectId: event.project_id || get().projectId,
            isBuilding: event.type !== 'build_complete',
            streamStatus: 'connected',
            streamError: null,
          })
        } else if (event.type !== 'build_complete') {
          set({ isBuilding: true, streamStatus: 'connected', streamError: null })
        }

        if (existing) {
          get().updateLiveTask(event.id, {
            status: normalizedStatus,
            title: normalizedTitle || existing.title,
          })
        } else {
          get().addLiveTask({
            id: event.id,
            type: event.type,
            title: normalizedTitle,
            status: normalizedStatus,
            timestamp: Date.now(),
            session_id: event.session_id || get().buildId || 'unknown',
          })
        }

        if (event.type === 'build_complete') {
          get().setBuildComplete()
        }
      },

      handleCardEvent(event) {
        const cardType = event.type
        const messageType =
          cardType === 'page'
            ? 'page_created'
            : cardType === 'version'
              ? 'version_summary'
            : cardType === 'validation'
              ? 'validation_failed'
              : cardType === 'build_plan'
                ? 'build_plan'
                : cardType === 'product_doc_ready'
                  ? 'product_doc_ready'
                : 'interview'
        const currentBuildId = get().buildId
        const sessionId = event.session_id || currentBuildId
        if (event.project_id && !get().projectId) {
          set({ projectId: event.project_id })
        }
        if (event.session_id && currentBuildId && event.session_id !== currentBuildId) {
          get().clearLiveTasks()
        }
        if (!get().buildId && event.session_id) {
          set({
            buildId: event.session_id,
            projectId: event.project_id || get().projectId,
            isBuilding: true,
            streamStatus: 'connected',
            streamError: null,
          })
        } else if (sessionId) {
          set({ isBuilding: true, streamStatus: 'connected', streamError: null })
        }

        if (cardType === 'product_doc_ready') {
          const projectId = event.data?.project_id || get().projectId
          if (projectId) {
            void useProjectStore.getState().loadProductDoc(projectId)
          }
          window.dispatchEvent(new CustomEvent('product-doc-ready', { detail: { projectId } }))
        }
        const taskId = crypto.randomUUID()
        if (cardType === 'build_plan' && event.data?.approval_required) {
          set({
            pendingBuildPlan: {
              plan: event.data as BuildPlanCardData,
              sourceTaskId: taskId,
            },
          })
        }

        get().addLiveTask({
          id: taskId,
          type: messageType,
          title: '',
          status: 'done',
          timestamp: Date.now(),
          session_id: sessionId || 'unknown',
          card: {
            type: cardType,
            data: event.data,
          },
        })
      },

      handlePreviewUpdate(event) {
        window.dispatchEvent(
          new CustomEvent('preview-update', {
            detail: { pageId: event.page_id },
          })
        )
      },

      handlePlanUpdate(data) {
        const buildId = get().buildId
        if (!buildId) return
        const planId = (data as BuildPlan).id || buildId
        window.dispatchEvent(
          new CustomEvent('build-plan-update', {
            detail: { id: planId, ...data },
          })
        )
      },

      setPendingBuildPlan(plan, sourceTaskId) {
        if (!plan) {
          set({ pendingBuildPlan: null })
          return
        }
        set({
          pendingBuildPlan: {
            plan,
            sourceTaskId: sourceTaskId || crypto.randomUUID(),
          },
        })
      },

      async approveBuildPlan(pages) {
        const { projectId: storedProjectId, pendingBuildPlan } = get()
        const projectId = storedProjectId || useProjectStore.getState().project?.id
        if (!projectId) return
        if (!storedProjectId) {
          set({ projectId })
        }

        set({
          isBuilding: true,
          streamStatus: 'connected',
          streamError: null,
        })

        try {
          const response = await fetch(
            `${API_BASE_URL}/api/projects/${projectId}/build/start`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ pages }),
            }
          )

          if (!response.ok) {
            throw new Error('Failed to start build')
          }

          const { build_id } = (await response.json()) as { build_id: string }
          set({ buildId: build_id })

          if (pendingBuildPlan?.sourceTaskId) {
            get().updateLiveTask(pendingBuildPlan.sourceTaskId, {
              status: 'running',
              card: {
                type: 'build_plan',
                data: {
                  ...pendingBuildPlan.plan,
                  approval_required: false,
                  build_id,
                },
              },
            })
          }
          set({ pendingBuildPlan: null })

          const eventSource = new EventSource(
            `${API_BASE_URL}/api/build/${build_id}/stream`
          )

          eventSource.addEventListener('task', (event) => {
            const data = JSON.parse((event as MessageEvent).data)
            get().handleTaskEvent(data)
            if (data?.type === 'build_complete') {
              eventSource.close()
            }
          })

          eventSource.addEventListener('card', (event) => {
            const data = JSON.parse((event as MessageEvent).data)
            get().handleCardEvent(data)
          })

          eventSource.addEventListener('preview_update', (event) => {
            const data = JSON.parse((event as MessageEvent).data)
            get().handlePreviewUpdate(data)
          })

          eventSource.addEventListener('plan_update', (event) => {
            const data = JSON.parse((event as MessageEvent).data)
            get().handlePlanUpdate(data)
          })

          eventSource.onerror = () => {
            eventSource.close()
            set({
              isBuilding: false,
              streamStatus: 'error',
              streamError: 'Connection lost while building',
            })
          }
        } catch (error) {
          console.error('Build failed:', error)
          set({
            isBuilding: false,
            streamStatus: 'error',
            streamError: 'Failed to start build',
          })
        }
      },

      dismissBuildPlan(taskId) {
        set({ pendingBuildPlan: null })
        get().removeLiveTask(taskId)
      },

      retryBuildPage(taskId) {
        const { buildId: storedBuildId, liveTasks } = get()
        const buildId =
          storedBuildId || liveTasks.find((task) => task.session_id)?.session_id
        if (!buildId) return

        const pageId = taskId.startsWith('page-') ? taskId.slice(5) : taskId
        set({ isBuilding: true, streamStatus: 'connected', streamError: null })
        const existing = liveTasks.find((task) => task.id === taskId)
        const retryTitle = existing?.title ? `Retrying ${existing.title}` : 'Retrying page'
        get().updateLiveTask(taskId, { status: 'running', title: retryTitle })

        const eventSource = new EventSource(
          `${API_BASE_URL}/api/build/${buildId}/retry/${pageId}`
        )

        eventSource.addEventListener('task', (event) => {
          const data = JSON.parse((event as MessageEvent).data)
          get().handleTaskEvent(data)
          if (data?.type === 'build_complete') {
            eventSource.close()
          }
        })

        eventSource.addEventListener('card', (event) => {
          const data = JSON.parse((event as MessageEvent).data)
          get().handleCardEvent(data)
        })

        eventSource.addEventListener('preview_update', (event) => {
          const data = JSON.parse((event as MessageEvent).data)
          get().handlePreviewUpdate(data)
        })

        eventSource.addEventListener('plan_update', (event) => {
          const data = JSON.parse((event as MessageEvent).data)
          get().handlePlanUpdate(data)
        })

        eventSource.onerror = () => {
          eventSource.close()
          set({
            isBuilding: false,
            streamStatus: 'error',
            streamError: 'Connection lost while retrying',
          })
        }
      },
    }),
    {
      name: 'build-store',
      partialize: (state) => ({
        buildId: state.buildId,
        projectId: state.projectId,
        phase: state.phase,
      }),
    }
  )
)
