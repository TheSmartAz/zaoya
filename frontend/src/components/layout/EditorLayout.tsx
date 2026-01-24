import { cn } from '@/lib/utils'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { ResizablePanelGroup } from '@/components/ui/resizable'

interface EditorLayoutProps {
  children: React.ReactNode
  projectName?: string
  className?: string
}

export function EditorLayout({
  children,
  projectName,
  className,
}: EditorLayoutProps) {
  return (
    <div className={cn('h-screen flex flex-col', className)}>
      <Header projectName={projectName} />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 flex overflow-hidden">
          <ResizablePanelGroup orientation="horizontal" id="editor-layout" className="h-full">
            {children}
          </ResizablePanelGroup>
        </main>
      </div>
    </div>
  )
}
