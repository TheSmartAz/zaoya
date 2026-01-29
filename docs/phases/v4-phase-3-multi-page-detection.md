# v4 Phase 3: Multi-Page Detection (多页面检测)

**Timeline**: Weeks 3-4
**Status**: Pending
**Dependencies**: Phase 2 (ProductDoc System) complete

---

## Phase Overview

This phase implements automatic multi-page detection and generation orchestration. The system intelligently determines when a project needs multiple pages, presents an editable build plan, and executes generation via the MultiTaskOrchestrator with real-time streaming.

### Connection to Project Goals

- **Complex Project Support**: Enable multi-page websites (portfolios, business sites)
- **User Control**: Editable build plan before execution
- **Visibility**: Real-time progress for multi-page builds

---

## Prerequisites

### Technical Prerequisites
- [ ] Phase 1 complete (Live Task Feed streaming)
- [ ] Phase 2 complete (ProductDoc with page_plan)
- [ ] Existing single-page orchestrator functional
- [ ] BuildPlanCard infrastructure exists

### Domain Prerequisites
- [ ] Project type indicators defined
- [ ] Multi-page detection heuristics validated

---

## Detailed Tasks

### Task 3.1: Implement MultiPageDetector

**Priority**: P0 (Critical)
**Files**: `backend/app/services/build_runtime/planner.py`

