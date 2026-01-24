import { EditorLayout } from '@/components/layout'
import { ChatPanel } from '@/components/chat'
import { PreviewPanel } from '@/components/preview'

export function EditorPage() {
  return (
    <EditorLayout projectName="My Landing Page">
      <ChatPanel />
      <PreviewPanel />
    </EditorLayout>
  )
}
