# Phase 1 Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the core "chat → preview" interaction for Zaoya - a v0-style AI mobile page generator with streaming chat, AI integration, and sandboxed preview rendering.

**Architecture:**
- **Monorepo structure**: Vite + React + TypeScript frontend, FastAPI Python backend
- **Streaming**: Server-Sent Events (SSE) for real-time AI response streaming
- **Security**: Sandboxed iframe rendering without `allow-same-origin`, postMessage communication
- **Reference patterns**: Copy proven AI service and chat API from `../Bubu/` project

**Tech Stack:**
- Frontend: Vite 5, React 18, TypeScript, Tailwind CSS, Zustand
- Backend: FastAPI, Uvicorn, httpx, SSE (via StreamingResponse)
- AI: OpenAI-compatible APIs (7 models: GLM-4.7, DeepSeek, Doubao, Qwen, Hunyuan, Kimi, MiniMax)

---

## Prerequisites Checklist

Before starting, verify:
- [ ] Node.js 18+ installed
- [ ] Python 3.10+ installed
- [ ] Access to `../Bubu/` project for reference patterns

---

## Task 1: Project Scaffolding

**Goal:** Set up monorepo structure with frontend and backend

### Step 1.1: Create backend directory structure

```bash
cd /Users/thesmartaz/Qoder-Project/zaoya
mkdir -p backend/app/api backend/app/services backend/app/models
```

Expected: Directories created

### Step 1.2: Create backend __init__ files

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/models/__init__.py`

**Create `backend/app/__init__.py`:**
```python
# Zaoya Backend Application
```

**Create `backend/app/api/__init__.py`:**
```python
# API routers
```

**Create `backend/app/services/__init__.py`:`
```python
# Business logic services
```

**Create `backend/app/models/__init__.py`:**
```python
# Pydantic models
```

Expected: Files created

### Step 1.3: Create backend requirements.txt

**Files:**
- Create: `backend/requirements.txt`

**Content:**
```txt
fastapi==0.109.2
uvicorn[standard]==0.27.1
python-dotenv==1.0.1
openai==1.12.0
pydantic==2.6.1
```

Expected: File created

### Step 1.4: Create backend .env.example

**Files:**
- Create: `backend/.env.example`

**Content:**
```bash
# GLM (智谱 AI)
GLM_4_7_KEY=your_glm_key_here
GLM_4_7_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_4_7_MODEL=glm-4.7

# DeepSeek
DEEPSEEK_KEY=your_deepseek_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# Doubao (豆包)
DOUBAO_KEY=your_doubao_key_here
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=ep-20241225172630-hkqxt

# Qwen (通义千问)
QWEN_KEY=your_qwen_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-max-latest

# Hunyuan (混元)
HUNYUAN_KEY=your_hunyuan_key_here
HUNYUAN_BASE_URL=https://api.hunyuan.cloud/v1
HUNYUAN_MODEL=hunyuan-2.0-thinking-20251109

# Kimi
KIMI_KEY=your_kimi_key_here
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2-thinking

# MiniMax
MINIMAX_KEY=your_minimax_key_here
MINIMAX_BASE_URL=https://api.minimax.chat/v1
MINIMAX_MODEL=abab6.5s-mini

# Default model
DEFAULT_MODEL=glm-4.7
```

Expected: File created

### Step 1.5: Copy .env from Bubu (if available)

```bash
cp ../Bubu/backend/.env backend/.env
```

