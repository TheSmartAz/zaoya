import { describe, expect, it, beforeEach, vi } from 'vitest'
import { useBuildStore } from '../buildStore'

const resetStore = () => {
  useBuildStore.getState().resetBuild()
  useBuildStore.setState({ liveTasks: [] })
}

describe('buildStore live task handling', () => {
  beforeEach(() => {
    resetStore()
  })

  it('adds task events and sets build session details', () => {
    useBuildStore.getState().handleTaskEvent({
      id: 'task-1',
      type: 'task_started',
      title: 'Planning',
      status: 'running',
      session_id: 'build-123',
      project_id: 'project-abc',
    })

    const state = useBuildStore.getState()
    expect(state.buildId).toBe('build-123')
    expect(state.projectId).toBe('project-abc')
    expect(state.isBuilding).toBe(true)
    expect(state.liveTasks).toHaveLength(1)
    expect(state.liveTasks[0].status).toBe('running')

    useBuildStore.getState().handleTaskEvent({
      id: 'task-1',
      type: 'task_done',
      title: 'Planning',
      status: 'done',
      session_id: 'build-123',
    })

    const updated = useBuildStore.getState()
    expect(updated.liveTasks[0].status).toBe('done')
  })

  it('marks build complete when build_complete event arrives', () => {
    useBuildStore.getState().handleTaskEvent({
      id: 'build-build-123',
      type: 'build_complete',
      title: 'Build complete',
      session_id: 'build-123',
    })

    expect(useBuildStore.getState().isBuilding).toBe(false)
  })

  it('adds card events with correct message type', () => {
    useBuildStore.getState().handleCardEvent({
      type: 'build_plan',
      data: {
        pages: [],
        tasks: [],
        estimated_tasks: 3,
        approval_required: true,
      },
      session_id: 'build-123',
    })

    const task = useBuildStore.getState().liveTasks[0]
    expect(task.type).toBe('build_plan')
    expect(task.card?.type).toBe('build_plan')
    expect(useBuildStore.getState().pendingBuildPlan).not.toBeNull()
  })

  it('dispatches preview update events', () => {
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

    useBuildStore.getState().handlePreviewUpdate({ page_id: 'page-1' })

    expect(dispatchSpy).toHaveBeenCalledTimes(1)
    dispatchSpy.mockRestore()
  })
})
