import type { ValidationErrorDetail } from '@/types/chat'

interface ValidationCardProps {
  errors: ValidationErrorDetail[]
  suggestions: string[]
  page_id?: string
  page_name?: string
  page_path?: string
  retry_count?: number
  onRetry?: () => void
}

const severityOrder: Array<'critical' | 'warning' | 'info'> = [
  'critical',
  'warning',
  'info',
]

const normalizeSeverity = (value?: string) => {
  if (value === 'warning' || value === 'info' || value === 'critical') return value
  return 'critical'
}

const slugify = (value: string) =>
  value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'page'

export function ValidationCard({
  errors,
  suggestions,
  page_name,
  page_path,
  retry_count,
  onRetry,
}: ValidationCardProps) {
  const normalizedErrors = errors.map((err) => {
    const severity = normalizeSeverity(err.severity)
    const fallbackPath = err.path
      ? err.path
      : page_path
        ? `pages/${page_path === '/' ? 'home' : page_path.replace(/^\//, '')}.html`
        : page_name
          ? `pages/${slugify(page_name)}.html`
          : undefined
    return {
      ...err,
      severity,
      path: err.path || fallbackPath,
    }
  })

  const grouped = normalizedErrors.reduce(
    (acc, err) => {
      acc[err.severity as 'critical' | 'warning' | 'info'].push(err)
      return acc
    },
    { critical: [] as ValidationErrorDetail[], warning: [], info: [] }
  )

  const handleViewCode = (err: ValidationErrorDetail) => {
    if (!err.path) return
    window.dispatchEvent(
      new CustomEvent('open-code-view', {
        detail: { path: err.path, line: err.line },
      })
    )
  }

  const handleFixPage = (err: ValidationErrorDetail) => {
    const label = err.path || page_name || page_path || 'this page'
    const fixLine = err.suggestedFix ? `Suggested fix: ${err.suggestedFix}` : ''
    const message = [
      `Fix validation errors on ${label}:`,
      `- ${err.message}`,
      fixLine,
    ]
      .filter(Boolean)
      .join('\n')
    window.dispatchEvent(
      new CustomEvent('chat-input', {
        detail: { message, autoSend: true },
      })
    )
  }

  const handleRollback = () => {
    window.dispatchEvent(new CustomEvent('open-version-history'))
  }

  return (
    <div className="max-w-md rounded-lg border border-red-200 bg-red-50 p-3">
      <div className="mb-2 flex items-center gap-2 text-red-700">
        <span className="text-lg">⚠️</span>
        <span className="font-medium">Validation failed</span>
        {typeof retry_count === 'number' && retry_count > 0 && (
          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">
            Retry {retry_count}
          </span>
        )}
      </div>

      <div className="mb-3 space-y-3">
        {severityOrder.map((severity) =>
          grouped[severity].length ? (
            <div key={severity} className="space-y-2">
              <div className="text-xs font-semibold uppercase text-red-600">
                {severity} ({grouped[severity].length})
              </div>
              {grouped[severity].map((err, index) => (
                <div key={`${severity}-${index}`} className="rounded border border-red-100 bg-white p-2">
                  <div className="text-sm text-red-700">{err.message}</div>
                  {(err.path || err.line) && (
                    <div className="mt-1 text-xs text-muted-foreground">
                      {err.path}
                      {err.line ? `:L${err.line}` : ''}
                    </div>
                  )}
                  {err.excerpt && (
                    <pre className="mt-2 max-h-24 overflow-auto rounded bg-red-50 p-2 text-[11px] text-red-800">
                      {err.excerpt}
                    </pre>
                  )}
                  {err.suggestedFix && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      {err.suggestedFix}
                    </div>
                  )}
                  <div className="mt-2 flex flex-wrap gap-2">
                    {err.path && (
                      <button
                        onClick={() => handleViewCode(err)}
                        className="rounded bg-white px-2 py-1 text-xs text-red-700 shadow hover:bg-red-100"
                      >
                        View Code
                      </button>
                    )}
                    <button
                      onClick={() => handleFixPage(err)}
                      className="rounded bg-white px-2 py-1 text-xs text-red-700 shadow hover:bg-red-100"
                    >
                      Fix This Page
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : null
        )}
      </div>

      {suggestions.length > 0 && (
        <div className="mb-3 text-sm text-muted-foreground">
          <div className="font-medium">Suggestions:</div>
          <ul className="list-inside list-disc">
            {suggestions.map((suggestion, index) => (
              <li key={index}>{suggestion}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700"
          >
            Retry
          </button>
        )}
        <button
          onClick={handleRollback}
          className="rounded border border-red-200 px-3 py-1 text-sm text-red-700 hover:bg-red-100"
        >
          Rollback Page
        </button>
      </div>
    </div>
  )
}
