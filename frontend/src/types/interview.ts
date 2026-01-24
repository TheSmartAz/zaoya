export interface InterviewOption {
  value: string
  label: string
  description?: string
}

export interface InterviewQuestion {
  id: string
  text: string
  type: 'single_select' | 'multi_select' | 'text' | 'date'
  options?: InterviewOption[]
  allowOther?: boolean
}

export interface InterviewGroup {
  id: string
  title: string
  icon?: string
  questions: InterviewQuestion[]
  currentIndex: number
  totalInGroup: number
}
