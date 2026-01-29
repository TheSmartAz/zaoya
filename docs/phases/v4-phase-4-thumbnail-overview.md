# v4 Phase 4: Thumbnail Overview (缩略图概览)

**Timeline**: Weeks 4-5
**Status**: Pending
**Dependencies**: Phase 3 (Multi-Page Detection) complete

---

## Phase Overview

This phase implements the full-screen multi-page overview with thumbnail grid. Users can see all pages at a glance, drag to reorder, and access page actions through hover menus. This provides intuitive page management for multi-page projects.

### Connection to Project Goals

- **Bird's-eye view**: Understand project structure at a glance
- **Direct manipulation**: Drag-to-reorder, inline actions
- **Mobile-first preview**: Thumbnails show mobile viewport (9:19.5 ratio)

---

## Prerequisites

### Technical Prerequisites
- [ ] Phase 3 complete (multi-page generation working)
- [ ] Pages stored with preview URLs
- [ ] Project state includes ordered page list
- [ ] Drag-and-drop library available (@dnd-kit or similar)

### Design Prerequisites
- [ ] Thumbnail dimensions finalized (160x347px)
- [ ] Hover action menu design approved
- [ ] Drag visual feedback defined

---

## Detailed Tasks

### Task 4.1: Define Thumbnail Specifications

**Priority**: P0 (Critical)
**Files**: `frontend/src/constants/preview.ts`

```typescript
// frontend/src/constants/preview.ts

export const THUMBNAIL = {
  // Size: 160 x 347 px (9:19.5 ratio, matching iPhone 14 Pro Max aspect)
  WIDTH: 160,
  HEIGHT: 347,
  ASPECT_RATIO: 9 / 19.5,

  // Grid layout
  GAP: 16,
  MIN_COLUMNS: 2,
  MAX_COLUMNS: 6,

  // Rendering
  SCALE: 0.2,  // Preview rendered at 5x size, scaled down
  VIEWPORT_WIDTH: 390,  // iPhone 14 viewport
  VIEWPORT_HEIGHT: 844,

  // Animation
  DRAG_OPACITY: 0.8,
  DROP_ANIMATION_MS: 200
} as const;

export const OVERVIEW = {
  HEADER_HEIGHT: 64,
  PADDING: 24,
  FOOTER_HEIGHT: 40
} as const;
```

**Acceptance Criteria**:
- [ ] Dimensions match spec (160x347)
- [ ] Aspect ratio correct (9:19.5)
- [ ] Constants exported and used consistently

---

### Task 4.2: Create PageThumbnail Component

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/preview/PageThumbnail.tsx`

```typescript
// frontend/src/components/preview/PageThumbnail.tsx

import { useState, useRef } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { cn } from '@/lib/utils';
import { MoreVertical } from 'lucide-react';
import { THUMBNAIL } from '@/constants/preview';

interface PageThumbnailProps {
  page: {
    id: string;
    name: string;
    path: string;
    thumbnailUrl?: string;
    is_main?: boolean;
  };
  onSelect: () => void;
  onRename: (newName: string) => void;
  onSetAsHome: () => void;
  onDelete: () => void;
  isDragging?: boolean;
}