```python
# backend/app/services/build_runtime/planner.py

from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class MultiPageDecision:
    """Result of multi-page detection analysis."""
    is_multi_page: bool
    pages: List[str] = None
    reason: str = ""
    confidence: float = 0.0

@dataclass
class PageSpec:
    """Specification for a single page."""
    id: str
    name: str
    path: str
    description: str
    is_main: bool
    sections: List[str]

class MultiPageDetector:
    """
    Detect if project needs multiple pages.

    Detection sources (priority order):
    1. ProductDoc page_plan (explicit)
    2. User message explicit request
    3. Content complexity analysis
    4. Project type inference
    """

    # Content-based indicators
    MULTI_SECTION_KEYWORDS = [
        "about", "features", "pricing", "contact", "blog",
        "team", "portfolio", "gallery", "testimonials",
        "services", "projects", "work", "faq", "careers"
    ]

    # Explicit multi-page requests
    EXPLICIT_PATTERNS = [
        r"multiple pages?",
        r"several pages?",
        r"more than one page",
        r"homepage and",
        r"landing page and",
        r"\d+ pages?",
        r"多个页面",
        r"几个页面",
        r"多页",
        r"首页和"
    ]

    # Project type → suggested pages
    PROJECT_TYPE_PAGES = {
        "portfolio": [
            PageSpec("home", "Home", "/", "作品集首页", True, ["hero", "featured_work"]),
            PageSpec("about", "About", "/about", "个人介绍", False, ["bio", "skills"]),
            PageSpec("projects", "Projects", "/projects", "作品展示", False, ["project_grid"]),
            PageSpec("contact", "Contact", "/contact", "联系方式", False, ["contact_form"])
        ],
        "business": [
            PageSpec("home", "Home", "/", "公司首页", True, ["hero", "features"]),
            PageSpec("about", "About", "/about", "关于我们", False, ["company_intro"]),
            PageSpec("services", "Services", "/services", "服务介绍", False, ["service_list"]),
            PageSpec("contact", "Contact", "/contact", "联系我们", False, ["contact_form"])
        ],
        "event": [
            PageSpec("home", "Home", "/", "活动首页", True, ["hero", "event_details"]),
            PageSpec("rsvp", "RSVP", "/rsvp", "报名页面", False, ["rsvp_form"]),
            PageSpec("gallery", "Gallery", "/gallery", "活动相册", False, ["photo_gallery"])
        ],
        "blog": [
            PageSpec("home", "Home", "/", "博客首页", True, ["hero", "recent_posts"]),
            PageSpec("posts", "Posts", "/posts", "文章列表", False, ["post_list"]),
            PageSpec("about", "About", "/about", "关于作者", False, ["author_bio"])
        ],
        "landing": [
            # Single page by default
            PageSpec("home", "Home", "/", "着陆页", True, ["hero", "features", "cta"])
        ]
    }

    async def detect(
        self,
        product_doc: "ProductDoc",
        user_message: str,
        project_type: Optional[str] = None
    ) -> MultiPageDecision:
        """
        Analyze project requirements and decide if multi-page is needed.

        Args:
            product_doc: Project's ProductDoc (source of truth)
            user_message: User's original request
            project_type: Inferred or explicit project type

        Returns:
            MultiPageDecision with pages list if multi-page
        """
        # 1. Check ProductDoc page_plan first (highest priority)
        if product_doc and product_doc.page_plan:
            pages = product_doc.page_plan.get("pages", [])
            if len(pages) > 1:
                return MultiPageDecision(
                    is_multi_page=True,
                    pages=[p["name"] for p in pages],
                    reason="ProductDoc specifies multiple pages",
                    confidence=1.0
                )

        # 2. Check for explicit multi-page requests
        if self._has_explicit_request(user_message):
            pages = self._extract_page_names(user_message)
            return MultiPageDecision(
                is_multi_page=True,
                pages=pages or ["Home", "About", "Contact"],
                reason="User explicitly requested multiple pages",
                confidence=0.95
            )

        # 3. Check content complexity
        if product_doc:
            sections = product_doc.content_structure.get("sections", [])
            if len(sections) > 5:
                return MultiPageDecision(
                    is_multi_page=True,
                    pages=self._suggest_pages_from_sections(sections),
                    reason=f"Content has {len(sections)} sections, splitting across pages",
                    confidence=0.8
                )

        # 4. Check project type
        if project_type and project_type in self.PROJECT_TYPE_PAGES:
            type_pages = self.PROJECT_TYPE_PAGES[project_type]
            if len(type_pages) > 1:
                return MultiPageDecision(
                    is_multi_page=True,
                    pages=[p.name for p in type_pages],
                    reason=f"Project type '{project_type}' typically has multiple pages",
                    confidence=0.7
                )

        # Default: single page
        return MultiPageDecision(
            is_multi_page=False,
            reason="No multi-page indicators detected",
            confidence=0.9
        )

    def _has_explicit_request(self, message: str) -> bool:
        """Check if message explicitly requests multiple pages."""
        message_lower = message.lower()
        return any(
            re.search(pattern, message_lower)
            for pattern in self.EXPLICIT_PATTERNS
        )

    def _extract_page_names(self, message: str) -> List[str]:
        """Extract page names from message if mentioned."""
        # Simple extraction - could use AI for more complex cases
        pages = []
        for keyword in self.MULTI_SECTION_KEYWORDS:
            if keyword.lower() in message.lower():
                pages.append(keyword.title())
        return pages if pages else None

    def _suggest_pages_from_sections(self, sections: List[dict]) -> List[str]:
        """
        Suggest page structure based on content sections.
        Groups related sections into pages.
        """
        pages = ["Home"]

        # Group by priority and category
        high_priority = [s for s in sections if s.get("priority") == "high"]
        low_priority = [s for s in sections if s.get("priority") != "high"]

        # Home gets high-priority sections
        # Create separate pages for low-priority content
        if len(low_priority) > 2:
            # Check for common page-worthy sections
            for section in low_priority:
                name = section.get("name", "").lower()
                if any(kw in name for kw in ["about", "team", "contact"]):
                    pages.append(section["name"].title())

        # Ensure uniqueness
        return list(dict.fromkeys(pages))

    def get_page_specs(
        self,
        decision: MultiPageDecision,
        product_doc: "ProductDoc",
        project_type: Optional[str] = None
    ) -> List[PageSpec]:
        """
        Convert decision into detailed PageSpecs.

        Args:
            decision: MultiPageDecision result
            product_doc: Source of content structure
            project_type: For default page templates

        Returns:
            List of PageSpec ready for generation
        """
        if not decision.is_multi_page:
            # Single page
            return [PageSpec(
                id="home",
                name="Home",
                path="/",
                description="主页",
                is_main=True,
                sections=[s["name"] for s in product_doc.content_structure.get("sections", [])]
            )]

        # Use ProductDoc page_plan if available
        if product_doc and product_doc.page_plan:
            return [
                PageSpec(
                    id=p.get("id", p["name"].lower()),
                    name=p["name"],
                    path=p["path"],
                    description=p.get("description", ""),
                    is_main=p.get("is_main", False),
                    sections=p.get("sections", [])
                )
                for p in product_doc.page_plan.get("pages", [])
            ]

        # Fall back to project type defaults
        if project_type and project_type in self.PROJECT_TYPE_PAGES:
            return self.PROJECT_TYPE_PAGES[project_type]

        # Generate from decision.pages
        specs = []
        for i, name in enumerate(decision.pages or ["Home"]):
            specs.append(PageSpec(
                id=name.lower().replace(" ", "-"),
                name=name,
                path="/" if i == 0 else f"/{name.lower().replace(' ', '-')}",
                description=f"{name} 页面",
                is_main=(i == 0),
                sections=[]
            ))
        return specs
```

