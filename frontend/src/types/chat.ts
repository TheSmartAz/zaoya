export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  type?: 'text' | 'interview' | 'plan'
}

export interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
}

export type LiveTaskMessageType =
  | 'agent_thinking'
  | 'task_started'
  | 'task_done'
  | 'task_failed'
  | 'tool_call'
  | 'page_created'
  | 'version_summary'
  | 'build_plan'
  | 'interview'
  | 'validation_failed'
  | 'product_doc_ready'
  | 'build_complete'

export interface PageCardData {
  id: string
  name: string
  path: string
  thumbnailUrl?: string
}

export interface BuildPlanPage {
  id: string
  name: string
  path: string
  is_main?: boolean
}

export interface BuildPlanCardData {
  pages: BuildPlanPage[]
  tasks?: { id: string; title: string; status: string }[]
  estimated_tasks: number
  build_id?: string
  features?: string[]
  design_system?: {
    style?: string
    theme?: string
    name?: string
    colors?: { primary?: string }
    color_palette?: string[]
  }
  estimated_complexity?: string
  project_type?: string
  reason?: string
  approval_required?: boolean
}

export interface InterviewCardData {
  questions: { id: string; question: string; hint?: string }[]
  answers: Record<string, string>
  stats?: {
    asked: number
    answered: number
    skipped: number
  }
}

export interface ValidationErrorDetail {
  ruleId?: string
  ruleCategory?: 'csp' | 'js-security' | 'html-whitelist' | 'resource' | 'runtime'
  path?: string
  line?: number
  excerpt?: string
  message: string
  suggestedFix?: string
  severity?: 'critical' | 'warning' | 'info'
  type?: string
}

export interface ValidationCardData {
  errors: ValidationErrorDetail[]
  suggestions: string[]
  page_id?: string
  page_name?: string
  page_path?: string
  retry_count?: number
}

export interface ProductDocCardData {
  project_id: string
}

export interface VersionCardData {
  id: string
  created_at: string
  change_summary: {
    files_changed: number
    lines_added: number
    lines_deleted: number
    tasks_completed: string[]
    description: string
  }
  validation_status: string
  is_pinned: boolean
  branch_label?: string | null
  page_id?: string | null
  page_name?: string | null
  page_path?: string | null
}

export interface LiveTaskMessage {
  id: string
  type: LiveTaskMessageType
  timestamp: number
  session_id: string
  title: string
  status: 'running' | 'done' | 'failed'
  card?: {
    type: 'page' | 'build_plan' | 'interview' | 'validation' | 'product_doc_ready' | 'version'
    data:
      | PageCardData
      | BuildPlanCardData
      | InterviewCardData
      | ValidationCardData
      | ProductDocCardData
      | VersionCardData
  }
  actions?: {
    label: string
    action: 'retry' | 'view' | 'edit' | 'start_build' | 'skip'
  }[]
}