Expected: `.env` copied (or error if not exists - that's OK)

### Step 1.6: Create backend main.py

**Files:**
- Create: `backend/app/main.py`

**Content:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

app = FastAPI(
    title="Zaoya API",
    description="AI-powered mobile page generator",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Zaoya API is running", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

Expected: File created

### Step 1.7: Create frontend directory structure

```bash
cd /Users/thesmartaz/Qoder-Project/zaoya
mkdir -p frontend/src/components/chat frontend/src/components/preview frontend/src/hooks frontend/src/stores frontend/src/types frontend/src/utils frontend/public
```

Expected: Directories created

### Step 1.8: Initialize frontend with Vite

```bash
cd frontend
npm create vite@latest . -- --template react-ts
```

Expected: Vite prompts, select:
- Framework: React
- Variant: TypeScript

Press Enter to confirm

### Step 1.9: Install frontend dependencies

```bash
cd frontend
npm install
npm install tailwindcss postcss autoprefixer zustand
```

Expected: Packages installed

### Step 1.10: Initialize Tailwind CSS

```bash
cd frontend
npx tailwindcss init -p
```

Expected: `tailwind.config.js` and `postcss.config.js` created

### Step 1.11: Configure Tailwind

**Files:**
- Modify: `frontend/tailwind.config.js`

**Content:**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Expected: File updated

### Step 1.12: Configure Vite

**Files:**
- Modify: `frontend/vite.config.ts`

**Content:**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

Expected: File updated

### Step 1.13: Configure TypeScript path alias

**Files:**
- Modify: `frontend/tsconfig.json`

**Find the `compilerOptions` section and add:**
```json
"baseUrl": ".",
"paths": {
  "@/*": ["./src/*"]
}
```

Expected: File updated

### Step 1.14: Add Tailwind directives to CSS

**Files:**
- Modify: `frontend/src/index.css`

**Replace entire content with:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

Expected: File updated

### Step 1.15: Create shared types

**Files:**
- Create: `frontend/src/types/index.ts`

**Content:**
```typescript
/** Chat message */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
}

/** Extracted code from AI response */
export interface ExtractedCode {
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
}

/** Chat API response (SSE chunk) */
export interface ChatStreamChunk {
  choices: Array<{
    delta: {
      content?: string;
    };
  }>;
}
```

Expected: File created

### Step 1.16: Commit scaffolding

```bash
cd /Users/thesmartaz/Qoder-Project/zaoya
git add backend/ frontend/
git commit -m "feat: add project scaffolding (frontend + backend)"
```

Expected: Commit created

---

## Task 2: AI Service (Backend)

**Goal:** Copy and adapt Bubu's AI service for Zaoya

### Step 2.1: Create AI service

**Files:**
- Create: `backend/app/services/ai_service.py`

**Content:**
```python
"""AI service for chat completion - supports 7 models"""
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Literal, AsyncGenerator

load_dotenv()

# Supported models
ModelType = Literal[
    "glm-4.7",
    "deepseek",
    "doubao",
    "qwen",
    "hunyuan",
    "kimi",
    "minimax"
]

# Model configurations
MODEL_CONFIGS = {
    "glm-4.7": {
        "key": os.getenv("GLM_4_7_KEY"),
        "base_url": os.getenv("GLM_4_7_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
        "model": os.getenv("GLM_4_7_MODEL", "glm-4.7")
    },
    "deepseek": {
        "key": os.getenv("DEEPSEEK_KEY"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    },
    "doubao": {
        "key": os.getenv("DOUBAO_KEY"),
        "base_url": os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        "model": os.getenv("DOUBAO_MODEL", "ep-20241225172630-hkqxt")
    },
    "qwen": {
        "key": os.getenv("QWEN_KEY"),
        "base_url": os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        "model": os.getenv("QWEN_MODEL", "qwen-max-latest")
    },
    "hunyuan": {
        "key": os.getenv("HUNYUAN_KEY"),
        "base_url": os.getenv("HUNYUAN_BASE_URL", "https://api.hunyuan.cloud/v1"),
        "model": os.getenv("HUNYUAN_MODEL", "hunyuan-2.0-thinking-20251109")
    },
    "kimi": {
        "key": os.getenv("KIMI_KEY"),
        "base_url": os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
        "model": os.getenv("KIMI_MODEL", "kimi-k2-thinking")
    },
    "minimax": {
        "key": os.getenv("MINIMAX_KEY"),
        "base_url": os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
        "model": os.getenv("MINIMAX_MODEL", "abab6.5s-mini")
    }
}

# Default model
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "glm-4.7")

# Zaoya system prompt
SYSTEM_PROMPT = """You are Zaoya, an AI assistant that generates mobile-first web pages.

Rules:
1. Generate HTML with Tailwind CSS classes
2. Use semantic HTML5 elements
3. Mobile-first design (max-width: 428px viewport recommended)
4. Only use Zaoya.* JavaScript helpers for interactivity
5. Return response in this format:

```html
<!-- Your HTML here -->
```

```javascript
// Optional: DOM event wiring using Zaoya.* only
```

Available Zaoya.* helpers:
- Zaoya.submitForm(formData)
- Zaoya.track(event, data)
- Zaoya.toast(message)
- Zaoya.navigate(path)

Design guidelines:
- Use emoji icons instead of images
- Make touch-friendly buttons (min 44px height)
- Use safe area insets for mobile
- Smooth transitions and animations
- Clean, modern aesthetic
"""

def get_client(model_key: str = "glm-4.7") -> AsyncOpenAI:
    """Get OpenAI client for specified model"""
    config = MODEL_CONFIGS.get(model_key, MODEL_CONFIGS["glm-4.7"])
    return AsyncOpenAI(
        api_key=config["key"],
        base_url=config["base_url"]
    )


def get_model_name(model_key: str = "glm-4.7") -> str:
    """Get actual model name for API calls"""
    config = MODEL_CONFIGS.get(model_key, MODEL_CONFIGS["glm-4.7"])
    return config["model"]


async def stream_chat(messages: list, model: str = DEFAULT_MODEL) -> AsyncGenerator:
    """Stream chat completion from AI

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model identifier (glm-4.7, deepseek, etc.)
    """
    client = get_client(model)
    model_name = get_model_name(model)

    # Format messages with system prompt
    messages_formatted = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    for msg in messages:
        messages_formatted.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    stream = await client.chat.completions.create(
        model=model_name,
        messages=messages_formatted,
        stream=True
    )

    return stream


def get_available_models() -> list[dict]:
    """Get list of available AI models"""
    return [
        {"id": "glm-4.7", "name": "GLM-4.7", "provider": "智谱 AI"},
        {"id": "deepseek", "name": "DeepSeek V3", "provider": "DeepSeek"},
        {"id": "doubao", "name": "豆包 Doubao", "provider": "字节跳动"},
        {"id": "qwen", "name": "通义千问 Qwen Max", "provider": "阿里云"},
        {"id": "hunyuan", "name": "混元 Hunyuan", "provider": "腾讯"},
        {"id": "kimi", "name": "Kimi K2", "provider": "月之暗面"},
        {"id": "minimax", "name": "MiniMax M2.1", "provider": "MiniMax"}
    ]
```

Expected: File created

### Step 2.2: Create Pydantic models

**Files:**
- Create: `backend/app/models/__init__.py`

**Content:**
```python
"""Pydantic models for API requests/responses"""
from pydantic import BaseModel
from typing import List, Optional


class Message(BaseModel):
    """Chat message"""
    role: str
    content: str
    id: Optional[str] = None
    timestamp: Optional[int] = None


class ChatRequest(BaseModel):
    """Chat API request"""
    messages: List[Message]
    model: Optional[str] = None
    stream: bool = True
```

Expected: File created

### Step 2.3: Create chat API endpoint

**Files:**
- Create: `backend/app/api/chat.py`

**Content:**
```python
"""Chat API with SSE streaming"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models import Message, ChatRequest
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest):
    """AI chat endpoint with SSE streaming"""
    from app.services.ai_service import stream_chat

    model = request.model or "glm-4.7"
    messages = [msg.model_dump() for msg in request.messages]

    async def generate():
        stream = await stream_chat(messages, model)
        async for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'choices': [{'delta': {'content': delta.content}}]})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/models")
async def get_models():
    """Get available AI models"""
    from app.services.ai_service import get_available_models
    return {"models": get_available_models()}
```

Expected: File created

### Step 2.4: Wire up chat router in main.py

**Files:**
- Modify: `backend/app/main.py`

**Add after CORS middleware:**
```python
from app.api.chat import router as chat_router

app.include_router(chat_router)
```

Expected: File updated

### Step 2.5: Test backend server

```bash
cd backend
source venv/bin/activate  # or: python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Expected: Server starts on http://localhost:8000

### Step 2.6: Test health endpoint (in another terminal)

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"healthy"}`

### Step 2.7: Test models endpoint

```bash
curl http://localhost:8000/api/chat/models
```

Expected: JSON with models list

### Step 2.8: Commit AI service

```bash
cd /Users/thesmartaz/Qoder-Project/zaoya
git add backend/
git commit -m "feat: add AI service with 7 model support and chat API"
```

Expected: Commit created

---

## Task 3: Chat State Management (Frontend)

**Goal:** Create Zustand store for chat state

### Step 3.1: Create chat store

**Files:**
- Create: `frontend/src/stores/chatStore.ts`

**Content:**
```typescript
import { create } from 'zustand'
import { ChatMessage } from '@/types'

interface ChatState {
  messages: ChatMessage[]
  isStreaming: boolean
  currentStreamText: string
  selectedModel: string
  availableModels: Array<{ id: string; name: string; provider: string }>

  // Actions
  addMessage: (message: ChatMessage) => void
  updateMessage: (id: string, content: string) => void
  setStreaming: (streaming: boolean) => void
  appendStreamText: (text: string) => void
  clearStreamText: () => void
  setSelectedModel: (model: string) => void
  setAvailableModels: (models: Array<{ id: string; name: string; provider: string }>) => void
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

  setAvailableModels: (models) => set({ availableModels: models })
}))
```

Expected: File created

### Step 3.2: Commit chat store

```bash
git add frontend/src/stores/
git commit -m "feat: add Zustand chat store"
```

Expected: Commit created

---

## Task 4: Chat Streaming Hook

**Goal:** Create hook for streaming chat requests

### Step 4.1: Create useChatStream hook

**Files:**
- Create: `frontend/src/hooks/useChatStream.ts`

**Content:**
```typescript
import { useCallback } from 'react'
import { useChatStore } from '@/stores/chatStore'

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

  // Load available models
  const loadModels = useCallback(async () => {
    try {
      const res = await fetch('/api/chat/models')
      const data = await res.json()
      setAvailableModels(data.models || [])
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }, [setAvailableModels])

  const sendMessage = useCallback(async (content: string) => {
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content,
      timestamp: Date.now()
    }

    addMessage(userMessage)
    setStreaming(true)

    // Create placeholder for assistant response
    const assistantMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant' as const,
      content: '',
      timestamp: Date.now()
    }
    addMessage(assistantMessage)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: messages.map(m => ({ role: m.role, content: m.content })),
          model: selectedModel,
          stream: true
        })
      })

      if (!response.ok) throw new Error('API request failed')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('Cannot read response')

      const decoder = new TextDecoder()
      let buffer = ''

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
                updateMessage(assistantMessage.id,
                  (messages.find(m => m.id === assistantMessage.id)?.content || '') + content
                )
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      updateMessage(assistantMessage.id, 'Sorry, an error occurred. Please try again.')
    } finally {
      setStreaming(false)
    }
  }, [messages, selectedModel, addMessage, updateMessage, setStreaming, setAvailableModels])

  return {
    messages,
    isStreaming,
    selectedModel,
    availableModels,
    sendMessage,
    setSelectedModel,
    loadModels
  }
}
```

Expected: File created

### Step 4.3: Commit streaming hook

```bash
git add frontend/src/hooks/
git commit -m "feat: add useChatStream hook with SSE parsing"
```

Expected: Commit created

---

## Task 5: Chat UI Components

**Goal:** Build chat interface components

### Step 5.1: Create MessageBubble component

**Files:**
- Create: `frontend/src/components/chat/MessageBubble.tsx`

**Content:**
```typescript
import { ChatMessage } from '@/types'

interface MessageBubbleProps {
  message: ChatMessage
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 ${
          isUser
            ? 'bg-indigo-600 text-white rounded-br-sm'
            : 'bg-gray-100 text-gray-900 rounded-bl-sm'
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
      </div>
    </div>
  )
}
```

Expected: File created

### Step 5.2: Create MessageList component

**Files:**
- Create: `frontend/src/components/chat/MessageList.tsx`

**Content:**
```typescript
import { useEffect, useRef } from 'react'
import { ChatMessage } from '@/types'
import { MessageBubble } from './MessageBubble'

interface MessageListProps {
  messages: ChatMessage[]
}

export function MessageList({ messages }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      <div ref={endRef} />
    </div>
  )
}
```

Expected: File created

### Step 5.3: Create InputBar component

**Files:**
- Create: `frontend/src/components/chat/InputBar.tsx`

**Content:**
```typescript
import { useState, FormEvent } from 'react'

interface InputBarProps {
  onSend: (content: string) => void
  disabled: boolean
}

export function InputBar({ onSend, disabled }: InputBarProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput('')
    }
  }

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe a page you want to create..."
          disabled={disabled}
          className="flex-1 rounded-full border border-gray-300 px-4 py-2 focus:border-indigo-500 focus:outline-none disabled:bg-gray-100"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="rounded-full bg-indigo-600 px-6 py-2 font-semibold text-white hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {disabled ? '...' : 'Send'}
        </button>
      </form>
    </div>
  )
}
```

Expected: File created

### Step 5.4: Create ChatPanel component

**Files:**
- Create: `frontend/src/components/chat/ChatPanel.tsx`

**Content:**
```typescript
import { useChatStream } from '@/hooks/useChatStream'
import { MessageList } from './MessageList'
import { InputBar } from './InputBar'

export function ChatPanel() {
  const { messages, isStreaming, sendMessage } = useChatStream()

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center border-b border-gray-200 bg-white px-4 py-3">
        <h1 className="text-xl font-bold text-indigo-600">Zaoya</h1>
      </header>
      <MessageList messages={messages} />
      <InputBar onSend={sendMessage} disabled={isStreaming} />
    </div>
  )
}
```

Expected: File created

### Step 5.5: Update App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

**Replace entire content with:**
```typescript
import { ChatPanel } from './components/chat/ChatPanel'

function App() {
  return <ChatPanel />
}

export default App
```

Expected: File updated

### Step 5.6: Commit chat UI

```bash
git add frontend/src/components/ frontend/src/App.tsx
git commit -m "feat: add chat UI components"
```

Expected: Commit created

---

## Task 6: Code Extraction

**Goal:** Extract HTML/JS from AI responses

### Step 6.1: Create code extractor utility

**Files:**
- Create: `frontend/src/utils/codeExtractor.ts`

**Content:**
```typescript
import { ExtractedCode } from '@/types'

/**
 * Extract HTML and JavaScript code from AI response
 * Supports markdown code blocks: ```html and ```javascript
 */
export function extractCode(response: string): ExtractedCode {
  // Try to extract HTML code block
  const htmlMatch = response.match(/```html\n([\s\S]*?)```/)

  // Try to extract JavaScript code block
  const jsMatch = response.match(/```javascript\n([\s\S]*?)```/)

  const html = htmlMatch?.[1]?.trim() || ''
  const js = jsMatch?.[1]?.trim() || null

  return {
    html,
    js,
    metadata: {
      hasHtml: !!html,
      hasJs: !!js
    }
  }
}

/**
 * Check if response contains code
 */
export function hasCode(response: string): boolean {
  return /```(html|javascript)/.test(response)
}
```

Expected: File created

### Step 6.2: Commit code extractor

```bash
git add frontend/src/utils/
git commit -m "feat: add code extraction utility"
```

Expected: Commit created

---

## Task 7: Preview Components

**Goal:** Create mobile preview with sandboxed iframe

### Step 7.1: Create zaoya-runtime.js

**Files:**
- Create: `frontend/public/zaoya-runtime.js`

**Content:**
```javascript
/**
 * Zaoya Runtime - Safe JavaScript helpers for generated pages
 * All communication happens via postMessage to parent
 */
(function() {
  'use strict'

  window.Zaoya = {
    /**
     * Submit form data to parent
     */
    submitForm: function(formData) {
      window.parent.postMessage({
        type: 'ZAOYA_FORM_SUBMIT',
        data: Object.fromEntries(formData)
      }, '*')
    },

    /**
     * Track analytics event
     */
    track: function(event, data) {
      window.parent.postMessage({
        type: 'ZAOYA_TRACK',
        event: event,
        data: data
      }, '*')
    },

    /**
     * Show toast message in parent
     */
    toast: function(message) {
      window.parent.postMessage({
        type: 'ZAOYA_TOAST',
        message: message
      }, '*')
    },

    /**
     * Navigate to path in parent
     */
    navigate: function(path) {
      window.parent.postMessage({
        type: 'ZAOYA_NAVIGATE',
        path: path
      }, '*')
    }
  }

  // Notify parent that runtime is ready
  window.parent.postMessage({ type: 'ZAOYA_READY' }, '*')
})()
```

Expected: File created

### Step 7.2: Create preview builder utility

**Files:**
- Create: `frontend/src/utils/previewBuilder.ts`

**Content:**
```typescript
/**
 * Build complete HTML document for preview iframe
 */
export function buildPreviewDocument(html: string, js: string | null): string {
  const jsScript = js ? `<script>${js}<\/script>` : ''

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <script src="https://cdn.tailwindcss.com"><\/script>
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
  </style>
</head>
<body>
  ${html}
  ${jsScript}
  <script src="/zaoya-runtime.js"><\/script>
</body>
</html>`
}
```

Expected: File created

### Step 7.3: Create PhoneFrame component

**Files:**
- Create: `frontend/src/components/preview/PhoneFrame.tsx`

**Content:**
```typescript
import { ReactNode } from 'react'

interface PhoneFrameProps {
  children: ReactNode
}

export function PhoneFrame({ children }: PhoneFrameProps) {
  return (
    <div className="relative flex items-center justify-center p-8">
      <div className="relative">
        {/* iPhone-style frame */}
        <div className="w-[375px] h-[812px] bg-black rounded-[40px] shadow-2xl p-3">
          {/* Notch */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-7 bg-black rounded-b-2xl z-10" />
          {/* Screen area */}
          <div className="w-full h-full bg-white rounded-[32px] overflow-hidden">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}
```

Expected: File created

### Step 7.4: Create PreviewPanel component

**Files:**
- Create: `frontend/src/components/preview/PreviewPanel.tsx`

**Content:**
```typescript
import { useRef, useEffect } from 'react'
import { buildPreviewDocument } from '@/utils/previewBuilder'

interface PreviewPanelProps {
  html: string
  js: string | null
}

export function PreviewPanel({ html, js }: PreviewPanelProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)

  useEffect(() => {
    const iframe = iframeRef.current
    if (!iframe) return

    const doc = buildPreviewDocument(html, js)
    iframe.srcdoc = doc
  }, [html, js])

  if (!html) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        <p>No preview available</p>
      </div>
    )
  }

  return (
    <iframe
      ref={iframeRef}
      sandbox="allow-scripts"
      className="w-full h-full border-0"
      title="Preview"
    />
  )
}
```

Expected: File created

### Step 7.5: Commit preview components

```bash
git add frontend/src/components/preview/ frontend/src/utils/previewBuilder.ts frontend/public/zaoya-runtime.js
git commit -m "feat: add preview components with phone frame and sandboxed iframe"
```

Expected: Commit created

---

## Task 8: Split-Screen Editor Layout

**Goal:** Create main editor page with chat and preview side-by-side

### Step 8.1: Create EditorPage component

**Files:**
- Create: `frontend/src/pages/EditorPage.tsx`

**Content:**
```typescript
import { useState } from 'react'
import { useChatStream } from '@/hooks/useChatStream'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { PreviewPanel } from '@/components/preview/PreviewPanel'
import { PhoneFrame } from '@/components/preview/PhoneFrame'
import { extractCode } from '@/utils/codeExtractor'

export function EditorPage() {
  const { messages, isStreaming } = useChatStream()
  const [generatedCode, setGeneratedCode] = useState<{ html: string; js: string | null } | null>(null)

  // Extract code from latest assistant message
  const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant')
  if (lastAssistantMsg && lastAssistantMsg.content) {
    const extracted = extractCode(lastAssistantMsg.content)
    if (extracted.html) {
      setGeneratedCode(extracted)
    }
  }

  return (
    <div className="flex h-screen">
      {/* Chat panel - left side */}
      <div className="w-1/2 min-w-[400px] border-r border-gray-200">
        <ChatPanel />
      </div>

      {/* Preview panel - right side */}
      <div className="w-1/2 flex items-center justify-center bg-gray-100">
        <PhoneFrame>
          <PreviewPanel
            html={generatedCode?.html || ''}
            js={generatedCode?.js || null}
          />
        </PhoneFrame>
      </div>
    </div>
  )
}
```

Expected: File created

### Step 8.2: Update App.tsx to use EditorPage

**Files:**
- Modify: `frontend/src/App.tsx`

**Replace entire content with:**
```typescript
import { EditorPage } from './pages/EditorPage'

function App() {
  return <EditorPage />
}

export default App
```

Expected: File updated

### Step 8.3: Fix ChatPanel - remove redundant header

**Files:**
- Modify: `frontend/src/components/chat/ChatPanel.tsx`

**Replace entire content with:**
```typescript
import { useChatStream } from '@/hooks/useChatStream'
import { MessageList } from './MessageList'
import { InputBar } from './InputBar'

export function ChatPanel() {
  const { messages, isStreaming, sendMessage } = useChatStream()

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center border-b border-gray-200 bg-white px-4 py-3">
        <h1 className="text-lg font-semibold text-gray-800">Chat</h1>
      </header>
      <MessageList messages={messages} />
      <InputBar onSend={sendMessage} disabled={isStreaming} />
    </div>
  )
}
```

Expected: File updated

### Step 8.4: Commit editor layout

```bash
git add frontend/src/pages/ frontend/src/App.tsx frontend/src/components/chat/ChatPanel.tsx
git commit -m "feat: add split-screen editor layout with chat and preview"
```

Expected: Commit created

---

## Task 9: PostMessage Handler

**Goal:** Handle messages from sandboxed iframe

### Step 9.1: Create usePreviewMessages hook

**Files:**
- Create: `frontend/src/hooks/usePreviewMessages.ts`

**Content:**
```typescript
import { useEffect } from 'react'

export function usePreviewMessages() {
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      // Only accept messages from same-origin (our iframe)
      // Note: Since iframe is sandboxed without allow-same-origin,
      // origin will be "null" - we still accept it

      const data = event.data
      if (!data || typeof data !== 'object') return

      switch (data.type) {
        case 'ZAOYA_READY':
          console.log('Zaoya runtime ready')
          break

        case 'ZAOYA_FORM_SUBMIT':
          console.log('Form submitted:', data.data)
          // TODO: Handle form submission
          break

        case 'ZAOYA_TRACK':
          console.log('Track event:', data.event, data.data)
          // TODO: Handle analytics tracking
          break

        case 'ZAOYA_TOAST':
          alert(data.message) // Simple toast for now
          break

        case 'ZAOYA_NAVIGATE':
          console.log('Navigate to:', data.path)
          // TODO: Handle navigation
          break
      }
    }

    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])
}
```

Expected: File created

### Step 9.2: Use hook in EditorPage

**Files:**
- Modify: `frontend/src/pages/EditorPage.tsx`

**Add at top with imports:**
```typescript
import { usePreviewMessages } from '@/hooks/usePreviewMessages'
```

**Add at start of component:**
```typescript
export function EditorPage() {
  usePreviewMessages() // Handle postMessages from iframe
  // ... rest of component
```

Expected: File updated

### Step 9.3: Commit postMessage handler

```bash
git add frontend/src/hooks/
git commit -m "feat: add postMessage handler for iframe communication"
```

Expected: Commit created

---

## Task 10: Fix State Management Issues

**Goal:** Fix circular dependency and state issues

### Step 10.1: Fix useChatStream to use store directly

**Files:**
- Modify: `frontend/src/hooks/useChatStream.ts`

**Replace entire content with:**
```typescript
import { useCallback, useEffect } from 'react'
import { useChatStore } from '@/stores/chatStore'

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
    fetch('/api/chat/models')
      .then(res => res.json())
      .then(data => setAvailableModels(data.models || []))
      .catch(() => console.error('Failed to load models'))
  }, [setAvailableModels])

  const sendMessage = useCallback(async (content: string) => {
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content,
      timestamp: Date.now()
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
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: messages.map(m => ({ role: m.role, content: m.content })),
          model: selectedModel,
          stream: true
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
      const assistantId = (Date.now()).toString()
      updateMessage(assistantId, 'Sorry, an error occurred. Please try again.')
    } finally {
      setStreaming(false)
    }
  }, [messages, selectedModel, addMessage, updateMessage, setStreaming, setAvailableModels])

  return {
    messages,
    isStreaming,
    selectedModel,
    availableModels,
    sendMessage,
    setSelectedModel
  }
}
```

Expected: File updated

### Step 10.2: Simplify EditorPage to not re-render on code changes

**Files:**
- Modify: `frontend/src/pages/EditorPage.tsx`

**Replace entire content with:**
```typescript
import { useState, useEffect } from 'react'
import { useChatStream } from '@/hooks/useChatStream'
import { usePreviewMessages } from '@/hooks/usePreviewMessages'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { PreviewPanel } from '@/components/preview/PreviewPanel'
import { PhoneFrame } from '@/components/preview/PhoneFrame'
import { extractCode } from '@/utils/codeExtractor'
import { useChatStore } from '@/stores/chatStore'

export function EditorPage() {
  usePreviewMessages()
  const { messages } = useChatStream()
  const [generatedCode, setGeneratedCode] = useState<{ html: string; js: string | null } | null>(null)

  // Extract code when messages change
  useEffect(() => {
    const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant')
    if (lastAssistantMsg && lastAssistantMsg.content) {
      const extracted = extractCode(lastAssistantMsg.content)
      if (extracted.html) {
        setGeneratedCode(extracted)
      }
    }
  }, [messages])

  return (
    <div className="flex h-screen">
      {/* Chat panel - left side */}
      <div className="w-1/2 min-w-[400px] border-r border-gray-200">
        <ChatPanel />
      </div>

      {/* Preview panel - right side */}
      <div className="w-1/2 flex items-center justify-center bg-gray-100">
        <PhoneFrame>
          <PreviewPanel
            html={generatedCode?.html || ''}
            js={generatedCode?.js || null}
          />
        </PhoneFrame>
      </div>
    </div>
  )
}
```

Expected: File updated

### Step 10.3: Commit state fixes

```bash
git add frontend/src/
git commit -m "fix: resolve state management and circular dependency issues"
```

Expected: Commit created

---

## Task 11: Final Testing

**Goal:** Verify end-to-end functionality

### Step 11.1: Start backend server

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Expected: Server running on http://localhost:8000

### Step 11.2: Start frontend server

```bash
cd frontend
npm run dev
```

Expected: Server running on http://localhost:5173

### Step 11.3: Test chat flow

1. Open http://localhost:5173
2. Verify split-screen layout visible
3. Verify welcome message displayed
4. Type "Create a simple login form"
5. Send message
6. Verify streaming response appears
7. Verify HTML preview renders in phone frame

Expected: All steps work correctly

### Step 11.4: Test iframe sandbox

1. Open browser DevTools
2. Inspect the preview iframe
3. Verify `sandbox="allow-scripts"` attribute present
4. Verify `zaoya-runtime.js` loaded (check Network tab)

Expected: Sandbox configured correctly

### Step 11.5: Test code extraction

1. Send message asking for a page with buttons
2. Verify HTML code block extracted
3. Verify preview renders correctly

Expected: Code extraction works

### Step 11.6: Create placeholder content when no code

**Files:**
- Modify: `frontend/src/components/preview/PreviewPanel.tsx`

**Replace entire content with:**
```typescript
import { useRef, useEffect } from 'react'
import { buildPreviewDocument } from '@/utils/previewBuilder'

interface PreviewPanelProps {
  html: string
  js: string | null
}

export function PreviewPanel({ html, js }: PreviewPanelProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)

  useEffect(() => {
    const iframe = iframeRef.current
    if (!iframe) return

    if (!html) {
      iframe.srcdoc = ''
      return
    }

    const doc = buildPreviewDocument(html, js)
    iframe.srcdoc = doc
  }, [html, js])

  if (!html) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        <div className="text-center">
          <p className="text-lg">📱</p>
          <p className="text-sm">Preview will appear here</p>
        </div>
      </div>
    )
  }

  return (
    <iframe
      ref={iframeRef}
      sandbox="allow-scripts"
      className="w-full h-full border-0"
      title="Preview"
    />
  )
}
```

Expected: Updated with placeholder

### Step 11.7: Commit final updates

```bash
git add frontend/src/
git commit -m "fix: add placeholder preview content when no code generated"
```

Expected: Commit created

---

## Task 12: Documentation

**Goal:** Add README and setup instructions

### Step 12.1: Create README.md

**Files:**
- Create: `README.md`

**Content:**
```markdown
# Zaoya

AI-powered mobile page generator - Create mobile web pages through chat.

## Project Structure

```
zaoya/
├── frontend/       # Vite + React + TypeScript
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom hooks
│   │   ├── pages/       # Page components
│   │   ├── stores/      # Zustand state
│   │   ├── types/       # TypeScript types
│   │   └── utils/       # Utilities
│   └── public/
│       └── zaoya-runtime.js  # Runtime for generated pages
├── backend/        # FastAPI Python
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── services/    # Business logic
│   │   └── models/      # Pydantic models
│   └── requirements.txt
└── docs/           # Documentation

```

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Usage

1. Type a description of the mobile page you want
2. AI generates HTML with Tailwind CSS
3. Preview appears in the phone frame on the right
4. Generated code uses Zaoya.* helpers for interactivity

## Tech Stack

- **Frontend**: Vite, React, TypeScript, Tailwind CSS, Zustand
- **Backend**: FastAPI, Uvicorn, OpenAI SDK
- **AI Models**: GLM-4.7, DeepSeek, Doubao, Qwen, Hunyuan, Kimi, MiniMax
```

Expected: README created

### Step 12.2: Commit documentation

```bash
git add README.md
git commit -m "docs: add README with setup instructions"
```

Expected: Commit created

### Step 12.3: Final commit for Phase 1

```bash
git add -A
git commit -m "phase-1: complete Phase 1 Foundation - chat to preview working"
```

Expected: Final commit created

---

## Acceptance Criteria Verification

After completing all tasks, verify:

- [ ] Can run `npm run dev` in frontend
- [ ] Can run `uvicorn app.main:app` in backend
- [ ] Chat interface displays messages with proper styling
- [ ] Typing in chat and pressing send triggers AI request
- [ ] AI response streams character-by-character in UI
- [ ] HTML code blocks are extracted from AI response
- [ ] Preview iframe renders extracted HTML
- [ ] Tailwind CSS loads and styles apply in preview
- [ ] zaoya-runtime.js loads in preview
- [ ] Zaoya.toast() calls show toast in parent app
- [ ] Preview iframe is properly sandboxed (no same-origin access)
- [ ] Mobile phone frame displays around preview
- [ ] Split-screen layout works on desktop (≥1024px)

---

## Definition of Done

Phase 1 is complete when:
1. A user can type a message describing a page
2. AI generates HTML response with streaming
3. Generated page renders in sandboxed mobile preview
4. Basic interactivity (Zaoya.* calls) works
5. Code is clean, typed, and documented
6. No console errors in normal operation
