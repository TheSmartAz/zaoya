import { cn } from '@/lib/utils'

interface DeviceFrameProps {
  children: React.ReactNode
  className?: string
}

// 19.5:9 aspect ratio (modern phone ratio like iPhone X/11/12/13 series)
// 19.5 / 9 ≈ 2.167
// Width: 360px, Height: 780px maintains 19.5:9 ratio
export function DeviceFrame({ children, className }: DeviceFrameProps) {
  return (
    <div
      className={cn(
        'relative bg-primary rounded-[44px] p-2.5 shadow-2xl',
        className
      )}
    >
      {/* Notch/Dynamic Island */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[100px] h-[28px] bg-primary rounded-b-3xl z-10" />

      {/* Screen - 19.5:9 aspect ratio (360x780) */}
      <div className="relative w-[360px] h-[780px] bg-background rounded-[36px] overflow-hidden">
        {children}
      </div>
    </div>
  )
}