**Acceptance Criteria**:
- [ ] ProductDoc page_plan takes priority
- [ ] Explicit requests detected correctly
- [ ] Content complexity triggers multi-page
- [ ] Project type provides sensible defaults
- [ ] Single-page is default when no indicators

---

### Task 3.2: Create BuildPlanCard Component

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/chat/cards/BuildPlanCard.tsx`

```typescript
// frontend/src/components/chat/cards/BuildPlanCard.tsx

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Plus, Trash2, GripVertical, Edit2, Check } from 'lucide-react';

interface BuildPlanPage {
  id: string;
  name: string;
  path: string;
  is_main?: boolean;
}

interface BuildPlanCardProps {
  plan: {
    pages: BuildPlanPage[];
    estimated_tasks: number;
    project_type?: string;
  };
  onApprove: (pages: BuildPlanPage[]) => void;
  onCancel: () => void;
}

export function BuildPlanCard({ plan, onApprove, onCancel }: BuildPlanCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedPages, setEditedPages] = useState<BuildPlanPage[]>(plan.pages);
  const [editingPageId, setEditingPageId] = useState<string | null>(null);

  const handleAddPage = () => {
    const newPage: BuildPlanPage = {
      id: `page-${Date.now()}`,
      name: '新页面',
      path: '/new-page',
      is_main: false
    };
    setEditedPages([...editedPages, newPage]);
    setEditingPageId(newPage.id);
  };

  const handleRemovePage = (pageId: string) => {
    // Don't allow removing the main page
    const page = editedPages.find(p => p.id === pageId);
    if (page?.is_main) return;

    setEditedPages(editedPages.filter(p => p.id !== pageId));
  };

  const handleUpdatePage = (pageId: string, updates: Partial<BuildPlanPage>) => {
    setEditedPages(editedPages.map(p =>
      p.id === pageId ? { ...p, ...updates } : p
    ));
  };

  const handleSetAsMain = (pageId: string) => {
    setEditedPages(editedPages.map(p => ({
      ...p,
      is_main: p.id === pageId,
      path: p.id === pageId ? '/' : (p.path === '/' ? `/${p.name.toLowerCase().replace(/\s+/g, '-')}` : p.path)
    })));
  };

  return (
    <div className="border rounded-lg p-4 max-w-md bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium flex items-center gap-2">
          📋 构建计划
        </h4>
        <button
          onClick={() => setIsEditing(!isEditing)}
          className="text-sm text-blue-500 hover:text-blue-700"
        >
          {isEditing ? '完成编辑' : '编辑'}
        </button>
      </div>

      {/* Summary */}
      <div className="text-sm text-gray-600 mb-4">
        {editedPages.length} 个页面 • 约 {plan.estimated_tasks} 个任务
        {plan.project_type && (
          <span className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded">
            {plan.project_type}
          </span>
        )}
      </div>

      {/* Page List */}
      <div className="space-y-2 mb-4">
        {editedPages.map((page) => (
          <PageItem
            key={page.id}
            page={page}
            isEditing={isEditing}
            isEditingName={editingPageId === page.id}
            onStartEdit={() => setEditingPageId(page.id)}
            onEndEdit={() => setEditingPageId(null)}
            onUpdate={(updates) => handleUpdatePage(page.id, updates)}
            onRemove={() => handleRemovePage(page.id)}
            onSetAsMain={() => handleSetAsMain(page.id)}
          />
        ))}

        {/* Add Page Button */}
        {isEditing && (
          <button
            onClick={handleAddPage}
            className="flex items-center gap-2 text-sm text-blue-500 hover:text-blue-700 py-2"
          >
            <Plus className="w-4 h-4" />
            添加页面
          </button>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-2 border-t">
        <button
          onClick={() => onApprove(editedPages)}
          className="flex-1 bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded font-medium"
        >
          开始构建
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
        >
          取消
        </button>
      </div>
    </div>
  );
}

interface PageItemProps {
  page: BuildPlanPage;
  isEditing: boolean;
  isEditingName: boolean;
  onStartEdit: () => void;
  onEndEdit: () => void;
  onUpdate: (updates: Partial<BuildPlanPage>) => void;
  onRemove: () => void;
  onSetAsMain: () => void;
}

function PageItem({
  page,
  isEditing,
  isEditingName,
  onStartEdit,
  onEndEdit,
  onUpdate,
  onRemove,
  onSetAsMain
}: PageItemProps) {
  const [tempName, setTempName] = useState(page.name);

  const handleSaveName = () => {
    const newPath = page.is_main ? '/' : `/${tempName.toLowerCase().replace(/\s+/g, '-')}`;
    onUpdate({ name: tempName, path: newPath });
    onEndEdit();
  };

  return (
    <div className={cn(
      "flex items-center gap-2 p-2 rounded",
      page.is_main ? "bg-blue-50 border border-blue-200" : "bg-gray-50"
    )}>
      {/* Drag Handle (editing mode) */}
      {isEditing && (
        <GripVertical className="w-4 h-4 text-gray-400 cursor-grab" />
      )}

      {/* Page Info */}
      <div className="flex-1 min-w-0">
        {isEditingName ? (
          <div className="flex items-center gap-1">
            <input
              type="text"
              value={tempName}
              onChange={(e) => setTempName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveName()}
              className="flex-1 px-2 py-1 text-sm border rounded"
              autoFocus
            />
            <button
              onClick={handleSaveName}
              className="p-1 text-green-600 hover:bg-green-50 rounded"
            >
              <Check className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{page.name}</span>
            {page.is_main && (
              <span className="text-xs text-blue-600 bg-blue-100 px-1.5 py-0.5 rounded">
                首页
              </span>
            )}
            {isEditing && !page.is_main && (
              <button
                onClick={onStartEdit}
                className="p-0.5 text-gray-400 hover:text-gray-600"
              >
                <Edit2 className="w-3 h-3" />
              </button>
            )}
          </div>
        )}
        <code className="text-xs text-gray-500">{page.path}</code>
      </div>

      {/* Actions (editing mode) */}
      {isEditing && !page.is_main && (
        <div className="flex items-center gap-1">
          <button
            onClick={onSetAsMain}
            className="text-xs text-blue-500 hover:text-blue-700 px-2 py-1"
          >
            设为首页
          </button>
          <button
            onClick={onRemove}
            className="p-1 text-red-500 hover:bg-red-50 rounded"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Shows page list with paths
- [ ] Edit mode allows add/remove pages
- [ ] Can rename pages (updates path automatically)
- [ ] Can set any page as main (updates path to /)
- [ ] Main page highlighted
- [ ] Approve triggers build with edited pages
- [ ] Cancel dismisses card

---

### Task 3.3: Implement MultiTaskOrchestrator

**Priority**: P0 (Critical)
**Files**: `backend/app/services/build_runtime/multi_task_orchestrator.py`

```python
# backend/app/services/build_runtime/multi_task_orchestrator.py

from typing import List, AsyncGenerator, Optional
from dataclasses import dataclass
import asyncio
import uuid

from app.services.build_runtime.events import BuildEvent, BuildEventType, BuildEventEmitter
from app.services.build_runtime.planner import PageSpec
from app.services.ai_service import AIService
from app.services.build_runtime.validator import HTMLValidator

@dataclass
class BuildSession:
    """Active build session state."""
    id: str
    project_id: str
    user_id: str
    pages: List[PageSpec]
    completed_pages: List[str]
    failed_pages: List[str]
    is_cancelled: bool = False

    def cancel(self):
        self.is_cancelled = True

class MultiTaskOrchestrator:
    """
    Orchestrates multi-page generation with real-time streaming.

    Responsibilities:
    - Manage build session state
    - Generate pages sequentially (home first, then others)
    - Emit events for each task
    - Handle cancellation
    - Retry failed tasks
    """

    def __init__(
        self,
        ai_service: AIService,
        validator: HTMLValidator,
        storage: "PageStorage"
    ):
        self.ai = ai_service
        self.validator = validator
        self.storage = storage
        self.emitter = BuildEventEmitter()

        # Active sessions
        self.sessions: dict[str, BuildSession] = {}

    async def start_build(
        self,
        project_id: str,
        user_id: str,
        pages: List[PageSpec],
        product_doc: "ProductDoc"
    ) -> str:
        """
        Start a new multi-page build.

        Args:
            project_id: Project identifier
            user_id: User identifier
            pages: List of PageSpecs to generate
            product_doc: Source of truth for content

        Returns:
            Build session ID
        """
        session_id = str(uuid.uuid4())
        session = BuildSession(
            id=session_id,
            project_id=project_id,
            user_id=user_id,
            pages=pages,
            completed_pages=[],
            failed_pages=[]
        )
        self.sessions[session_id] = session
        return session_id

    async def stream_progress(
        self,
        session_id: str,
        product_doc: "ProductDoc"
    ) -> AsyncGenerator[BuildEvent, None]:
        """
        Stream build progress events.

        Yields BuildEvents for:
        - task_started: When page generation begins
        - task_done: When page completes
        - task_failed: When page fails
        - card (page): When page is ready
        - preview_update: After each page save
        - build_complete: When all pages done
        """
        session = self.sessions.get(session_id)
        if not session:
            yield self.emitter.task_failed("unknown", "构建会话不存在")
            return

        try:
            # Find main page (generate first)
            main_page = next((p for p in session.pages if p.is_main), session.pages[0])
            other_pages = [p for p in session.pages if p.id != main_page.id]

            # Generate main page first
            async for event in self._generate_page(session, main_page, product_doc):
                yield event
                if session.is_cancelled:
                    yield self.emitter.task_failed(
                        f"page-{main_page.id}",
                        "构建已取消"
                    )
                    return

            # Generate other pages sequentially
            for page in other_pages:
                if session.is_cancelled:
                    yield self.emitter.task_failed(
                        f"page-{page.id}",
                        "构建已取消"
                    )
                    return

                async for event in self._generate_page(session, page, product_doc):
                    yield event

            # Build complete
            yield self.emitter.build_complete(
                f"所有 {len(session.pages)} 个页面已生成完成"
            )

        finally:
            # Cleanup session after completion
            if session_id in self.sessions:
                del self.sessions[session_id]

    async def _generate_page(
        self,
        session: BuildSession,
        page: PageSpec,
        product_doc: "ProductDoc"
    ) -> AsyncGenerator[BuildEvent, None]:
        """
        Generate a single page with task events.
        """
        task_id = f"page-{page.id}"

        # Emit task started
        yield self.emitter.task_started(task_id, f"生成 {page.name} 页面")

        try:
            # Build generation prompt
            prompt = self._build_page_prompt(page, product_doc, session)

            # Generate HTML
            html = await self.ai.generate_page_html(prompt)

            # Validate
            validation = self.validator.validate(html)

            if not validation.is_valid:
                yield BuildEvent(
                    type=BuildEventType.TASK_FAILED,
                    task_id=task_id,
                    title=f"{page.name} 验证失败",
                    card_type="validation",
                    card_data=validation.to_dict()
                )
                session.failed_pages.append(page.id)
                return

            # Save page
            await self.storage.save_page(
                project_id=session.project_id,
                page_id=page.id,
                path=page.path,
                html=html
            )

            # Update session
            session.completed_pages.append(page.id)

            # Emit success
            yield self.emitter.task_done(task_id, f"{page.name} 完成")

            # Emit page card
            yield self.emitter.page_card(page.id, page.name, page.path)

            # Emit preview update
            yield self.emitter.preview_update(page.id)

        except Exception as e:
            yield self.emitter.task_failed(
                task_id,
                f"{page.name} 生成失败: {str(e)}"
            )
            session.failed_pages.append(page.id)

    def _build_page_prompt(
        self,
        page: PageSpec,
        product_doc: "ProductDoc",
        session: BuildSession
    ) -> str:
        """Build AI prompt for page generation."""

        # Get relevant sections from ProductDoc
        sections = product_doc.content_structure.get("sections", [])
        page_sections = [s for s in sections if s["name"] in page.sections] or sections

        # Design requirements
        design = product_doc.design_requirements or {}

        # Previous pages context (for consistency)
        prev_pages = [
            p.name for p in session.pages
            if p.id in session.completed_pages
        ]

        return f"""
生成一个移动端优先的 HTML 页面。

## 页面信息
- 名称: {page.name}
- 路径: {page.path}
- 描述: {page.description}
- 是否首页: {page.is_main}

## 项目概述
{product_doc.overview}

## 本页内容区块
{self._format_sections(page_sections)}

## 设计要求
- 风格: {design.get('style', '简约现代')}
- 配色: {', '.join(design.get('colors', ['黑白为主']))}
- 字体: {design.get('typography', '无衬线体')}
- 氛围: {design.get('mood', '专业')}

## 已生成页面
{', '.join(prev_pages) if prev_pages else '这是第一个页面'}

## 技术要求
- 使用 Tailwind CSS（通过 CDN）
- 移动优先响应式设计
- 语义化 HTML
- 不使用外部图片（使用 placeholder 或 SVG）
- 导航包含所有页面链接

输出完整的 HTML 文档。
"""

    def _format_sections(self, sections: List[dict]) -> str:
        """Format sections for prompt."""
        return "\n".join([
            f"- {s['name']}: {s.get('description', '')} (优先级: {s.get('priority', 'medium')})"
            for s in sections
        ])

    async def cancel_build(self, session_id: str) -> bool:
        """Cancel an active build."""
        session = self.sessions.get(session_id)
        if session:
            session.cancel()
            return True
        return False

    async def retry_page(
        self,
        session_id: str,
        page_id: str,
        product_doc: "ProductDoc"
    ) -> AsyncGenerator[BuildEvent, None]:
        """Retry a failed page generation."""
        session = self.sessions.get(session_id)
        if not session:
            yield self.emitter.task_failed("retry", "构建会话不存在")
            return

        page = next((p for p in session.pages if p.id == page_id), None)
        if not page:
            yield self.emitter.task_failed("retry", "页面不存在")
            return

        # Remove from failed list
        if page_id in session.failed_pages:
            session.failed_pages.remove(page_id)

        # Regenerate
        async for event in self._generate_page(session, page, product_doc):
            yield event
```

**Acceptance Criteria**:
- [ ] Build sessions tracked properly
- [ ] Main page generated first
- [ ] Events emitted for all task states
- [ ] Cancellation stops generation
- [ ] Failed pages can be retried
- [ ] Session cleanup after completion

---

### Task 3.4: Integrate MultiPageDetector into Chat Flow

**Priority**: P0 (Critical)
**Files**: `backend/app/api/project_chat.py`

```python
# backend/app/api/project_chat.py (additions)

from app.services.build_runtime.planner import MultiPageDetector, MultiPageDecision

@router.post("/api/projects/{project_id}/chat")
async def project_chat(
    project_id: str,
    req: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    async def event_generator():
        # ... existing intent detection ...

        # After interview complete, check for multi-page
        if intent == "build" and product_doc:
            detector = MultiPageDetector()
            decision = await detector.detect(
                product_doc=product_doc,
                user_message=req.message,
                project_type=project.template_type
            )

            if decision.is_multi_page:
                # Get page specs
                page_specs = detector.get_page_specs(
                    decision=decision,
                    product_doc=product_doc,
                    project_type=project.template_type
                )

                # Emit BuildPlanCard
                yield {
                    "event": "card",
                    "data": json.dumps({
                        "type": "build_plan",
                        "data": {
                            "pages": [
                                {
                                    "id": p.id,
                                    "name": p.name,
                                    "path": p.path,
                                    "is_main": p.is_main
                                }
                                for p in page_specs
                            ],
                            "estimated_tasks": len(page_specs) * 3,  # ~3 tasks per page
                            "project_type": project.template_type,
                            "reason": decision.reason
                        }
                    })
                }

                # Wait for user approval (via separate endpoint)
                return

            # Single page - proceed immediately
            # ... existing single page flow ...
```

**Acceptance Criteria**:
- [ ] Multi-page detection runs after interview
- [ ] BuildPlanCard emitted when multi-page detected
- [ ] Single-page projects skip BuildPlanCard
- [ ] Decision reason included in card data

---

### Task 3.5: Create Build Approval Endpoint

**Priority**: P0 (Critical)
**Files**: `backend/app/api/build.py`

```python
# backend/app/api/build.py

from pydantic import BaseModel
from typing import List

class BuildStartRequest(BaseModel):
    pages: List[dict]  # [{id, name, path, is_main}]

@router.post("/api/projects/{project_id}/build/start")
async def start_build(
    project_id: str,
    req: BuildStartRequest,
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Start build after user approves BuildPlan.

    Returns build_id for streaming via chat endpoint.
    """
    # Verify project ownership
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get ProductDoc
    product_doc = db.query(ProductDoc).filter(
        ProductDoc.project_id == project_id
    ).first()
    if not product_doc:
        raise HTTPException(status_code=400, detail="ProductDoc required")

    # Convert to PageSpecs
    page_specs = [
        PageSpec(
            id=p["id"],
            name=p["name"],
            path=p["path"],
            description="",
            is_main=p.get("is_main", False),
            sections=[]
        )
        for p in req.pages
    ]

    # Start build
    orchestrator = MultiTaskOrchestrator(ai_service, validator, storage)
    build_id = await orchestrator.start_build(
        project_id=project_id,
        user_id=user_id,
        pages=page_specs,
        product_doc=product_doc
    )

    # Store orchestrator reference
    active_builds[build_id] = orchestrator

    return {"build_id": build_id, "pages": len(page_specs)}

@router.get("/api/build/{build_id}/stream")
async def stream_build(
    build_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Stream build progress as SSE.
    Used after build is started via /build/start.
    """
    orchestrator = active_builds.get(build_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="Build not found")

    # Get ProductDoc for the project
    session = orchestrator.sessions.get(build_id)
    if not session:
        raise HTTPException(status_code=404, detail="Build session not found")

    product_doc = db.query(ProductDoc).filter(
        ProductDoc.project_id == session.project_id
    ).first()

    async def event_generator():
        async for event in orchestrator.stream_progress(build_id, product_doc):
            yield {
                "event": event.type.value if hasattr(event.type, 'value') else 'task',
                "data": json.dumps(event.to_sse_event()["data"])
            }

    return EventSourceResponse(event_generator())
```

**Acceptance Criteria**:
- [ ] Build starts with user-approved pages
- [ ] Build ID returned for streaming
- [ ] ProductDoc loaded for generation
- [ ] SSE stream provides progress

---

### Task 3.6: Handle BuildPlanCard Actions in Frontend

**Priority**: P0 (Critical)
**Files**: `frontend/src/stores/buildStore.ts`

```typescript
// frontend/src/stores/buildStore.ts (additions)

interface BuildState {
  // ... existing state
  pendingBuildPlan: BuildPlanCardData | null;
}

interface BuildActions {
  // ... existing actions
  setPendingBuildPlan: (plan: BuildPlanCardData | null) => void;
  approveBuildPlan: (pages: BuildPlanPage[]) => Promise<void>;
}

export const useBuildStore = create<BuildState & BuildActions>((set, get) => ({
  // ... existing implementation

  pendingBuildPlan: null,

  setPendingBuildPlan: (plan) => {
    set({ pendingBuildPlan: plan });
  },

  approveBuildPlan: async (pages: BuildPlanPage[]) => {
    const { projectId } = get();
    if (!projectId) return;

    set({ pendingBuildPlan: null, isBuilding: true });

    try {
      // Start build
      const response = await fetch(`/api/projects/${projectId}/build/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pages })
      });

      if (!response.ok) {
        throw new Error('Failed to start build');
      }

      const { build_id } = await response.json();
      set({ buildId: build_id });

      // Connect to SSE stream
      const eventSource = new EventSource(`/api/build/${build_id}/stream`);

      eventSource.addEventListener('task', (e) => {
        get().handleTaskEvent(JSON.parse(e.data));
      });

      eventSource.addEventListener('card', (e) => {
        get().handleCardEvent(JSON.parse(e.data));
      });

      eventSource.addEventListener('preview_update', (e) => {
        get().handlePreviewUpdate(JSON.parse(e.data));
      });

      eventSource.onerror = () => {
        eventSource.close();
        set({ isBuilding: false });
      };

    } catch (error) {
      console.error('Build failed:', error);
      set({ isBuilding: false });
    }
  }
}));
```

**Acceptance Criteria**:
- [ ] Pending build plan stored when card received
- [ ] Approve triggers build start
- [ ] SSE connection established
- [ ] Events processed correctly
- [ ] Error handling for failed builds

---

### Task 3.7: Update ChatMessageList for BuildPlanCard

**Priority**: P1 (High)
**Files**: `frontend/src/components/chat/ChatMessageList.tsx`

```typescript
// frontend/src/components/chat/ChatMessageList.tsx (additions)

