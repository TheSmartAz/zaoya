# v4 Phase 1: Live Task Feed (实时任务流)

**Timeline**: Weeks 1-2
**Status**: Pending
**Dependencies**: v3 implementation complete

---

## Phase Overview

This phase transforms the build experience from a black-box process into a transparent, real-time streaming experience. Users will see exactly what's happening during generation through lightweight one-line task items in the chat panel, with interactive cards for significant results.

### Connection to Project Goals

- **North Star**: "Watch your project come alive - see every task, agent, and tool in action"
- Aligns with competitive features from Lovable, v0, and Manus
- Creates foundation for all subsequent v4 features (ProductDoc, multi-page, etc.)

---

## Prerequisites

### Technical Prerequisites
- [ ] v3 build system operational
- [ ] Chat SSE streaming endpoint functional (`/api/projects/{project_id}/chat`)
- [ ] Frontend chat store (Zustand) in place
- [ ] Build orchestrator emitting internal events

### Knowledge Prerequisites
- Understanding of SSE (Server-Sent Events) protocol
- Familiarity with existing chat message types
- Knowledge of build orchestrator event flow

---

## Detailed Tasks

### Task 1.1: Define LiveTaskMessage Types

**Priority**: P0 (Critical)
**Files**: `frontend/src/types/chat.ts`

Create TypeScript types for the new message system:

```typescript
// frontend/src/types/chat.ts

type LiveTaskMessageType =
  | 'agent_thinking'
  | 'task_started'
  | 'task_done'
  | 'task_failed'
  | 'tool_call'
  | 'page_created'
  | 'build_plan'
  | 'interview'
  | 'validation_failed'
  | 'build_complete';

interface LiveTaskMessage {
  id: string;
  type: LiveTaskMessageType;
  timestamp: number;
  session_id: string;  // Build session for grouping

  // For one-line items
  title: string;
  status: 'running' | 'done' | 'failed';

  // For cards (only populated for card-type messages)
  card?: {
    type: 'page' | 'build_plan' | 'interview' | 'validation';
    data: PageCardData | BuildPlanCardData | InterviewCardData | ValidationCardData;
  };

  // Actions (retry, view, etc.)
  actions?: {
    label: string;
    action: 'retry' | 'view' | 'edit' | 'start_build' | 'skip';
  }[];
}

// Card data interfaces
interface PageCardData {
  id: string;
  name: string;
  path: string;
  thumbnailUrl?: string;
}

interface BuildPlanCardData {
  pages: { id: string; name: string; path: string }[];
  tasks: { id: string; title: string; status: string }[];
  estimated_tasks: number;
}

interface InterviewCardData {
  questions: { id: string; question: string; hint?: string }[];
  answers: Record<string, string>;
}

interface ValidationCardData {
  errors: { type: string; message: string; line?: number }[];
  suggestions: string[];
}
```

**Acceptance Criteria**:
- [ ] All message types defined
- [ ] Card data interfaces complete
- [ ] Types exported and importable

---

### Task 1.2: Extend Chat SSE Endpoint

**Priority**: P0 (Critical)
**Files**: `backend/app/api/project_chat.py`

Merge build progress events into the existing chat endpoint:

```python
# backend/app/api/project_chat.py

from sse_starlette.sse import EventSourceResponse
import json

@router.post("/api/projects/{project_id}/chat")
async def project_chat(
    project_id: str,
    req: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    """
    SSE stream for chat + build progress.

    Event types:
    - message: AI text response (existing)
    - task: Task status update (started/done/failed)
    - card: Card content (page, build_plan, interview, validation)
    - preview_update: Signal to refresh preview
    - error: Error occurred
    """
    async def event_generator():
        try:
            # Existing chat/intent logic...

            # If build is triggered, stream progress
            if should_build:
                build_id = await orchestrator.start_build(
                    project_id=project_id,
                    user_message=req.message,
                    product_doc=product_doc
                )

                async for event in orchestrator.stream_progress(build_id):
                    if event.type == 'task':
                        yield {
                            "event": "task",
                            "data": json.dumps({
                                "id": event.task_id,
                                "type": event.task_type,
                                "title": event.title,
                                "status": event.status,
                                "session_id": build_id
                            })
                        }
                    elif event.type == 'card':
                        yield {
                            "event": "card",
                            "data": json.dumps({
                                "type": event.card_type,
                                "data": event.card_data,
                                "session_id": build_id
                            })
                        }
                    elif event.type == 'preview_update':
                        yield {
                            "event": "preview_update",
                            "data": json.dumps({
                                "page_id": event.page_id,
                                "session_id": build_id
                            })
                        }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)})
            }

    return EventSourceResponse(event_generator())
```

