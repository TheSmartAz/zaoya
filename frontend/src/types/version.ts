export interface VersionChangeSummary {
  files_changed: number
  lines_added: number
  lines_deleted: number
  tasks_completed: string[]
  description: string
}

export interface VersionSummary {
  id: string
  project_id: string
  parent_version_id?: string | null
  branch_id?: string | null
  branch_label?: string | null
  created_at: string
  trigger_message_id?: string | null
  snapshot_id?: string | null
  change_summary: VersionChangeSummary
  validation_status: string
  is_pinned: boolean
}

export interface VersionPage {
  id: string
  name: string
  slug?: string | null
  path: string
  is_home: boolean
  content: Record<string, unknown>
  design_system: Record<string, unknown>
  sort_order: number
  lines_added?: number
  lines_deleted?: number
  is_missing?: boolean
}

export interface VersionDetail extends VersionSummary {
  pages: VersionPage[]
}

export interface VersionQuota {
  limit: number
  used: number
  warning: boolean
  can_create: boolean
}

export interface VersionListResponse {
  versions: VersionSummary[]
  quota?: VersionQuota
}
