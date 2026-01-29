import { create } from 'zustand'
import type {
  Project,
  ProjectPage,
  DesignSystem,
  PageCreate,
  PageUpdate,
} from '@/types/project'
import type { ProductDoc } from '@/types/productDoc'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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

const toPath = (name: string) => {
  const slug = name.trim().toLowerCase().replace(/\s+/g, '-')
  return `/${slug || 'page'}`
}

interface ProjectStore {
  project: Project | null
  projects: Project[]
  pages: ProjectPage[]
  currentPageId: string | null
  previewHtml: string | null
  versionPreview: {
    versionId: string
    pageId?: string | null
    pageName?: string | null
    pagePath?: string | null
    html: string
    js?: string | null
  } | null
  designSystem: DesignSystem
  productDoc: ProductDoc | null
  isLoadingProductDoc: boolean

  setProject: (project: Project | null) => void
  loadProjects: () => Promise<void>
  createProject: (name: string) => Promise<Project>
  loadProject: (projectId: string) => Promise<void>

  setPages: (pages: ProjectPage[]) => void
  setCurrentPage: (pageId: string) => void
  loadPages: (
    projectId: string,
    options?: { preserveSelection?: boolean }
  ) => Promise<void>
  createPage: (projectId: string, data: PageCreate) => Promise<ProjectPage>
  savePage: (pageId: string, data: PageUpdate) => Promise<void>
  reorderPages: (pageIds: string[]) => Promise<void>
  renamePage: (pageId: string, name: string) => Promise<void>
  setAsHomePage: (pageId: string) => Promise<void>
  deletePage: (pageId: string) => Promise<void>

  updateDesignSystem: (updates: Partial<DesignSystem>) => void
  setPreviewHtml: (html: string) => void
  setVersionPreview: (preview: ProjectStore['versionPreview']) => void
  loadProductDoc: (projectId: string) => Promise<void>
  updateProductDoc: (updates: Partial<ProductDoc>) => void
  clearProductDoc: () => void
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  project: null,
  projects: [],
  pages: [],
  currentPageId: null,
  previewHtml: null,
  versionPreview: null,
  designSystem: defaultDesignSystem,
  productDoc: null,
  isLoadingProductDoc: false,

  setProject: (project) => set({ project }),

  loadProjects: async () => {
    const response = await fetch(`${API_BASE_URL}/api/projects`)
    if (!response.ok) throw new Error('Failed to load projects')
    const projects = (await response.json()) as Project[]
    set({ projects })
  },

  createProject: async (name: string) => {
    const response = await fetch(`${API_BASE_URL}/api/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (!response.ok) throw new Error('Failed to create project')
    const project = (await response.json()) as Project
    set({ project })
    return project
  },

  loadProject: async (projectId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}`)
    if (!response.ok) throw new Error('Failed to load project')
    const project = (await response.json()) as Project
    set({ project, pages: [], currentPageId: null, productDoc: null, versionPreview: null })
  },

  setPages: (pages) => {
    set({ pages })
    if (pages.length > 0) {
      const homePage = pages.find((p) => p.is_home) || pages[0]
      set({ currentPageId: homePage.id })
      if (homePage.design_system) {
        set({ designSystem: homePage.design_system as DesignSystem })
      }
    } else {
      set({ currentPageId: null })
    }
  },

  setCurrentPage: (pageId: string) => {
    const { pages } = get()
    const page = pages.find((p) => p.id === pageId)
    if (page) {
      set({ currentPageId: pageId })
      if (page.design_system) {
        set({ designSystem: page.design_system as DesignSystem })
      }
    }
  },

