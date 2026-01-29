import { useEffect, useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useProjectStore, useVersionStore } from '@/stores'
import type { VersionPage, VersionSummary } from '@/types/version'

interface VersionHistoryPanelProps {
  onCollapse?: () => void
  onShowBuild?: () => void
}

export function VersionHistoryPanel({ onCollapse, onShowBuild }: VersionHistoryPanelProps) {
  const project = useProjectStore((state) => state.project)
  const loadPages = useProjectStore((state) => state.loadPages)
  const versions = useVersionStore((state) => state.versions)
  const branches = useVersionStore((state) => state.branches)
  const activeBranchId = useVersionStore((state) => state.activeBranchId)
  const quota = useVersionStore((state) => state.quota)
  const loadVersions = useVersionStore((state) => state.loadVersions)
  const loadBranches = useVersionStore((state) => state.loadBranches)
  const activateBranch = useVersionStore((state) => state.activateBranch)
  const createBranch = useVersionStore((state) => state.createBranch)
  const getVersionDetail = useVersionStore((state) => state.getVersionDetail)
  const pinVersion = useVersionStore((state) => state.pinVersion)
  const rollbackPages = useVersionStore((state) => state.rollbackPages)
  const setActiveVersion = useVersionStore((state) => state.setActiveVersion)
  const [search, setSearch] = useState('')
  const [historyBranchId, setHistoryBranchId] = useState<string>('all')
  const [rollbackState, setRollbackState] = useState<{
    version: VersionSummary
    pages: VersionPage[]
    selected: Record<string, boolean>
    isSubmitting: boolean
    error?: string
  } | null>(null)
  const effectiveBranchId =
    historyBranchId === 'all' ? null : historyBranchId || activeBranchId

  useEffect(() => {
    if (project?.id) {
      void loadBranches(project.id)
    }
  }, [project?.id, loadBranches])

  useEffect(() => {
    if (project?.id) {
      void loadVersions(project.id, effectiveBranchId)
    }
  }, [project?.id, loadVersions, effectiveBranchId])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return versions
    return versions.filter((version) =>
      version.change_summary?.description?.toLowerCase().includes(term) ||
      version.change_summary?.tasks_completed?.some((task) =>
        task.toLowerCase().includes(term)
      ) ||
      version.branch_label?.toLowerCase().includes(term)
    )
  }, [versions, search])

  const treeNodes = useMemo<Array<VersionSummary & { depth: number; isBranchRoot: boolean }>>(() => {
    const byId = new Map(filtered.map((version) => [version.id, version]))
    const depthCache = new Map<string, number>()

    const resolveDepth = (version: VersionSummary): number => {
      if (depthCache.has(version.id)) {
        return depthCache.get(version.id) || 0
      }
      const parentId = version.parent_version_id
      if (!parentId) {
        depthCache.set(version.id, 0)
        return 0
      }
      const parent = byId.get(parentId)
      if (!parent) {
        depthCache.set(version.id, 0)
        return 0
      }
      const depth = resolveDepth(parent) + 1
      depthCache.set(version.id, depth)
      return depth
    }

    return filtered
      .map((version) => {
        const parent = version.parent_version_id
          ? byId.get(version.parent_version_id)
          : undefined
        return {
          ...version,
          depth: resolveDepth(version),
          isBranchRoot:
            Boolean(parent?.branch_id) &&
            Boolean(version.branch_id) &&
            parent?.branch_id !== version.branch_id,
        }
      })
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
  }, [filtered])

  const handleVersionPreview = async (version: VersionSummary) => {
    if (!project?.id) return
    const detail = await getVersionDetail(project.id, version.id)
    if (!detail || !detail.pages.length) return
    const page = detail.pages.find((item) => item.is_home) || detail.pages[0]
    const html = (page.content?.html as string | undefined) || ''
    const js = (page.content?.js as string | undefined) || ''
    setActiveVersion(version.id)
    window.dispatchEvent(
      new CustomEvent('open-version-preview', {
        detail: {
          versionId: version.id,
          pageId: page.id,
          pageName: page.name,
          pagePath: page.path,
          html,
          js,
        },
      })
    )
  }

  const handleVersionCode = (version: VersionSummary) => {
    setActiveVersion(version.id)
    window.dispatchEvent(new CustomEvent('open-code-view'))
  }

  const handleTogglePin = (version: VersionSummary) => {
    if (!project?.id) return
    void pinVersion(project.id, version.id, !version.is_pinned)
  }

  const handleRollback = async (version: VersionSummary) => {
    if (!project?.id) return
    const detail = await getVersionDetail(project.id, version.id, { includeDiff: true })
    if (!detail) return
    const selected: Record<string, boolean> = {}
    detail.pages.forEach((page) => {
      selected[page.id] = !page.is_missing
    })
    setRollbackState({
      version,
      pages: detail.pages,
      selected,
      isSubmitting: false,
    })
  }

  const handleRollbackSubmit = async () => {
    if (!project?.id || !rollbackState) return
    const pageIds = rollbackState.pages
      .filter((page) => rollbackState.selected[page.id])
      .map((page) => page.id)
    if (!pageIds.length) {
      setRollbackState({
        ...rollbackState,
        error: 'Select at least one page to rollback.',
      })
      return
    }
    setRollbackState({ ...rollbackState, isSubmitting: true, error: undefined })
    const result = await rollbackPages(project.id, rollbackState.version.id, pageIds)
    if (!result) {
      setRollbackState({
        ...rollbackState,
        isSubmitting: false,
        error: 'Rollback failed. Try again.',
      })
      return
    }
    await loadPages(project.id, { preserveSelection: true })
    window.dispatchEvent(new CustomEvent('open-preview'))
    setRollbackState(null)
  }

  return (
    <Card className="w-80 h-full flex flex-col">
      <CardHeader className="pb-2 flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Version History</CardTitle>
          <div className="flex items-center gap-2">
            {onShowBuild && (
              <button
                onClick={onShowBuild}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Build
              </button>
            )}
            {onCollapse && (
              <button
                onClick={onCollapse}
                className="text-muted-foreground hover:text-foreground"
                aria-label="Collapse history"
              >
                −
              </button>
            )}
          </div>
        </div>
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search versions"
          className="mt-2"
        />
        {branches.length > 0 && (
          <select
            className="mt-2 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
            value={historyBranchId}
            onChange={(event) => {
              const nextId = event.target.value
              if (!project?.id) return
              if (nextId === 'all') {
                setHistoryBranchId('all')
                return
              }
              void activateBranch(project.id, nextId)
                .then(() => {
                  setHistoryBranchId(nextId)
                  return loadPages(project.id, { preserveSelection: false })
                })
            }}
          >
            <option value="all">All branches</option>
            {branches.map((branch) => (
              <option key={branch.id} value={branch.id}>
                {branch.label || branch.name}
              </option>
            ))}
          </select>
        )}
        {quota && historyBranchId !== 'all' && (
          <div
            className={
              quota.can_create
                ? quota.warning
                  ? 'mt-2 text-xs text-orange-600'
                  : 'mt-2 text-xs text-muted-foreground'
                : 'mt-2 text-xs text-red-600'
            }
          >
            {quota.limit === -1
              ? `Versions used: ${quota.used}`
              : `Versions: ${quota.used}/${quota.limit}`}
            {quota.warning && quota.can_create && ' • Approaching limit'}
            {!quota.can_create && ' • Limit reached'}
          </div>
        )}
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden pt-0">
        <ScrollArea className="h-[calc(100vh-250px)]">
          <div className="space-y-3 pr-2">
            {treeNodes.length === 0 ? (
              <div className="text-sm text-muted-foreground">No versions yet.</div>
            ) : (
              treeNodes.map((version) => {
                const summary = version.change_summary
                const createdAt = new Date(version.created_at).toLocaleString()
                const indent = Math.min(version.depth || 0, 6) * 14
                return (
                  <div
                    key={version.id}
                    className={`rounded-lg border bg-white p-3 relative ${version.depth ? 'pl-4' : ''}`}
                    style={{ marginLeft: indent }}
                  >
                    {version.depth ? (
                      <span className="absolute left-0 top-0 h-full w-px bg-gray-200" />
                    ) : null}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="text-sm font-semibold">
                            {summary.description || 'Version update'}
                          </p>
                          {version.branch_label && (
                            <span
                              className={
                                version.isBranchRoot
                                  ? 'rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] text-blue-600'
                                  : 'rounded-full border px-2 py-0.5 text-[10px] text-gray-500'
                              }
                            >
                              {version.isBranchRoot ? 'Branch ' : ''}
                              {version.branch_label}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">{createdAt}</p>
                      </div>
                      <button
                        className={
                          version.is_pinned
                            ? 'text-orange-600 text-xs'
                            : 'text-gray-400 text-xs'
                        }
                        onClick={() => handleTogglePin(version)}
                      >
                        📌
                      </button>
                    </div>
                    <div className="mt-2 text-xs text-gray-600 flex flex-wrap gap-2">
                      <span>{summary.files_changed} files</span>
                      <span className="text-green-600">+{summary.lines_added}</span>
                      <span className="text-red-500">-{summary.lines_deleted}</span>
                    </div>
                    {summary.tasks_completed?.length ? (
                      <div className="mt-2 text-xs text-gray-500">
                        Tasks: {summary.tasks_completed.join(', ')}
                      </div>
                    ) : null}
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleVersionPreview(version)}>
                        预览
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => handleVersionCode(version)}>
                        代码
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          if (!project?.id) return
                          const name = window.prompt('Branch name')
                          if (!name) return
                          const branch = await createBranch(project.id, version.id, {
                            name,
                            label: name,
                            set_active: true,
                          })
                          await loadBranches(project.id)
                          const branchId = branch?.id || activeBranchId
                          if (branchId) {
                            setHistoryBranchId(branchId)
                          }
                          await loadPages(project.id, { preserveSelection: false })
                        }}
                      >
                        创建分支
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleRollback(version)}>
                        页面回滚
                      </Button>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </ScrollArea>

        {rollbackState && (
          <div className="mt-4 rounded-lg border bg-white p-3">
            <p className="text-sm font-semibold">Rollback pages</p>
            <p className="text-xs text-muted-foreground mb-2">
              Select pages to rollback to this version. This will create a new version.
            </p>
            <div className="space-y-2 max-h-40 overflow-auto">
              {rollbackState.pages.map((page) => (
                <label
                  key={page.id}
                  className={`flex items-center gap-2 text-sm ${
                    page.is_missing ? 'opacity-60' : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={Boolean(rollbackState.selected[page.id])}
                    disabled={page.is_missing}
                    onChange={(event) =>
                      setRollbackState({
                        ...rollbackState,
                        selected: {
                          ...rollbackState.selected,
                          [page.id]: event.target.checked,
                        },
                      })
                    }
                  />
                  <span className="flex-1">{page.name}</span>
                  {page.is_missing ? (
                    <span className="text-xs text-red-500">Missing in current draft</span>
                  ) : (
                    <span className="text-xs text-gray-500">
                      +{page.lines_added ?? 0} -{page.lines_deleted ?? 0}
                    </span>
                  )}
                </label>
              ))}
            </div>
            {rollbackState.error && (
              <p className="mt-2 text-xs text-red-600">{rollbackState.error}</p>
            )}
            <div className="mt-3 flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setRollbackState(null)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleRollbackSubmit}
                disabled={rollbackState.isSubmitting}
              >
                Confirm rollback
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
