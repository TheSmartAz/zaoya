import { create } from 'zustand'
import type { ChatMessage } from '@/types/chat'

interface ChatStore {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null

  // Actions
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => string
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearMessages: () => void
  appendToMessage: (id: string, content: string) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,
  error: null,

  addMessage: (message) => {
    const id = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id,
          timestamp: Date.now(),
        },
      ],
    }))
    return id
  },

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearMessages: () => set({ messages: [] }),

  appendToMessage: (id, content) =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === id
          ? { ...message, content: message.content + content }
          : message
      ),
    })),
}))