**Acceptance Criteria**:
- [ ] Endpoint emits `task`, `card`, `preview_update`, `error` events
- [ ] Events include `session_id` for grouping
- [ ] Backward compatible with existing chat functionality
- [ ] Error handling prevents stream crashes

---

### Task 1.3: Create Build Event Emitter

**Priority**: P0 (Critical)
**Files**: `backend/app/services/build_runtime/events.py`

Create a standardized event emitter for the build system:

```python
# backend/app/services/build_runtime/events.py

from dataclasses import dataclass
from typing import Optional, Dict, Any, Literal
from enum import Enum

class BuildEventType(Enum):
    TASK_STARTED = "task_started"
    TASK_DONE = "task_done"
    TASK_FAILED = "task_failed"
    AGENT_THINKING = "agent_thinking"
    TOOL_CALL = "tool_call"
    CARD = "card"
    PREVIEW_UPDATE = "preview_update"
    BUILD_COMPLETE = "build_complete"

@dataclass
class BuildEvent:
    type: BuildEventType
    task_id: Optional[str] = None
    title: Optional[str] = None
    status: Optional[Literal['running', 'done', 'failed']] = None
    card_type: Optional[str] = None
    card_data: Optional[Dict[str, Any]] = None
    page_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

    def to_sse_event(self) -> Dict[str, Any]:
        """Convert to SSE-compatible format."""
        if self.type in [BuildEventType.TASK_STARTED,
                         BuildEventType.TASK_DONE,
                         BuildEventType.TASK_FAILED]:
            return {
                "event": "task",
                "data": {
                    "id": self.task_id,
                    "type": self.type.value,
                    "title": self.title,
                    "status": self.status
                }
            }
        elif self.type == BuildEventType.CARD:
            return {
                "event": "card",
                "data": {
                    "type": self.card_type,
                    "data": self.card_data
                }
            }
        elif self.type == BuildEventType.PREVIEW_UPDATE:
            return {
                "event": "preview_update",
                "data": {"page_id": self.page_id}
            }
        elif self.type == BuildEventType.BUILD_COMPLETE:
            return {
                "event": "task",
                "data": {
                    "type": "build_complete",
                    "title": self.message or "构建完成"
                }
            }
        return {}

class BuildEventEmitter:
    """Emit build events for SSE streaming."""

    def task_started(self, task_id: str, title: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.TASK_STARTED,
            task_id=task_id,
            title=title,
            status='running'
        )

    def task_done(self, task_id: str, title: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.TASK_DONE,
            task_id=task_id,
            title=title,
            status='done'
        )

    def task_failed(self, task_id: str, title: str, error: str = None) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.TASK_FAILED,
            task_id=task_id,
            title=title,
            status='failed',
            error=error
        )

    def page_card(self, page_id: str, name: str, path: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.CARD,
            card_type='page',
            card_data={
                'id': page_id,
                'name': name,
                'path': path
            }
        )

    def preview_update(self, page_id: str) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.PREVIEW_UPDATE,
            page_id=page_id
        )

    def build_complete(self, message: str = None) -> BuildEvent:
        return BuildEvent(
            type=BuildEventType.BUILD_COMPLETE,
            message=message
        )
```

