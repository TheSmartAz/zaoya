import { cn } from '@/lib/utils'
import { Check, Loader2, RotateCw, X } from 'lucide-react'

interface TaskItemProps {
  title: string
  status: 'running' | 'done' | 'failed'
  onRetry?: () => void
}

export function TaskItem({ title, status, onRetry }: TaskItemProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-2 py-1 text-sm',
        status === 'failed' && 'text-red-600'
      )}
    >
      {status === 'running' && (
        <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
      )}
      {status === 'done' && <Check className="h-4 w-4 text-green-500" />}
      {status === 'failed' && <X className="h-4 w-4 text-red-500" />}

      <span className={cn(status === 'done' && 'text-muted-foreground')}>
        {status === 'running' ? `${title}...` : title}
      </span>

      {status === 'failed' && onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1 text-xs text-blue-500 hover:text-blue-700"
        >
          <RotateCw className="h-3 w-3" />
          Retry
        </button>
      )}
    </div>
  )
}

export function AgentThinkingItem({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 py-1 text-sm text-muted-foreground">
      <div className="flex h-4 w-4 items-center justify-center">
        <span className="text-base">🤖</span>
      </div>
      <span>{message}</span>
    </div>
  )
}
