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

export interface ProjectPage {
  id: string
  name: string
  path: string
  isHome: boolean
  html: string
  css?: string
  js?: string
}

export interface Project {
  id: string
  name: string
  description?: string
  pages: ProjectPage[]
  designSystem: DesignSystem
  currentPageId: string
  createdAt: number
  updatedAt: number
}