**Acceptance Criteria**:
- [ ] All event types supported
- [ ] Events serialize to SSE-compatible format
- [ ] Helper methods for common events

---

### Task 1.4: Implement One-Line Task Components

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/chat/TaskItem.tsx`

Create lightweight task display components:

```typescript
// frontend/src/components/chat/TaskItem.tsx

import { cn } from '@/lib/utils';
import { Loader2, Check, X, RotateCw } from 'lucide-react';

interface TaskItemProps {
  title: string;
  status: 'running' | 'done' | 'failed';
  onRetry?: () => void;
}

export function TaskItem({ title, status, onRetry }: TaskItemProps) {
  return (
    <div className={cn(
      "flex items-center gap-2 py-1 text-sm",
      status === 'failed' && "text-red-600"
    )}>
      {/* Status icon */}
      {status === 'running' && (
        <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      )}
      {status === 'done' && (
        <Check className="w-4 h-4 text-green-500" />
      )}
      {status === 'failed' && (
        <X className="w-4 h-4 text-red-500" />
      )}

      {/* Task title */}
      <span className={cn(
        status === 'done' && "text-gray-500"
      )}>
        {status === 'running' ? `${title}...` : title}
      </span>

      {/* Retry button (failed only) */}
      {status === 'failed' && onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1 text-xs text-blue-500 hover:text-blue-700"
        >
          <RotateCw className="w-3 h-3" />
          重试
        </button>
      )}
    </div>
  );
}

