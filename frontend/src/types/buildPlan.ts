export type BuildTaskCategory =
  | 'planning'
  | 'generation'
  | 'validation'
  | 'assets'
  | 'storage'
  | 'finalization'

export type BuildTaskStatus = 'pending' | 'running' | 'done' | 'failed' | 'skipped'

export interface BuildTask {
  id: string
  name: string
  description?: string
  category: BuildTaskCategory
  status: BuildTaskStatus
  parent_id?: string
  page_id?: string
  started_at?: number
  completed_at?: number
  error?: string
  estimated_ms?: number
}

export interface BuildPlanPage {
  id: string
  name: string
  path: string
  is_main: boolean
  task_count: number
}

export interface BuildPlan {
  id: string
  project_id: string
  created_at: string | null
  pages: BuildPlanPage[]
  tasks: BuildTask[]
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  estimated_duration_ms?: number | null
  actual_duration_ms?: number | null
  started_at?: string | null
  completed_at?: string | null
  status: 'draft' | 'approved' | 'running' | 'completed' | 'failed' | 'cancelled'
}
