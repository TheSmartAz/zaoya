import { useState } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
} from '@dnd-kit/sortable'
import { ArrowLeft } from 'lucide-react'
import type { ProjectPage } from '@/types/project'
import { PageThumbnail } from './PageThumbnail'
import { THUMBNAIL, OVERVIEW } from '@/constants/preview'

interface MultiPageOverviewProps {
  pages: ProjectPage[]
  onBack: () => void
  onSelectPage: (pageId: string) => void
  onReorder: (pageIds: string[]) => void
  onRename: (pageId: string, newName: string) => void
  onSetAsHome: (pageId: string) => void
  onDelete: (pageId: string) => void
}

export function MultiPageOverview({
  pages,
  onBack,
  onSelectPage,
  onReorder,
  onRename,
  onSetAsHome,
  onDelete,
}: MultiPageOverviewProps) {
  const [activeId, setActiveId] = useState<string | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = pages.findIndex((page) => page.id === active.id)
      const newIndex = pages.findIndex((page) => page.id === over.id)

      if (oldIndex !== -1 && newIndex !== -1) {
        const newOrder = arrayMove(pages, oldIndex, newIndex)
        onReorder(newOrder.map((page) => page.id))
      }
    }

    setActiveId(null)
  }

  const handleDragCancel = () => {
    setActiveId(null)
  }

  const activePage = activeId ? pages.find((page) => page.id === activeId) : null

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
          type="button"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>返回编辑</span>
        </button>

        <span className="text-gray-500">多页面概览 ({pages.length} 个页面)</span>

        <div className="w-24" />
      </header>

      {/* Thumbnail Grid */}
      <main className="flex-1 overflow-auto" style={{ padding: OVERVIEW.PADDING }}>
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
          <SortableContext items={pages.map((page) => page.id)} strategy={rectSortingStrategy}>
            <div className="flex flex-wrap justify-center" style={{ gap: THUMBNAIL.GAP }}>
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

          <DragOverlay adjustScale>
            {activePage ? (
              <PageThumbnail
                page={activePage}
                onSelect={() => {}}
                onRename={() => {}}
                onSetAsHome={() => {}}
                onDelete={() => {}}
                sortable={false}
              />
            ) : null}
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
  )
}
