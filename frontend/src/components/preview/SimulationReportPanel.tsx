import { useCallback, useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface SimulationReportEntry {
  received_at: string
  report: Record<string, unknown>
}

interface SimulationReport {
  project_id: string
  status: 'passed' | 'failed'
  csp_violations: SimulationReportEntry[]
  resource_errors: SimulationReportEntry[]
  runtime_errors: SimulationReportEntry[]
  count: number
  since_minutes: number
  timestamp: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const formatEntry = (entry: SimulationReportEntry) => {
  const report = entry.report || {}
  if (report['blocked-uri']) {
    return `Blocked ${report['blocked-uri']} (${report['violated-directive'] || 'CSP'})`
  }
  if (report['url']) {
    return `${report['tag'] || 'resource'} failed: ${report['url']}`
  }
  if (report['message']) {
    return String(report['message'])
  }
  return JSON.stringify(report).slice(0, 140)
}

export function SimulationReportPanel({
  projectId,
  active,
}: {
  projectId?: string
  active: boolean
}) {
  const [report, setReport] = useState<SimulationReport | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadReport = useCallback(async () => {
    if (!projectId) return
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(
        `${API_BASE_URL}/p-sim-report/${projectId}?since_minutes=30`
      )
      if (!response.ok) {
        throw new Error('Failed to load simulation report')
      }
      const data = (await response.json()) as SimulationReport
      setReport(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report')
      setReport(null)
    } finally {
      setIsLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    if (!active || !projectId) return
    void loadReport()
    const interval = window.setInterval(() => void loadReport(), 8000)
    return () => window.clearInterval(interval)
  }, [active, projectId, loadReport])

  if (!active) return null

  const status = report?.status || 'passed'
  const statusLabel = status === 'passed' ? 'Passed' : 'Issues found'
  const statusClass =
    status === 'passed' ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-800'

  return (
    <div className="border-b bg-white px-4 py-3 text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', statusClass)}>
            Simulation {statusLabel}
          </span>
          <span className="text-muted-foreground">
            {report?.count ?? 0} report(s) in last 30m
          </span>
        </div>
        <Button size="sm" variant="ghost" onClick={() => void loadReport()}>
          Refresh
        </Button>
      </div>

      {isLoading && <div className="mt-2 text-muted-foreground">Loading report...</div>}
      {error && <div className="mt-2 text-red-600">{error}</div>}

      {report && report.count > 0 && (
        <div className="mt-2 space-y-2">
          {report.csp_violations.length > 0 && (
            <ReportSection title="CSP violations" entries={report.csp_violations} />
          )}
          {report.resource_errors.length > 0 && (
            <ReportSection title="Resource errors" entries={report.resource_errors} />
          )}
          {report.runtime_errors.length > 0 && (
            <ReportSection title="Runtime errors" entries={report.runtime_errors} />
          )}
        </div>
      )}
    </div>
  )
}

function ReportSection({
  title,
  entries,
}: {
  title: string
  entries: SimulationReportEntry[]
}) {
  const sample = entries.slice(0, 3)
  return (
    <div>
      <div className="font-medium text-gray-700">
        {title} ({entries.length})
      </div>
      <ul className="mt-1 space-y-1 text-muted-foreground">
        {sample.map((entry, index) => (
          <li key={`${title}-${index}`}>{formatEntry(entry)}</li>
        ))}
        {entries.length > sample.length && (
          <li className="text-xs text-gray-400">+{entries.length - sample.length} more</li>
        )}
      </ul>
    </div>
  )
}
