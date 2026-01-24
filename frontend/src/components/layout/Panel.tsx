import { cn } from '@/lib/utils'

interface PanelProps {
  children: React.ReactNode
  className?: string
}

export function Panel({ children, className }: PanelProps) {
  return (
    <div className={cn('flex flex-col h-full min-w-0 overflow-hidden', className)}>
      {children}
    </div>
  )
}

export function PanelHeader({ children, className }: PanelProps) {
  return (
    <div className={cn('flex items-center h-12 px-4 border-b shrink-0', className)}>
      {children}
    </div>
  )
}

export function PanelContent({ children, className }: PanelProps) {
  return (
    <div className={cn('flex-1 overflow-hidden', className)}>
      {children}
    </div>
  )
}