import { BuildPlanCard } from './cards/BuildPlanCard';
import { useBuildStore } from '@/stores/buildStore';

// In render:
if (task.card?.type === 'build_plan') {
  const { approveBuildPlan, setPendingBuildPlan } = useBuildStore();

  return (
    <BuildPlanCard
      key={task.id}
      plan={task.card.data as BuildPlanCardData}
      onApprove={(pages) => approveBuildPlan(pages)}
      onCancel={() => setPendingBuildPlan(null)}
    />
  );
}
```

**Acceptance Criteria**:
- [ ] BuildPlanCard renders in chat
- [ ] Approve triggers build
- [ ] Cancel dismisses card

---

## Technical Considerations

### Page Generation Order

**Decision**: Generate main page first, then others sequentially.

**Rationale**:
- Main page establishes design patterns
- Users see primary content immediately
- Subsequent pages can reference main page style

**Alternative considered**: Parallel generation
- Pro: Faster total time
- Con: Inconsistent styles, higher resource usage
- **Rejected** for v4, consider for v5 with style extraction

### Build Session Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                      Build Session States                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Created] ──approve──> [Running] ──complete──> [Done]          │
│      │                      │                                    │
│      │                      │                                    │
│   cancel                 cancel/                                 │
│      │                   error                                   │
│      ▼                      ▼                                    │
│  [Cancelled]          [Partial/Failed]                          │
│                             │                                    │
│                          retry                                   │
│                             │                                    │
│                             ▼                                    │
│                        [Running]                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Handling Edits During Build

If user edits BuildPlan while build is running:
- Option A: Ignore (currently running pages)
- Option B: Cancel and restart
- **Decision**: Disable edit after build starts (simplest)

---

## Acceptance Criteria

### Functional

- [ ] Multi-page projects detected correctly
- [ ] BuildPlanCard shows page list
- [ ] Pages can be added/removed/renamed
- [ ] Build proceeds with approved pages
- [ ] All pages generated successfully
- [ ] Preview updates after each page
- [ ] Build can be cancelled
- [ ] Failed pages show retry option

### Detection Accuracy

- [ ] > 85% correct detection of multi-page needs
- [ ] ProductDoc page_plan always respected
- [ ] Explicit requests always detected

### Performance

- [ ] Detection completes in < 500ms
- [ ] First page visible within 30s
- [ ] Full multi-page build < 2min (4 pages)

---

## Risk Factors

### Risk 1: Detection False Positives
- **Impact**: Medium - Unnecessary multi-page for simple projects
- **Mitigation**: Conservative detection thresholds
- **Mitigation**: User can edit to single page

### Risk 2: Page Inconsistency
- **Impact**: Medium - Pages look different
- **Mitigation**: Pass previous page context to AI
- **Mitigation**: Use shared design tokens

### Risk 3: Long Build Times
- **Impact**: Medium - User impatience
- **Mitigation**: Show progress (live tasks)
- **Mitigation**: Allow background builds (future)

---

## Estimated Scope

**Complexity**: Large

**Key Effort Drivers**:
- MultiPageDetector heuristics (25%)
- MultiTaskOrchestrator implementation (35%)
- BuildPlanCard UI (20%)
- Integration and testing (20%)

---

## Testing Checklist

- [ ] Unit: MultiPageDetector returns correct decisions
- [ ] Unit: PageSpec generation from various sources
- [ ] Unit: BuildPlanCard editing works
- [ ] Integration: Detection → Card → Approval → Build
- [ ] Integration: Cancel stops generation
- [ ] Integration: Retry regenerates failed page
- [ ] E2E: Complete multi-page build
- [ ] E2E: Edit plan then build

---

**Document Version**: 1.0
**Created**: 2026-01-27
**Status**: Ready for Implementation
