import { cn } from '@/lib/utils'

interface DeviceFrameProps {
  children: React.ReactNode
  className?: string
}

export function DeviceFrame({ children, className }: DeviceFrameProps) {
  return (
    <div
      className={cn(
        'relative bg-primary rounded-[40px] p-2 shadow-2xl',
        className
      )}
    >
      {/* Notch */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[120px] h-[24px] bg-primary rounded-b-2xl z-10" />

      {/* Screen */}
      <div className="relative w-[375px] h-[667px] bg-background rounded-[32px] overflow-hidden">
        {children}
      </div>
    </div>
  )
}
