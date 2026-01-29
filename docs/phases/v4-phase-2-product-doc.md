# v4 Phase 2: ProductDoc System

**Timeline**: Weeks 2-3
**Status**: Pending
**Dependencies**: Phase 1 (Live Task Feed) complete

---

## Phase Overview

ProductDoc is the **source of truth** for every project. This phase implements ProductDoc as a structured PRD that captures interview answers, content requirements, and design specifications. ProductDoc lives in the Preview Panel as a dedicated view, ensuring users always have access to project requirements.

### Connection to Project Goals

- **Source of Truth**: All build decisions reference ProductDoc
- **User Transparency**: Users understand what AI is building and why
- **Iteration Support**: Chat-based editing allows refinement without losing context

---

## Prerequisites

### Technical Prerequisites
- [ ] Phase 1 complete (Live Task Feed functional)
- [ ] Preview Panel infrastructure exists
- [ ] Interview system generates structured data
- [ ] Backend can persist document-level data

### Design Prerequisites
- [ ] ProductDoc markdown rendering style defined
- [ ] View switching UI pattern established

---

## Detailed Tasks

### Task 2.1: Define ProductDoc Data Model

**Priority**: P0 (Critical)
**Files**:
- `frontend/src/types/productDoc.ts`
- `backend/app/models/product_doc.py`

Frontend TypeScript types:

```typescript
// frontend/src/types/productDoc.ts

export interface ProductDoc {
  id: string;
  project_id: string;
  created_at: string;
  updated_at: string;

  // Required sections
  overview: string;
  target_users?: string[];

  // Content structure (flexible based on project complexity)
  content_structure: {
    sections: ContentSection[];
  };

  // Design requirements (if applicable)
  design_requirements?: {
    style?: string;
    colors?: string[];
    typography?: string;
    mood?: string;
  };

  // Page plan
  page_plan: {
    pages: PagePlanItem[];
  };

  // Technical constraints (if applicable)
  technical_constraints?: string[];

  // Raw interview data (for reference)
  interview_answers: InterviewAnswer[];

  // Generation metadata
  generation_count: number;
  last_generated_at?: string;
}

interface ContentSection {
  name: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  content_hints?: string[];
}

interface PagePlanItem {
  id: string;
  name: string;
  path: string;
  description: string;
  is_main: boolean;
  sections: string[]; // References to content_structure.sections
}

interface InterviewAnswer {
  question_id: string;
  question: string;
  answer: string;
  answered_at: string;
}
```

Backend SQLAlchemy model:

```python
# backend/app/models/product_doc.py

from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class ProductDoc(Base):
    __tablename__ = "product_docs"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Content stored as JSON
    overview = Column(String, nullable=False)
    target_users = Column(JSON, default=list)
    content_structure = Column(JSON, default=dict)
    design_requirements = Column(JSON, nullable=True)
    page_plan = Column(JSON, default=dict)
    technical_constraints = Column(JSON, nullable=True)
    interview_answers = Column(JSON, default=list)

    # Metadata
    generation_count = Column(Integer, default=0)
    last_generated_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="product_doc")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "overview": self.overview,
            "target_users": self.target_users,
            "content_structure": self.content_structure,
            "design_requirements": self.design_requirements,
            "page_plan": self.page_plan,
            "technical_constraints": self.technical_constraints,
            "interview_answers": self.interview_answers,
            "generation_count": self.generation_count,
            "last_generated_at": self.last_generated_at.isoformat() if self.last_generated_at else None
        }
```

**Acceptance Criteria**:
- [ ] TypeScript types match backend model
- [ ] JSON fields properly serialized
- [ ] Timestamps auto-update
- [ ] One-to-one relationship with Project

---

### Task 2.2: Create ProductDoc API Endpoints

**Priority**: P0 (Critical)
**Files**: `backend/app/api/product_doc.py`

