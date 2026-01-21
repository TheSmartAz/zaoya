# Phase 1: Foundation

**Duration**: Weeks 1-3
**Status**: Pending
**Complexity**: Large

---

## Overview

Phase 1 establishes the technical foundation for Zaoya. By the end of this phase, a user can chat with AI and see a generated mobile page rendered in a sandboxed preview. This phase proves the core technical loop works before adding business features.

### Connection to Project Goals

- Validates the fundamental "chat → preview" interaction
- Sets up architecture that supports the full v0 security model
- Enables rapid iteration in subsequent phases
- Reuses proven patterns from Bubu project

---

## Prerequisites

- [ ] Node.js 18+ installed
- [ ] Python 3.10+ installed
- [ ] Access to AI API keys (copy from Bubu's .env)
- [ ] Basic understanding of Vite, React, FastAPI
- [ ] Bubu project available as reference (`../Bubu/`)

---

## Detailed Tasks

### Task 1.1: Project Scaffolding

**Goal**: Set up monorepo structure with frontend and backend

#### Sub-tasks

1. **Initialize project structure**
   ```
   zaoya/
   ├── frontend/           # Vite + React app
   │   ├── src/
   │   │   ├── components/
   │   │   ├── hooks/
   │   │   ├── pages/
   │   │   ├── stores/
   │   │   ├── types/
   │   │   ├── utils/
   │   │   ├── App.tsx
   │   │   └── main.tsx
   │   ├── public/
   │   ├── index.html
   │   ├── vite.config.ts
   │   ├── tailwind.config.js
   │   ├── tsconfig.json
   │   └── package.json
   ├── backend/            # FastAPI app
   │   ├── app/
   │   │   ├── api/
   │   │   │   ├── __init__.py
   │   │   │   └── chat.py
   │   │   ├── services/
   │   │   │   ├── __init__.py
   │   │   │   └── ai_service.py
   │   │   ├── models/
   │   │   │   └── __init__.py
   │   │   ├── __init__.py
   │   │   └── main.py
   │   ├── requirements.txt
   │   └── .env.example
   ├── shared/             # Shared types/constants
   │   └── types.ts
   ├── docs/
   ├── SPEC-v0.md
   ├── SPEC-v1.md
   └── README.md
   ```

2. **Set up frontend (Vite + React + TypeScript)**
   ```bash
   cd frontend
   npm create vite@latest . -- --template react-ts
   npm install tailwindcss postcss autoprefixer
   npm install zustand react-router-dom
   npm install @tanstack/react-query  # optional, for data fetching
   npx tailwindcss init -p
   ```

3. **Set up backend (FastAPI)**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn python-dotenv httpx sse-starlette
   ```

4. **Configure development proxy**
   - Vite proxy: `/api` → `http://localhost:8000`
   - CORS configuration in FastAPI

5. **Create shared types**
   - `Message` type (role, content, timestamp)
   - `Project` type (id, name, html, js, metadata)
   - `GenerationResponse` type

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/vite.config.ts` | Dev server + proxy config |
| `frontend/tailwind.config.js` | Tailwind setup |
| `frontend/src/types/index.ts` | TypeScript types |
| `backend/app/main.py` | FastAPI app entry |
| `backend/.env.example` | Environment template |

---

### Task 1.2: Chat Interface with Streaming

**Goal**: Build the chat UI component with real-time streaming responses

#### Sub-tasks

1. **Create chat components**
   ```
   frontend/src/components/
   ├── chat/
   │   ├── ChatPanel.tsx        # Main chat container
   │   ├── MessageList.tsx      # Scrollable message history
   │   ├── MessageBubble.tsx    # Individual message display
   │   ├── InputBar.tsx         # User input + send button
   │   └── StreamingText.tsx    # Animated typing effect
   ```

2. **Implement streaming hook**
   ```typescript
   // frontend/src/hooks/useChatStream.ts
   interface UseChatStreamOptions {
     onChunk: (chunk: string) => void;
     onComplete: (fullResponse: string) => void;
     onError: (error: Error) => void;
   }

   export function useChatStream() {
     const sendMessage = async (
       messages: Message[],
       options: UseChatStreamOptions
     ) => {
       const response = await fetch('/api/chat', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ messages }),
       });

       const reader = response.body?.getReader();
       const decoder = new TextDecoder();

       // SSE parsing loop...
     };

     return { sendMessage };
   }
   ```

3. **Create chat state store**
   ```typescript
   // frontend/src/stores/chatStore.ts
   interface ChatState {
     messages: Message[];
     isStreaming: boolean;
     currentStreamText: string;
     addMessage: (msg: Message) => void;
     setStreaming: (streaming: boolean) => void;
     appendStreamText: (text: string) => void;
   }
   ```

4. **Style chat interface**
   - Mobile-first responsive layout
   - Split-screen preparation (chat left, preview right)
   - Smooth scroll to bottom on new messages
   - Loading states during streaming

#### API Endpoint

```python
# backend/app/api/chat.py
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest):
    async def generate():
        async for chunk in ai_service.stream_chat(request.messages):
            yield {"data": chunk}

    return EventSourceResponse(generate())