// Agent thinking variant
export function AgentThinkingItem({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 py-1 text-sm text-gray-500">
      <div className="w-4 h-4 flex items-center justify-center">
        <span className="text-base">🤖</span>
      </div>
      <span>{message}</span>
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Running state shows spinner
- [ ] Done state shows checkmark
- [ ] Failed state shows X with retry button
- [ ] Styling matches spec (lightweight, one-line)

---

### Task 1.5: Create Card Components

**Priority**: P1 (High)
**Files**:
- `frontend/src/components/chat/cards/PageCard.tsx`
- `frontend/src/components/chat/cards/ValidationCard.tsx`

```typescript
// frontend/src/components/chat/cards/PageCard.tsx

interface PageCardProps {
  page: {
    id: string;
    name: string;
    path: string;
  };
  onViewPreview: () => void;
}

export function PageCard({ page, onViewPreview }: PageCardProps) {
  return (
    <div className="border rounded-lg p-3 max-w-xs bg-white shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">📄</span>
        <span className="font-medium">Page: {page.name}</span>
      </div>
      <code className="text-xs text-gray-500 block mb-2">{page.path}</code>
      <button
        onClick={onViewPreview}
        className="text-sm text-blue-500 hover:text-blue-700"
      >
        查看预览
      </button>
    </div>
  );
}

// frontend/src/components/chat/cards/ValidationCard.tsx

interface ValidationCardProps {
  errors: { type: string; message: string; line?: number }[];
  suggestions: string[];
  onRetry: () => void;
}

export function ValidationCard({ errors, suggestions, onRetry }: ValidationCardProps) {
  return (
    <div className="border border-red-200 rounded-lg p-3 max-w-md bg-red-50">
      <div className="flex items-center gap-2 mb-2 text-red-700">
        <span className="text-lg">⚠️</span>
        <span className="font-medium">验证失败</span>
      </div>

      <div className="space-y-1 mb-3">
        {errors.map((err, i) => (
          <div key={i} className="text-sm text-red-600">
            {err.line && <span className="font-mono">L{err.line}: </span>}
            {err.message}
          </div>
        ))}
      </div>

      {suggestions.length > 0 && (
        <div className="text-sm text-gray-600 mb-3">
          <div className="font-medium">建议:</div>
          <ul className="list-disc list-inside">
            {suggestions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={onRetry}
        className="text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
      >
        重试
      </button>
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] PageCard displays page info with view button
- [ ] ValidationCard shows errors with retry
- [ ] Cards are visually distinct from one-line items
- [ ] Max width prevents chat overflow

---

### Task 1.6: Implement Abort Button

**Priority**: P1 (High)
**Files**: `frontend/src/components/chat/InputBar.tsx`

Transform send button to abort button during build:

```typescript
// frontend/src/components/chat/InputBar.tsx

interface InputBarProps {
  isBuilding: boolean;
  disabled?: boolean;
  onSend: (message: string) => void;
  onAbort: () => void;
}

export function InputBar({
  isBuilding,
  disabled,
  onSend,
  onAbort
}: InputBarProps) {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim()) {
      onSend(message);
      setMessage('');
    }
  };

  return (
    <div className="flex items-center gap-2 border rounded-lg p-2 bg-white">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && !isBuilding && handleSend()}
        className="flex-1 outline-none px-2"
        placeholder="输入消息..."
        disabled={isBuilding || disabled}
      />

      {isBuilding ? (
        <button
          onClick={onAbort}
          className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded flex items-center gap-2"
        >
          <span className="text-lg">■</span>
          终止
        </button>
      ) : (
        <button
          onClick={handleSend}
          disabled={!message.trim() || disabled}
          className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          发送
        </button>
      )}
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Button changes to red abort during build
- [ ] Input is disabled during build
- [ ] Abort triggers backend cancellation
- [ ] Visual feedback is immediate

---

### Task 1.7: Add Abort API Endpoint

**Priority**: P1 (High)
**Files**: `backend/app/api/build.py`

```python
# backend/app/api/build.py

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

# Store active builds (in production, use Redis)
active_builds: Dict[str, "BuildSession"] = {}

@router.post("/api/build/{build_id}/abort")
async def abort_build(
    build_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Abort an ongoing build.
    Sets cancellation flag and waits for graceful shutdown.
    """
    if build_id not in active_builds:
        raise HTTPException(status_code=404, detail="Build not found")

    build = active_builds[build_id]

    # Verify ownership
    if build.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Signal cancellation
    build.cancel()

    return {"status": "cancelled", "build_id": build_id}
```

**Acceptance Criteria**:
- [ ] Endpoint accepts build_id
- [ ] Verifies user ownership
- [ ] Signals cancellation to orchestrator
- [ ] Returns success status

---

### Task 1.8: Update buildStore with LiveTask Support

**Priority**: P0 (Critical)
**Files**: `frontend/src/stores/buildStore.ts`

```typescript
// frontend/src/stores/buildStore.ts

import { create } from 'zustand';

interface BuildState {
  // Session
  buildId: string | null;
  projectId: string | null;
  isBuilding: boolean;

  // Live tasks
  liveTasks: LiveTaskMessage[];
}

interface BuildActions {
  // Build control
  startBuild: (projectId: string) => void;
  abortBuild: () => Promise<void>;
  setBuildComplete: () => void;

  // Live task management
  addLiveTask: (task: LiveTaskMessage) => void;
  updateLiveTask: (taskId: string, updates: Partial<LiveTaskMessage>) => void;
  clearLiveTasks: () => void;

  // SSE event handling
  handleTaskEvent: (event: any) => void;
  handleCardEvent: (event: any) => void;
  handlePreviewUpdate: (event: any) => void;
}

export const useBuildStore = create<BuildState & BuildActions>((set, get) => ({
  // Initial state
  buildId: null,
  projectId: null,
  isBuilding: false,
  liveTasks: [],

  // Actions
  startBuild: (projectId: string) => {
    const buildId = crypto.randomUUID();
    set({
      buildId,
      projectId,
      isBuilding: true,
      liveTasks: []
    });
  },

  abortBuild: async () => {
    const { buildId } = get();
    if (!buildId) return;

    await fetch(`/api/build/${buildId}/abort`, { method: 'POST' });
    set({ isBuilding: false });
  },

  setBuildComplete: () => {
    set({ isBuilding: false });
  },

  addLiveTask: (task) => {
    set((state) => ({
      liveTasks: [...state.liveTasks, task]
    }));
  },

  updateLiveTask: (taskId, updates) => {
    set((state) => ({
      liveTasks: state.liveTasks.map((t) =>
        t.id === taskId ? { ...t, ...updates } : t
      )
    }));
  },

  clearLiveTasks: () => {
    set({ liveTasks: [] });
  },

  handleTaskEvent: (event) => {
    const { liveTasks } = get();
    const existing = liveTasks.find(t => t.id === event.id);

    if (existing) {
      get().updateLiveTask(event.id, {
        status: event.status,
        title: event.title
      });
    } else {
      get().addLiveTask({
        id: event.id,
        type: event.type,
        title: event.title,
        status: event.status,
        timestamp: Date.now(),
        session_id: event.session_id
      });
    }

    // Handle build complete
    if (event.type === 'build_complete') {
      get().setBuildComplete();
    }
  },

  handleCardEvent: (event) => {
    get().addLiveTask({
      id: crypto.randomUUID(),
      type: event.type,
      title: '',
      status: 'done',
      timestamp: Date.now(),
      session_id: event.session_id,
      card: {
        type: event.type,
        data: event.data
      }
    });
  },

  handlePreviewUpdate: (event) => {
    // Dispatch event for preview panel to refresh
    window.dispatchEvent(new CustomEvent('preview-update', {
      detail: { pageId: event.page_id }
    }));
  }
}));
```

**Acceptance Criteria**:
- [ ] Store tracks build state
- [ ] Live tasks added/updated correctly
- [ ] Event handlers process all SSE events
- [ ] Preview update triggers refresh

---

### Task 1.9: Integrate SSE Handling in Chat Panel

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/ChatPanel.tsx` or equivalent

Create hook for SSE event handling:

```typescript
// frontend/src/hooks/useBuildStream.ts

import { useEffect, useRef } from 'react';
import { useBuildStore } from '@/stores/buildStore';

export function useBuildStream(projectId: string) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const {
    isBuilding,
    handleTaskEvent,
    handleCardEvent,
    handlePreviewUpdate
  } = useBuildStore();

  useEffect(() => {
    if (!isBuilding) {
      // Close existing connection
      eventSourceRef.current?.close();
      return;
    }

    // SSE events are merged into chat endpoint
    // This hook processes build-specific events

    const handleSSEMessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);

      switch (event.type) {
        case 'task':
          handleTaskEvent(data);
          break;
        case 'card':
          handleCardEvent(data);
          break;
        case 'preview_update':
          handlePreviewUpdate(data);
          break;
      }
    };

    // Note: Actual EventSource connection managed by chat hook
    // This registers handlers for build events
    window.addEventListener('build-sse-event', handleSSEMessage as any);

    return () => {
      window.removeEventListener('build-sse-event', handleSSEMessage as any);
    };
  }, [isBuilding, handleTaskEvent, handleCardEvent, handlePreviewUpdate]);
}
```

**Acceptance Criteria**:
- [ ] Hook processes SSE events
- [ ] Events dispatched to correct handlers
- [ ] Cleanup on unmount/build end

---

### Task 1.10: Render LiveTasks in Chat

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/chat/ChatMessageList.tsx`