export function PageThumbnail({
  page,
  onSelect,
  onRename,
  onSetAsHome,
  onDelete,
  isDragging = false
}: PageThumbnailProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [tempName, setTempName] = useState(page.name);
  const menuRef = useRef<HTMLDivElement>(null);

  // Sortable hook for drag-and-drop
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition
  } = useSortable({ id: page.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? THUMBNAIL.DRAG_OPACITY : 1
  };

  const handleRename = () => {
    if (tempName.trim() && tempName !== page.name) {
      onRename(tempName.trim());
    }
    setIsRenaming(false);
    setShowMenu(false);
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="relative group"
      {...attributes}
    >
      {/* Thumbnail Container */}
      <div
        className={cn(
          "relative rounded-lg overflow-hidden bg-gray-100 cursor-pointer",
          "border-2 transition-all",
          page.is_main ? "border-blue-400" : "border-transparent",
          "hover:border-gray-300 hover:shadow-md"
        )}
        style={{
          width: THUMBNAIL.WIDTH,
          height: THUMBNAIL.HEIGHT
        }}
        onClick={onSelect}
        {...listeners}
      >
        {/* Thumbnail Image */}
        {page.thumbnailUrl ? (
          <img
            src={page.thumbnailUrl}
            alt={page.name}
            className="w-full h-full object-cover object-top"
            draggable={false}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <PagePlaceholder />
          </div>
        )}

        {/* Main Page Badge */}
        {page.is_main && (
          <div className="absolute top-2 left-2 bg-blue-500 text-white text-xs px-2 py-0.5 rounded">
            首页
          </div>
        )}

        {/* Hover Overlay */}
        <div className={cn(
          "absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors",
          "flex items-center justify-center"
        )}>
          <span className={cn(
            "text-white text-sm font-medium px-3 py-1 rounded bg-black/50",
            "opacity-0 group-hover:opacity-100 transition-opacity"
          )}>
            点击预览
          </span>
        </div>

        {/* Menu Button (top-right) */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            setShowMenu(!showMenu);
          }}
          className={cn(
            "absolute top-2 right-2 p-1 rounded bg-white/80 hover:bg-white",
            "opacity-0 group-hover:opacity-100 transition-opacity",
            "shadow-sm"
          )}
        >
          <MoreVertical className="w-4 h-4 text-gray-600" />
        </button>
      </div>

      {/* Page Info */}
      <div className="mt-2 text-center">
        {isRenaming ? (
          <input
            type="text"
            value={tempName}
            onChange={(e) => setTempName(e.target.value)}
            onBlur={handleRename}
            onKeyDown={(e) => e.key === 'Enter' && handleRename()}
            className="text-sm font-medium text-center border-b border-blue-500 outline-none w-full"
            autoFocus
          />
        ) : (
          <div className="text-sm font-medium text-gray-800">{page.name}</div>
        )}
        <code className="text-xs text-gray-500">{page.path}</code>
      </div>

      {/* Actions Menu */}
      {showMenu && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />

          {/* Menu */}
          <div
            ref={menuRef}
            className="absolute top-10 right-0 z-20 bg-white rounded-lg shadow-lg border py-1 min-w-[120px]"
          >
            <MenuButton onClick={() => {
              setIsRenaming(true);
              setShowMenu(false);
            }}>
              重命名
            </MenuButton>

            {!page.is_main && (
              <MenuButton onClick={() => {
                onSetAsHome();
                setShowMenu(false);
              }}>
                设为首页
              </MenuButton>
            )}

            <div className="border-t my-1" />

            {!page.is_main && (
              <MenuButton
                onClick={() => {
                  onDelete();
                  setShowMenu(false);
                }}
                className="text-red-600 hover:bg-red-50"
              >
                删除
              </MenuButton>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function MenuButton({
  children,
  onClick,
  className
}: {
  children: React.ReactNode;
  onClick: () => void;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full px-4 py-2 text-left text-sm hover:bg-gray-50",
        className
      )}
    >
      {children}
    </button>
  );
}

function PagePlaceholder() {
  return (
    <svg
      className="w-12 h-12"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1"
    >
      <rect x="4" y="2" width="16" height="20" rx="2" />
      <line x1="8" y1="6" x2="16" y2="6" />
      <line x1="8" y1="10" x2="16" y2="10" />
      <line x1="8" y1="14" x2="12" y2="14" />
    </svg>
  );
}
```

**Acceptance Criteria**:
- [ ] Thumbnail renders at correct size
- [ ] Main page badge visible
- [ ] Hover shows overlay and menu button
- [ ] Menu opens with actions
- [ ] Rename works inline
- [ ] Drag attributes applied

---

### Task 4.3: Create MultiPageOverview Component

**Priority**: P0 (Critical)
**Files**: `frontend/src/components/preview/MultiPageOverview.tsx`

```typescript
// frontend/src/components/preview/MultiPageOverview.tsx

import { useState, useCallback } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragOverlay,
  DragStartEvent
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy
} from '@dnd-kit/sortable';
import { ArrowLeft } from 'lucide-react';
import { PageThumbnail } from './PageThumbnail';
import { THUMBNAIL, OVERVIEW } from '@/constants/preview';
import { cn } from '@/lib/utils';

interface PageInfo {
  id: string;
  name: string;
  path: string;
  thumbnailUrl?: string;
  is_main?: boolean;
}

interface MultiPageOverviewProps {
  pages: PageInfo[];
  onBack: () => void;
  onSelectPage: (pageId: string) => void;
  onReorder: (pageIds: string[]) => void;
  onRename: (pageId: string, newName: string) => void;
  onSetAsHome: (pageId: string) => void;
  onDelete: (pageId: string) => void;
}

export function MultiPageOverview({
  pages,
  onBack,
  onSelectPage,
  onReorder,
  onRename,
  onSetAsHome,
  onDelete
}: MultiPageOverviewProps) {
  const [activeId, setActiveId] = useState<string | null>(null);

  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8 // Prevent accidental drags
      }
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates
    })
  );

  // Handle drag start
  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  // Handle drag end
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = pages.findIndex((p) => p.id === active.id);
      const newIndex = pages.findIndex((p) => p.id === over.id);

      const newOrder = arrayMove(pages, oldIndex, newIndex);
      onReorder(newOrder.map((p) => p.id));
    }

    setActiveId(null);
  };

  // Get active page for drag overlay
  const activePage = activeId ? pages.find((p) => p.id === activeId) : null;

  return (
    <div className="fixed inset-0 bg-gray-50 z-50 flex flex-col">
      {/* Header */}
      <header
        className="flex items-center justify-between px-6 bg-white border-b"
        style={{ height: OVERVIEW.HEADER_HEIGHT }}
      >
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>返回编辑</span>
        </button>

        <span className="text-gray-500">
          多页面概览 ({pages.length} 个页面)
        </span>

        <div className="w-24" /> {/* Spacer for centering */}
      </header>

      {/* Thumbnail Grid */}
      <main
        className="flex-1 overflow-auto"
        style={{ padding: OVERVIEW.PADDING }}
      >
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={pages.map((p) => p.id)}
            strategy={rectSortingStrategy}
          >
            <div
              className="flex flex-wrap justify-center"
              style={{ gap: THUMBNAIL.GAP }}
            >
              {pages.map((page) => (
                <PageThumbnail
                  key={page.id}
                  page={page}
                  onSelect={() => onSelectPage(page.id)}
                  onRename={(name) => onRename(page.id, name)}
                  onSetAsHome={() => onSetAsHome(page.id)}
                  onDelete={() => onDelete(page.id)}
                  isDragging={activeId === page.id}
                />
              ))}
            </div>
          </SortableContext>

          {/* Drag Overlay */}
          <DragOverlay adjustScale={true}>
            {activePage && (
              <PageThumbnail
                page={activePage}
                onSelect={() => {}}
                onRename={() => {}}
                onSetAsHome={() => {}}
                onDelete={() => {}}
              />
            )}
          </DragOverlay>
        </DndContext>
      </main>

      {/* Footer */}
      <footer
        className="flex items-center justify-center text-sm text-gray-400 bg-white border-t"
        style={{ height: OVERVIEW.FOOTER_HEIGHT }}
      >
        拖拽调整顺序 • 悬停显示操作 • 点击预览
      </footer>
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Full-screen overlay
- [ ] Header with back button and count
- [ ] Grid of thumbnails
- [ ] Drag-and-drop reordering works
- [ ] Drag overlay shows page being dragged
- [ ] Footer with hints
- [ ] Scroll for many pages

---

### Task 4.4: Implement Thumbnail Generation

**Priority**: P0 (Critical)
**Files**: `backend/app/services/thumbnail_service.py`

```python
# backend/app/services/thumbnail_service.py

from typing import Optional
import asyncio
from playwright.async_api import async_playwright
import base64
from io import BytesIO
from PIL import Image

class ThumbnailService:
    """
    Generate page thumbnails using headless browser.

    Thumbnails are 160x347px (9:19.5 ratio) PNG images.
    """

    VIEWPORT_WIDTH = 390  # iPhone 14 width
    VIEWPORT_HEIGHT = 844  # iPhone 14 height
    THUMBNAIL_WIDTH = 160
    THUMBNAIL_HEIGHT = 347

    async def generate_thumbnail(
        self,
        html: str,
        page_id: str,
        project_id: str
    ) -> str:
        """
        Generate thumbnail from HTML content.

        Args:
            html: Full HTML document
            page_id: Page identifier
            project_id: Project identifier

        Returns:
            URL to stored thumbnail (or base64 data URL)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={
                    "width": self.VIEWPORT_WIDTH,
                    "height": self.VIEWPORT_HEIGHT
                },
                device_scale_factor=2  # Retina quality
            )

            # Load HTML
            await page.set_content(html, wait_until="networkidle")

            # Wait for fonts and images
            await page.wait_for_timeout(500)

            # Take screenshot
            screenshot = await page.screenshot(
                type="png",
                full_page=False  # Only viewport
            )

            await browser.close()

        # Resize to thumbnail
        thumbnail = self._resize_to_thumbnail(screenshot)

        # Store and return URL
        url = await self._store_thumbnail(thumbnail, page_id, project_id)

        return url

    def _resize_to_thumbnail(self, screenshot_bytes: bytes) -> bytes:
        """Resize screenshot to thumbnail dimensions."""
        img = Image.open(BytesIO(screenshot_bytes))

        # Resize maintaining aspect ratio
        img = img.resize(
            (self.THUMBNAIL_WIDTH * 2, self.THUMBNAIL_HEIGHT * 2),  # 2x for retina
            Image.Resampling.LANCZOS
        )

        # Convert back to bytes
        output = BytesIO()
        img.save(output, format='PNG', optimize=True)
        return output.getvalue()

    async def _store_thumbnail(
        self,
        thumbnail_bytes: bytes,
        page_id: str,
        project_id: str
    ) -> str:
        """
        Store thumbnail and return URL.

        For v4, use base64 data URL.
        Future: Upload to CDN/S3.
        """
        # Base64 encode for simplicity
        b64 = base64.b64encode(thumbnail_bytes).decode('utf-8')
        return f"data:image/png;base64,{b64}"

        # Future: Upload to storage
        # path = f"thumbnails/{project_id}/{page_id}.png"
        # await self.storage.upload(path, thumbnail_bytes)
        # return f"https://cdn.zaoya.app/{path}"


# Singleton instance
thumbnail_service = ThumbnailService()
```

**Acceptance Criteria**:
- [ ] Thumbnails generated at correct size
- [ ] Mobile viewport used (390px width)
- [ ] Retina quality (2x)
- [ ] PNG format optimized
- [ ] URL returned (base64 or CDN)

---

### Task 4.5: Integrate Thumbnail Generation into Build

**Priority**: P1 (High)
**Files**: `backend/app/services/build_runtime/multi_task_orchestrator.py`

```python
# backend/app/services/build_runtime/multi_task_orchestrator.py (additions)

from app.services.thumbnail_service import thumbnail_service

async def _generate_page(self, session, page, product_doc):
    # ... existing generation code ...

    # After saving HTML, generate thumbnail
    yield self.emitter.task_started(
        f"thumb-{page.id}",
        f"生成 {page.name} 缩略图"
    )

    try:
        thumbnail_url = await thumbnail_service.generate_thumbnail(
            html=html,
            page_id=page.id,
            project_id=session.project_id
        )

        # Update page with thumbnail URL
        await self.storage.update_page_thumbnail(
            project_id=session.project_id,
            page_id=page.id,
            thumbnail_url=thumbnail_url
        )

        yield self.emitter.task_done(
            f"thumb-{page.id}",
            f"{page.name} 缩略图完成"
        )

    except Exception as e:
        # Thumbnail failure is non-critical
        yield self.emitter.task_done(
            f"thumb-{page.id}",
            f"{page.name} 缩略图跳过"
        )

    # ... rest of existing code ...
```

**Acceptance Criteria**:
- [ ] Thumbnail generated after page save
- [ ] Task events emitted for thumbnail
- [ ] Failure doesn't block build
- [ ] Thumbnail URL stored with page

---

### Task 4.6: Add Page Reorder API

**Priority**: P1 (High)
**Files**: `backend/app/api/pages.py`

```python
# backend/app/api/pages.py

from pydantic import BaseModel
from typing import List

class ReorderPagesRequest(BaseModel):
    page_ids: List[str]

@router.patch("/api/projects/{project_id}/pages/reorder")
async def reorder_pages(
    project_id: str,
    req: ReorderPagesRequest,
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Reorder pages in a project.

    The page_ids list should contain all page IDs in the desired order.
    The first page becomes the main page.
    """
    # Verify ownership
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get all pages
    pages = db.query(Page).filter(Page.project_id == project_id).all()
    page_map = {p.id: p for p in pages}

    # Validate all IDs exist
    for page_id in req.page_ids:
        if page_id not in page_map:
            raise HTTPException(status_code=400, detail=f"Page {page_id} not found")

    # Update order and main status
    for i, page_id in enumerate(req.page_ids):
        page = page_map[page_id]
        page.order = i
        page.is_main = (i == 0)
        page.path = "/" if i == 0 else f"/{page.name.lower().replace(' ', '-')}"

    db.commit()

    return {"status": "reordered", "page_ids": req.page_ids}

@router.patch("/api/projects/{project_id}/pages/{page_id}")
async def update_page(
    project_id: str,
    page_id: str,
    req: PageUpdateRequest,
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update page details (name, etc.)."""
    # ... implementation ...
    pass

@router.delete("/api/projects/{project_id}/pages/{page_id}")
async def delete_page(
    project_id: str,
    page_id: str,
    user_id: str = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete a page (cannot delete main page)."""
    page = db.query(Page).filter(
        Page.id == page_id,
        Page.project_id == project_id
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if page.is_main:
        raise HTTPException(status_code=400, detail="Cannot delete main page")

    db.delete(page)
    db.commit()

    return {"status": "deleted", "page_id": page_id}
```

**Acceptance Criteria**:
- [ ] Reorder updates page order
- [ ] First page becomes main
- [ ] Paths updated automatically
- [ ] Delete works for non-main pages
- [ ] Main page protected from deletion

---

### Task 4.7: Connect Overview to projectStore

**Priority**: P1 (High)
**Files**: `frontend/src/stores/projectStore.ts`

```typescript
// frontend/src/stores/projectStore.ts (additions)

interface ProjectActions {
  // ... existing actions
  reorderPages: (pageIds: string[]) => Promise<void>;
  renamePage: (pageId: string, name: string) => Promise<void>;
  setAsHomePage: (pageId: string) => Promise<void>;
  deletePage: (pageId: string) => Promise<void>;
}

export const useProjectStore = create<ProjectState & ProjectActions>((set, get) => ({
  // ... existing implementation

  reorderPages: async (pageIds: string[]) => {
    const { projectId, pages } = get();
    if (!projectId) return;

    // Optimistic update
    const reorderedPages = pageIds.map((id, i) => {
      const page = pages.find(p => p.id === id)!;
      return {
        ...page,
        order: i,
        is_main: i === 0,
        path: i === 0 ? '/' : `/${page.name.toLowerCase().replace(/\s+/g, '-')}`
      };
    });
    set({ pages: reorderedPages });

    // API call
    try {
      await fetch(`/api/projects/${projectId}/pages/reorder`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ page_ids: pageIds })
      });
    } catch (error) {
      // Revert on failure
      set({ pages });
      console.error('Failed to reorder pages:', error);
    }
  },

  renamePage: async (pageId: string, name: string) => {
    const { projectId, pages } = get();
    if (!projectId) return;

    // Optimistic update
    const updatedPages = pages.map(p =>
      p.id === pageId
        ? {
            ...p,
            name,
            path: p.is_main ? '/' : `/${name.toLowerCase().replace(/\s+/g, '-')}`
          }
        : p
    );
    set({ pages: updatedPages });

    // API call
    await fetch(`/api/projects/${projectId}/pages/${pageId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
  },

  setAsHomePage: async (pageId: string) => {
    const { pages } = get();
    // Reorder with new home first
    const newOrder = [
      pageId,
      ...pages.filter(p => p.id !== pageId).map(p => p.id)
    ];
    await get().reorderPages(newOrder);
  },

  deletePage: async (pageId: string) => {
    const { projectId, pages, currentPageId, setCurrentPage } = get();
    if (!projectId) return;

    // Don't delete main page
    const page = pages.find(p => p.id === pageId);
    if (page?.is_main) return;

    // Optimistic update
    const updatedPages = pages.filter(p => p.id !== pageId);
    set({ pages: updatedPages });

    // If deleted page was current, switch to main
    if (currentPageId === pageId) {
      const mainPage = updatedPages.find(p => p.is_main);
      if (mainPage) setCurrentPage(mainPage.id);
    }

    // API call
    await fetch(`/api/projects/${projectId}/pages/${pageId}`, {
      method: 'DELETE'
    });
  }
}));
```

**Acceptance Criteria**:
- [ ] Reorder persists to backend
- [ ] Rename updates name and path
- [ ] Set as home reorders pages
- [ ] Delete removes page
- [ ] Optimistic updates for responsiveness
- [ ] Current page switches if deleted

---

### Task 4.8: Add DnD Kit Dependencies

**Priority**: P0 (Critical)
**Files**: `frontend/package.json`

```json
{
  "dependencies": {
    "@dnd-kit/core": "^6.1.0",
    "@dnd-kit/sortable": "^8.0.0",
    "@dnd-kit/utilities": "^3.2.2"
  }
}
```

```bash
# Installation command
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

