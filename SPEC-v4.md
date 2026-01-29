# Zaoya (造鸭) - v4 Specification

> **"Live agentic building with real-time visibility."**

v4 enhances the chat experience with real-time task execution display, inline result cards, ProductDoc in Preview Panel, and multi-page generation via orchestrator.

---

## Vision v4

**North Star**: "Watch your project come alive - see every task, agent, and tool in action."

v4 adds real-time visibility into the build process, similar to Lovable, v0, and Manus:

- **Live Task Feed** - See what's happening as it happens in the chat (one-line per task with spinner)
- **Agent/Tool Call Display** - Know which agent or tool is executing
- **Inline Result Cards** - Pages, Build Plans, and Interviews as interactive cards
- **ProductDoc in Preview Panel** - PRD as source of truth, switchable view in Preview
- **Multi-Page Generation** - Automatic multi-page detection and generation via orchestrator
- **Multi-Page Overview** - Full-screen thumbnail grid for page management

---

## What Changed from v3

| v3 Feature | v4 Change | Rationale |
|------------|-----------|-----------|
| Build Timeline Panel | **Kept** but task display moved to chat | Tasks shown as one-line items in chat |
| Separate task list UI | **Replaced** - Inline task items in chat | Better context, chat-first experience |
| Build controls | **Simplified** - Send button becomes abort button during build | Natural interaction |
| Page Panel | **Replaced** - Dropdown + thumbnail overview | Simpler, with powerful overview mode |
| Single-page focus | **Enhanced** - Multi-page auto-detection | Better for complex projects |
| Static build status | **Replaced** - Real-time SSE streaming | Live visibility like v0/Lovable |
| ProductDoc as card | **Moved to** Preview Panel as dedicated view | Source of truth, always accessible |

---

## Core Loop (v4)

```
[User Request] → [Intent Detection] → [Adaptive Interview]
                                              ↓
                                      [ProductDoc Generated]
                                              ↓
                            ┌─────────────────┴─────────────────┐
                            ↓                                   ↓
                   [Single Page Flow]                 [Multi-Page Flow]
                            ↓                                   ↓
                  [SingleTaskOrchestrator]          [MultiTaskOrchestrator]
                            ↓                                   ↓
              ┌─────────────────────────┐          ┌─────────────────────────┐
              │ Live Task Feed in Chat  │          │ Live Task Feed in Chat  │
              │ - One-line task items   │          │ - Page planning         │
              │ - Spinner → ✓/✗         │          │ - Per-page generation   │
              │ - Cards for results     │          │ - Cross-page linking    │
              └─────────────────────────┘          └─────────────────────────┘
                            ↓                                   ↓
                            └─────────────────┬─────────────────┘
                                              ↓
                                      [Preview Update (per task)]
                                              ↓
                                      [User Iteration via Chat]
```

---

## Part A: Live Task Feed in Chat

### Design Philosophy