```python
# backend/app/api/product_doc.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.auth import get_current_user
from app.models.product_doc import ProductDoc
from app.database import get_db

router = APIRouter()

class ProductDocResponse(BaseModel):
    id: str
    project_id: str
    overview: str
    target_users: List[str]
    content_structure: dict
    design_requirements: Optional[dict]
    page_plan: dict
    technical_constraints: Optional[List[str]]
    interview_answers: List[dict]
    generation_count: int
    created_at: str
    updated_at: str

class ProductDocUpdateRequest(BaseModel):
    overview: Optional[str] = None
    target_users: Optional[List[str]] = None
    content_structure: Optional[dict] = None
    design_requirements: Optional[dict] = None
    page_plan: Optional[dict] = None
    technical_constraints: Optional[List[str]] = None

@router.get("/api/projects/{project_id}/product-doc")
async def get_product_doc(
    project_id: str,
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
) -> ProductDocResponse:
    """
    Get project's ProductDoc.
    Returns 404 if no ProductDoc exists yet (interview not completed).
    """
    doc = db.query(ProductDoc).filter(
        ProductDoc.project_id == project_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="ProductDoc not found")

    # Verify project ownership
    project = db.query(Project).filter(Project.id == project_id).first()
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return ProductDocResponse(**doc.to_dict())

@router.patch("/api/projects/{project_id}/product-doc")
async def update_product_doc(
    project_id: str,
    req: ProductDocUpdateRequest,
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
) -> ProductDocResponse:
    """
    Update ProductDoc fields.
    Note: In practice, updates come via AI in chat, not direct API calls.
    This endpoint is for programmatic updates.
    """
    doc = db.query(ProductDoc).filter(
        ProductDoc.project_id == project_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="ProductDoc not found")

    # Verify ownership
    project = db.query(Project).filter(Project.id == project_id).first()
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Apply updates
    update_data = req.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    db.commit()
    db.refresh(doc)

    return ProductDocResponse(**doc.to_dict())

@router.post("/api/projects/{project_id}/product-doc/regenerate")
async def regenerate_from_interview(
    project_id: str,
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
) -> ProductDocResponse:
    """
    Regenerate ProductDoc from interview answers.
    Used when user wants to restart from interview data.
    """
    doc = db.query(ProductDoc).filter(
        ProductDoc.project_id == project_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="ProductDoc not found")

    # Regenerate using AI
    from app.services.ai_service import regenerate_product_doc
    updated_doc = await regenerate_product_doc(doc.interview_answers, project_id)

    # Update in DB
    doc.overview = updated_doc.overview
    doc.content_structure = updated_doc.content_structure
    doc.page_plan = updated_doc.page_plan
    doc.generation_count += 1
    doc.last_generated_at = datetime.utcnow()

    db.commit()
    db.refresh(doc)

    return ProductDocResponse(**doc.to_dict())
```

**Acceptance Criteria**:
- [ ] GET returns ProductDoc or 404
- [ ] PATCH updates specified fields only
- [ ] POST /regenerate rebuilds from interviews
- [ ] Authorization checks on all endpoints

---

### Task 2.3: Implement Interview → ProductDoc Generation

**Priority**: P0 (Critical)
**Files**: `backend/app/services/product_doc_service.py`

