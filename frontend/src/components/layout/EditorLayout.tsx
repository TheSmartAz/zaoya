import { cn } from '@/lib/utils'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { ResizablePanelGroup } from '@/components/ui/resizable'

interface EditorLayoutProps {
  children: React.ReactNode
  projectName?: string
  className?: string
  rightPanel?: React.ReactNode
  leftPanel?: React.ReactNode
}

export function EditorLayout({
  children,
  projectName,
  className,
  rightPanel,
  leftPanel,
}: EditorLayoutProps) {
  return (
    <div className={cn('h-screen flex flex-col', className)}>
      <Header projectName={projectName} />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        {leftPanel && (
          <aside className="w-56 border-r bg-background flex flex-col">
            {leftPanel}
          </aside>
        )}
        <div className="flex-1 flex overflow-hidden">
          <main className="flex-1 flex overflow-hidden">
            <ResizablePanelGroup
              orientation="horizontal"
              id="editor-layout"
              className="h-full"
            >
              {children}
            </ResizablePanelGroup>
          </main>
          {rightPanel && (
            <aside className="w-80 border-l bg-background overflow-hidden flex flex-col">
              {rightPanel}
            </aside>
          )}
        </div>
      </div>
    </div>
  )
}
