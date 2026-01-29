import { cn } from '@/lib/utils'

interface QuickActionChipProps {
  label: string
  onClick: () => void
  active?: boolean
  className?: string
}

export function QuickActionChip({
  label,
  onClick,
  active,
  className,
}: QuickActionChipProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium border transition-colors',
        active
          ? 'bg-primary text-primary-foreground border-transparent'
          : 'bg-background text-foreground border-border hover:bg-muted hover:border-muted-foreground/30',
        className
      )}
    >
      {label}
    </button>
  )
}
