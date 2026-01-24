import { create } from 'zustand'
import type { Project, DesignSystem, ProjectPage } from '@/types/project'

const defaultDesignSystem: DesignSystem = {
  colors: {
    primary: '#18181b',
    secondary: '#71717a',
    accent: '#2563eb',
    background: '#ffffff',
    text: '#18181b',
  },
  typography: {
    headingFont: 'Geist',
    bodyFont: 'Geist',
  },
  spacing: 'comfortable',
  borderRadius: 'medium',
  animationLevel: 'subtle',
}

interface ProjectStore {
  project: Project | null
  previewHtml: string | null

  // Actions
  createProject: (name: string) => void
  updateProjectName: (name: string) => void
  updateDesignSystem: (updates: Partial<DesignSystem>) => void
  setPreviewHtml: (html: string) => void
  addPage: (page: Omit<ProjectPage, 'id'>) => void
  updatePage: (pageId: string, updates: Partial<ProjectPage>) => void
  setCurrentPage: (pageId: string) => void
}

export const useProjectStore = create<ProjectStore>((set) => ({
  project: null,
  previewHtml: null,

  createProject: (name) =>
    set({
      project: {
        id: `proj-${Date.now()}`,
        name,
        pages: [
          {
            id: 'home',
            name: 'Home',
            path: '/',
            isHome: true,
            html: '',
          },
        ],
        designSystem: defaultDesignSystem,
        currentPageId: 'home',
        createdAt: Date.now(),
        updatedAt: Date.now(),
      },
    }),

  updateProjectName: (name) =>
    set((state) => ({
      project: state.project
        ? { ...state.project, name, updatedAt: Date.now() }
        : null,
    })),

  updateDesignSystem: (updates) =>
    set((state) => ({
      project: state.project
        ? {
            ...state.project,
            designSystem: { ...state.project.designSystem, ...updates },
            updatedAt: Date.now(),
          }
        : null,
    })),

  setPreviewHtml: (html) => set({ previewHtml: html }),

  addPage: (page) =>
    set((state) => ({
      project: state.project
        ? {
            ...state.project,
            pages: [
              ...state.project.pages,
              { ...page, id: `page-${Date.now()}` },
            ],
            updatedAt: Date.now(),
          }
        : null,
    })),

  updatePage: (pageId, updates) =>
    set((state) => ({
      project: state.project
        ? {
            ...state.project,
            pages: state.project.pages.map((p) =>
              p.id === pageId ? { ...p, ...updates } : p
            ),
            updatedAt: Date.now(),
          }
        : null,
    })),

  setCurrentPage: (pageId) =>
    set((state) => ({
      project: state.project
        ? { ...state.project, currentPageId: pageId }
        : null,
    })),
}))
