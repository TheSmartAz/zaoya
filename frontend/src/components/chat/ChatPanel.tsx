import { useState } from 'react'
import { Panel, PanelContent } from '@/components/layout'
import { MessageList, type Message } from './MessageList'
import { InputBar } from './InputBar'
import { cn } from '@/lib/utils'

interface ChatPanelProps {
  className?: string
}

export function ChatPanel({ className }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])

  const handleSend = (content: string) => {
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
    }
    setMessages((prev) => [...prev, userMessage])

    // Simulate AI response (replace with real API later)
    setTimeout(() => {
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: `I'll help you create that. Let me ask a few questions to understand what you need...`,
      }
      setMessages((prev) => [...prev, aiMessage])
    }, 500)
  }

  return (
    <Panel className={cn('w-80 border-r', className)}>
      <PanelContent className="flex flex-col">
        <MessageList messages={messages} className="flex-1" />
        <InputBar onSend={handleSend} />
      </PanelContent>
    </Panel>
  )
}