```typescript
// frontend/src/components/chat/ChatMessageList.tsx

import { useBuildStore } from '@/stores/buildStore';
import { TaskItem, AgentThinkingItem } from './TaskItem';
import { PageCard } from './cards/PageCard';
import { ValidationCard } from './cards/ValidationCard';

export function ChatMessageList({ messages }: { messages: ChatMessage[] }) {
  const { liveTasks } = useBuildStore();

  // Combine messages and live tasks chronologically
  const allItems = [...messages, ...liveTasks].sort(
    (a, b) => (a.timestamp || 0) - (b.timestamp || 0)
  );

  return (
    <div className="flex flex-col gap-1 p-4">
      {allItems.map((item) => {
        // Regular chat message
        if ('role' in item) {
          return <ChatMessage key={item.id} message={item} />;
        }

        // Live task item
        const task = item as LiveTaskMessage;

        // Card types
        if (task.card) {
          switch (task.card.type) {
            case 'page':
              return (
                <PageCard
                  key={task.id}
                  page={task.card.data as PageCardData}
                  onViewPreview={() => {/* navigate to preview */}}
                />
              );
            case 'validation':
              return (
                <ValidationCard
                  key={task.id}
                  {...(task.card.data as ValidationCardData)}
                  onRetry={() => {/* retry task */}}
                />
              );
          }
        }

        // One-line task items
        if (task.type === 'agent_thinking') {
          return <AgentThinkingItem key={task.id} message={task.title} />;
        }

        return (
          <TaskItem
            key={task.id}
            title={task.title}
            status={task.status}
            onRetry={task.status === 'failed' ? () => {/* retry */} : undefined}
          />
        );
      })}
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Messages and tasks render together chronologically
- [ ] Cards render for appropriate types
- [ ] One-line items render for tasks
- [ ] Scroll follows new content

---

## Technical Considerations

### SSE vs WebSocket

**Decision**: Use SSE (Server-Sent Events)

**Rationale**:
- Simpler than WebSocket for unidirectional streaming
- HTTP-compatible (works through proxies/CDNs)
- Automatic reconnection built-in
- Already used in chat endpoint

### Event Batching

Consider batching rapid events to prevent UI thrashing:

```typescript
// Debounce rapid task updates
const batchedUpdates = useDebouncedCallback(
  (tasks: LiveTaskMessage[]) => {
    set({ liveTasks: tasks });
  },
  16 // ~60fps
);
```

### Memory Management

Clear old tasks when:
- Build completes
- User starts new conversation
- Task list exceeds threshold (e.g., 100 items)

---

## Acceptance Criteria

### Functional

- [ ] Tasks appear in chat as one-line items during build
- [ ] Spinners animate for running tasks
- [ ] Checkmarks appear for completed tasks
- [ ] Failed tasks show retry button
- [ ] Cards render for pages and validation errors
- [ ] Abort button stops build
- [ ] Preview updates incrementally per task

### Performance

- [ ] First task appears within 2 seconds of build start
- [ ] UI remains responsive during streaming
- [ ] No memory leaks from SSE connections

### UX

- [ ] Clear visual distinction between task states
- [ ] Chat scrolls to show new tasks
- [ ] Abort is responsive and provides feedback

---

## Risk Factors

### Risk 1: SSE Connection Stability
- **Impact**: High - Users lose visibility if connection drops
- **Mitigation**: Implement reconnection with exponential backoff
- **Mitigation**: Show "Reconnecting..." status

### Risk 2: Build State Mismatch
- **Impact**: Medium - UI shows wrong state if events lost
- **Mitigation**: Include build_id and sequence numbers
- **Mitigation**: Provide "Refresh" action

### Risk 3: Performance with Many Tasks
- **Impact**: Medium - Slow rendering with 50+ tasks
- **Mitigation**: Virtualize task list
- **Mitigation**: Collapse old tasks into summary

---

## Estimated Scope

**Complexity**: Large

**Key Effort Drivers**:
- SSE event system integration (40%)
- Frontend component development (35%)
- Store and state management (15%)
- Testing and edge cases (10%)

---

## Testing Checklist

- [ ] Unit: TaskItem renders all states correctly
- [ ] Unit: Card components render data
- [ ] Unit: buildStore handles all event types
- [ ] Integration: SSE events flow to UI
- [ ] Integration: Abort cancels build
- [ ] E2E: Full build shows live progress
- [ ] E2E: Failed task shows retry, retry works
- [ ] Performance: 50+ tasks don't degrade UI

---

**Document Version**: 1.0
**Created**: 2026-01-27
**Status**: Ready for Implementation