  loadPages: async (projectId: string, options?: { preserveSelection?: boolean }) => {
    const preserveSelection = options?.preserveSelection ?? false
    const previousPageId = get().currentPageId
    const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/pages`)
    if (!response.ok) throw new Error('Failed to load pages')
    const pages = (await response.json()) as ProjectPage[]
    set({ pages })

    if (pages.length === 0) {
      set({ currentPageId: null })
      return
    }

    if (preserveSelection && previousPageId) {
      const existing = pages.find((page) => page.id === previousPageId)
      if (existing) {
        set({ currentPageId: existing.id })
        if (existing.design_system) {
          set({ designSystem: existing.design_system as DesignSystem })
        }
        return
      }
    }

    const homePage = pages.find((page) => page.is_home) || pages[0]
    set({ currentPageId: homePage.id })
    if (homePage.design_system) {
      set({ designSystem: homePage.design_system as DesignSystem })
    }
  },

  createPage: async (projectId: string, data: PageCreate) => {
    const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/pages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error('Failed to create page')
    const page = (await response.json()) as ProjectPage
    set((state) => ({
      pages: [...state.pages, page],
      currentPageId: page.id,
    }))
    return page
  },

  savePage: async (pageId: string, data: PageUpdate) => {
    const response = await fetch(`${API_BASE_URL}/api/projects/pages/${pageId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error('Failed to save page')
    const updated = (await response.json()) as ProjectPage
    set((state) => ({
      pages: state.pages.map((p) => (p.id === pageId ? updated : p)),
    }))
  },

  reorderPages: async (pageIds: string[]) => {
    const { project, pages } = get()
    const projectId = project?.id
    if (!projectId) return

    const previousPages = pages
    const reorderedPages = pageIds.map((id, index) => {
      const page = pages.find((item) => item.id === id)
      if (!page) return null
      return {
        ...page,
        sort_order: index,
        is_home: index === 0,
        path: index === 0 ? '/' : toPath(page.name),
      }
    })

    const nextPages = reorderedPages.filter((page): page is ProjectPage => page !== null)
    set({ pages: nextPages })

    try {
      await fetch(`${API_BASE_URL}/api/projects/${projectId}/pages/reorder`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ page_ids: pageIds }),
      })
    } catch (error) {
      set({ pages: previousPages })
      console.error('Failed to reorder pages:', error)
    }
  },

  renamePage: async (pageId: string, name: string) => {
    const { project, pages } = get()
    const projectId = project?.id
    if (!projectId) return

    const updatedPages = pages.map((page) =>
      page.id === pageId
        ? {
            ...page,
            name,
            path: page.is_home ? '/' : toPath(name),
          }
        : page
    )
    set({ pages: updatedPages })

    try {
      await fetch(`${API_BASE_URL}/api/projects/pages/${pageId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, path: updatedPages.find((p) => p.id === pageId)?.path }),
      })
    } catch (error) {
      set({ pages })
      console.error('Failed to rename page:', error)
    }
  },

  setAsHomePage: async (pageId: string) => {
    const { pages } = get()
    const newOrder = [pageId, ...pages.filter((page) => page.id !== pageId).map((page) => page.id)]
    await get().reorderPages(newOrder)
  },

  deletePage: async (pageId: string) => {
    const { pages, currentPageId } = get()
    const page = pages.find((item) => item.id === pageId)
    if (!page || page.is_home) return

    const remainingPages = pages.filter((item) => item.id !== pageId)
    const nextCurrentPageId =
      currentPageId === pageId
        ? remainingPages.find((item) => item.is_home)?.id || remainingPages[0]?.id || null
        : currentPageId

    set({ pages: remainingPages, currentPageId: nextCurrentPageId })

    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/pages/${pageId}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to delete page')
    } catch (error) {
      set({ pages, currentPageId })
      console.error('Failed to delete page:', error)
    }
  },

  updateDesignSystem: (updates) => {
    set((state) => ({
      designSystem: { ...state.designSystem, ...updates },
    }))
  },

  setPreviewHtml: (html) => set({ previewHtml: html }),

  setVersionPreview: (preview) => set({ versionPreview: preview }),

  loadProductDoc: async (projectId: string) => {
    set({ isLoadingProductDoc: true })

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/product-doc`
      )

      if (response.ok) {
        const doc = (await response.json()) as ProductDoc
        set({ productDoc: doc, isLoadingProductDoc: false })
      } else if (response.status === 404) {
        set({ productDoc: null, isLoadingProductDoc: false })
      } else {
        throw new Error('Failed to load ProductDoc')
      }
    } catch (error) {
      console.error('Error loading ProductDoc:', error)
      set({ productDoc: null, isLoadingProductDoc: false })
    }
  },

  updateProductDoc: (updates: Partial<ProductDoc>) => {
    const { productDoc } = get()
    if (productDoc) {
      set({
        productDoc: {
          ...productDoc,
          ...updates,
          updated_at: new Date().toISOString(),
        },
      })
    }
  },

  clearProductDoc: () => {
    set({ productDoc: null })
  },
}))
