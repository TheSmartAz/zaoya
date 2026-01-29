import { useEffect, useState } from 'react'
import { Panel, PanelContent } from '@/components/layout'
import { ResizablePanel } from '@/components/ui/resizable'
import { useProjectStore, useVersionStore } from '@/stores'
import { cn } from '@/lib/utils'
import type { ProjectPage } from '@/types/project'
import { PreviewToolbar } from './PreviewToolbar'
import { ProductDocView } from './ProductDocView'
import { PreviewIframe } from './PreviewIframe'
import { SimulationReportPanel } from './SimulationReportPanel'
import { MultiPageOverview } from './MultiPageOverview'
import { CodeTab } from './CodeTab'

interface PreviewPanelProps {
  className?: string
  projectId?: string
  page?: ProjectPage
}

export function PreviewPanel({ className, projectId, page }: PreviewPanelProps) {
  const [view, setView] = useState<'preview' | 'productDoc' | 'code'>('preview')
  const [previewMode, setPreviewMode] = useState<'preview' | 'simulation'>(() =>
    projectId ? 'simulation' : 'preview'
  )
  const [previewModeTouched, setPreviewModeTouched] = useState(false)
  const [codeFocus, setCodeFocus] = useState<{
    path?: string
    line?: number
  } | null>(null)
  const [isOverviewOpen, setOverviewOpen] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const {
    pages,
    currentPageId,
    productDoc,
    isLoadingProductDoc,
    setCurrentPage,
    loadPages,
    reorderPages,
    renamePage,
    setAsHomePage,
    deletePage,
    loadProductDoc,
    previewHtml,
    versionPreview,
    setVersionPreview,
    project,
  } = useProjectStore()
  const activeVersionId = useVersionStore((state) => state.activeVersionId)
  const setActiveVersion = useVersionStore((state) => state.setActiveVersion)

  const currentPage =
    page || pages.find((p) => p.id === currentPageId) || pages[0] || null
  const isVersionPreview = Boolean(versionPreview)
  const hasVersionContext = isVersionPreview || Boolean(activeVersionId)
  const previewPage = isVersionPreview
    ? {
        id: versionPreview?.pageId || 'version',
        name: versionPreview?.pageName || 'Version Preview',
        path: versionPreview?.pagePath || '',
      }
    : currentPage
  const htmlContent = isVersionPreview
    ? versionPreview?.html || null
    : (currentPage?.content?.html as string | undefined) || previewHtml
  const simulationAvailable = Boolean(projectId && currentPage && !isVersionPreview)

  useEffect(() => {
    if (projectId) {
      void loadProductDoc(projectId)
    }
  }, [projectId, loadProductDoc])

  useEffect(() => {
    setPreviewModeTouched(false)
    setPreviewMode(projectId ? 'simulation' : 'preview')
  }, [projectId])

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ pageId?: string }>).detail
      if (!detail?.pageId || detail.pageId === currentPageId) {
        setRefreshKey((prev) => prev + 1)
      }
    }

    window.addEventListener('preview-update', handler as EventListener)
    return () => window.removeEventListener('preview-update', handler as EventListener)
  }, [currentPageId])

  useEffect(() => {
    if (!projectId) return
    const hasPending = pages.some(
      (page) =>
        page.thumbnail_status &&
        page.thumbnail_status !== 'done' &&
        page.thumbnail_status !== 'failed'
    )
    if (!hasPending) return
    const interval = setInterval(() => {
      void loadPages(projectId, { preserveSelection: true })
    }, 5000)
    return () => clearInterval(interval)
  }, [pages, projectId, loadPages])

  useEffect(() => {
    const handleProductDocReady = () => {
      if (projectId) {
        void loadProductDoc(projectId)
      }
      setView('productDoc')
    }

    window.addEventListener('product-doc-ready', handleProductDocReady)
    window.addEventListener('open-product-doc', handleProductDocReady)
    return () => {
      window.removeEventListener('product-doc-ready', handleProductDocReady)
      window.removeEventListener('open-product-doc', handleProductDocReady)
    }
  }, [projectId, loadProductDoc])

  useEffect(() => {
    const handleOpenPreview = (event: Event) => {
      const detail = (event as CustomEvent<{ pageId?: string }>).detail
      setOverviewOpen(false)
      setView('preview')
      setVersionPreview(null)
      setActiveVersion(null)
      if (detail?.pageId) {
        setCurrentPage(detail.pageId)
      }
    }

    const handleOpenOverview = () => {
      setView('preview')
      setOverviewOpen(true)
      setVersionPreview(null)
      setActiveVersion(null)
    }

    const handleOpenCode = (event: Event) => {
      const detail = (event as CustomEvent<{ path?: string; line?: number }>).detail
      setCodeFocus(detail ? { path: detail.path, line: detail.line } : null)
      setView('code')
    }

    window.addEventListener('open-preview', handleOpenPreview as EventListener)
    window.addEventListener('open-overview', handleOpenOverview as EventListener)
    window.addEventListener('open-code-view', handleOpenCode as EventListener)
    return () => {
      window.removeEventListener('open-preview', handleOpenPreview as EventListener)
      window.removeEventListener('open-overview', handleOpenOverview as EventListener)
      window.removeEventListener('open-code-view', handleOpenCode as EventListener)
    }
  }, [setCurrentPage, setActiveVersion, setVersionPreview])

  useEffect(() => {
    const handleVersionPreview = (
      event: Event
    ) => {
      const detail = (
        event as CustomEvent<{
          versionId: string
          pageId?: string | null
          pageName?: string | null
          pagePath?: string | null
          html: string
          js?: string | null
        }>
      ).detail
      if (!detail?.versionId || !detail?.html) return
      setOverviewOpen(false)
      setView('preview')
      setVersionPreview({
        versionId: detail.versionId,
        pageId: detail.pageId,
        pageName: detail.pageName,
        pagePath: detail.pagePath,
        html: detail.html,
        js: detail.js,
      })
    }

    window.addEventListener('open-version-preview', handleVersionPreview as EventListener)
    return () =>
      window.removeEventListener(
        'open-version-preview',
        handleVersionPreview as EventListener
      )
  }, [setVersionPreview])

  useEffect(() => {
    if (!productDoc && view === 'productDoc' && !isLoadingProductDoc) {
      setView('preview')
    }
  }, [productDoc, view, isLoadingProductDoc])

  useEffect(() => {
    if (!project?.can_view_code && view === 'code') {
      setView('preview')
    }
  }, [project?.can_view_code, view])

  useEffect(() => {
    if (!simulationAvailable && previewMode === 'simulation') {
      setPreviewMode('preview')
    }
  }, [previewMode, simulationAvailable])

  useEffect(() => {
    if (simulationAvailable && !previewModeTouched && previewMode !== 'simulation') {
      setPreviewMode('simulation')
    }
  }, [simulationAvailable, previewModeTouched, previewMode])

  const handleViewChange = (nextView: 'preview' | 'productDoc' | 'code') => {
    if (nextView === 'code' && !versionPreview) {
      setActiveVersion(null)
    }
    if (nextView === 'preview' && !versionPreview) {
      setActiveVersion(null)
    }
    if (nextView !== 'code') {
      setCodeFocus(null)
    }
    setView(nextView)
  }

  const handlePreviewModeChange = (mode: 'preview' | 'simulation') => {
    setPreviewModeTouched(true)
    setPreviewMode(mode)
  }

  return (
    <ResizablePanel id="preview-panel" defaultSize={75} minSize={40}>
      <Panel className={cn('flex-1 bg-muted/50', className)}>
        <PreviewToolbar
          currentView={view}
          previewMode={previewMode}
          currentPage={previewPage}
          pages={isVersionPreview ? [] : pages}
          hasProductDoc={!!productDoc}
          canViewCode={!!project?.can_view_code}
          simulationAvailable={simulationAvailable}
          versionLabel={hasVersionContext ? 'Viewing version' : undefined}
          onExitVersion={
            hasVersionContext
              ? () => {
                  setVersionPreview(null)
                  setActiveVersion(null)
                }
              : undefined
          }
          onViewChange={handleViewChange}
          onPreviewModeChange={handlePreviewModeChange}
          onPageChange={setCurrentPage}
          onOpenOverview={() => setOverviewOpen(true)}
        />
        {previewMode === 'simulation' && view === 'preview' && (
          <SimulationReportPanel projectId={projectId || undefined} active />
        )}
        <PanelContent>
          {isOverviewOpen ? (
            <MultiPageOverview
              pages={pages}
              onBack={() => setOverviewOpen(false)}
              onSelectPage={(pageId) => {
                setCurrentPage(pageId)
                setOverviewOpen(false)
              }}
              onReorder={reorderPages}
              onRename={renamePage}
              onSetAsHome={setAsHomePage}
              onDelete={deletePage}
            />
          ) : view === 'productDoc' ? (
            productDoc ? (
              <ProductDocView doc={productDoc} />
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                {isLoadingProductDoc ? 'Loading ProductDoc...' : 'ProductDoc not available yet.'}
              </div>
            )
          ) : view === 'code' ? (
            projectId ? (
              <CodeTab projectId={projectId} versionId={activeVersionId} focus={codeFocus} />
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                Select a project to view code.
              </div>
            )
          ) : (
            <PreviewIframe
              html={htmlContent || null}
              page={previewPage}
              projectId={projectId}
              mode={previewMode}
              refreshKey={refreshKey}
            />
          )}
        </PanelContent>
      </Panel>
    </ResizablePanel>
  )
}
