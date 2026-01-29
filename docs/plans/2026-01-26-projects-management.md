# Projects Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Add project management features including a Dashboard listing all projects, multi-page support within projects, project export/import, and a homepage with chat input that navigates to the editor.

**Architecture:**
- Frontend: React + Zustand stores for state management
- Backend: FastAPI endpoints for project CRUD, export/import
- Database: PostgreSQL for projects, snapshots, and project_pages table
- The homepage will have a chat input that creates/selects a project and navigates to the editor

**Tech Stack:**
- Frontend: Vite + React + TypeScript + Zustand + React Router
- Backend: FastAPI + SQLAlchemy + Pydantic
- Database: PostgreSQL with JSONB columns

---

## Plan Corrections (2026-01-26)

- **Async DB access:** Use `AsyncSession` + `await db.execute(...)` (the repo is async); avoid sync `Session`.
- **API paths:** Projects router is mounted at `/api`, so page/export/import routes must be `/projects/...`, not `/{project_id}...`.
- **Project CRUD source of truth:** Move list/get/update/delete to DB-backed queries (keep `_projects_storage` in sync only if needed for legacy modules like versions/submissions).
- **Migration chain:** The next migration should follow `20260126_0012`; use a new revision (e.g., `20260126_0013`) with a proper `down_revision`.
- **ORM defaults:** `ProjectPage.id` should default to `uuid4`; `updated_at` should `onupdate=datetime.utcnow`.
- **Layout integration:** `EditorLayout` already renders a global sidebar; add a `leftPanel` slot for the Pages list instead of nesting another full layout.
- **Preview source:** `PreviewPanel` should accept the current page and prefer `page.content.html` before `previewHtml`.

---

## Phases

### Phase 0: Project CRUD normalization (DB-backed)
### Phase 1: Project Pages Management
### Phase 2: Homepage with Chat Input
### Phase 3: Project Export/Import
### Phase 4: UI Integration

---

## Phase 0: Project CRUD normalization (DB-backed)

### Task 0: Move project CRUD to DB (keep legacy cache in sync)

**Files:**
- Modify: `backend/app/api/projects.py`

**Steps:**
1. Replace list/get/update/delete to query `projects` via `AsyncSession`.
2. Keep `_projects_storage` updates in `create_project`, `update_project`, and `delete_project` only if required by other modules (e.g., versions/submissions).
3. Ensure the API responses use DB fields (`template_inputs`, `notification_*`, `created_at`, `updated_at`) consistently.

---

## Phase 1: Project Pages Management

### Task 1: Create project_pages database table

**Files:**
- Create: `backend/app/models/db/project_page.py`
- Modify: `backend/app/models/db/__init__.py:20-25`
- Modify: `backend/alembic/versions/20260126_0013_add_project_pages_table.py`

**Step 1: Create Alembic migration**

Run:
```bash
cd backend && python -m alembic revision -m "add_project_pages_table"
```

**Step 2: Write migration**

```python
"""add_project_pages_table

Revision ID: 20260126_0013
Revises: 20260126_0012
Create Date: 2026-01-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic
revision = '20260126_0013'
down_revision = '20260126_0012'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'project_pages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=True),
        sa.Column('path', sa.String(255), nullable=False, default='/'),
        sa.Column('is_home', sa.Boolean(), default=False, nullable=False),
        sa.Column('content', JSONB, default={}, nullable=False),
        sa.Column('design_system', JSONB, default={}, nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_project_pages_project_id', 'project_pages', ['project_id'])
    op.create_index('ix_project_pages_path', 'project_pages', ['project_id', 'path'], unique=True)


def downgrade():
    op.drop_index('ix_project_pages_path', table_name='project_pages')
    op.drop_index('ix_project_pages_project_id', table_name='project_pages')
    op.drop_table('project_pages')
```

**Step 3: Create ProjectPage ORM model**

```python
# backend/app/models/db/project_page.py
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.db.base import Base


class ProjectPage(Base):
    __tablename__ = "project_pages"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False, default="/")
    is_home: Mapped[bool] = mapped_column(default=False, nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    design_system: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="pages")
```

**Step 4: Update Base imports**

Modify: `backend/app/models/db/__init__.py`

