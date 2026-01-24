import { useEffect } from 'react'
import { EditorLayout } from '@/components/layout'
import { ChatPanel } from '@/components/chat'
import { PreviewPanel } from '@/components/preview'
import { ResizableHandle } from '@/components/ui/resizable'
import { useProjectStore } from '@/stores'

export function EditorPage() {
  const { project, createProject } = useProjectStore()

  useEffect(() => {
    if (!project) {
      createProject('My Landing Page')
    }
  }, [project, createProject])

  return (
    <EditorLayout projectName={project?.name}>
      <ChatPanel />
      <ResizableHandle withHandle panelIds={['chat-panel', 'preview-panel']} />
      <PreviewPanel />
    </EditorLayout>
  )
}
