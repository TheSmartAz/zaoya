import { cn } from '@/lib/utils'
import { DeviceFrame } from './DeviceFrame'
import type { ProjectPage } from '@/types/project'

interface PreviewIframeProps {
  html: string | null
  page?: ProjectPage | null
  projectId?: string
  mode?: 'preview' | 'simulation'
  className?: string
  refreshKey?: number
}

export function PreviewIframe({
  html,
  page,
  projectId,
  mode = 'preview',
  className,
  refreshKey,
}: PreviewIframeProps) {
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  const getSimulationUrl = () => {
    if (!projectId) return null
    if (!page) return `${apiBase}/p-sim/${projectId}`
    const slug =
      page.slug ||
      (page.path && page.path !== '/' ? page.path.replace(/^\//, '') : '')
    return slug ? `${apiBase}/p-sim/${projectId}/${slug}` : `${apiBase}/p-sim/${projectId}`
  }

  const buildPreviewDocument = (rawHtml: string) => {
    const match = rawHtml.match(/<body[^>]*>([\s\S]*?)<\/body>/i)
    const bodyHtml = match?.[1] ? match[1] : rawHtml
    return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Zaoya Preview</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="antialiased">
    ${bodyHtml}
    <script src="/zaoya-runtime.js" defer></script>
  </body>
</html>`
  }

  const useSimulation = mode === 'simulation' && Boolean(projectId)
  const simulationUrl = useSimulation ? getSimulationUrl() : null
  const shouldShowIframe = useSimulation ? Boolean(simulationUrl) : Boolean(html)

  return (
    <div className={cn('flex h-full items-center justify-center p-6', className)}>
      <DeviceFrame>
        {shouldShowIframe ? (
          <iframe
            key={refreshKey}
            src={useSimulation ? simulationUrl || undefined : undefined}
            srcDoc={useSimulation || !html ? undefined : buildPreviewDocument(html)}
            className="h-full w-full border-0"
            sandbox="allow-scripts"
            title={useSimulation ? 'Publish Simulation' : 'Preview'}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-base font-medium">Your page will appear here</p>
              <p className="mt-1 text-sm">
                {page
                  ? 'Chat with AI to generate content for this page'
                  : 'Select or create a page to start'}
              </p>
            </div>
          </div>
        )}
      </DeviceFrame>
    </div>
  )
}
