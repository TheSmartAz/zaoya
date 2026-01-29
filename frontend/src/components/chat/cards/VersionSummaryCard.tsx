import { Button } from '@/components/ui/button'
import type { VersionCardData } from '@/types/chat'

interface VersionSummaryCardProps {
  data: VersionCardData
  onViewPreview?: () => void
  onViewCode?: () => void
  onTogglePin?: () => void
  onCreateBranch?: () => void
}

export function VersionSummaryCard({
  data,
  onViewPreview,
  onViewCode,
  onTogglePin,
  onCreateBranch,
}: VersionSummaryCardProps) {
  const summary = data.change_summary
  const createdAt = new Date(data.created_at).toLocaleString()

  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-gray-900">Version snapshot</p>
          <p className="text-xs text-gray-500">{createdAt}</p>
          {summary.description && (
            <p className="mt-2 text-sm text-gray-700">{summary.description}</p>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onTogglePin}
          className={data.is_pinned ? 'text-orange-600' : 'text-gray-500'}
        >
          📌
        </Button>
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-xs text-gray-600">
        <span>{summary.files_changed} files</span>
        <span className="text-green-600">+{summary.lines_added}</span>
        <span className="text-red-500">-{summary.lines_deleted}</span>
        {data.branch_label && <span>{data.branch_label}</span>}
      </div>
      {summary.tasks_completed?.length ? (
        <div className="mt-2 text-xs text-gray-500">
          Tasks: {summary.tasks_completed.join(', ')}
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="outline" size="sm" onClick={onViewPreview}>
          查看预览
        </Button>
        <Button variant="outline" size="sm" onClick={onViewCode}>
          查看代码
        </Button>
        {onCreateBranch && (
          <Button variant="outline" size="sm" onClick={onCreateBranch}>
            创建分支
          </Button>
        )}
      </div>
    </div>
  )
}
