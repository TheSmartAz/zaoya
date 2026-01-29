export type FileScope = 'draft' | 'snapshot' | 'published' | 'version'

export interface FileEntry {
  path: string
  source: string
  size?: number
  mime_type?: string
  language?: string
}

export interface FileListResponse {
  scope: FileScope
  files: FileEntry[]
}

export interface FileContentResponse {
  path: string
  source: string
  content?: string | null
  url?: string | null
  size?: number
  mime_type?: string
  language?: string
}
