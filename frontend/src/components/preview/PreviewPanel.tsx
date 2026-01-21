import { useRef, useEffect } from 'react'
import { buildPreviewDocument } from '@/utils/previewBuilder'

interface PreviewPanelProps {
  html: string
  js: string | null
}

export function PreviewPanel({ html, js }: PreviewPanelProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)

  useEffect(() => {
    const iframe = iframeRef.current
    if (!iframe) return

    if (!html) {
      iframe.srcdoc = ''
      return
    }

    const doc = buildPreviewDocument(html, js)
    iframe.srcdoc = doc
  }, [html, js])

  if (!html) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        <div className="text-center">
          <p className="text-lg">📱</p>
          <p className="text-sm">Preview will appear here</p>
        </div>
      </div>
    )
  }

  return (
    <iframe
      ref={iframeRef}
      sandbox="allow-scripts"
      className="w-full h-full border-0"
      title="Preview"
    />
  )
}
