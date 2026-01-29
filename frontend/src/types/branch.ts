export interface Branch {
  id: string
  project_id: string
  name: string
  label?: string | null
  parent_branch_id?: string | null
  created_from_version_id?: string | null
  is_default: boolean
  created_at: string
}

export interface BranchListResponse {
  branches: Branch[]
  active_branch_id?: string | null
}