```python
from app.models.db.analytics import AnalyticsEvent
from app.models.db.asset import Asset
from app.models.db.audit_event import AuditEvent
from app.models.db.build_run import BuildRun
from app.models.db.credit import Credit
from app.models.db.custom_domain import CustomDomain
from app.models.db.experiment import Experiment
from app.models.db.interview_state import InterviewState
from app.models.db.project import Project
from app.models.db.project_page import ProjectPage  # ADD THIS
from app.models.db.snapshot import Snapshot
from app.models.db.subscription import Subscription
from app.models.db.user import User

__all__ = [
    "AnalyticsEvent",
    "Asset",
    "AuditEvent",
    "BuildRun",
    "Credit",
    "CustomDomain",
    "Experiment",
    "InterviewState",
    "Project",
    "ProjectPage",  # ADD THIS
    "Snapshot",
    "Subscription",
    "User",
]
```

**Step 5: Update Project model to include pages relationship**

Modify: `backend/app/models/db/project.py`

Add import:
```python
from app.models.db.project_page import ProjectPage
```

Add relationship after `published_snapshot_id`:
```python
pages: Mapped[list["ProjectPage"]] = relationship(
    back_populates="project", order_by="ProjectPage.sort_order"
)
```

**Step 6: Run migration**

Run:
```bash
cd backend && python -m alembic upgrade head
```

**Step 7: Commit**

```bash
git add backend/alembic/versions/20260126_0013_add_project_pages_table.py \
        backend/app/models/db/project_page.py \
        backend/app/models/db/__init__.py \
        backend/app/models/db/project.py
git commit -m "feat: add project_pages table for multi-page support"
```

---

### Task 2: Add pages API endpoints

**Files:**
- Modify: `backend/app/api/projects.py:1-300`

**Step 1: Add page-related schemas**

Add to the top of projects.py (after imports):

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


# Page schemas
class PageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(default="/", max_length=255)
    is_home: bool = False


class PageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    path: Optional[str] = Field(None, max_length=255)
    is_home: Optional[bool] = None
    sort_order: Optional[int] = None


class PageResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    slug: Optional[str]
    path: str
    is_home: bool
    content: dict
    design_system: dict
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Step 2: Add page endpoints**

Add before the `delete_project` endpoint:

```python
@router.get("/projects/{project_id}/pages", response_model=list[PageResponse])
async def list_project_pages(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pages in a project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    pages = db.query(ProjectPage).filter(
        ProjectPage.project_id == project_id
    ).order_by(ProjectPage.sort_order).all()

    return pages


@router.post("/projects/{project_id}/pages", response_model=PageResponse)
async def create_project_page(
    project_id: UUID,
    page_data: PageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new page in a project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # If this is the first page or marked as home, update other pages
    if page_data.is_home:
        db.query(ProjectPage).filter(
            ProjectPage.project_id == project_id
        ).update({"is_home": False})

    # If no home page exists, mark this as home
    existing_home = db.query(ProjectPage).filter(
        ProjectPage.project_id == project_id,
        ProjectPage.is_home == True,
    ).first()
    if not existing_home:
        page_data.is_home = True

    page = ProjectPage(
        project_id=project_id,
        name=page_data.name,
        path=page_data.path,
        is_home=page_data.is_home,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@router.patch("/projects/pages/{page_id}", response_model=PageResponse)
async def update_project_page(
    page_id: UUID,
    page_data: PageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a project page"""
    page = db.query(ProjectPage).join(Project).filter(
        ProjectPage.id == page_id,
        Project.user_id == current_user.id,
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if page_data.is_home == True:
        db.query(ProjectPage).filter(
            ProjectPage.project_id == page.project_id,
            ProjectPage.id != page_id,
        ).update({"is_home": False})

    if page_data.name is not None:
        page.name = page_data.name
    if page_data.path is not None:
        page.path = page_data.path
    if page_data.is_home is not None:
        page.is_home = page_data.is_home
    if page_data.sort_order is not None:
        page.sort_order = page_data.sort_order

    db.commit()
    db.refresh(page)
    return page


@router.delete("/projects/pages/{page_id}")
async def delete_project_page(
    page_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project page"""
    page = db.query(ProjectPage).join(Project).filter(
        ProjectPage.id == page_id,
        Project.user_id == current_user.id,
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Don't allow deleting the only page
    page_count = db.query(ProjectPage).filter(
        ProjectPage.project_id == page.project_id
    ).count()
    if page_count <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the only page in a project")

    db.delete(page)
    db.commit()
    return {"success": True}
```

**Step 3: Commit**

```bash
git add backend/app/api/projects.py
git commit -m "feat: add pages API endpoints for multi-page management"
```

---

### Task 3: Update frontend types for pages

