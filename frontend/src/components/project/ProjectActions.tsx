import { useState } from 'react'
import type { Project } from '@/types/project'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface ProjectActionsProps {
  project: Project
  onImportComplete?: () => void
}

export function ProjectActions({ project, onImportComplete }: ProjectActionsProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [importError, setImportError] = useState<string | null>(null)

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/${project.id}/export`)
      if (!response.ok) throw new Error('Export failed')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `zaoya-${project.name.replace(/\s+/g, '-')}-${project.id.slice(0, 8)}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsImporting(true)
    setImportError(null)

    try {
      const text = await file.text()
      const data = JSON.parse(text)

      const response = await fetch(`${API_BASE_URL}/api/projects/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data }),
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || 'Import failed')
      }

      onImportComplete?.()
    } catch (error) {
      console.error('Import failed:', error)
      setImportError(error instanceof Error ? error.message : 'Import failed')
    } finally {
      setIsImporting(false)
      event.target.value = ''
    }
  }

  return (
    <div className="flex gap-2 relative">
      <button
        onClick={handleExport}
        disabled={isExporting}
        className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
      >
        {isExporting ? 'Exporting...' : 'Export'}
      </button>
      <label className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 cursor-pointer">
        {isImporting ? 'Importing...' : 'Import'}
        <input
          type="file"
          accept=".json"
          className="hidden"
          onChange={handleImport}
          disabled={isImporting}
        />
      </label>
      {importError && (
        <div className="absolute top-full right-0 mt-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded whitespace-nowrap">
          {importError}
        </div>
      )}
    </div>
  )
}
