interface PageCardProps {
  page: {
    id: string
    name: string
    path: string
  }
  onViewPreview: () => void
}

export function PageCard({ page, onViewPreview }: PageCardProps) {
  return (
    <div className="max-w-xs rounded-lg border bg-white p-3 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-lg">📄</span>
        <span className="font-medium">Page: {page.name}</span>
      </div>
      <code className="mb-2 block text-xs text-muted-foreground">{page.path}</code>
      <button
        onClick={onViewPreview}
        className="text-sm text-blue-500 hover:text-blue-700"
      >
        View preview
      </button>
    </div>
  )
}