**Files:**
- Modify: `frontend/src/types/project.ts`

**Step 1: Add Page type and update Project type**

```typescript
// Add Page interface
export interface ProjectPage {
  id: string;
  project_id: string;
  name: string;
  slug?: string;
  path: string;
  is_home: boolean;
  content: Record<string, unknown>;
  design_system: DesignSystem;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

// Update Project interface to include pages
export interface Project {
  id: string;
  user_id: string;
  public_id?: string;
  slug?: string;
  name: string;
  template_id?: string;
  template_inputs: Record<string, unknown>;
  status: 'draft' | 'published';
  current_draft_id?: string;
  published_snapshot_id?: string;
  notification_email?: string;
  notification_enabled: boolean;
  published_at?: string;
  created_at: string;
  updated_at: string;
  pages?: ProjectPage[];  // ADD THIS
}

// Add page-related types for API
export interface PageCreate {
  name: string;
  path?: string;
  is_home?: boolean;
}

export interface PageUpdate {
  name?: string;
  path?: string;
  is_home?: boolean;
  sort_order?: number;
}
```

**Step 2: Commit**

```bash
git add frontend/src/types/project.ts
git commit -m "feat: add Page type to frontend types"
```

---

### Task 4: Add pages to projectStore

**Files:**
- Modify: `frontend/src/stores/projectStore.ts`

**Step 1: Add page state and actions**

```typescript
interface ProjectState {
  // ... existing state ...

  // Pages state
  pages: ProjectPage[];
  currentPageId: string | null;

  // ... existing actions ...

  // Page actions
  setPages: (pages: ProjectPage[]) => void;
  setCurrentPage: (pageId: string) => void;
  addPage: (page: ProjectPage) => void;
  updatePage: (pageId: string, updates: Partial<ProjectPage>) => void;
  removePage: (pageId: string) => void;
  loadPages: (projectId: string) => Promise<void>;
  createPage: (projectId: string, data: PageCreate) => Promise<ProjectPage>;
  savePage: (pageId: string, data: PageUpdate) => Promise<void>;
  deletePage: (pageId: string) => Promise<void>;
}
```

**Step 2: Implement page actions**

Add to the store implementation:

```typescript
setPages: (pages) => set({ pages }),

setCurrentPage: (pageId) => {
  const { pages } = get();
  const page = pages.find((p) => p.id === pageId);
  if (page) {
    set({ currentPageId: pageId });
    // Also update design system from page
    if (page.design_system) {
      set({ designSystem: page.design_system as DesignSystem });
    }
  }
},

addPage: (page) => set((state) => ({
  pages: [...state.pages, page],
  currentPageId: page.id,
})),

updatePage: (pageId, updates) => set((state) => ({
  pages: state.pages.map((p) =>
    p.id === pageId ? { ...p, ...updates } as ProjectPage : p
  ),
})),

removePage: (pageId) => set((state) => ({
  pages: state.pages.filter((p) => p.id !== pageId),
  currentPageId: state.currentPageId === pageId
    ? state.pages.find((p) => p.id !== pageId)?.id || null
    : state.currentPageId,
})),

loadPages: async (projectId) => {
  const response = await fetch(`/api/projects/${projectId}/pages`);
  if (!response.ok) throw new Error('Failed to load pages');
  const pages = await response.json();
  set({ pages });
  // Set current page to home page or first page
  const homePage = pages.find((p: ProjectPage) => p.is_home) || pages[0];
  if (homePage) {
    set({ currentPageId: homePage.id });
    if (homePage.design_system) {
      set({ designSystem: homePage.design_system as DesignSystem });
    }
  }
},

createPage: async (projectId, data) => {
  const response = await fetch(`/api/projects/${projectId}/pages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create page');
  const page = await response.json();
  get().addPage(page);
  return page;
},

