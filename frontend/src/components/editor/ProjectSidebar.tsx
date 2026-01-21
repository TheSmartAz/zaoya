import { useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { FileText, Plus, Settings, Palette, Trash2, GripVertical } from 'lucide-react';
import { useProjectStore } from '@/stores/projectStore';
import type { Page } from '@/types/page';

interface SortablePageProps {
  page: Page;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

function SortablePage({ page, isActive, onSelect, onDelete }: SortablePageProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: page.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors group ${
        isActive ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'
      }`}
    >
      <button
        {...attributes}
        {...listeners}
        className="p-1 hover:bg-gray-200 rounded"
        title="Drag to reorder"
      >
        <GripVertical size={16} />
      </button>
      <FileText size={16} />
      <span className="flex-1 truncate text-sm" onClick={onSelect}>
        {page.title}
      </span>
      {page.is_home && <span className="text-xs text-gray-500">Home</span>}
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        className="p-1 hover:bg-red-100 text-red-500 rounded opacity-0 group-hover:opacity-100"
        title="Delete page"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

interface ProjectSidebarProps {
  projectId: string;
  selectedPageId: string | null;
  onPageSelect: (pageId: string) => void;
  onAddPage: () => void;
  onOpenDesign: () => void;
  onOpenSettings: () => void;
}

export function ProjectSidebar({
  projectId,
  selectedPageId,
  onPageSelect,
  onAddPage,
  onOpenDesign,
  onOpenSettings,
}: ProjectSidebarProps) {
  const { pages, loadDraft, reorderPages, deletePage } = useProjectStore();

  useEffect(() => {
    loadDraft(projectId);
  }, [projectId, loadDraft]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = pages.findIndex((p) => p.id === active.id);
    const newIndex = pages.findIndex((p) => p.id === over.id);
    const newPageIds = arrayMove(pages, oldIndex, newIndex).map((p) => p.id);

    reorderPages(projectId, newPageIds);
  };

  const handleDeletePage = async (pageId: string) => {
    if (confirm('Are you sure you want to delete this page?')) {
      await deletePage(projectId, pageId);
    }
  };

  return (
    <div className="w-64 bg-white border-r flex flex-col h-full">
      {/* Project name header */}
      <div className="p-4 border-b">
        <h2 className="font-semibold truncate">My Project</h2>
      </div>

      {/* Pages list */}
      <div className="flex-1 overflow-y-auto p-2">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext items={pages.map((p) => p.id)} strategy={verticalListSortingStrategy}>
            {pages.map((page) => (
              <SortablePage
                key={page.id}
                page={page}
                isActive={selectedPageId === page.id}
                onSelect={() => onPageSelect(page.id)}
                onDelete={() => handleDeletePage(page.id)}
              />
            ))}
          </SortableContext>
        </DndContext>

        <button
          onClick={onAddPage}
          className="w-full mt-2 p-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-blue-400 hover:text-blue-500 transition-colors flex items-center justify-center gap-2 text-sm"
        >
          <Plus size={16} />
          Add Page
        </button>
      </div>

      {/* Bottom actions */}
      <div className="p-2 border-t">
        <button
          onClick={onOpenDesign}
          className="w-full p-2 text-left hover:bg-gray-100 rounded-lg flex items-center gap-2 text-sm"
        >
          <Palette size={16} />
          Design
        </button>
        <button
          onClick={onOpenSettings}
          className="w-full p-2 text-left hover:bg-gray-100 rounded-lg flex items-center gap-2 text-sm"
        >
          <Settings size={16} />
          Settings
        </button>
      </div>
    </div>
  );
}
