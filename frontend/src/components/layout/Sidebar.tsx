import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Home, Settings, History, Layers } from 'lucide-react'
import { buttonVariants } from '@/components/ui/button'

interface SidebarProps {
  className?: string
}

const sidebarItems = [
  { icon: Home, label: 'Home', to: '/' },
  { icon: Layers, label: 'Pages', href: '#pages' },
  { icon: History, label: 'History', href: '#history' },
  { icon: Settings, label: 'Settings', to: '/settings' },
]

export function Sidebar({ className }: SidebarProps) {
  const itemClass = (isActive?: boolean) =>
    cn(
      buttonVariants({ variant: 'ghost', size: 'icon' }),
      'h-10 w-10',
      isActive && 'bg-accent text-accent-foreground'
    )

  return (
    <aside
      className={cn(
        'w-12 border-r bg-background flex flex-col items-center py-2 gap-1',
        className
      )}
    >
      {sidebarItems.map((item) => (
        item.to ? (
          <NavLink
            key={item.label}
            to={item.to}
            className={({ isActive }) => itemClass(isActive)}
            title={item.label}
            aria-label={item.label}
          >
            <item.icon className="h-5 w-5" />
          </NavLink>
        ) : item.href ? (
          <a
            key={item.label}
            href={item.href}
            className={itemClass(false)}
            title={item.label}
            aria-label={item.label}
          >
            <item.icon className="h-5 w-5" />
          </a>
        ) : (
          <button
            key={item.label}
            className={itemClass(false)}
            title={item.label}
            aria-label={item.label}
            type="button"
          >
            <item.icon className="h-5 w-5" />
          </button>
        )
      ))}
    </aside>
  )
}
