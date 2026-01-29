import { useEffect, useRef, useState } from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { MoreVertical } from 'lucide-react'
import html2canvas from 'html2canvas'
import { cn } from '@/lib/utils'
import { THUMBNAIL } from '@/constants/preview'
import type { ProjectPage } from '@/types/project'
import { useProjectStore } from '@/stores'
import { ThumbnailDisplay } from './ThumbnailDisplay'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface PageThumbnailProps {
  page: ProjectPage
  onSelect: () => void
  onRename: (newName: string) => void
  onSetAsHome: () => void
  onDelete: () => void
  isDragging?: boolean
  sortable?: boolean
}

export function PageThumbnail({
  page,
  onSelect,
  onRename,
  onSetAsHome,
  onDelete,
  isDragging = false,
  sortable = true,
}: PageThumbnailProps) {
  const [showMenu, setShowMenu] = useState(false)
  const [isRenaming, setIsRenaming] = useState(false)
  const [tempName, setTempName] = useState(page.name)
  const [isRetrying, setIsRetrying] = useState(false)
  const autoRetryAttempted = useRef(false)

  const projectId = useProjectStore((state) => state.project?.id)
  const loadPages = useProjectStore((state) => state.loadPages)

  useEffect(() => {
    setTempName(page.name)
  }, [page.name])

  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: page.id,
    disabled: !sortable,
  })
  const dragAttributes = sortable ? attributes : undefined
  const dragListeners = sortable ? listeners : undefined

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? THUMBNAIL.DRAG_OPACITY : 1,
  }

  const handleRename = (commit: boolean) => {
    const trimmed = tempName.trim()
    if (commit && trimmed && trimmed !== page.name) {
      onRename(trimmed)
    } else if (!commit) {
      setTempName(page.name)
    }
    setIsRenaming(false)
    setShowMenu(false)
  }

  const handleThumbnailRetry = async (options?: { allowServerFallback?: boolean }) => {
    if (!projectId || isRetrying) return
    setIsRetrying(true)
    const allowServerFallback = options?.allowServerFallback ?? true

    let dataUrl: string | null = null
    const html = (page.content?.html as string | undefined) || ''
    if (html) {
      try {
        dataUrl = await captureThumbnailFromHtml(html)
      } catch (error) {
        console.warn('Client-side thumbnail capture failed:', error)
      }
    }

    if (!dataUrl && !allowServerFallback) {
      setIsRetrying(false)
      return
    }

    const payload: Record<string, unknown> = {
      page_id: page.id,
      type: 'thumbnail',
    }
    if (dataUrl) {
      payload.data_url = dataUrl
    }

    try {
      await fetch(`${API_BASE_URL}/api/projects/${projectId}/thumbnails/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
    } catch (error) {
      console.error('Failed to retry thumbnail:', error)
    } finally {
      if (projectId) {
        await loadPages(projectId, { preserveSelection: true })
      }
      setIsRetrying(false)
    }
  }

  useEffect(() => {
    if (!projectId) return
    if (autoRetryAttempted.current) return
    if (page.thumbnail_status !== 'failed') return
    if (page.thumbnail_url) return
    const html = (page.content?.html as string | undefined) || ''
    if (!html) return
    autoRetryAttempted.current = true
    void handleThumbnailRetry({ allowServerFallback: false })
  }, [page.thumbnail_status, page.content, projectId])

  return (
    <div ref={setNodeRef} style={style} className="relative group" {...dragAttributes}>
      {/* Thumbnail Container */}
      <div
        className={cn(
          'relative rounded-lg overflow-hidden bg-gray-100 cursor-pointer',
          'border-2 transition-all',
          page.is_home ? 'border-blue-400' : 'border-transparent',
          'hover:border-gray-300 hover:shadow-md'
        )}
        style={{
          width: THUMBNAIL.WIDTH,
          height: THUMBNAIL.HEIGHT,
        }}
        onClick={onSelect}
        {...dragListeners}
      >
        {/* Thumbnail Preview */}
        <ThumbnailDisplay
          imageUrl={page.thumbnail_url}
          status={page.thumbnail_status}
          error={page.thumbnail_error}
          onRetry={page.thumbnail_status === 'failed' ? handleThumbnailRetry : undefined}
          isRetrying={isRetrying}
        />

        {/* Main Page Badge */}
        {page.is_home && (
          <div className="absolute top-2 left-2 bg-blue-500 text-white text-xs px-2 py-0.5 rounded">
            首页
          </div>
        )}

        {/* Hover Overlay */}
        <div
          className={cn(
            'absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors',
            'flex items-center justify-center'
          )}
        >
          <span
            className={cn(
              'text-white text-sm font-medium px-3 py-1 rounded bg-black/50',
              'opacity-0 group-hover:opacity-100 transition-opacity'
            )}
          >
            点击预览
          </span>
        </div>

        {/* Menu Button (top-right) */}
        <button
          onPointerDown={(event) => event.stopPropagation()}
          onClick={(event) => {
            event.stopPropagation()
            setShowMenu((prev) => !prev)
          }}
          className={cn(
            'absolute top-2 right-2 p-1 rounded bg-white/80 hover:bg-white',
            'opacity-0 group-hover:opacity-100 transition-opacity',
            'shadow-sm'
          )}
          aria-label="Page actions"
          type="button"
        >
          <MoreVertical className="w-4 h-4 text-gray-600" />
        </button>
      </div>

      {/* Page Info */}
      <div className="mt-2 text-center">
        {isRenaming ? (
          <input
            type="text"
            value={tempName}
            onChange={(event) => setTempName(event.target.value)}
            onBlur={() => handleRename(true)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') handleRename(true)
              if (event.key === 'Escape') handleRename(false)
            }}
            className="text-sm font-medium text-center border-b border-blue-500 outline-none w-full"
            autoFocus
          />
        ) : (
          <div className="text-sm font-medium text-gray-800">{page.name}</div>
        )}
        <code className="text-xs text-gray-500">{page.path}</code>
      </div>

      {/* Actions Menu */}
      {showMenu && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />

          {/* Menu */}
          <div className="absolute top-10 right-0 z-20 bg-white rounded-lg shadow-lg border py-1 min-w-[120px]">
            <MenuButton
              onClick={() => {
                setIsRenaming(true)
                setShowMenu(false)
              }}
            >
              重命名
            </MenuButton>

            {!page.is_home && (
              <MenuButton
                onClick={() => {
                  onSetAsHome()
                  setShowMenu(false)
                }}
              >
                设为首页
              </MenuButton>
            )}

            <div className="border-t my-1" />

            {!page.is_home && (
              <MenuButton
                onClick={() => {
                  onDelete()
                  setShowMenu(false)
                }}
                className="text-red-600 hover:bg-red-50"
              >
                删除
              </MenuButton>
            )}
          </div>
        </>
      )}
    </div>
  )
}

async function captureThumbnailFromHtml(rawHtml: string): Promise<string> {
  const iframe = document.createElement('iframe')
  iframe.style.position = 'absolute'
  iframe.style.left = '-9999px'
  iframe.style.top = '0'
  iframe.style.width = `${THUMBNAIL.VIEWPORT_WIDTH}px`
  iframe.style.height = `${THUMBNAIL.VIEWPORT_HEIGHT}px`
  iframe.style.border = '0'

  const srcDoc = buildCaptureDocument(rawHtml)

  const loadPromise = new Promise<void>((resolve) => {
    iframe.onload = () => resolve()
  })

  iframe.srcdoc = srcDoc
  document.body.appendChild(iframe)

  try {
    await loadPromise
    await new Promise((resolve) => setTimeout(resolve, 600))
    const doc = iframe.contentDocument
    if (!doc) throw new Error('Missing iframe document')
    const canvas = await html2canvas(doc.body, {
      backgroundColor: '#ffffff',
      width: THUMBNAIL.VIEWPORT_WIDTH,
      height: THUMBNAIL.VIEWPORT_HEIGHT,
      windowWidth: THUMBNAIL.VIEWPORT_WIDTH,
      windowHeight: THUMBNAIL.VIEWPORT_HEIGHT,
      useCORS: true,
      scale: 2,
      scrollX: 0,
      scrollY: 0,
    })
    return canvas.toDataURL('image/png')
  } finally {
    iframe.remove()
  }
}

function buildCaptureDocument(rawHtml: string): string {
  const match = rawHtml.match(/<body[^>]*>([\s\S]*?)<\/body>/i)
  let bodyHtml = match?.[1] ? match[1] : rawHtml
  bodyHtml = bodyHtml.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')

  return `<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <script src=\"https://cdn.tailwindcss.com\"></script>
    <style>body{margin:0}</style>
  </head>
  <body class=\"antialiased bg-white\">
    ${bodyHtml}
  </body>
</html>`
}

function MenuButton({
  children,
  onClick,
  className,
}: {
  children: React.ReactNode
  onClick: () => void
  className?: string
}) {
  return (
    <button
      onClick={onClick}
      className={cn('w-full px-4 py-2 text-left text-sm hover:bg-gray-50', className)}
      type="button"
    >
      {children}
    </button>
  )
}
