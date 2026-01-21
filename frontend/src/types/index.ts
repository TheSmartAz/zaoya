/** Chat message metadata */
export interface ChatMessageMeta {
  isQuickAction?: boolean;
}

/** Chat message */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  meta?: ChatMessageMeta;
}

/** Extracted code from AI response */
export interface ExtractedCode {
  html: string;
  js: string | null;
  metadata: Record<string, unknown>;
}

/** Generation response */
export interface GenerationResponse {
  html: string;
  js: string | null;
  metadata: Record<string, unknown>;
}

/** AI model info */
export interface AIModel {
  id: string;
  name: string;
  provider: string;
}

/** Chat API request */
export interface ChatRequest {
  messages: Omit<ChatMessage, 'id' | 'timestamp'>[];
  model?: string;
  stream: boolean;
  template?: {
    id: string;
    name: string;
    systemPromptAddition: string;
  };
  templateInputs?: Record<string, string>;
  interviewAnswers?: Record<string, string>;
  isQuickAction?: boolean;
}

/** Chat API response (SSE chunk) */
export interface ChatStreamChunk {
  choices: Array<{
    delta: {
      content?: string;
    };
  }>;
}

// Re-export Phase 2 types
export * from './template';
export * from './interview';
export * from './quickAction';
export * from './version';

// Re-export Phase 3 types
export * from './auth';
export * from './project';
