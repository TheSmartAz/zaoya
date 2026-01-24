import { Panel, PanelContent } from '@/components/layout'
import { DeviceFrame } from './DeviceFrame'
import { useProjectStore } from '@/stores'
import { cn } from '@/lib/utils'

interface PreviewPanelProps {
  className?: string
}

export function PreviewPanel({ className }: PreviewPanelProps) {
  const previewHtml = useProjectStore((state) => state.previewHtml)

  return (
    <Panel className={cn('flex-1 bg-muted/50', className)}>
      <PanelContent className="flex items-center justify-center p-8">
        <DeviceFrame>
          {previewHtml ? (
            <iframe
              srcDoc={previewHtml}
              className="w-full h-full border-0"
              sandbox="allow-scripts"
              title="Preview"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <p className="text-lg font-medium">Your page will appear here</p>
                <p className="text-sm mt-1">
                  Start by describing what you want to create
                </p>
              </div>
            </div>
          )}
        </DeviceFrame>
      </PanelContent>
    </Panel>
  )
}
