import { useEffect, useMemo, useState } from 'react'
import { Plus, Trash2, GripVertical, Edit2, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useBuildPlan } from '@/hooks/useBuildPlan'
import type { BuildPlanCardData, BuildPlanPage } from '@/types/chat'
import type { BuildPlan, BuildTask } from '@/types/buildPlan'

interface BuildPlanCardProps {
  plan: BuildPlanCardData
  onApprove?: (pages: BuildPlanPage[]) => void
  onCancel?: () => void
}

export function BuildPlanCard({ plan, onApprove, onCancel }: BuildPlanCardProps) {
  const isEditable = Boolean(onApprove && onCancel)
  const [isEditing, setIsEditing] = useState(false)
  const [editedPages, setEditedPages] = useState<BuildPlanPage[]>(plan.pages)
  const [editingPageId, setEditingPageId] = useState<string | null>(null)
  const livePlan = useBuildPlan(plan.build_id ?? null)
  const isRunning = Boolean(plan.build_id) && !plan.approval_required

  useEffect(() => {
    setEditedPages(plan.pages)
  }, [plan.pages])

  if (isRunning) {
    if (!livePlan) {
      return (
        <div className="border rounded-lg p-4 max-w-md bg-white shadow-sm">
          <h4 className="font-medium mb-2">📋 构建进度</h4>
          <div className="text-sm text-gray-500">加载构建计划中...</div>
        </div>
      )
    }

    return <RunningBuildPlanCard plan={livePlan} />
  }

  const designStyle =
    plan.design_system?.style ||
    plan.design_system?.theme ||
    plan.design_system?.name ||
    plan.estimated_complexity
  const colorPrimary =
    plan.design_system?.colors?.primary || plan.design_system?.color_palette?.[0]

  const estimatedTasksLabel = useMemo(() => {
    if (!plan.estimated_tasks) return null
    return `${plan.estimated_tasks} tasks`
  }, [plan.estimated_tasks])

  const handleAddPage = () => {
    const newPage: BuildPlanPage = {
      id: `page-${Date.now()}`,
      name: 'New Page',
      path: '/new-page',
      is_main: false,
    }
    setEditedPages((prev) => [...prev, newPage])
    setEditingPageId(newPage.id)
  }

  const handleRemovePage = (pageId: string) => {
    const page = editedPages.find((p) => p.id === pageId)
    if (page?.is_main) return
    setEditedPages(editedPages.filter((p) => p.id !== pageId))
  }

  const handleUpdatePage = (pageId: string, updates: Partial<BuildPlanPage>) => {
    setEditedPages((prev) =>
      prev.map((p) => (p.id === pageId ? { ...p, ...updates } : p))
    )
  }

  const handleSetAsMain = (pageId: string) => {
    setEditedPages((prev) =>
      prev.map((p) => {
        if (p.id === pageId) {
          return { ...p, is_main: true, path: '/' }
        }
        const normalizedPath = p.path === '/' ? `/${slugify(p.name)}` : p.path
        return { ...p, is_main: false, path: normalizedPath }
      })
    )
  }

  return (
    <div className="border rounded-lg p-4 max-w-md bg-white shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium flex items-center gap-2">
          📋 Build plan
        </h4>
        {isEditable && (
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="text-sm text-blue-500 hover:text-blue-700"
          >
            {isEditing ? 'Done' : 'Edit'}
          </button>
        )}
      </div>

      <div className="text-sm text-gray-600 mb-4">
        {editedPages.length} pages
        {estimatedTasksLabel && <span className="ml-2">• {estimatedTasksLabel}</span>}
        {plan.project_type && (
          <span className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded">
            {plan.project_type}
          </span>
        )}
      </div>

      {(designStyle || colorPrimary) && (
        <div className="mb-3 text-xs text-muted-foreground">
          {designStyle && <span className="mr-3">Style: {designStyle}</span>}
          {colorPrimary && <span>Primary: {colorPrimary}</span>}
        </div>
      )}

      {plan.reason && (
        <div className="mb-3 text-xs text-muted-foreground">
          Reason: {plan.reason}
        </div>
      )}

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

        {isEditing && (
          <button
            onClick={handleAddPage}
            className="flex items-center gap-2 text-sm text-blue-500 hover:text-blue-700 py-2"
          >
            <Plus className="w-4 h-4" />
            Add page
          </button>
        )}
      </div>

      {plan.tasks && plan.tasks.length > 0 && !isEditing && (
        <div className="mb-4">
          <div className="text-xs font-medium text-muted-foreground">Tasks</div>
          <ul className="mt-1 space-y-1 text-sm">
            {plan.tasks.map((task) => (
              <li key={task.id} className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-blue-400" />
                <span>{task.title}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {plan.features && plan.features.length > 0 && !isEditing && (
        <div className="mb-4">
          <div className="text-xs font-medium text-muted-foreground">Features</div>
          <div className="mt-1 flex flex-wrap gap-2">
            {plan.features.map((feature) => (
              <span
                key={feature}
                className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700"
              >
                {feature}
              </span>
            ))}
          </div>
        </div>
      )}

      {isEditable && (
        <div className="flex gap-2 pt-2 border-t">
          <button
            onClick={() => onApprove?.(editedPages)}
            className="flex-1 bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded font-medium"
          >
            Start build
          </button>
          <button
            onClick={() => onCancel?.()}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  )
}

function RunningBuildPlanCard({ plan }: { plan: BuildPlan }) {
  const finishedCount = plan.tasks.filter((task) =>
    ['done', 'failed', 'skipped'].includes(task.status)
  ).length
  const percent = plan.total_tasks
    ? Math.round((finishedCount / plan.total_tasks) * 100)
    : 0

  const projectTasks = plan.tasks.filter((task) => !task.page_id)

  return (
    <div className="border rounded-lg p-4 max-w-md bg-white shadow-sm">
      <h4 className="font-medium mb-2">📋 构建进度</h4>

      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>
            {plan.completed_tasks} / {plan.total_tasks} 任务完成
          </span>
          <span>{percent}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      <div className="space-y-3">
        {projectTasks.length > 0 && (
          <TaskGroup label="项目任务" tasks={projectTasks} />
        )}
        {plan.pages.map((page) => (
          <TaskGroup
            key={page.id}
            label={page.name}
            isMain={page.is_main}
            tasks={plan.tasks.filter((task) => task.page_id === page.id)}
          />
        ))}
      </div>

      {plan.failed_tasks > 0 && (
        <div className="mt-3 p-2 bg-red-50 rounded text-sm text-red-600">
          {plan.failed_tasks} 个任务失败
        </div>
      )}
    </div>
  )
}

function TaskGroup({
  label,
  isMain,
  tasks,
}: {
  label: string
  isMain?: boolean
  tasks: BuildTask[]
}) {
  const finishedCount = tasks.filter((task) =>
    ['done', 'failed', 'skipped'].includes(task.status)
  ).length

  return (
    <div
      className={cn(
        'p-2 rounded',
        isMain ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'
      )}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-sm">
          {label}
          {isMain && <span className="text-xs text-blue-600 ml-1">(首页)</span>}
        </span>
        <span className="text-xs text-gray-500">
          {finishedCount}/{tasks.length}
        </span>
      </div>
      <div className="flex flex-wrap gap-1">
        {tasks.map((task) => (
          <TaskDot key={task.id} status={task.status} title={task.name} />
        ))}
      </div>
    </div>
  )
}

function TaskDot({
  status,
  title,
}: {
  status: BuildTask['status']
  title: string
}) {
  const colors = {
    pending: 'bg-gray-300',
    running: 'bg-blue-500 animate-pulse',
    done: 'bg-green-500',
    failed: 'bg-red-500',
    skipped: 'bg-gray-400',
  }

  return (
    <div
      className={cn('w-2 h-2 rounded-full', colors[status])}
      title={`${title}: ${status}`}
    />
  )
}

interface PageItemProps {
  page: BuildPlanPage
  isEditing: boolean
  isEditingName: boolean
  onStartEdit: () => void
  onEndEdit: () => void
  onUpdate: (updates: Partial<BuildPlanPage>) => void
  onRemove: () => void
  onSetAsMain: () => void
}

function PageItem({
  page,
  isEditing,
  isEditingName,
  onStartEdit,
  onEndEdit,
  onUpdate,
  onRemove,
  onSetAsMain,
}: PageItemProps) {
  const [tempName, setTempName] = useState(page.name)

  useEffect(() => {
    setTempName(page.name)
  }, [page.name])

  const handleSaveName = () => {
    const newPath = page.is_main ? '/' : `/${slugify(tempName)}`
    onUpdate({ name: tempName, path: newPath })
    onEndEdit()
  }

  return (
    <div
      className={cn(
        'flex items-center gap-2 p-2 rounded',
        page.is_main ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'
      )}
    >
      {isEditing && <GripVertical className="w-4 h-4 text-gray-400 cursor-grab" />}

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
                Home
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

      {isEditing && !page.is_main && (
        <div className="flex items-center gap-1">
          <button
            onClick={onSetAsMain}
            className="text-xs text-blue-500 hover:text-blue-700 px-2 py-1"
          >
            Set as home
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
  )
}

function slugify(value: string) {
  const slug = value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return slug || 'page'
}