savePage: async (pageId, data) => {
  const { pages } = get();
  const page = pages.find((p) => p.id === pageId);
  if (!page) throw new Error('Page not found');

  const response = await fetch(`/api/projects/pages/${pageId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to save page');
  const updated = await response.json();
  get().updatePage(pageId, updated);
},

deletePage: async (pageId) => {
  const response = await fetch(`/api/projects/pages/${pageId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete page');
  get().removePage(pageId);
},
```

**Step 3: Commit**

```bash
git add frontend/src/stores/projectStore.ts
git commit -m "feat: add pages state and actions to projectStore"
```

---

## Phase 2: Homepage with Chat Input

### Task 5: Create Dashboard page

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/App.tsx:50-80`

**Step 1: Create DashboardPage component**

```typescript
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import type { Project } from '../types/project';

export function DashboardPage() {
  const navigate = useNavigate();
  const { projects, loadProjects, createProject } = useProjectStore();
  const [newProjectName, setNewProjectName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleCreateProject = async () => {
    if (!newProjectName.trim() || isCreating) return;

    setIsCreating(true);
    try {
      const project = await createProject(newProjectName.trim());
      navigate(`/editor/${project.id}`);
    } catch (error) {
      console.error('Failed to create project:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleEnterProject = (project: Project) => {
    navigate(`/editor/${project.id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Zaoya</h1>
          <button className="text-sm text-gray-600 hover:text-gray-900">
            Settings
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Quick Start Section */}
        <section className="mb-12">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Create a New Project
          </h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()}
              placeholder="Describe what you want to build..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isCreating}
            />
            <button
              onClick={handleCreateProject}
              disabled={!newProjectName.trim() || isCreating}
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isCreating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </section>

        {/* Projects Grid */}
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Your Projects ({projects.length})
          </h2>

          {projects.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No projects yet. Create your first one above!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => (
                <div
                  key={project.id}
                  onClick={() => handleEnterProject(project)}
                  className="bg-white p-6 rounded-lg border hover:shadow-md hover:border-blue-300 cursor-pointer transition-all"
                >
                  <h3 className="font-semibold text-gray-900 mb-2">
                    {project.name}
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        project.status === 'published'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {project.status}
                    </span>
                    <span>•</span>
                    <span>
                      {new Date(project.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
```

**Step 2: Update App.tsx routes**

Modify imports and add route:

```typescript
import { DashboardPage } from './pages/DashboardPage';

// In the router configuration:
<Route path="/" element={<DashboardPage />} />
<Route path="/editor/:projectId" element={<EditorPage />} />
```

**Step 3: Commit**

```bash
git add frontend/src/pages/DashboardPage.tsx
git add frontend/src/App.tsx
git commit -m "feat: add Dashboard page with project list and chat input"
```

---

### Task 6: Update EditorPage to load pages on mount

**Files:**
- Modify: `frontend/src/pages/EditorPage.tsx`

**Step 1: Add page loading to useEffect**

```typescript
useEffect(() => {
  if (!project) {
    void createProject('My Landing Page').then((newProject) => {
      if (newProject) {
        void loadPages(newProject.id);
      }
    });
  } else {
    void loadPages(project.id);
  }
}, [project, createProject, loadPages]);
```

**Step 2: Commit**

```bash
git add frontend/src/pages/EditorPage.tsx
git commit -m "feat: load pages when entering editor"
```

---

## Phase 3: Project Export/Import

### Task 7: Add project export API endpoint

**Files:**
- Modify: `backend/app/api/projects.py`
- Create: `backend/app/services/export_service.py`

**Step 1: Create export service**

```python
# backend/app/services/export_service.py
import json
from datetime import datetime
from typing import BinaryIO
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.db import Project, ProjectPage


def export_project_to_json(db: Session, project_id: UUID) -> dict:
    """Export project and all its pages to a JSON-compatible dict."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    pages = db.query(ProjectPage).filter(
        ProjectPage.project_id == project_id
    ).order_by(ProjectPage.sort_order).all()

    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "project": {
            "name": project.name,
            "template_id": project.template_id,
            "template_inputs": project.template_inputs,
            "notification_email": project.notification_email,
            "notification_enabled": project.notification_enabled,
        },
        "pages": [
            {
                "name": page.name,
                "slug": page.slug,
                "path": page.path,
                "is_home": page.is_home,
                "content": page.content,
                "design_system": page.design_system,
                "sort_order": page.sort_order,
            }
            for page in pages
        ],
    }

    return export_data


def export_project_to_file(db: Session, project_id: UUID) -> BinaryIO:
    """Export project to a file-like object with JSON content."""
    data = export_project_to_json(db, project_id)
    content = json.dumps(data, indent=2, ensure_ascii=False)
    from io import BytesIO
    return BytesIO(content.encode("utf-8"))
```

**Step 2: Add export endpoint to projects.py**

Add after the `delete_project` endpoint:

```python
@router.get("/projects/{project_id}/export")
async def export_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export project as JSON file"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.services.export_service import export_project_to_json

    export_data = export_project_to_json(db, project_id)

    from fastapi.responses import StreamingResponse
    import json
    from io import BytesIO

    content = json.dumps(export_data, indent=2, ensure_ascii=False)
    buffer = BytesIO(content.encode("utf-8"))

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="zaoya-project-{project_id}.json"'
        },
    )
```

**Step 3: Commit**

```bash
git add backend/app/services/export_service.py
git add backend/app/api/projects.py
git commit -m "feat: add project export API endpoint"
```

---

### Task 8: Add project import API endpoint

**Files:**
- Modify: `backend/app/api/projects.py`

**Step 1: Add import schema**

Add after `PageResponse`:

```python
class ProjectImportData(BaseModel):
    project: dict
    pages: list[dict]


class ProjectImportRequest(BaseModel):
    data: ProjectImportData
```

**Step 2: Add import endpoint**

Add after the export endpoint:

```python
@router.post("/projects/import")
async def import_project(
    request: ProjectImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import project from JSON data"""
    import_data = request.data

    # Create new project
    project = Project(
        user_id=current_user.id,
        name=import_data["project"].get("name", "Imported Project"),
        template_id=import_data["project"].get("template_id"),
        template_inputs=import_data["project"].get("template_inputs", {}),
        notification_email=import_data["project"].get("notification_email"),
        notification_enabled=import_data["project"].get("notification_enabled", False),
        status="draft",
    )
    db.add(project)
    db.flush()

    # Create pages
    for page_data in import_data.get("pages", []):
        page = ProjectPage(
            project_id=project.id,
            name=page_data.get("name", "Page"),
            slug=page_data.get("slug"),
            path=page_data.get("path", "/"),
            is_home=page_data.get("is_home", False),
            content=page_data.get("content", {}),
            design_system=page_data.get("design_system", {}),
            sort_order=page_data.get("sort_order", 0),
        )
        db.add(page)

    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "message": "Project imported successfully",
    }
```

**Step 3: Commit**

```bash
git add backend/app/api/projects.py
git commit -m "feat: add project import API endpoint"
```

---

### Task 9: Add frontend export/import UI

**Files:**
- Create: `frontend/src/components/project/ProjectActions.tsx`
- Modify: `frontend/src/pages/DashboardPage.tsx`

**Step 1: Create ProjectActions component**

```typescript
import { useState } from 'react';
import type { Project } from '../../types/project';

interface ProjectActionsProps {
  project: Project;
  onImport?: () => void;
}

export function ProjectActions({ project, onImport }: ProjectActionsProps) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const response = await fetch(`/api/projects/${project.id}/export`);
      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `zaoya-${project.name.replace(/\s+/g, '-')}-${project.id.slice(0, 8)}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex gap-2">
      <button
        onClick={handleExport}
        disabled={isExporting}
        className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
      >
        {isExporting ? 'Exporting...' : 'Export'}
      </button>
      {onImport && (
        <label className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">
          Import
          <input
            type="file"
            accept=".json"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                onImport();
              }
            }}
          />
        </label>
      )}
    </div>
  );
}
```

**Step 2: Update DashboardPage with export/import**

Add import and component to DashboardPage:

```typescript
import { ProjectActions } from '../components/project/ProjectActions';

// In the projects mapping section:
<div className="bg-white p-6 rounded-lg border hover:shadow-md hover:border-blue-300 cursor-pointer transition-all relative group">
  <div onClick={() => handleEnterProject(project)}>
    <h3 className="font-semibold text-gray-900 mb-2">
      {project.name}
    </h3>
    <div className="flex items-center gap-2 text-sm text-gray-500">
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
        project.status === 'published'
          ? 'bg-green-100 text-green-800'
          : 'bg-yellow-100 text-yellow-800'
      }`}>
        {project.status}
      </span>
      <span>•</span>
      <span>{new Date(project.updated_at).toLocaleDateString()}</span>
    </div>
  </div>
  <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
    <ProjectActions project={project} />
  </div>
</div>
```

**Step 3: Commit**

```bash
git add frontend/src/components/project/ProjectActions.tsx
git add frontend/src/pages/DashboardPage.tsx
git commit -m "feat: add export/import UI to Dashboard"
```

---

## Phase 4: UI Integration

### Task 10: Add page sidebar to EditorPage

**Files:**
- Modify: `frontend/src/pages/EditorPage.tsx`

**Step 1: Add page list sidebar**

```typescript
// In the return statement, add sidebar:
<div className="flex h-full">
  {/* Page Sidebar */}
  <aside className="w-48 bg-white border-r flex flex-col">
    <div className="p-3 border-b">
      <h2 className="font-semibold text-sm text-gray-700">Pages</h2>
    </div>
    <div className="flex-1 overflow-y-auto p-2">
      {pages.map((page) => (
        <button
          key={page.id}
          onClick={() => setCurrentPage(page.id)}
          className={`w-full text-left px-3 py-2 rounded text-sm mb-1 ${
            currentPageId === page.id
              ? 'bg-blue-100 text-blue-700'
              : 'hover:bg-gray-100'
          }`}
        >
          {page.is_home && <span className="mr-1">🏠</span>}
          {page.name}
        </button>
      ))}
    </div>
    <div className="p-2 border-t">
      <button
        onClick={() => {
          const name = prompt('Page name:');
          if (name) {
            const { project } = useProjectStore.getState();
            if (project) {
              void createPage(project.id, { name });
            }
          }
        }}
        className="w-full px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded"
      >
        + Add Page
      </button>
    </div>
  </aside>

  {/* Main Content - existing editor components */}
  <div className="flex-1 flex">
    {/* ChatPanel */}
    <ChatPanel />
    {/* PreviewPanel */}
    <PreviewPanel />
  </div>
</div>
```

**Step 2: Add pages state extraction**

```typescript
const { pages, currentPageId, setCurrentPage, createPage } = useProjectStore();
```

**Step 3: Commit**

```bash
git add frontend/src/pages/EditorPage.tsx
git commit -m "feat: add page sidebar to EditorPage"
```

---

### Task 11: Add project switcher to Header

**Files:**
- Modify: `frontend/src/components/layout/Header.tsx`

**Step 1: Add project dropdown**

```typescript
import { useProjectStore } from '../../stores/projectStore';
import { useNavigate, useParams } from 'react-router-dom';

// In the header component:
const { projects, project } = useProjectStore();
const navigate = useNavigate();
const params = useParams();

const [showProjectDropdown, setShowProjectDropdown] = useState(false);

const handleSwitchProject = (projectId: string) => {
  setShowProjectDropdown(false);
  navigate(`/editor/${projectId}`);
};

return (
  <header className="flex items-center justify-between px-4 py-2 bg-white border-b">
    {/* Left side */}
    <div className="flex items-center gap-4">
      <button
        onClick={() => navigate('/')}
        className="text-lg font-bold"
      >
        Zaoya
      </button>

      {/* Project Switcher */}
      <div className="relative">
        <button
          onClick={() => setShowProjectDropdown(!showProjectDropdown)}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 rounded hover:bg-gray-200"
        >
          <span>{project?.name || 'Select Project'}</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {showProjectDropdown && (
          <div className="absolute top-full left-0 mt-1 w-48 bg-white border rounded shadow-lg z-50">
            <div className="p-2 border-b">
              <button
                onClick={() => {
                  setShowProjectDropdown(false);
                  navigate('/');
                }}
                className="w-full text-left px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded"
              >
                + Create New Project
              </button>
            </div>
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => handleSwitchProject(p.id)}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 ${
                  p.id === params.projectId ? 'bg-blue-50' : ''
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>

    {/* Right side - existing elements */}
  </header>
);
```

**Step 2: Commit**

```bash
git add frontend/src/components/layout/Header.tsx
git commit -m "feat: add project switcher to Header"
```

---

## Summary

**Tasks completed:**

| # | Task | Status |
|---|------|--------|
| 0 | Move project CRUD to DB (keep legacy cache in sync) | ⬜ |
| 1 | Create project_pages table | ⬜ |
| 2 | Add pages API endpoints | ⬜ |
| 3 | Update frontend types | ⬜ |
| 4 | Add pages to projectStore | ⬜ |
| 5 | Create Dashboard page | ⬜ |
| 6 | Update EditorPage to load pages | ⬜ |
| 7 | Add project export API | ⬜ |
| 8 | Add project import API | ⬜ |
| 9 | Add export/import UI | ⬜ |
| 10 | Add page sidebar to EditorPage | ⬜ |
| 11 | Add project switcher to Header | ⬜ |

**Total: 12 tasks**

---

## Next Steps

After completing all tasks, run the following to verify:

```bash
# Backend
cd backend
python -m alembic upgrade head
pytest tests/ -v

# Frontend
cd frontend
npm run build
npm run preview
```

Check the browser at:
- `/` - Dashboard with project list
- `/editor/{projectId}` - Editor with page sidebar