The chat panel becomes the central place to understand what's happening. Unlike heavy card-based UIs, v4 uses **lightweight one-line task items**:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Zaoya                                                          [Settings]     │
├────────────────────┬────────────────────────────────────────────────────────────┤
│  Chat              │  Preview                     [Preview ▼] [ProductDoc] [⋯] │
│                    │                                                           │
│  ┌────────────────┐│  ┌─────────────────────────────────────────────────────┐  │
│  │ 🤖 理解你的需求...││  │                                                     │  │
│  └────────────────┘│  │         [Preview Area]                              │  │
│                    │  │                                                     │  │
│  ⚙️ 创建 Hero 区块... │  │                                                     │  │
│  ✓ Hero 区块完成     │  └─────────────────────────────────────────────────────┘  │
│  ⚙️ 创建 Features... │                                                          │
│  ✓ Features 完成     │                                                          │
│  ⚙️ 创建 CTA 区块... │                                                          │
│                    │                                                           │
│  ┌────────────────┐│                                                           │
│  │ 📄 Page: Home  ││                                                           │
│  │   /index.html  ││                                                           │
│  │   [查看预览]    ││                                                           │
│  └────────────────┘│                                                           │
│                    │                                                           │
│  ✓ HTML 验证通过    │                                                           │
│  ✓ JS 安全检查通过  │                                                           │
│                    │                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │ 输入消息...                                                    [■ 终止]  │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
└────────────────────┴────────────────────────────────────────────────────────────┘
```

### Task Display Strategy

**One-line items** (not cards) for most tasks:
- `⚙️ 正在处理: {task_name}...` (with spinner)
- `✓ {task_name}` (completed successfully)
- `✗ {task_name} [重试]` (failed with retry button)

**Cards** only for significant results:
- `PageCard` - When a page is generated
- `BuildPlanCard` - When build plan is ready (editable before start)
- `InterviewCard` - Interview questions (inline answering)
- `ValidationCard` - When validation fails (with error details + retry)

### Message Types in Chat

| Type | Display | Interactive |
|------|---------|-------------|
| `agent_thinking` | One-line with spinner | No |
| `task_started` | One-line with spinner | No |
| `task_done` | One-line with ✓ | No |
| `task_failed` | One-line with ✗ | [重试] button |
| `tool_call` | One-line (optional, can be hidden) | No |
| `page_created` | **Card** | [查看预览] |
| `build_plan` | **Card** (editable) | [开始构建] [编辑] |
| `interview` | **Card** | Inline answer + [跳过] |
| `validation_failed` | **Card** | Error details + [重试] |
| `build_complete` | AI message + QuickActionChips | Chips clickable |

### Message Data Structure

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

  // For cards
  card?: {
    type: 'page' | 'build_plan' | 'interview' | 'validation';
    data: PageCardData | BuildPlanCardData | InterviewCardData | ValidationCardData;
  };

  // Actions
  actions?: {
    label: string;
    action: 'retry' | 'view' | 'edit' | 'start_build' | 'skip';
  }[];
}
```

### Real-Time Streaming via SSE (Merged with Chat)

```python
# backend/app/api/project_chat.py (extended)

@router.post("/api/projects/{project_id}/chat")
async def project_chat(
    project_id: str,
    req: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    """
    SSE stream for chat + build progress.
    Event types:
    - message: AI text response
    - task: Task status update (started/done/failed)
    - card: Card content (page, build_plan, interview, validation)
    - preview_update: Signal to refresh preview
    """
    async def event_generator():
        # ... existing chat logic ...

        # During build, emit task events
        async for event in orchestrator.stream_progress(build_id):
            if event.type == 'task':
                yield {
                    "event": "task",
                    "data": json.dumps({
                        "id": event.task_id,
                        "title": event.title,
                        "status": event.status
                    })
                }
            elif event.type == 'card':
                yield {
                    "event": "card",
                    "data": json.dumps(event.card_data)
                }
            elif event.type == 'preview_update':
                yield {
                    "event": "preview_update",
                    "data": json.dumps({"page_id": event.page_id})
                }

    return EventSourceResponse(event_generator())
```

### Abort Button (Replaces Send During Build)

```typescript
// frontend/src/components/chat/InputBar.tsx

function InputBar({ isBuilding, onSend, onAbort }: InputBarProps) {
  return (
    <div className="flex items-center gap-2 border rounded-lg p-2">
      <input
        type="text"
        className="flex-1"
        placeholder="输入消息..."
        disabled={isBuilding}
      />
      {isBuilding ? (
        <button
          onClick={onAbort}
          className="bg-red-500 text-white px-4 py-2 rounded"
        >
          ■ 终止
        </button>
      ) : (
        <button onClick={onSend} className="bg-primary text-white px-4 py-2 rounded">
          发送
        </button>
      )}
    </div>
  );
}
```

---

## Part B: ProductDoc in Preview Panel

### Design Philosophy

ProductDoc is the **source of truth** for the project. It captures all interview answers, content requirements, and design specifications in a PRD format. It lives in the Preview Panel as a dedicated view, not as a chat card.