**Acceptance Criteria**:
- [ ] DnD kit installed
- [ ] No version conflicts
- [ ] Types available

---

### Task 4.9: Integrate Overview into PreviewPanel

**Priority**: P1 (High)
**Files**: `frontend/src/components/preview/PreviewPanel.tsx`

```typescript
// frontend/src/components/preview/PreviewPanel.tsx (updates)

import { MultiPageOverview } from './MultiPageOverview';
import { useProjectStore } from '@/stores/projectStore';

export function PreviewPanel({ projectId }: PreviewPanelProps) {
  const [isOverviewOpen, setOverviewOpen] = useState(false);

  const {
    pages,
    currentPageId,
    setCurrentPage,
    reorderPages,
    renamePage,
    setAsHomePage,
    deletePage
  } = useProjectStore();

  // If overview is open, render full-screen
  if (isOverviewOpen) {
    return (
      <MultiPageOverview
        pages={pages}
        onBack={() => setOverviewOpen(false)}
        onSelectPage={(pageId) => {
          setCurrentPage(pageId);
          setOverviewOpen(false);
        }}
        onReorder={reorderPages}
        onRename={renamePage}
        onSetAsHome={setAsHomePage}
        onDelete={deletePage}
      />
    );
  }

  // Regular preview panel
  return (
    <div className="flex flex-col h-full">
      <PreviewToolbar
        // ... props
        onOpenOverview={() => setOverviewOpen(true)}
      />
      {/* ... rest of panel */}
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Overview button in toolbar works
- [ ] Full-screen overlay appears
- [ ] Back button returns to editor
- [ ] Selecting page closes overview and shows page

---

## Technical Considerations

### Thumbnail Caching

Consider caching strategies:
- **Browser**: Cache thumbnails aggressively (immutable after generation)
- **CDN**: Future - serve thumbnails from CDN
- **Regeneration**: Trigger on page edit

### DnD Performance

For many pages (>20):
- Use virtualization if needed
- Debounce reorder API calls
- Show loading state during drag

### Thumbnail Generation Timing

Options:
1. **Sync**: Generate during build (current approach)
2. **Async**: Generate in background after build
3. **On-demand**: Generate when overview opened

**Decision**: Sync during build (simplest, acceptable latency)

---

## Acceptance Criteria

### Functional

- [ ] Overview shows all pages as thumbnails
- [ ] Thumbnails correct size (160x347)
- [ ] Thumbnails show page preview
- [ ] Drag-to-reorder works
- [ ] Hover menu shows actions
- [ ] Rename, set as home, delete work
- [ ] Main page protected from deletion
- [ ] Back returns to editor
- [ ] Click opens page preview

### Visual

- [ ] Main page has badge
- [ ] Drag shows overlay
- [ ] Hover shows menu button
- [ ] Grid responsive to window size

### Performance

- [ ] Thumbnail generation < 2s per page
- [ ] Drag smooth (60fps)
- [ ] Overview opens < 500ms

---

## Risk Factors

### Risk 1: Playwright Dependency
- **Impact**: High - Server needs browser
- **Mitigation**: Use Playwright in worker process
- **Alternative**: Client-side screenshot (html2canvas)

### Risk 2: Thumbnail Size
- **Impact**: Low - Base64 images are large
- **Mitigation**: Optimize PNG compression
- **Future**: CDN storage

### Risk 3: DnD Complexity
- **Impact**: Medium - Edge cases in drag behavior
- **Mitigation**: Use well-tested library (@dnd-kit)
- **Mitigation**: Thorough testing

---

## Estimated Scope

**Complexity**: Medium-Large

**Key Effort Drivers**:
- DnD implementation (30%)
- Thumbnail generation service (25%)
- Overview UI components (25%)
- API and store integration (20%)

---

## Testing Checklist

- [ ] Unit: PageThumbnail renders correctly
- [ ] Unit: Menu actions work
- [ ] Integration: Drag-and-drop reorders
- [ ] Integration: Reorder persists to backend
- [ ] Integration: Thumbnail generated during build
- [ ] E2E: Open overview, drag pages, close
- [ ] E2E: Delete page from overview
- [ ] Performance: 10 pages renders smoothly

---

**Document Version**: 1.0
**Created**: 2026-01-27
**Status**: Ready for Implementation
