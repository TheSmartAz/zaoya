import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

interface PageLayoutProps {
  title: string
  description?: string
  className?: string
  children: ReactNode
  headerActions?: ReactNode
}

export function PageLayout({
  title,
  description,
  className,
  children,
  headerActions,
}: PageLayoutProps) {
  return (
    <div className={cn('h-screen flex flex-col', className)}>
      <Header projectName={title} showActions={false} actions={headerActions} />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <div className="flex-1 overflow-auto bg-muted/20">
          <main className="min-h-full">
            <div className="mx-auto flex w-full max-w-5xl flex-col px-6 py-6">
              <div className="mb-6">
                <h1 className="text-2xl font-semibold">{title}</h1>
                {description && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    {description}
                  </p>
                )}
              </div>
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
