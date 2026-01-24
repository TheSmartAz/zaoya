export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  type?: 'text' | 'interview' | 'plan'
}

export interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
}
