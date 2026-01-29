export interface ProductDoc {
  id: string
  project_id: string
  created_at: string
  updated_at: string

  overview: string
  target_users?: string[]

  content_structure: {
    sections: ContentSection[]
  }

  design_requirements?: {
    style?: string
    colors?: string[]
    typography?: string
    mood?: string
  }

  page_plan: {
    pages: PagePlanItem[]
  }

  technical_constraints?: string[]

  interview_answers: InterviewAnswer[]

  generation_count: number
  last_generated_at?: string
}

export interface ContentSection {
  name: string
  description: string
  priority: 'high' | 'medium' | 'low'
  content_hints?: string[]
}

export interface PagePlanItem {
  id: string
  name: string
  path: string
  description: string
  is_main: boolean
  sections: string[]
}

export interface InterviewAnswer {
  question_id: string
  question: string
  answer: string
  answered_at: string
}