### Preview Panel Views

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Preview ▼]  [ProductDoc]                            [Home ▼] [⋯]         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ProductDoc View                                 │   │
│  │                                                                      │   │
│  │  # 项目需求文档                                                      │   │
│  │                                                                      │   │
│  │  ## 概述                                                             │   │
│  │  一个简洁的个人作品集网站，展示设计作品和联系方式。                    │   │
│  │                                                                      │   │
│  │  ## 目标用户                                                         │   │
│  │  - 潜在客户和雇主                                                    │   │
│  │  - 同行设计师                                                        │   │
│  │                                                                      │   │
│  │  ## 内容结构                                                         │   │
│  │  - Hero: 个人介绍 + 头像                                             │   │
│  │  - Projects: 作品展示网格                                            │   │
│  │  - Contact: 联系表单                                                 │   │
│  │                                                                      │   │
│  │  ## 设计要求                                                         │   │
│  │  - 风格: 简约现代                                                    │   │
│  │  - 配色: 黑白为主，蓝色强调                                          │   │
│  │  - 字体: 无衬线体                                                    │   │
│  │                                                                      │   │
│  │  ## 页面规划                                                         │   │
│  │  - Home (/)                                                          │   │
│  │  - About (/about)                                                    │   │
│  │  - Contact (/contact)                                                │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ProductDoc Structure (Flexible PRD)

```typescript
// frontend/src/types/productDoc.ts

interface ProductDoc {
  id: string;
  project_id: string;
  created_at: string;
  updated_at: string;

  // Required sections
  overview: string;
  target_users?: string[];

  // Content (flexible based on project complexity)
  content_structure: {
    sections: { name: string; description: string }[];
  };

  // Design (if applicable)
  design_requirements?: {
    style?: string;
    colors?: string[];
    typography?: string;
  };

  // Pages
  page_plan: {
    pages: { name: string; path: string; description: string }[];
  };

  // Technical (if applicable)
  technical_constraints?: string[];

  // Raw interview data
  interview_answers: { question: string; answer: string }[];
}
```

### ProductDoc Behavior

| Aspect | Behavior |
|--------|----------|
| Visibility | Appears after interview completes, not before |
| Editing | Read-only; user says "修改 ProductDoc 的..." in chat to update |
| Format | Markdown-like display, similar to PDF |
| Source of truth | All build decisions reference this document |

### Preview Panel Toolbar

```typescript
// frontend/src/components/preview/PreviewToolbar.tsx

interface PreviewToolbarProps {
  currentView: 'preview' | 'productDoc';
  currentPage: { id: string; name: string; path: string };
  pages: { id: string; name: string; path: string }[];
  hasProductDoc: boolean;
  onViewChange: (view: 'preview' | 'productDoc') => void;
  onPageChange: (pageId: string) => void;
  onOpenOverview: () => void;
}

function PreviewToolbar({
  currentView,
  currentPage,
  pages,
  hasProductDoc,
  onViewChange,
  onPageChange,
  onOpenOverview
}: PreviewToolbarProps) {
  return (
    <div className="flex items-center justify-between border-b p-2">
      {/* Left: View tabs */}
      <div className="flex gap-1">
        <button
          className={cn("px-3 py-1 rounded", currentView === 'preview' && "bg-gray-100")}
          onClick={() => onViewChange('preview')}
        >
          Preview
        </button>
        {hasProductDoc && (
          <button
            className={cn("px-3 py-1 rounded", currentView === 'productDoc' && "bg-gray-100")}
            onClick={() => onViewChange('productDoc')}
          >
            ProductDoc
          </button>
        )}
      </div>

      {/* Right: Page selector + overview button */}
      <div className="flex items-center gap-2">
        <PageDropdown
          current={currentPage}
          pages={pages}
          onChange={onPageChange}
        />
        <button
          className="p-2 hover:bg-gray-100 rounded"
          onClick={onOpenOverview}
          title="查看所有页面"
        >
          ⋯
        </button>
      </div>
    </div>
  );
}
```

---

## Part C: Multi-Page Overview

### Design Philosophy

When user clicks the `⋯` button, the entire EditorPage is replaced with a full-screen multi-page overview. This provides a bird's-eye view of all pages with drag-to-reorder, hover actions, and easy navigation.

