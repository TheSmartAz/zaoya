import { useEffect, useMemo, useRef, useState } from 'react'
import { ChevronDown, ChevronRight, FileText, Folder, Image } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { FileContentResponse, FileEntry, FileScope } from '@/types/files'
import { CodeMirrorViewer, type CodeMirrorHandle } from './CodeMirrorViewer'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface CodeTabProps {
  projectId: string
  versionId?: string | null
  focus?: { path?: string; line?: number } | null
}

interface TreeNode {
  name: string
  path: string
  type: 'folder' | 'file'
  children?: TreeNode[]
  entry?: FileEntry
}

const ROOT_FOLDERS = ['pages', 'components', 'assets']

const buildTree = (files: FileEntry[]): TreeNode[] => {
  const root: TreeNode = { name: '', path: '', type: 'folder', children: [] }
  const ensureFolder = (parent: TreeNode, name: string, path: string) => {
    const existing = parent.children?.find(
      (child) => child.type === 'folder' && child.name === name
    )
    if (existing) return existing
    const folder: TreeNode = { name, path, type: 'folder', children: [] }
    parent.children?.push(folder)
    return folder
  }

  files.forEach((file) => {
    const parts = file.path.split('/').filter(Boolean)
    let current = root
    let currentPath = ''
    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      const isFile = index === parts.length - 1
      if (isFile) {
        current.children?.push({
          name: part,
          path: currentPath,
          type: 'file',
          entry: file,
        })
      } else {
        current = ensureFolder(current, part, currentPath)
      }
    })
  })

  ROOT_FOLDERS.forEach((folder) => {
    ensureFolder(root, folder, folder)
  })

  const sortNodes = (nodes: TreeNode[]) => {
    nodes.sort((a, b) => {
      if (a.type !== b.type) return a.type === 'folder' ? -1 : 1
      return a.name.localeCompare(b.name)
    })
    nodes.forEach((node) => {
      if (node.children) sortNodes(node.children)
    })
  }

  if (root.children) sortNodes(root.children)
  return root.children || []
}