```python
# backend/app/services/product_doc_service.py

from typing import List
from app.services.ai_service import AIService
from app.models.product_doc import ProductDoc
import uuid
import json

class ProductDocService:
    """Generate and manage ProductDoc from interview answers."""

    def __init__(self, ai_service: AIService):
        self.ai = ai_service

    async def generate_from_interview(
        self,
        project_id: str,
        interview_answers: List[dict],
        project_type: str
    ) -> ProductDoc:
        """
        Generate ProductDoc from completed interview.

        Args:
            project_id: Project identifier
            interview_answers: List of {question, answer} dicts
            project_type: Template type (e.g., 'portfolio', 'landing')

        Returns:
            Populated ProductDoc instance
        """
        # Build prompt for AI
        prompt = self._build_generation_prompt(interview_answers, project_type)

        # Call AI to generate structured doc
        response = await self.ai.generate_structured(
            prompt=prompt,
            schema=PRODUCT_DOC_SCHEMA,
            model="glm-4"
        )

        # Parse response
        doc_data = json.loads(response)

        # Create ProductDoc
        return ProductDoc(
            id=str(uuid.uuid4()),
            project_id=project_id,
            overview=doc_data["overview"],
            target_users=doc_data.get("target_users", []),
            content_structure=doc_data["content_structure"],
            design_requirements=doc_data.get("design_requirements"),
            page_plan=doc_data["page_plan"],
            technical_constraints=doc_data.get("technical_constraints"),
            interview_answers=interview_answers,
            generation_count=1
        )

    def _build_generation_prompt(
        self,
        interview_answers: List[dict],
        project_type: str
    ) -> str:
        """Build AI prompt for ProductDoc generation."""

        answers_text = "\n".join([
            f"Q: {a['question']}\nA: {a['answer']}"
            for a in interview_answers
        ])

        return f"""
基于以下用户访谈回答，生成一个完整的产品需求文档 (ProductDoc)。

项目类型: {project_type}

访谈内容:
{answers_text}

请生成以下结构的JSON:
{{
    "overview": "项目简介（2-3句话）",
    "target_users": ["目标用户1", "目标用户2"],
    "content_structure": {{
        "sections": [
            {{
                "name": "区块名称",
                "description": "区块描述",
                "priority": "high/medium/low",
                "content_hints": ["内容提示1", "内容提示2"]
            }}
        ]
    }},
    "design_requirements": {{
        "style": "设计风格",
        "colors": ["主色", "辅色"],
        "typography": "字体风格",
        "mood": "整体氛围"
    }},
    "page_plan": {{
        "pages": [
            {{
                "name": "页面名称",
                "path": "/path",
                "description": "页面描述",
                "is_main": true/false,
                "sections": ["区块引用"]
            }}
        ]
    }},
    "technical_constraints": ["约束1", "约束2"]
}}

确保:
1. 内容基于用户回答，不要编造信息
2. 页面规划合理，首页标记为 is_main: true
3. 设计要求符合用户偏好
4. 区块优先级反映用户重点
"""

PRODUCT_DOC_SCHEMA = {
    "type": "object",
    "required": ["overview", "content_structure", "page_plan"],
    "properties": {
        "overview": {"type": "string"},
        "target_users": {"type": "array", "items": {"type": "string"}},
        "content_structure": {
            "type": "object",
            "properties": {
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "description", "priority"],
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "priority": {"enum": ["high", "medium", "low"]},
                            "content_hints": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            }
        },
        "design_requirements": {"type": "object"},
        "page_plan": {
            "type": "object",
            "properties": {
                "pages": {"type": "array"}
            }
        },
        "technical_constraints": {"type": "array", "items": {"type": "string"}}
    }
}
```

**Acceptance Criteria**:
- [ ] AI generates valid ProductDoc from interview
- [ ] JSON schema enforces required fields
- [ ] Content reflects interview answers (no hallucination)
- [ ] Page plan includes at least one main page

---

### Task 2.4: Create ProductDoc Preview View

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/preview/ProductDocView.tsx`

```typescript
// frontend/src/components/preview/ProductDocView.tsx

import { ProductDoc } from '@/types/productDoc';
import { cn } from '@/lib/utils';

interface ProductDocViewProps {
  doc: ProductDoc;
  className?: string;
}