### Overview Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ← 返回编辑                                          多页面概览 (3 个页面)           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│   │             │    │             │    │             │    │             │         │
│   │             │    │             │    │             │    │             │         │
│   │   [Home]    │    │   [About]   │    │  [Contact]  │    │  [Pricing]  │         │
│   │    首页     │    │    关于     │    │    联系     │    │    定价     │         │
│   │             │    │             │    │             │    │             │         │
│   │             │    │             │    │             │    │             │         │
│   │  160x347px  │    │  160x347px  │    │  160x347px  │    │  160x347px  │         │
│   │             │    │             │    │             │    │             │         │
│   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘         │
│        Home              About            Contact            Pricing               │
│         /               /about            /contact           /pricing              │
│                                                                                     │
│   (Drag to reorder • Hover for actions • Click to preview)                         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Thumbnail Specifications

| Property | Value |
|----------|-------|
| Size | 160 x 347 px (9:19.5 ratio) |
| Gap | 16px |
| Layout | Responsive flex-wrap |
| Overflow | Scroll (no pagination) |

### Hover Actions

When hovering over a thumbnail:

```
┌─────────────┐
│   [⋮]      │  ← Actions menu (top-right)
│             │
│   Preview   │
│   of page   │
│             │
└─────────────┘
    Home
      /

Actions menu:
┌──────────────┐
│ 重命名       │
│ 设为首页     │
│ ────────── │
│ 删除        │
└──────────────┘
```

### Drag to Reorder

- Thumbnails are draggable
- Drop zones show between thumbnails
- Order persists to project

### Overview Component

```typescript
// frontend/src/components/preview/MultiPageOverview.tsx

interface MultiPageOverviewProps {
  pages: { id: string; name: string; path: string; thumbnailUrl: string }[];
  onBack: () => void;
  onSelectPage: (pageId: string) => void;
  onReorder: (pageIds: string[]) => void;
  onRename: (pageId: string, newName: string) => void;
  onSetAsHome: (pageId: string) => void;
  onDelete: (pageId: string) => void;
}

function MultiPageOverview({
  pages,
  onBack,
  onSelectPage,
  onReorder,
  onRename,
  onSetAsHome,
  onDelete
}: MultiPageOverviewProps) {
  return (
    <div className="fixed inset-0 bg-white z-50 overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <button onClick={onBack} className="flex items-center gap-2">
          ← 返回编辑
        </button>
        <span className="text-gray-500">多页面概览 ({pages.length} 个页面)</span>
      </div>

      {/* Thumbnail Grid */}
      <div className="p-6">
        <DndContext onDragEnd={handleDragEnd}>
          <div className="flex flex-wrap gap-4">
            {pages.map(page => (
              <PageThumbnail
                key={page.id}
                page={page}
                onSelect={() => onSelectPage(page.id)}
                onRename={(name) => onRename(page.id, name)}
                onSetAsHome={() => onSetAsHome(page.id)}
                onDelete={() => onDelete(page.id)}
              />
            ))}
          </div>
        </DndContext>

        <div className="mt-4 text-sm text-gray-400 text-center">
          拖拽调整顺序 • 悬停显示操作 • 点击预览
        </div>
      </div>
    </div>
  );
}
```

### Page Dropdown (Quick Switch)

```typescript
// frontend/src/components/preview/PageDropdown.tsx

function PageDropdown({
  current,
  pages,
  onChange
}: PageDropdownProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1 border rounded"
      >
        {current.name}
        <ChevronDown className="w-4 h-4" />
      </button>

      {open && (
        <div className="absolute top-full right-0 mt-1 bg-white border rounded shadow-lg z-10">
          {pages.map(page => (
            <button
              key={page.id}
              onClick={() => {
                onChange(page.id);
                setOpen(false);
              }}
              className={cn(
                "w-full px-4 py-2 text-left hover:bg-gray-50",
                page.id === current.id && "bg-gray-100"
              )}
            >
              <div className="font-medium">{page.name}</div>
              <div className="text-xs text-gray-500">{page.path}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Part D: Multi-Page Detection & Generation

### Multi-Page Detection

The orchestrator automatically detects when a project needs multiple pages:

```python
# backend/app/services/build_runtime/planner.py

