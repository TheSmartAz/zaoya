import { AlertTriangle, Clock, Loader2, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ThumbnailDisplayProps {
  imageUrl?: string | null
  status?: string | null
  error?: string | null
  onRetry?: () => void
  isRetrying?: boolean
}

export function ThumbnailDisplay({
  imageUrl,
  status,
  error,
  onRetry,
  isRetrying = false,
}: ThumbnailDisplayProps) {
  const normalized = status || (imageUrl ? 'done' : 'pending')
  const showImage = Boolean(imageUrl)

  return (
    <div className="relative w-full h-full">
      {showImage ? (
        <img
          src={imageUrl || undefined}
          alt="Page thumbnail"
          className="w-full h-full object-cover object-top"
          draggable={false}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center text-gray-400">
          <PlaceholderIcon />
        </div>
      )}

      {normalized === 'queued' || normalized === 'pending' ? (
        <StatusOverlay>
          <Clock className="w-5 h-5" />
          <span className="text-xs">等待生成</span>
        </StatusOverlay>
      ) : null}

      {normalized === 'running' ? (
        <StatusOverlay>
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-xs">生成中...</span>
        </StatusOverlay>
      ) : null}

      {normalized === 'failed' ? (
        <div className="absolute inset-0 bg-black/40 text-white flex flex-col items-center justify-center px-3 text-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          <div className="text-xs">
            {error ? error : '缩略图生成失败'}
          </div>
          {onRetry ? (
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation()
                onRetry()
              }}
              className={cn(
                'mt-1 inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs',
                'bg-white/90 text-gray-900 hover:bg-white'
              )}
              disabled={isRetrying}
            >
              <RefreshCw className={cn('w-3 h-3', isRetrying && 'animate-spin')} />
              {isRetrying ? '重试中' : '重试'}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

function StatusOverlay({ children }: { children: React.ReactNode }) {
  return (
    <div className="absolute inset-0 bg-black/30 text-white flex flex-col items-center justify-center gap-1">
      {children}
    </div>
  )
}

function PlaceholderIcon() {
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
  )
}
