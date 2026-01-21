import { useCallback, useEffect } from 'react'
import { useChatStore } from '@/stores/chatStore'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

interface SendMessageOptions {
  template?: { id: string; name: string; systemPromptAddition: string } | null
  templateInputs?: Record<string, string>
  interviewAnswers?: Record<string, string>
  isQuickAction?: boolean
}

export function useChatStream() {
  const {
    messages,
    isStreaming,
    selectedModel,
    availableModels,
    addMessage,
    updateMessage,
    setStreaming,
    setAvailableModels,
    setSelectedModel
  } = useChatStore()

  // Load available models on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/chat/models`)
      .then(res => res.json())
      .then(data => setAvailableModels(data.models || []))
      .catch(() => console.error('Failed to load models'))
  }, [setAvailableModels])

  const sendMessage = useCallback(async (content: string, options: SendMessageOptions = {}) => {
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content,
      timestamp: Date.now(),
      meta: options.isQuickAction ? { isQuickAction: true } : undefined
    }

    addMessage(userMessage)
    setStreaming(true)

    // Create placeholder for assistant response
    const assistantId = (Date.now() + 1).toString()
    const assistantMessage = {
      id: assistantId,
      role: 'assistant' as const,
      content: '',
      timestamp: Date.now()
    }
    addMessage(assistantMessage)

    try {
      const outgoingMessages = [...messages, userMessage]
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: outgoingMessages.map(m => ({ role: m.role, content: m.content })),
          model: selectedModel,
          stream: true,
          template: options.template || undefined,
          templateInputs: options.templateInputs || undefined,
          interviewAnswers: options.interviewAnswers || undefined,
          isQuickAction: options.isQuickAction || false
        })
      })

      if (!response.ok) throw new Error('API request failed')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('Cannot read response')

      const decoder = new TextDecoder()
      let buffer = ''
      let accumulatedContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') continue

            try {
              const json = JSON.parse(data)
              const content = json.choices?.[0]?.delta?.content
              if (content) {
                accumulatedContent += content
                updateMessage(assistantId, accumulatedContent)
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      updateMessage(assistantId, 'Sorry, an error occurred. Please try again.')
    } finally {
      setStreaming(false)
    }
  }, [messages, selectedModel, addMessage, updateMessage, setStreaming])

  return {
    messages,
    isStreaming,
    selectedModel,
    availableModels,
    sendMessage,
    setSelectedModel
  }
}