class MultiPageDetector:
    """Detect if project needs multiple pages."""

    INDICATORS = {
        # Content-based indicators
        "multi_section_content": [
            "about", "features", "pricing", "contact", "blog",
            "team", "portfolio", "gallery", "testimonials"
        ],

        # Explicit multi-page requests
        "explicit_multi_page": [
            "multiple pages", "several pages", "more than one page",
            "homepage and", "landing page and", "多个页面", "几个页面"
        ],

        # Project type indicators
        "project_types": {
            "portfolio": {"pages": ["home", "about", "projects", "contact"]},
            "business_site": {"pages": ["home", "about", "services", "contact"]},
            "blog": {"pages": ["home", "posts", "about", "contact"]},
            "ecommerce": {"pages": ["home", "products", "cart", "checkout"]},
            "event": {"pages": ["home", "rsvp", "details", "gallery"]},
        }
    }

    async def detect(
        self,
        product_doc: ProductDoc,
        user_message: str
    ) -> MultiPageDecision:
        """
        Analyze project requirements and decide if multi-page is needed.
        Uses ProductDoc as primary source.
        """
        # Check ProductDoc page_plan first
        if product_doc.page_plan and len(product_doc.page_plan.pages) > 1:
            return MultiPageDecision(
                is_multi_page=True,
                pages=[p.name for p in product_doc.page_plan.pages],
                reason="ProductDoc specifies multiple pages"
            )

        # Check for explicit multi-page requests
        if self._has_explicit_request(user_message):
            return MultiPageDecision(
                is_multi_page=True,
                reason="User explicitly requested multiple pages"
            )

        # Check content sections
        sections = product_doc.content_structure.sections
        if len(sections) > 5:
            return MultiPageDecision(
                is_multi_page=True,
                reason=f"Content has {len(sections)} sections, splitting across pages"
            )

        return MultiPageDecision(is_multi_page=False)
```

### BuildPlanCard (Editable)

Users can edit the page list in BuildPlanCard before starting the build:

```typescript
// frontend/src/components/chat/cards/BuildPlanCard.tsx

interface BuildPlanCardProps {
  plan: {
    pages: { id: string; name: string; path: string }[];
    tasks: { id: string; title: string; status: string }[];
    estimated_tasks: number;
  };
  onApprove: () => void;
  onEditPages: (pages: { name: string; path: string }[]) => void;
}

function BuildPlanCard({ plan, onApprove, onEditPages }: BuildPlanCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedPages, setEditedPages] = useState(plan.pages);

  return (
    <div className="border rounded-lg p-4 max-w-md">
      <h4 className="font-medium mb-2 flex items-center gap-2">
        📋 构建计划
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="text-sm text-blue-500"
        >
          {isEditing ? '完成' : '编辑'}
        </button>
      </h4>

      <div className="text-sm text-gray-600 mb-3">
        {plan.pages.length} 个页面 • 约 {plan.estimated_tasks} 个任务
      </div>

      {/* Page List (editable) */}
      <div className="space-y-1 mb-3">
        {editedPages.map((page, i) => (
          <div key={i} className="flex items-center gap-2 text-sm">
            <span className="font-medium">{page.name}</span>
            <code className="text-xs text-gray-500">{page.path}</code>
            {isEditing && (
              <button
                onClick={() => {
                  setEditedPages(editedPages.filter((_, j) => j !== i));
                }}
                className="text-red-500 text-xs"
              >
                删除
              </button>
            )}
          </div>
        ))}
        {isEditing && (
          <button
            onClick={() => {
              const name = prompt('页面名称:');
              if (name) {
                setEditedPages([
                  ...editedPages,
                  { name, path: `/${name.toLowerCase().replace(/\s+/g, '-')}` }
                ]);
              }
            }}
            className="text-sm text-blue-500"
          >
            + 添加页面
          </button>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => {
            onEditPages(editedPages);
            onApprove();
          }}
          className="bg-primary text-white px-4 py-2 rounded"
        >
          开始构建
        </button>
      </div>
    </div>
  );
}
```

### Multi-Task Orchestrator

```python
# backend/app/services/build_runtime/multi_task_orchestrator.py

