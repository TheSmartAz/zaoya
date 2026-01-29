import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { EditorLayout } from '@/components/layout'
import { ChatPanel } from '@/components/chat'
import { PreviewPanel } from '@/components/preview'
import { ResizableHandle } from '@/components/ui/resizable'
import { useProjectStore } from '@/stores'
import { BuildTimeline } from '@/components/build/BuildTimeline'
import { VersionHistoryPanel } from '@/components/version/VersionHistoryPanel'

export function EditorPage() {
  const params = useParams()
  const projectId = params.projectId

  const {
    project,
    pages,
    currentPageId,
    loadProject,
    loadPages,
    setCurrentPage,
  } = useProjectStore()

  const [rightPanelMode, setRightPanelMode] = useState<'build' | 'history' | 'hidden'>(
    'build'
  )
  const currentPageRef = useRef<string | null>(currentPageId)

  useEffect(() => {
    if (projectId) {
      void loadProject(projectId).then(() => loadPages(projectId))
    }
  }, [projectId, loadProject, loadPages])

  useEffect(() => {
    currentPageRef.current = currentPageId
  }, [currentPageId])

  useEffect(() => {
    if (!projectId) return

    const handlePreviewUpdate = (event: Event) => {
      const detail = (event as CustomEvent<{ pageId?: string }>).detail
      const updatedPageId = detail?.pageId
      void loadPages(projectId, { preserveSelection: true }).then(() => {
        if (
          updatedPageId &&
          (!currentPageRef.current || currentPageRef.current === updatedPageId)
        ) {
          setCurrentPage(updatedPageId)
        }
      })
    }

    window.addEventListener('preview-update', handlePreviewUpdate as EventListener)
    return () => {
      window.removeEventListener('preview-update', handlePreviewUpdate as EventListener)
    }
  }, [projectId, loadPages, setCurrentPage])

  useEffect(() => {
    const handleOpenHistory = () => setRightPanelMode('history')
    window.addEventListener('open-version-history', handleOpenHistory)
    return () => window.removeEventListener('open-version-history', handleOpenHistory)
  }, [])

  const currentPage = pages.find((p) => p.id === currentPageId)

  return (
    <>
      <EditorLayout
        projectName={project?.name}
        rightPanel={
          rightPanelMode === 'build' ? (
            <BuildTimeline
              onCollapse={() => setRightPanelMode('hidden')}
              onShowHistory={() => setRightPanelMode('history')}
            />
          ) : rightPanelMode === 'history' ? (
            <VersionHistoryPanel
              onCollapse={() => setRightPanelMode('hidden')}
              onShowBuild={() => setRightPanelMode('build')}
            />
          ) : null
        }
      >
        <ChatPanel />
        <ResizableHandle withHandle panelIds={['chat-panel', 'preview-panel']} />
        <PreviewPanel page={currentPage} projectId={project?.id} />
      </EditorLayout>
      {rightPanelMode === 'hidden' && (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
          <button
            className="bg-primary text-primary-foreground px-4 py-2 rounded-lg shadow-lg"
            onClick={() => setRightPanelMode('build')}
          >
            Build Timeline
          </button>
          <button
            className="bg-white text-gray-800 border px-4 py-2 rounded-lg shadow-lg"
            onClick={() => setRightPanelMode('history')}
          >
            Version History
          </button>
        </div>
      )}
    </>
  )
}
