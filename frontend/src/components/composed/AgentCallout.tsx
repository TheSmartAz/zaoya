import { cn } from '@/lib/utils'
import { ClipboardList, Palette, Settings } from 'lucide-react'

type AgentType = 'requirements' | 'ux' | 'tech'

interface AgentCalloutProps {
  type: AgentType
  message: string
  className?: string
}

const agentConfig: Record<AgentType, { icon: typeof ClipboardList; label: string }> = {
  requirements: { icon: ClipboardList, label: 'RequirementsAgent' },
  ux: { icon: Palette, label: 'UXAgent' },
  tech: { icon: Settings, label: 'TechAgent' },
}

export function AgentCallout({ type, message, className }: AgentCalloutProps) {
  const config = agentConfig[type]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-muted text-muted-foreground text-xs animate-fade-in',
        className
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      <span className="font-medium">{config.label}:</span>
      <span>{message}</span>
    </div>
  )
}
