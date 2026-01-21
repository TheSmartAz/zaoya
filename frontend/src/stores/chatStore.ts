import { create } from 'zustand'
import { ChatMessage } from '@/types'

interface ChatState {
  messages: ChatMessage[]
  isStreaming: boolean
  currentStreamText: string
  selectedModel: string
  availableModels: Array<{ id: string; name: string; provider: string }>
  interviewAnswers: Record<string, string>

  // Actions
  addMessage: (message: ChatMessage) => void
  updateMessage: (id: string, content: string) => void
  setStreaming: (streaming: boolean) => void
  appendStreamText: (text: string) => void
  clearStreamText: () => void
  setSelectedModel: (model: string) => void
  setAvailableModels: (models: Array<{ id: string; name: string; provider: string }>) => void
  setInterviewAnswers: (answers: Record<string, string>) => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [
    {
      id: '1',
      role: 'assistant',
      content: '👋 Hi! I\'m Zaoya. I help you create mobile web pages.\n\nTry asking:\n• "Create a birthday card with pink theme"\n• "Make a simple todo list app"\n• "Design a landing page for a coffee shop"',
      timestamp: Date.now()
    }
  ],
  isStreaming: false,
  currentStreamText: '',
  selectedModel: 'glm-4.7',
  availableModels: [],
  interviewAnswers: {},

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  updateMessage: (id, content) => set((state) => ({
    messages: state.messages.map(msg =>
      msg.id === id ? { ...msg, content } : msg
    )
  })),

  setStreaming: (streaming) => set({ isStreaming: streaming }),

  appendStreamText: (text) => set((state) => ({
    currentStreamText: state.currentStreamText + text
  })),

  clearStreamText: () => set({ currentStreamText: '' }),

  setSelectedModel: (model) => set({ selectedModel: model }),

  setAvailableModels: (models) => set({ availableModels: models }),

  setInterviewAnswers: (answers) => set({ interviewAnswers: answers })
}))
