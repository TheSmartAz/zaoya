import { useEffect } from 'react'
import { EditorLayout } from '@/components/layout'
import { ChatPanel } from '@/components/chat'
import { PreviewPanel } from '@/components/preview'
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
      <PreviewPanel />
    </EditorLayout>
  )
}
