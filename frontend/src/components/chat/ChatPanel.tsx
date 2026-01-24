import { Panel, PanelContent } from '@/components/layout'
import { MessageList } from './MessageList'
import { InputBar } from './InputBar'
import { useChatStore } from '@/stores'
import { cn } from '@/lib/utils'

interface ChatPanelProps {
  className?: string
}

export function ChatPanel({ className }: ChatPanelProps) {
  const { messages, isLoading, addMessage } = useChatStore()

  const handleSend = (content: string) => {
    addMessage({ role: 'user', content })

    // Simulate AI response (replace with real API later)
    useChatStore.getState().setLoading(true)
    setTimeout(() => {
      addMessage({
        role: 'assistant',
        content: `I'll help you create that. Let me ask a few questions to understand what you need...`,
      })
      useChatStore.getState().setLoading(false)
    }, 500)
  }

  return (
    <Panel className={cn('w-80 border-r', className)}>
      <PanelContent className="flex flex-col">
        <MessageList messages={messages} className="flex-1" />
        <InputBar onSend={handleSend} disabled={isLoading} />
      </PanelContent>
    </Panel>
  )
}
