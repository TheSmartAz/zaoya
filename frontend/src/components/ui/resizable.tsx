import { useRef, useState, useCallback, useEffect, ReactNode } from 'react'
import { cn } from '@/lib/utils'

type PanelElement = HTMLDivElement & {
  setPanelSize?: (size: number) => void
  minSize?: number
  maxSize?: number
}

interface ResizablePanelGroupProps {
  children: ReactNode
  className?: string
  orientation?: 'horizontal' | 'vertical'
  id?: string
}

export function ResizablePanelGroup({
  children,
  className,
  orientation = 'horizontal',
  id,
}: ResizablePanelGroupProps) {
  return (
    <div
      id={id}
      className={cn(
        'flex h-full w-full',
        orientation === 'vertical' ? 'flex-col' : '',
        className
      )}
      data-orientation={orientation}
    >
      {children}
    </div>
  )
}

interface ResizablePanelProps {
  children: ReactNode
  className?: string
  id?: string
  defaultSize?: number
  minSize?: number
  maxSize?: number
}

export function ResizablePanel({
  children,
  className,
  id,
  defaultSize = 50,
  minSize = 10,
  maxSize = 90,
}: ResizablePanelProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState(defaultSize)

  // Expose size and setter for parent to access
  useEffect(() => {
    if (panelRef.current) {
      const panel = panelRef.current as PanelElement
      panel.dataset.panelSize = String(size)
      panel.setPanelSize = setSize
      panel.minSize = minSize
      panel.maxSize = maxSize
    }
  }, [size, minSize, maxSize])

  return (
    <div
      ref={panelRef}
      id={id}
      className={cn('overflow-hidden', className)}
      style={{
        flex: `${size} 1 0%`,
        minWidth: `${minSize}%`,
        maxWidth: `${maxSize}%`,
      }}
      data-panel="true"
    >
      {children}
    </div>
  )
}

interface ResizableHandleProps {
  className?: string
  withHandle?: boolean
  panelIds?: [string, string] // [leftPanelId, rightPanelId]
  orientation?: 'horizontal' | 'vertical'
}

export function ResizableHandle({
  className,
  withHandle = false,
  panelIds,
  orientation = 'horizontal',
}: ResizableHandleProps) {
  const handleRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!panelIds || !panelIds[0] || !panelIds[1]) return

      const leftPanel = document.getElementById(panelIds[0]) as PanelElement | null
      const rightPanel = document.getElementById(panelIds[1]) as PanelElement | null
      const group = leftPanel?.parentElement

      if (!leftPanel || !rightPanel || !group) return

      const groupRect = group.getBoundingClientRect()
      const isHorizontal = orientation === 'horizontal'

      // Calculate new sizes
      let newSize: number
      if (isHorizontal) {
        const x = e.clientX - groupRect.left
        newSize = (x / groupRect.width) * 100
      } else {
        const y = e.clientY - groupRect.top
        newSize = (y / groupRect.height) * 100
      }

      // Get constraints from panels
      const leftMin = leftPanel.minSize ?? 10
      const leftMax = leftPanel.maxSize ?? 90
      const rightMin = rightPanel.minSize ?? 10
      const rightMax = rightPanel.maxSize ?? 90

      // Apply constraints
      const clampedSize = Math.max(leftMin, Math.min(leftMax, newSize))
      const clampedRightSize = 100 - clampedSize

      // Check if right panel constraints are satisfied
      if (clampedRightSize >= rightMin && clampedRightSize <= rightMax) {
        const leftSetter = leftPanel.setPanelSize
        const rightSetter = rightPanel.setPanelSize

        if (leftSetter) leftSetter(clampedSize)
        if (rightSetter) rightSetter(clampedRightSize)
      }
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, panelIds, orientation])

  return (
    <div
      ref={handleRef}
      className={cn(
        'relative flex shrink-0 bg-border',
        orientation === 'horizontal' ? 'w-px items-center justify-center' : 'h-px justify-center flex-row',
        isDragging && 'bg-primary',
        className
      )}
      onMouseDown={handleMouseDown}
      data-resizable-handle="true"
      style={{
        cursor: orientation === 'horizontal' ? 'col-resize' : 'row-resize',
        zIndex: isDragging ? 50 : 1,
      }}
    >
      {withHandle && (
        <div className={cn(
          'z-10 flex items-center justify-center rounded-sm border bg-border',
          orientation === 'horizontal' ? 'h-4 w-3' : 'h-3 w-4'
        )}>
          <svg className={cn('text-muted-foreground', orientation === 'horizontal' ? 'h-2.5 w-2.5' : 'h-2.5 w-2.5')} viewBox="0 0 15 15" fill="currentColor">
            <path d="M5 5h1v1H5V5zm4 0h1v1H9V5zM5 9h1v1H5V9zm4 0h1v1H9V9z" fillRule="evenodd" clipRule="evenodd" />
          </svg>
        </div>
      )}
    </div>
  )
}