export function CodeTab({ projectId, versionId, focus }: CodeTabProps) {
  const [scope, setScope] = useState<FileScope>('draft')
  const [files, setFiles] = useState<FileEntry[]>([])
  const [selectedPath, setSelectedPath] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<FileContentResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const editorRef = useRef<CodeMirrorHandle>(null)

  const tree = useMemo(() => buildTree(files), [files])

  useEffect(() => {
    if (!projectId) return
    const controller = new AbortController()

    const loadFiles = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const endpoint = versionId
          ? `${API_BASE_URL}/api/projects/${projectId}/versions/${versionId}/files`
          : `${API_BASE_URL}/api/projects/${projectId}/files?scope=${scope}`
        const response = await fetch(endpoint, { signal: controller.signal })
        if (!response.ok) {
          const message =
            response.status === 403
              ? 'Code access is restricted to the project owner.'
              : 'Failed to load files.'
          throw new Error(message)
        }
        const data = (await response.json()) as { files: FileEntry[] }
        setFiles(data.files || [])
        if (data.files?.length) {
          const stillExists = data.files.find((file) => file.path === selectedPath)
          setSelectedPath(stillExists ? stillExists.path : data.files[0].path)
        } else {
          setSelectedPath(null)
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return
        setError(err instanceof Error ? err.message : 'Failed to load files.')
        setFiles([])
        setSelectedPath(null)
      } finally {
        setIsLoading(false)
      }
    }

    void loadFiles()

    return () => controller.abort()
  }, [projectId, scope, versionId])

  useEffect(() => {
    if (!projectId || !selectedPath) {
      setFileContent(null)
      return
    }
    const controller = new AbortController()

    const loadContent = async () => {
      try {
        const endpoint = versionId
          ? `${API_BASE_URL}/api/projects/${projectId}/versions/${versionId}/files/content?path=${encodeURIComponent(
              selectedPath
            )}`
          : `${API_BASE_URL}/api/projects/${projectId}/files/content?scope=${scope}&path=${encodeURIComponent(
              selectedPath
            )}`
        const response = await fetch(endpoint, { signal: controller.signal })
        if (!response.ok) {
          throw new Error('Failed to load file content.')
        }
        const data = (await response.json()) as FileContentResponse
        setFileContent(data)
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return
        setFileContent(null)
      }
    }

    void loadContent()

    return () => controller.abort()
  }, [projectId, selectedPath, scope, versionId])

  useEffect(() => {
    editorRef.current?.setSearchQuery(searchQuery)
  }, [searchQuery])

  useEffect(() => {
    if (!focus?.path) return
    setSelectedPath(focus.path)
    setSearchQuery('')
  }, [focus?.path])

  useEffect(() => {
    if (!focus?.line || !focus?.path) return
    if (selectedPath !== focus.path) return
    editorRef.current?.scrollToLine(focus.line)
  }, [focus?.line, focus?.path, selectedPath, fileContent])

  const handleSelect = (path: string) => {
    setSelectedPath(path)
    setSearchQuery('')
  }

  const activeFile = files.find((file) => file.path === selectedPath)

  return (
    <div className="flex h-full overflow-hidden">
      <aside className="w-64 shrink-0 border-r bg-white">
        <div className="flex items-center justify-between border-b px-3 py-2">
          <span className="text-xs font-semibold text-gray-600">Files</span>
          {versionId ? (
            <span className="rounded border px-2 py-1 text-[10px] uppercase text-gray-500">
              Version
            </span>
          ) : (
            <select
              value={scope}
              onChange={(event) => setScope(event.target.value as FileScope)}
              className="rounded border px-2 py-1 text-xs text-gray-600"
            >
              <option value="draft">Draft</option>
              <option value="snapshot">Snapshot</option>
              <option value="published">Published</option>
            </select>
          )}
        </div>
        <div className="h-full overflow-auto px-2 py-3">
          {isLoading ? (
            <div className="text-xs text-gray-500">Loading files...</div>
          ) : error ? (
            <div className="text-xs text-red-500">{error}</div>
          ) : (
            <FileTree nodes={tree} selectedPath={selectedPath} onSelect={handleSelect} />
          )}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-2 border-b bg-white px-4 py-2">
          <div className="flex-1 text-xs text-gray-500">
            {activeFile?.path || 'Select a file to view'}
          </div>
          <div className="flex items-center gap-2">
            <Input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search in file..."
              className="h-8 w-48 text-xs"
            />
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => editorRef.current?.findPrevious()}
              title="Previous match"
            >
              <ChevronUpIcon />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => editorRef.current?.findNext()}
              title="Next match"
            >
              <ChevronDownIcon />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-hidden bg-muted/30">
          {fileContent?.url ? (
            <div className="flex h-full flex-col items-center justify-center gap-4 p-6 text-center">
              <Image className="h-10 w-10 text-gray-400" />
              <div className="text-sm text-gray-600">
                <div className="font-medium">{fileContent.path}</div>
                <a
                  href={fileContent.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-blue-600 hover:underline"
                >
                  Open asset
                </a>
              </div>
            </div>
          ) : fileContent && fileContent.content !== undefined ? (
            <CodeMirrorViewer
              ref={editorRef}
              value={fileContent.content || ''}
              language={fileContent.language}
              className="h-full"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-gray-500">
              {selectedPath ? 'No preview available.' : 'Select a file to view.'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function FileTree({
  nodes,
  selectedPath,
  onSelect,
}: {
  nodes: TreeNode[]
  selectedPath: string | null
  onSelect: (path: string) => void
}) {
  const [expanded, setExpanded] = useState<Set<string>>(
    () => new Set(ROOT_FOLDERS)
  )

  const toggle = (path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }

  const renderNode = (node: TreeNode, depth: number) => {
    const isFolder = node.type === 'folder'
    const isExpanded = expanded.has(node.path)
    const padding = { paddingLeft: `${depth * 12 + 8}px` }

    if (isFolder) {
      return (
        <div key={node.path}>
          <button
            type="button"
            onClick={() => toggle(node.path)}
            className="flex w-full items-center gap-1 rounded px-1 py-1 text-left text-xs text-gray-700 hover:bg-gray-100"
            style={padding}
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3 text-gray-500" />
            ) : (
              <ChevronRight className="h-3 w-3 text-gray-500" />
            )}
            <Folder className="h-3 w-3 text-gray-500" />
            <span>{node.name}</span>
          </button>
          {isExpanded &&
            node.children?.map((child) => renderNode(child, depth + 1))}
        </div>
      )
    }

    return (
      <button
        key={node.path}
        type="button"
        onClick={() => onSelect(node.path)}
        className={cn(
          'flex w-full items-center gap-1 rounded px-1 py-1 text-left text-xs hover:bg-gray-100',
          selectedPath === node.path ? 'bg-gray-100 text-gray-900' : 'text-gray-600'
        )}
        style={padding}
      >
        <FileText className="h-3 w-3 text-gray-400" />
        <span className="truncate">{node.name}</span>
      </button>
    )
  }

  return <div className="space-y-0.5">{nodes.map((node) => renderNode(node, 0))}</div>
}

function ChevronUpIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M6 15l6-6 6 6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ChevronDownIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M6 9l6 6 6-6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