class MultiTaskOrchestrator:
    """
    Orchestrates multi-page generation with parallel task execution.
    """

    async def generate_multi_page(
        self,
        project_id: str,
        user_id: str,
        product_doc: ProductDoc,
        page_plan: List[PageSpec]
    ) -> AsyncGenerator[BuildEvent, None]:
        """
        Generate multiple pages with real-time streaming events.
        """
        # Generate home page first
        home = next((p for p in page_plan if p.is_main), page_plan[0])

        async for event in self._generate_page(project_id, home, product_doc):
            yield event
            if event.type == 'task_done':
                yield BuildEvent(type='preview_update', page_id=home.id)

        # Parallel generation for other pages (or sequential if needed)
        for page in page_plan:
            if page.id == home.id:
                continue

            async for event in self._generate_page(project_id, page, product_doc):
                yield event
                if event.type == 'task_done':
                    yield BuildEvent(type='preview_update', page_id=page.id)

        # Final completion event
        yield BuildEvent(
            type='build_complete',
            message='所有页面已生成完成'
        )

    async def _generate_page(
        self,
        project_id: str,
        page: PageSpec,
        product_doc: ProductDoc
    ) -> AsyncGenerator[BuildEvent, None]:
        """Generate a single page with task events."""

        # Emit task started
        yield BuildEvent(
            type='task_started',
            task_id=f"page-{page.id}",
            title=f"生成 {page.name} 页面"
        )

        try:
            # Generate page content
            html = await self.ai_service.generate_page(page, product_doc)

            # Validate
            validation = self.validator.run(html)

            if not validation.is_valid:
                yield BuildEvent(
                    type='task_failed',
                    task_id=f"page-{page.id}",
                    title=f"{page.name} 验证失败",
                    card={
                        'type': 'validation',
                        'data': validation.to_dict()
                    }
                )
                return

            # Save page
            await self.storage.save_page(project_id, page.id, html)

            # Emit success
            yield BuildEvent(
                type='task_done',
                task_id=f"page-{page.id}",
                title=f"{page.name} 完成"
            )

            # Emit page card
            yield BuildEvent(
                type='card',
                card={
                    'type': 'page',
                    'data': {
                        'id': page.id,
                        'name': page.name,
                        'path': page.path
                    }
                }
            )

        except Exception as e:
            yield BuildEvent(
                type='task_failed',
                task_id=f"page-{page.id}",
                title=f"{page.name} 生成失败",
                error=str(e)
            )
```

---

## Part E: Updated Store Structure

### buildStore (Refactored with LiveTaskMessage)

```typescript
// frontend/src/stores/buildStore.ts

interface BuildState {
  // Session
  buildId: string | null;
  projectId: string | null;
  isBuilding: boolean;

  // Live tasks (core data structure)
  liveTasks: LiveTaskMessage[];

  // ProductDoc
  productDoc: ProductDoc | null;

  // Pages
  pages: PageInfo[];
  currentPageId: string | null;

  // Overview mode
  isOverviewOpen: boolean;
}

interface BuildActions {
  // Build control
  startBuild: (projectId: string, pagesPlan: PageSpec[]) => Promise<void>;
  abortBuild: () => Promise<void>;
  retryTask: (taskId: string) => Promise<void>;

  // Live task management
  addLiveTask: (task: LiveTaskMessage) => void;
  updateLiveTask: (taskId: string, updates: Partial<LiveTaskMessage>) => void;

  // ProductDoc
  setProductDoc: (doc: ProductDoc) => void;
  updateProductDoc: (updates: Partial<ProductDoc>) => void;

  // Pages
  addPage: (page: PageInfo) => void;
  removePage: (pageId: string) => void;
  reorderPages: (pageIds: string[]) => void;
  setCurrentPage: (pageId: string) => void;
  renamePage: (pageId: string, name: string) => void;
  setAsHomePage: (pageId: string) => void;

  // Overview
  openOverview: () => void;
  closeOverview: () => void;

  // Stream handling
  handleStreamEvent: (event: BuildEvent) => void;
}
```

---

## Part F: API Changes

### Updated Endpoints

```python
# backend/app/api/build.py

@router.post("/api/build/start")
async def start_build(
    req: BuildStartRequest,
    user_id: str = Depends(get_current_user)
) -> BuildResponse:
    """
    Start a new build. Returns build_id for streaming.
    """
    pass

