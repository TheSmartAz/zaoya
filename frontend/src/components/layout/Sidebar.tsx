import { cn } from '@/lib/utils'
import { Home, Settings, History, Layers } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SidebarProps {
  className?: string
}

const sidebarItems = [
  { icon: Home, label: 'Home', href: '/' },
  { icon: Layers, label: 'Pages', href: '#pages' },
  { icon: History, label: 'History', href: '#history' },
  { icon: Settings, label: 'Settings', href: '#settings' },
]

export function Sidebar({ className }: SidebarProps) {
  return (
    <aside
      className={cn(
        'w-12 border-r bg-background flex flex-col items-center py-2 gap-1',
        className
      )}
    >
      {sidebarItems.map((item) => (
        <Button
          key={item.label}
          variant="ghost"
          size="icon"
          className="h-10 w-10"
          title={item.label}
        >
          <item.icon className="h-5 w-5" />
        </Button>
      ))}
    </aside>
  )
}
