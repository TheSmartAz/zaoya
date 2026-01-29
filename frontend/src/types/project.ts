export interface DesignSystem {
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    text: string
  }
  typography: {
    headingFont: string
    bodyFont: string
  }
  spacing: 'compact' | 'comfortable' | 'spacious'
  borderRadius: 'none' | 'small' | 'medium' | 'large'
  animationLevel: 'none' | 'subtle' | 'moderate' | 'energetic'
}

// ProjectPage matches the project_pages database table
export interface ProjectPage {
  id: string
  project_id: string
  name: string
  slug?: string
  path: string
  is_home: boolean
  content: Record<string, unknown>
  design_system: DesignSystem
  thumbnail_url?: string | null
  thumbnail_job_id?: string | null
  thumbnail_status?: string | null
  thumbnail_error?: string | null
  thumbnail_updated_at?: string | null
  sort_order: number
  created_at: string
  updated_at: string
}

export interface PageCreate {
  name: string
  path?: string
  is_home?: boolean
}

export interface PageUpdate {
  name?: string
  path?: string
  is_home?: boolean
  sort_order?: number
  content?: Record<string, unknown>
  design_system?: DesignSystem
}

export interface Project {
  id: string
  user_id?: string
  owner_id?: string | null
  name: string
  template_id?: string
  template_inputs?: Record<string, unknown>
  render_templates?: Record<string, unknown>
  status: 'draft' | 'published'
  public_id?: string
  active_branch_id?: string | null
  notification_email?: string
  notification_enabled: boolean
  published_at?: string
  created_at: string
  updated_at: string
  pages?: ProjectPage[]
  can_view_code?: boolean
}

export interface ProjectWithPages extends Project {
  pages: ProjectPage[]
}
