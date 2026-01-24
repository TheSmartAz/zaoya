import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'

interface HeaderProps {
  projectName?: string
  className?: string
}

export function Header({ projectName = 'Untitled', className }: HeaderProps) {
  return (
    <header
      className={cn(
        'h-12 border-b bg-background flex items-center justify-between px-4',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <span className="font-semibold text-lg">Zaoya</span>
        <span className="text-muted-foreground">/</span>
        <span className="text-sm">{projectName}</span>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm">
          Preview
        </Button>
        <Button size="sm">Publish</Button>
      </div>
    </header>
  )
}
