export type MessageRole = 'user' | 'assistant' | 'system'

export interface Message {
  role: MessageRole
  content: string
  timestamp: number
}

export interface Project {
  id: string
  name: string
  html: string
  js: string | null
  metadata: Record<string, unknown>
}

export interface GenerationResponse {
  html: string
  js: string | null
  metadata: Record<string, unknown>
}