```

#### Component Design

```tsx
// ChatPanel.tsx structure
<div className="flex flex-col h-full">
  <MessageList messages={messages} />
  <InputBar onSend={handleSend} disabled={isStreaming} />
</div>
```

---

### Task 1.3: AI Integration

**Goal**: Connect to AI APIs using Bubu's proven configuration

#### Sub-tasks

1. **Copy Bubu's AI service pattern**
   - Model configuration (7 models supported)
   - OpenAI-compatible API interface
   - Streaming response handling
   - Error handling and retries

2. **Create AI service**
   ```python
   # backend/app/services/ai_service.py
   from typing import AsyncGenerator
   import httpx

   class AIService:
       def __init__(self):
           self.models = {
               "glm-4.7": {"base_url": "...", "api_key": "..."},
               "deepseek-v3": {"base_url": "...", "api_key": "..."},
               # ... other models from Bubu
           }
           self.default_model = "glm-4.7"

       async def stream_chat(
           self,
           messages: list[dict],
           model: str = None
       ) -> AsyncGenerator[str, None]:
           model = model or self.default_model
           config = self.models[model]

           async with httpx.AsyncClient() as client:
               async with client.stream(
                   "POST",
                   f"{config['base_url']}/chat/completions",
                   json={
                       "model": model,
                       "messages": messages,
                       "stream": True,
                   },
                   headers={"Authorization": f"Bearer {config['api_key']}"},
               ) as response:
                   async for line in response.aiter_lines():
                       # Parse SSE and yield content
                       yield parsed_content
   ```

3. **Create system prompt for page generation**
   ```python
   SYSTEM_PROMPT = """You are Zaoya, an AI that generates mobile-first web pages.

   Rules:
   1. Generate HTML with Tailwind CSS classes
   2. Use semantic HTML5 elements
   3. Mobile-first design (max-width: 428px viewport)
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
   """
   ```

4. **Environment configuration**
   ```bash
   # backend/.env.example
   GLM_API_KEY=your_key_here
   GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
   DEEPSEEK_API_KEY=your_key_here
   DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
   # ... other models
   DEFAULT_MODEL=glm-4.7
   ```

---

### Task 1.4: Basic Page Generation + Preview

**Goal**: Extract HTML/JS from AI response and render in preview

#### Sub-tasks

1. **Create code extraction utility**
   ```typescript
   // frontend/src/utils/codeExtractor.ts
   interface ExtractedCode {
     html: string;
     js: string | null;
     metadata: Record<string, unknown>;
   }

   export function extractCode(response: string): ExtractedCode {
     const htmlMatch = response.match(/```html\n([\s\S]*?)```/);
     const jsMatch = response.match(/```javascript\n([\s\S]*?)```/);

     return {
       html: htmlMatch?.[1] || '',
       js: jsMatch?.[1] || null,
       metadata: {},
     };
   }
   ```

2. **Create preview component**
   ```typescript
   // frontend/src/components/preview/PreviewPanel.tsx
   interface PreviewPanelProps {
     html: string;
     js: string | null;
   }

   export function PreviewPanel({ html, js }: PreviewPanelProps) {
     const iframeRef = useRef<HTMLIFrameElement>(null);

     useEffect(() => {
       const doc = buildPreviewDocument(html, js);
       // Update iframe srcdoc or use postMessage
     }, [html, js]);

     return (
       <div className="preview-container">
         <div className="phone-frame">
           <iframe
             ref={iframeRef}
             sandbox="allow-scripts"
             className="w-full h-full"
           />
         </div>
       </div>
     );
   }
   ```

3. **Build preview document wrapper**
   ```typescript
   // frontend/src/utils/previewBuilder.ts
   export function buildPreviewDocument(html: string, js: string | null): string {
     return `
       <!DOCTYPE html>
       <html>
       <head>
         <meta charset="UTF-8">
         <meta name="viewport" content="width=device-width, initial-scale=1.0">
         <script src="https://cdn.tailwindcss.com"></script>
         <script src="/zaoya-runtime.js"></script>
       </head>
       <body>
         ${html}
         ${js ? `<script>${js}</script>` : ''}
       </body>
       </html>
     `;
   }
   ```

4. **Create split-screen editor layout**
   ```tsx
   // frontend/src/pages/EditorPage.tsx
   export function EditorPage() {
     const [generatedCode, setGeneratedCode] = useState<ExtractedCode | null>(null);

     return (
       <div className="flex h-screen">
         <div className="w-1/2 border-r">
           <ChatPanel onGenerate={setGeneratedCode} />
         </div>
         <div className="w-1/2 flex items-center justify-center bg-gray-100">
           <PreviewPanel
             html={generatedCode?.html || ''}
             js={generatedCode?.js || null}
           />
         </div>
       </div>
     );
   }
   ```

---

### Task 1.5: Sandbox Iframe Rendering

**Goal**: Securely render user-generated content in isolated iframe

#### Sub-tasks

1. **Create zaoya-runtime.js**
   ```javascript
   // frontend/public/zaoya-runtime.js
   window.Zaoya = {
     submitForm: function(formData) {
       window.parent.postMessage({
         type: 'ZAOYA_FORM_SUBMIT',
         data: Object.fromEntries(formData),
       }, '*');
     },

     track: function(event, data) {
       window.parent.postMessage({
         type: 'ZAOYA_TRACK',
         event: event,
         data: data,
       }, '*');
     },

     toast: function(message) {
       window.parent.postMessage({
         type: 'ZAOYA_TOAST',
         message: message,
       }, '*');
     },

     navigate: function(path) {
       window.parent.postMessage({
         type: 'ZAOYA_NAVIGATE',
         path: path,
       }, '*');
     },
   };
   ```

2. **Set up postMessage listener in parent**
   ```typescript
   // frontend/src/hooks/usePreviewMessages.ts
   export function usePreviewMessages() {
     useEffect(() => {
       const handler = (event: MessageEvent) => {
         if (event.data?.type?.startsWith('ZAOYA_')) {
           switch (event.data.type) {
             case 'ZAOYA_FORM_SUBMIT':
               handleFormSubmit(event.data.data);
               break;
             case 'ZAOYA_TRACK':
               handleTrack(event.data.event, event.data.data);
               break;
             case 'ZAOYA_TOAST':
               showToast(event.data.message);
               break;
             case 'ZAOYA_NAVIGATE':
               handleNavigate(event.data.path);
               break;
           }
         }
       };

       window.addEventListener('message', handler);
       return () => window.removeEventListener('message', handler);
     }, []);
   }
   ```

3. **Configure iframe sandbox attributes**
   ```html
   <iframe
     sandbox="allow-scripts"
     <!-- NO allow-same-origin for security -->
   />
   ```

4. **Add phone frame UI**
   ```tsx
   // frontend/src/components/preview/PhoneFrame.tsx
   export function PhoneFrame({ children }: { children: React.ReactNode }) {
     return (
       <div className="relative">
         {/* iPhone-style frame */}
         <div className="w-[375px] h-[812px] bg-black rounded-[40px] p-3 shadow-xl">
           {/* Notch */}
           <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-6 bg-black rounded-b-2xl" />
           {/* Screen */}
           <div className="w-full h-full bg-white rounded-[32px] overflow-hidden">
             {children}
           </div>
         </div>
       </div>
     );
   }
   ```

---

## Technical Considerations

### Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `vite` | ^5.0 | Build tool |
| `react` | ^18.0 | UI framework |
| `tailwindcss` | ^3.4 | Styling |
| `zustand` | ^4.0 | State management |
| `react-router-dom` | ^6.0 | Routing |
| `fastapi` | ^0.109 | Backend framework |
| `uvicorn` | ^0.27 | ASGI server |
| `httpx` | ^0.26 | Async HTTP client |
| `sse-starlette` | ^2.0 | SSE support |

### Architecture Decisions

1. **Why Zustand over Redux?**
   - Simpler API, less boilerplate
   - Better TypeScript support
   - Smaller bundle size
   - Sufficient for v0 complexity

2. **Why SSE over WebSockets?**
   - Simpler to implement
   - Works better with HTTP/2
   - Matches AI API streaming format
   - One-way is sufficient for chat

3. **Why sandbox without allow-same-origin?**
   - Maximum isolation for user content
   - postMessage provides controlled communication
   - Prevents XSS from accessing parent context

---

## Acceptance Criteria

- [ ] Can run `npm run dev` in frontend and `uvicorn app.main:app` in backend
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

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI API rate limits | Medium | High | Implement retry logic, use multiple model fallbacks |
| Streaming parsing edge cases | Medium | Medium | Test with various AI responses, handle malformed SSE |
| CORS issues during development | High | Low | Configure Vite proxy correctly |
| Iframe sandbox too restrictive | Low | Medium | Test all Zaoya.* functions work via postMessage |
| AI generates invalid HTML | Medium | Medium | Add basic HTML validation before render |

---

## Estimated Effort

| Task | Complexity | Effort |
|------|------------|--------|
| 1.1 Project Scaffolding | Small | 1-2 days |
| 1.2 Chat Interface | Medium | 2-3 days |
| 1.3 AI Integration | Medium | 2-3 days |
| 1.4 Page Generation + Preview | Medium | 2-3 days |
| 1.5 Sandbox Rendering | Small | 1-2 days |
| **Testing & Polish** | - | 2-3 days |
| **Total** | **Large** | **10-16 days (2-3 weeks)** |

---

## Definition of Done

Phase 1 is complete when:
1. A user can type a message describing a page
2. AI generates HTML response with streaming
3. Generated page renders in sandboxed mobile preview
4. Basic interactivity (Zaoya.* calls) works
5. Code is clean, typed, and documented
6. No console errors in normal operation