@router.post("/api/build/{build_id}/abort")
async def abort_build(
    build_id: str,
    user_id: str = Depends(get_current_user)
):
    """Abort ongoing build."""
    pass

@router.post("/api/build/{build_id}/retry/{task_id}")
async def retry_task(
    build_id: str,
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """Retry a failed task."""
    pass

# backend/app/api/product_doc.py (new)

@router.get("/api/projects/{project_id}/product-doc")
async def get_product_doc(
    project_id: str,
    user_id: str = Depends(get_current_user)
) -> ProductDoc:
    """Get project's ProductDoc."""
    pass

@router.patch("/api/projects/{project_id}/product-doc")
async def update_product_doc(
    project_id: str,
    req: ProductDocUpdateRequest,
    user_id: str = Depends(get_current_user)
) -> ProductDoc:
    """Update ProductDoc (via AI command in chat)."""
    pass

# backend/app/api/pages.py (updated)

@router.patch("/api/projects/{project_id}/pages/reorder")
async def reorder_pages(
    project_id: str,
    req: ReorderPagesRequest,
    user_id: str = Depends(get_current_user)
):
    """Reorder project pages."""
    pass
```

---

## Part G: Cross-Page Element Sharing

### v4 Scope

**Not supported in v4**: Each page is generated independently with its own header/footer. This keeps implementation simple.

For v5, consider:
- Extracting shared components after first page generation
- Layout templates with content slots
- Project-level component library

---

## Implementation Roadmap

### Priority Order

1. **实时任务流** (Week 1-2)
   - SSE event types merged into chat endpoint
   - One-line task display in chat
   - Abort button during build

2. **ProductDoc** (Week 2-3)
   - ProductDoc data model
   - Preview Panel view switching
   - Interview → ProductDoc generation
   - Read-only display with chat-based editing

3. **多页面检测** (Week 3-4)
   - MultiPageDetector implementation
   - BuildPlanCard with editable page list
   - MultiTaskOrchestrator

4. **缩略图概览** (Week 4-5)
   - Full-screen overview component
   - Thumbnail rendering (160x347px)
   - Drag-to-reorder
   - Hover actions menu

5. **BuildPlan 修复** (Week 5-6)
   - Ensure BuildPlan reflects actual task list
   - Real-time status updates in BuildPlanCard

---

## Success Metrics (v4)

| Metric | v3 | v4 Target |
|--------|----|--------------|
| User understanding of build progress | N/A | > 80% report "clear visibility" |
| Time to first task display | N/A | < 2 seconds |
| Multi-page detection accuracy | N/A | > 85% |
| ProductDoc usefulness rating | N/A | > 4/5 |
| Page overview interaction rate | N/A | > 60% use overview at least once |
| Streaming reliability | N/A | 99% uptime during builds |

---

## Summary

v4 transforms the build experience with:

| What's Changed | From | To |
|---------------|------|-----|
| Task display | Timeline Panel | One-line items in chat |
| ProductDoc | Not visible | Dedicated view in Preview Panel |
| Page management | Separate panel | Dropdown + full-screen overview |
| Build control | Panel buttons | Input bar abort button |
| BuildPlan | Inaccurate | Accurate + editable page list |
| Preview updates | On completion | Per-task incremental |

**Result**: Users can watch their project build in real-time, reference the ProductDoc as source of truth, manage multiple pages intuitively, and interact with results directly in the chat.

---

**Document Version**: 4.1
**Created**: 2026-01-27
**Updated**: 2026-01-27
**Status**: Draft - Ready for Implementation

**Change Log**:
- 4.0: Initial v4 specification
- 4.1: Major revision based on interview feedback
  - Changed task display from cards to one-line items
  - Moved ProductDoc to Preview Panel as dedicated view
  - Added full-screen multi-page overview with thumbnails
  - Specified thumbnail size: 160x347px (9:19.5)
  - Added drag-to-reorder for pages
  - Abort button replaces send button during build
  - Preview updates incrementally per task
  - BuildPlan to be fixed for accuracy
  - Defined implementation priority order
