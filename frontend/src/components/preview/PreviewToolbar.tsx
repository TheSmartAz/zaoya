import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

interface PreviewToolbarProps {
  currentView: 'preview' | 'productDoc' | 'code'
  previewMode: 'preview' | 'simulation'
  currentPage: { id: string; name: string; path: string } | null
  pages: { id: string; name: string; path: string }[]
  hasProductDoc: boolean
  canViewCode: boolean
  simulationAvailable: boolean
  versionLabel?: string
  onExitVersion?: () => void
  onViewChange: (view: 'preview' | 'productDoc' | 'code') => void
  onPreviewModeChange: (mode: 'preview' | 'simulation') => void
  onPageChange: (pageId: string) => void
  onOpenOverview: () => void
}

export function PreviewToolbar({
  currentView,
  previewMode,
  currentPage,
  pages,
  hasProductDoc,
  canViewCode,
  simulationAvailable,
  versionLabel,
  onExitVersion,
  onViewChange,
  onPreviewModeChange,
  onPageChange,
  onOpenOverview,
}: PreviewToolbarProps) {
  return (
    <div className="flex items-center justify-between border-b bg-white px-3 py-2">
      <div className="flex gap-1">
        <TabButton
          active={currentView === 'preview'}
          onClick={() => onViewChange('preview')}
        >
          Preview
        </TabButton>
        {hasProductDoc && (
          <TabButton
            active={currentView === 'productDoc'}
            onClick={() => onViewChange('productDoc')}
          >
            ProductDoc
          </TabButton>
        )}
        {canViewCode && (
          <TabButton active={currentView === 'code'} onClick={() => onViewChange('code')}>
            Code
          </TabButton>
        )}
      </div>

      <div className="flex items-center gap-2">
        {versionLabel && (
          <div className="flex items-center gap-2 rounded-full bg-orange-50 px-3 py-1 text-xs text-orange-700">
            <span>{versionLabel}</span>
            {onExitVersion && (
              <button
                onClick={onExitVersion}
                className="rounded-full bg-white px-2 py-0.5 text-xs font-medium text-orange-700 shadow"
              >
                Back to Draft
              </button>
            )}
          </div>
        )}
        {currentView === 'preview' && (
          <>
            <PreviewModeToggle
              mode={previewMode}
              simulationAvailable={simulationAvailable}
              onChange={onPreviewModeChange}
            />
            {previewMode === 'simulation' && (
              <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">
                Simulation
              </span>
            )}
            {pages.length > 0 && (
              <>
                <PageDropdown current={currentPage} pages={pages} onChange={onPageChange} />
                <button
                  onClick={onOpenOverview}
                  className="rounded p-2 text-gray-600 hover:bg-gray-100"
                  title="查看所有页面"
                >
                  <MoreIcon />
                </button>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'rounded px-3 py-1.5 text-sm transition-colors',
        active
          ? 'bg-gray-100 text-gray-900 font-medium'
          : 'text-gray-600 hover:bg-gray-50'
      )}
    >
      {children}
    </button>
  )
}

function PageDropdown({
  current,
  pages,
  onChange,
}: {
  current: { id: string; name: string; path: string } | null
  pages: { id: string; name: string; path: string }[]
  onChange: (pageId: string) => void
}) {
  const [open, setOpen] = useState(false)

  if (!current) return null

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded border px-3 py-1.5 hover:bg-gray-50"
      >
        <span className="text-sm font-medium text-gray-800">{current.name}</span>
        <ChevronDown className="h-4 w-4 text-gray-500" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-20 mt-1 min-w-[160px] rounded-lg border bg-white shadow-lg">
            {pages.map((page) => (
              <button
                key={page.id}
                onClick={() => {
                  onChange(page.id)
                  setOpen(false)
                }}
                className={cn(
                  'w-full px-4 py-2 text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg',
                  page.id === current.id && 'bg-gray-50'
                )}
              >
                <div className="text-sm font-medium text-gray-800">{page.name}</div>
                <code className="text-xs text-gray-500">{page.path}</code>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function PreviewModeToggle({
  mode,
  simulationAvailable,
  onChange,
}: {
  mode: 'preview' | 'simulation'
  simulationAvailable: boolean
  onChange: (mode: 'preview' | 'simulation') => void
}) {
  return (
    <div className="flex items-center rounded-full border bg-white p-0.5 text-xs">
      <button
        onClick={() => onChange('preview')}
        className={cn(
          'rounded-full px-3 py-1 text-xs transition-colors',
          mode === 'preview'
            ? 'bg-gray-900 text-white'
            : 'text-gray-600 hover:bg-gray-100'
        )}
      >
        Preview
      </button>
      <button
        onClick={() => onChange('simulation')}
        disabled={!simulationAvailable}
        title={
          simulationAvailable
            ? 'Publish simulation'
            : 'Publish simulation is available after the project is saved'
        }
        className={cn(
          'rounded-full px-3 py-1 text-xs transition-colors',
          mode === 'simulation'
            ? 'bg-gray-900 text-white'
            : 'text-gray-600 hover:bg-gray-100',
          !simulationAvailable && 'cursor-not-allowed opacity-50 hover:bg-transparent'
        )}
      >
        Publish Sim
      </button>
    </div>
  )
}

function MoreIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <circle cx="5" cy="12" r="1.5" fill="currentColor" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" />
      <circle cx="19" cy="12" r="1.5" fill="currentColor" />
    </svg>
  )
}
