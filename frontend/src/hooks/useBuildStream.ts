import { useEffect, useRef } from 'react'
import { useBuildStore } from '@/stores'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function useBuildStream(projectId: string) {
  const buildId = useBuildStore((state) => state.buildId)
  const buildProjectId = useBuildStore((state) => state.projectId)
  const isBuilding = useBuildStore((state) => state.isBuilding)
  const streamStatus = useBuildStore((state) => state.streamStatus)
  const setStreamStatus = useBuildStore((state) => state.setStreamStatus)
  const setStreamError = useBuildStore((state) => state.setStreamError)
  const loadBuild = useBuildStore((state) => state.loadBuild)
  const resetBuild = useBuildStore((state) => state.resetBuild)
  const handleTaskEvent = useBuildStore((state) => state.handleTaskEvent)
  const handleCardEvent = useBuildStore((state) => state.handleCardEvent)
  const handlePreviewUpdate = useBuildStore((state) => state.handlePreviewUpdate)
  const handlePlanUpdate = useBuildStore((state) => state.handlePlanUpdate)

  const eventSourceRef = useRef<EventSource | null>(null)
  const retryRef = useRef(0)
  const retryTimeoutRef = useRef<number | null>(null)

  useEffect(() => {
    if (!projectId || !buildProjectId) return
    if (projectId !== buildProjectId) {
      resetBuild()
    }
  }, [projectId, buildProjectId, resetBuild])

  useEffect(() => {
    if (!buildId || streamStatus !== 'idle') return
    const restore = async () => {
      await loadBuild()
      if (useBuildStore.getState().isBuilding) {
        setStreamStatus('reconnecting')
      }
    }
    void restore()
  }, [buildId, streamStatus, loadBuild, setStreamStatus])

  useEffect(() => {
    const handleSseEvent = (event: Event) => {
      const detail = (event as CustomEvent<{ event: string; data: any }>).detail
      if (!detail) return

      switch (detail.event) {
        case 'task':
          handleTaskEvent(detail.data)
          break
        case 'card':
          handleCardEvent(detail.data)
          break
        case 'preview_update':
          handlePreviewUpdate(detail.data)
          break
        case 'plan_update':
          handlePlanUpdate(detail.data)
          break
        default:
          break
      }
    }

    window.addEventListener('build-sse-event', handleSseEvent as EventListener)
    return () => {
      window.removeEventListener('build-sse-event', handleSseEvent as EventListener)
    }
  }, [handleTaskEvent, handleCardEvent, handlePreviewUpdate, handlePlanUpdate])

  useEffect(() => {
    if (!buildId || !isBuilding) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      return
    }

    if (streamStatus !== 'reconnecting') {
      return
    }

    const connect = () => {
      const url = `${API_BASE_URL}/api/build/${buildId}/stream`
      const source = new EventSource(url)
      eventSourceRef.current = source

      source.addEventListener('open', () => {
        retryRef.current = 0
        setStreamStatus('connected')
        setStreamError(null)
      })

      source.addEventListener('task', (event) => {
        const data = JSON.parse((event as MessageEvent).data)
        handleTaskEvent(data)
      })

      source.addEventListener('card', (event) => {
        const data = JSON.parse((event as MessageEvent).data)
        handleCardEvent(data)
      })

      source.addEventListener('preview_update', (event) => {
        const data = JSON.parse((event as MessageEvent).data)
        handlePreviewUpdate(data)
      })

      source.addEventListener('plan_update', (event) => {
        const data = JSON.parse((event as MessageEvent).data)
        handlePlanUpdate(data)
      })

      source.addEventListener('error', () => {
        source.close()
        eventSourceRef.current = null
        setStreamStatus('reconnecting')
        setStreamError('Connection lost, retrying...')
        void loadBuild()

        const retryDelay = Math.min(1000 * 2 ** retryRef.current, 10000)
        retryRef.current += 1
        if (retryTimeoutRef.current) {
          window.clearTimeout(retryTimeoutRef.current)
        }
        retryTimeoutRef.current = window.setTimeout(connect, retryDelay)
      })
    }

    connect()

    return () => {
      if (retryTimeoutRef.current) {
        window.clearTimeout(retryTimeoutRef.current)
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [
    buildId,
    isBuilding,
    streamStatus,
    setStreamStatus,
    setStreamError,
    handleTaskEvent,
    handleCardEvent,
    handlePreviewUpdate,
    handlePlanUpdate,
    loadBuild,
  ])
}