export function ProductDocView({ doc, className }: ProductDocViewProps) {
  return (
    <div className={cn("h-full overflow-auto bg-gray-50 p-6", className)}>
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-sm p-6">
        {/* Header */}
        <h1 className="text-2xl font-bold mb-4">项目需求文档</h1>
        <p className="text-sm text-gray-500 mb-6">
          最后更新: {new Date(doc.updated_at).toLocaleString('zh-CN')}
        </p>

        {/* Overview */}
        <Section title="概述">
          <p className="text-gray-700">{doc.overview}</p>
        </Section>

        {/* Target Users */}
        {doc.target_users && doc.target_users.length > 0 && (
          <Section title="目标用户">
            <ul className="list-disc list-inside text-gray-700">
              {doc.target_users.map((user, i) => (
                <li key={i}>{user}</li>
              ))}
            </ul>
          </Section>
        )}

        {/* Content Structure */}
        <Section title="内容结构">
          <div className="space-y-3">
            {doc.content_structure.sections.map((section, i) => (
              <div key={i} className="border-l-2 border-blue-200 pl-3">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{section.name}</span>
                  <PriorityBadge priority={section.priority} />
                </div>
                <p className="text-sm text-gray-600">{section.description}</p>
                {section.content_hints && section.content_hints.length > 0 && (
                  <div className="text-xs text-gray-500 mt-1">
                    提示: {section.content_hints.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>

        {/* Design Requirements */}
        {doc.design_requirements && (
          <Section title="设计要求">
            <div className="grid grid-cols-2 gap-4 text-sm">
              {doc.design_requirements.style && (
                <div>
                  <span className="text-gray-500">风格:</span>{' '}
                  <span className="font-medium">{doc.design_requirements.style}</span>
                </div>
              )}
              {doc.design_requirements.typography && (
                <div>
                  <span className="text-gray-500">字体:</span>{' '}
                  <span className="font-medium">{doc.design_requirements.typography}</span>
                </div>
              )}
              {doc.design_requirements.mood && (
                <div>
                  <span className="text-gray-500">氛围:</span>{' '}
                  <span className="font-medium">{doc.design_requirements.mood}</span>
                </div>
              )}
              {doc.design_requirements.colors && (
                <div className="col-span-2">
                  <span className="text-gray-500">配色:</span>{' '}
                  <div className="inline-flex gap-1 ml-2">
                    {doc.design_requirements.colors.map((color, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-gray-100 rounded text-xs"
                      >
                        {color}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Section>
        )}

        {/* Page Plan */}
        <Section title="页面规划">
          <div className="space-y-2">
            {doc.page_plan.pages.map((page, i) => (
              <div
                key={i}
                className={cn(
                  "flex items-start gap-3 p-2 rounded",
                  page.is_main && "bg-blue-50"
                )}
              >
                <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">
                  {page.path}
                </code>
                <div className="flex-1">
                  <div className="font-medium">
                    {page.name}
                    {page.is_main && (
                      <span className="text-xs text-blue-600 ml-2">(首页)</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">{page.description}</p>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Technical Constraints */}
        {doc.technical_constraints && doc.technical_constraints.length > 0 && (
          <Section title="技术约束">
            <ul className="list-disc list-inside text-gray-700 text-sm">
              {doc.technical_constraints.map((constraint, i) => (
                <li key={i}>{constraint}</li>
              ))}
            </ul>
          </Section>
        )}

        {/* Edit hint */}
        <div className="mt-8 p-3 bg-gray-50 rounded text-sm text-gray-500 text-center">
          在聊天中说 "修改概述为..." 或 "添加新页面..." 来更新此文档
        </div>
      </div>
    </div>
  );
}

// Helper components
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <h2 className="text-lg font-semibold mb-2 text-gray-800">{title}</h2>
      {children}
    </div>
  );
}

function PriorityBadge({ priority }: { priority: 'high' | 'medium' | 'low' }) {
  const colors = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-green-100 text-green-700'
  };

  const labels = {
    high: '高',
    medium: '中',
    low: '低'
  };

  return (
    <span className={cn("text-xs px-1.5 py-0.5 rounded", colors[priority])}>
      {labels[priority]}
    </span>
  );
}
```

**Acceptance Criteria**:
- [ ] All ProductDoc sections render
- [ ] Priority badges show correct colors
- [ ] Main page highlighted
- [ ] Edit hint displayed at bottom
- [ ] Responsive layout within panel

---

### Task 2.5: Implement Preview Panel View Switching

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/preview/PreviewToolbar.tsx`

```typescript
// frontend/src/components/preview/PreviewToolbar.tsx

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';

interface PreviewToolbarProps {
  currentView: 'preview' | 'productDoc';
  currentPage: { id: string; name: string; path: string } | null;
  pages: { id: string; name: string; path: string }[];
  hasProductDoc: boolean;
  onViewChange: (view: 'preview' | 'productDoc') => void;
  onPageChange: (pageId: string) => void;
  onOpenOverview: () => void;
}

export function PreviewToolbar({
  currentView,
  currentPage,
  pages,
  hasProductDoc,
  onViewChange,
  onPageChange,
  onOpenOverview
}: PreviewToolbarProps) {
  return (
    <div className="flex items-center justify-between border-b bg-white px-3 py-2">
      {/* Left: View tabs */}
      <div className="flex gap-1">
        <TabButton
          active={currentView === 'preview'}
          onClick={() => onViewChange('preview')}
        >
          Preview
        </TabButton>
        {hasProductDoc && (
          <TabButton
            active={currentView === 'productDoc'}
            onClick={() => onViewChange('productDoc')}
          >
            ProductDoc
          </TabButton>
        )}
      </div>

      {/* Right: Page selector + overview button */}
      <div className="flex items-center gap-2">
        {currentView === 'preview' && pages.length > 0 && (
          <>
            <PageDropdown
              current={currentPage}
              pages={pages}
              onChange={onPageChange}
            />
            <button
              onClick={onOpenOverview}
              className="p-2 hover:bg-gray-100 rounded text-gray-600"
              title="查看所有页面"
            >
              <MoreIcon />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-3 py-1.5 text-sm rounded transition-colors",
        active
          ? "bg-gray-100 text-gray-900 font-medium"
          : "text-gray-600 hover:bg-gray-50"
      )}
    >
      {children}
    </button>
  );
}

function PageDropdown({
  current,
  pages,
  onChange
}: {
  current: { id: string; name: string; path: string } | null;
  pages: { id: string; name: string; path: string }[];
  onChange: (pageId: string) => void;
}) {
  const [open, setOpen] = useState(false);

  if (!current) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 border rounded hover:bg-gray-50"
      >
        <span className="text-sm font-medium">{current.name}</span>
        <ChevronDown className="w-4 h-4 text-gray-500" />
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute top-full right-0 mt-1 bg-white border rounded-lg shadow-lg z-20 min-w-[160px]">
            {pages.map((page) => (
              <button
                key={page.id}
                onClick={() => {
                  onChange(page.id);
                  setOpen(false);
                }}
                className={cn(
                  "w-full px-4 py-2 text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg",
                  page.id === current.id && "bg-gray-50"
                )}
              >
                <div className="font-medium text-sm">{page.name}</div>
                <code className="text-xs text-gray-500">{page.path}</code>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function MoreIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <circle cx="5" cy="12" r="1.5" fill="currentColor" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" />
      <circle cx="19" cy="12" r="1.5" fill="currentColor" />
    </svg>
  );
}
```

**Acceptance Criteria**:
- [ ] Tabs switch between Preview and ProductDoc
- [ ] ProductDoc tab only visible when doc exists
- [ ] Page dropdown shows all pages
- [ ] Current page highlighted in dropdown
- [ ] Overview button triggers full-screen view

---

### Task 2.6: Integrate ProductDoc into PreviewPanel

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/preview/PreviewPanel.tsx`

```typescript
// frontend/src/components/preview/PreviewPanel.tsx

import { useState, useEffect } from 'react';
import { PreviewToolbar } from './PreviewToolbar';
import { ProductDocView } from './ProductDocView';
import { PreviewIframe } from './PreviewIframe';
import { MultiPageOverview } from './MultiPageOverview';
import { useProjectStore } from '@/stores/projectStore';
import { useBuildStore } from '@/stores/buildStore';

interface PreviewPanelProps {
  projectId: string;
}

export function PreviewPanel({ projectId }: PreviewPanelProps) {
  const [view, setView] = useState<'preview' | 'productDoc'>('preview');
  const [isOverviewOpen, setOverviewOpen] = useState(false);

  const {
    pages,
    currentPageId,
    productDoc,
    setCurrentPage,
    loadProductDoc
  } = useProjectStore();

  const { liveTasks } = useBuildStore();

  // Load ProductDoc on mount
  useEffect(() => {
    loadProductDoc(projectId);
  }, [projectId, loadProductDoc]);

  // Listen for preview updates
  useEffect(() => {
    const handler = (e: CustomEvent) => {
      // Refresh iframe for updated page
      const pageId = e.detail.pageId;
      if (pageId === currentPageId) {
        // Force refresh
        setRefreshKey(prev => prev + 1);
      }
    };

    window.addEventListener('preview-update', handler as EventListener);
    return () => window.removeEventListener('preview-update', handler as EventListener);
  }, [currentPageId]);

  const [refreshKey, setRefreshKey] = useState(0);
  const currentPage = pages.find(p => p.id === currentPageId) || pages[0];

  // Full-screen overview
  if (isOverviewOpen) {
    return (
      <MultiPageOverview
        pages={pages}
        onBack={() => setOverviewOpen(false)}
        onSelectPage={(pageId) => {
          setCurrentPage(pageId);
          setOverviewOpen(false);
        }}
        // Other handlers for reorder, rename, etc.
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <PreviewToolbar
        currentView={view}
        currentPage={currentPage}
        pages={pages}
        hasProductDoc={!!productDoc}
        onViewChange={setView}
        onPageChange={setCurrentPage}
        onOpenOverview={() => setOverviewOpen(true)}
      />

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {view === 'productDoc' && productDoc ? (
          <ProductDocView doc={productDoc} />
        ) : (
          <PreviewIframe
            key={refreshKey}
            pageId={currentPageId}
            projectId={projectId}
          />
        )}
      </div>
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] View switches between preview and ProductDoc
- [ ] Preview refreshes on `preview-update` events
- [ ] Overview opens full-screen
- [ ] ProductDoc loads on mount
- [ ] Graceful fallback if no ProductDoc exists

---

### Task 2.7: Add ProductDoc to projectStore

**Priority**: P0 (Critical)
**Files**: `frontend/src/stores/projectStore.ts`

```typescript
// frontend/src/stores/projectStore.ts (additions)

interface ProjectState {
  // ... existing state
  productDoc: ProductDoc | null;
  isLoadingProductDoc: boolean;
}

interface ProjectActions {
  // ... existing actions
  loadProductDoc: (projectId: string) => Promise<void>;
  updateProductDoc: (updates: Partial<ProductDoc>) => void;
  clearProductDoc: () => void;
}

export const useProjectStore = create<ProjectState & ProjectActions>((set, get) => ({
  // ... existing implementation

  productDoc: null,
  isLoadingProductDoc: false,

  loadProductDoc: async (projectId: string) => {
    set({ isLoadingProductDoc: true });

    try {
      const response = await fetch(`/api/projects/${projectId}/product-doc`);

      if (response.ok) {
        const doc = await response.json();
        set({ productDoc: doc, isLoadingProductDoc: false });
      } else if (response.status === 404) {
        // No ProductDoc yet (interview not complete)
        set({ productDoc: null, isLoadingProductDoc: false });
      } else {
        throw new Error('Failed to load ProductDoc');
      }
    } catch (error) {
      console.error('Error loading ProductDoc:', error);
      set({ productDoc: null, isLoadingProductDoc: false });
    }
  },

  updateProductDoc: (updates: Partial<ProductDoc>) => {
    const { productDoc } = get();
    if (productDoc) {
      set({
        productDoc: {
          ...productDoc,
          ...updates,
          updated_at: new Date().toISOString()
        }
      });
    }
  },

  clearProductDoc: () => {
    set({ productDoc: null });
  }
}));
```

**Acceptance Criteria**:
- [ ] ProductDoc loaded from API
- [ ] Loading state tracked
- [ ] 404 handled (no doc yet)
- [ ] Updates merge correctly

---

### Task 2.8: Implement Chat-Based ProductDoc Editing

**Priority**: P1 (High)
**Files**: `backend/app/services/intent_detector.py`

Add intent detection for ProductDoc edit requests:

```python
# backend/app/services/intent_detector.py (additions)

class ProductDocEditIntent:
    """Detect and parse ProductDoc edit requests."""

    EDIT_PATTERNS = [
        r"修改.*(概述|overview).*为",
        r"更新.*(目标用户|target)",
        r"添加.*页面",
        r"删除.*页面",
        r"修改.*设计.*要求",
        r"更改.*风格",
        r"添加.*约束",
    ]

    FIELD_MAP = {
        "概述": "overview",
        "overview": "overview",
        "目标用户": "target_users",
        "target": "target_users",
        "风格": "design_requirements.style",
        "配色": "design_requirements.colors",
        "页面": "page_plan.pages",
    }

    def detect(self, message: str) -> Optional[dict]:
        """
        Detect if message is a ProductDoc edit request.

        Returns:
            {
                "type": "product_doc_edit",
                "field": "overview",
                "action": "update",
                "value": "new value"
            }
            or None if not an edit request
        """
        for pattern in self.EDIT_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return self._parse_edit_request(message)
        return None

    def _parse_edit_request(self, message: str) -> dict:
        """Parse edit details from message."""
        # Use AI to extract structured edit
        # ... implementation
        pass
```

**Acceptance Criteria**:
- [ ] Edit intents detected from chat
- [ ] Field mapping covers all ProductDoc fields
- [ ] AI extracts new values correctly
- [ ] Changes persist to database

---

### Task 2.9: Emit ProductDoc Card After Interview

**Priority**: P1 (High)
**Files**: `backend/app/services/interview_service.py`

After interview completes, emit ProductDoc created event:

```python
# backend/app/services/interview_service.py (additions)

async def complete_interview(
    self,
    project_id: str,
    answers: List[dict]
) -> AsyncGenerator[BuildEvent, None]:
    """
    Complete interview and generate ProductDoc.
    Emits events for streaming to frontend.
    """
    # Signal interview completion
    yield BuildEvent(
        type=BuildEventType.TASK_STARTED,
        task_id="interview-complete",
        title="正在生成项目需求文档..."
    )

    # Generate ProductDoc
    doc = await self.product_doc_service.generate_from_interview(
        project_id=project_id,
        interview_answers=answers,
        project_type=self.project_type
    )

    # Save to database
    db.add(doc)
    db.commit()

    # Signal completion
    yield BuildEvent(
        type=BuildEventType.TASK_DONE,
        task_id="interview-complete",
        title="项目需求文档已生成"
    )

    # Emit ProductDoc ready event (triggers view switch)
    yield BuildEvent(
        type=BuildEventType.CARD,
        card_type="product_doc_ready",
        card_data={"project_id": project_id}
    )
```

**Acceptance Criteria**:
- [ ] ProductDoc generated after interview
- [ ] Task events show progress
- [ ] Card event triggers UI update
- [ ] ProductDoc tab becomes visible

---

## Technical Considerations

### ProductDoc Versioning

Consider tracking ProductDoc versions:
- Store version history in separate table
- Allow "undo" via version restore
- Show version diff in UI (future feature)

### AI Prompt Quality

ProductDoc generation quality depends heavily on prompt engineering:
- Include examples of good ProductDocs
- Enforce JSON schema strictly
- Validate against interview content

### Edit Conflict Handling

When user edits via chat while build is running:
- Queue edits until build completes
- Or cancel build and apply edit
- Show warning if edit conflicts with in-progress work

---

## Acceptance Criteria

### Functional

- [ ] ProductDoc generated from interview answers
- [ ] ProductDoc displays in Preview Panel
- [ ] View switching works (Preview ↔ ProductDoc)
- [ ] ProductDoc tab appears after interview
- [ ] Chat-based editing updates ProductDoc
- [ ] Changes persist to database

### Data Integrity

- [ ] ProductDoc references interview answers
- [ ] Updates preserve non-modified fields
- [ ] Invalid edits rejected with feedback

### UX

- [ ] ProductDoc view is readable and well-structured
- [ ] Edit hint explains how to modify
- [ ] Loading states shown appropriately
- [ ] Errors displayed clearly

---

## Risk Factors

### Risk 1: AI Generation Quality
- **Impact**: High - Poor ProductDoc leads to poor builds
- **Mitigation**: Extensive prompt engineering
- **Mitigation**: Human review of generated docs
- **Mitigation**: Allow easy regeneration

### Risk 2: Edit Intent Misdetection
- **Impact**: Medium - User frustration when edits fail
- **Mitigation**: Confirmation before applying edits
- **Mitigation**: "Did you mean to edit X?" clarification

### Risk 3: Sync Between ProductDoc and Build
- **Impact**: Medium - Build ignores recent edits
- **Mitigation**: Check ProductDoc version before build
- **Mitigation**: Lock ProductDoc during build

---

## Estimated Scope

**Complexity**: Large

**Key Effort Drivers**:
- AI generation prompt engineering (35%)
- Frontend components and views (30%)
- API and data model (20%)
- Edit intent detection (15%)

---

## Testing Checklist

- [ ] Unit: ProductDoc model serialization
- [ ] Unit: ProductDocView renders all sections
- [ ] Unit: View switching works
- [ ] Integration: Interview → ProductDoc generation
- [ ] Integration: Chat edit → ProductDoc update
- [ ] E2E: Complete interview, view ProductDoc
- [ ] E2E: Edit ProductDoc via chat

---

**Document Version**: 1.0
**Created**: 2026-01-27
**Status**: Ready for Implementation
