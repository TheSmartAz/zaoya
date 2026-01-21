import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Project, ProjectState } from '@/types/project';
import type { Page, PageCreate, DraftResponse, DesignSystem, NavigationConfig } from '@/types/page';
import type { DesignSystem as DS, NavigationConfig as NC } from '@/types/design';
import { getAuthHeaders } from './authStore';

const GUEST_PROJECTS_KEY = 'zaoya-guest-projects';
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      projects: [],
      currentProjectId: null,

      createGuestProject: (name, templateId, templateInputs) => {
        const project: Project = {
          id: `guest_${generateId()}`,
          name,
          templateId,
          templateInputs,
          currentVersion: null,
          isGuest: true,
          status: 'draft',
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };

        set((state) => ({
          projects: [...state.projects, project],
          currentProjectId: project.id,
        }));

        return project;
      },

      setCurrentProject: (projectId) => {
        set({ currentProjectId: projectId });
      },

      updateProject: (projectId, updates) => {
        set((state) => ({
          projects: state.projects.map((p) =>
            p.id === projectId
              ? { ...p, ...updates, updatedAt: Date.now() }
              : p
          ),
        }));
      },

      convertToUserProject: async (projectId) => {
        const project = get().projects.find((p) => p.id === projectId);
        if (!project || !project.isGuest) {
          throw new Error('Project not found or not a guest project');
        }

        const headers = getAuthHeaders();
        if (!headers.Authorization) {
          throw new Error('Not authenticated');
        }

        // Save to server
        const response = await fetch(`${API_BASE}/api/projects`, {
          method: 'POST',
          headers: {
            ...headers,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            id: project.id,
            name: project.name,
            template_id: project.templateId,
            template_inputs: project.templateInputs,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to save project');
        }

        const savedProject = await response.json();

        const normalizedProject: Project = {
          id: savedProject.id,
          name: savedProject.name,
          templateId: savedProject.template_id,
          templateInputs: savedProject.template_inputs || {},
          currentVersion: null,
          isGuest: false,
          status: savedProject.status || 'draft',
          publicId: savedProject.public_id || undefined,
          publishedUrl: savedProject.published_url || undefined,
          notification_email: savedProject.notification_email,
          notification_enabled: savedProject.notification_enabled,
          createdAt: Date.parse(savedProject.created_at) || Date.now(),
          updatedAt: Date.parse(savedProject.updated_at) || Date.now(),
        };

        // Update local state - remove guest project, add saved project
        set((state) => ({
          projects: [
            ...state.projects.filter((p) => p.id !== projectId),
            normalizedProject,
          ],
          currentProjectId: normalizedProject.id,
        }));

        return normalizedProject;
      },

      deleteProject: (projectId) => {
        set((state) => ({
          projects: state.projects.filter((p) => p.id !== projectId),
          currentProjectId:
            state.currentProjectId === projectId ? null : state.currentProjectId,
        }));
      },

      getProject: (projectId) => {
        return get().projects.find((p) => p.id === projectId);
      },

      getCurrentProject: () => {
        const { currentProjectId, projects } = get();
        if (!currentProjectId) return null;
        return projects.find((p) => p.id === currentProjectId) || null;
      },

      // Multi-page state
      currentDraft: null as DraftResponse | null,
      pages: [] as Page[],

      loadDraft: async (projectId: string) => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) {
          throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE}/api/projects/${projectId}/draft`, {
          headers,
        });
        if (!response.ok) throw new Error('Failed to load draft');
        const draft: DraftResponse = await response.json();

        // Load pages
        const pagesResponse = await fetch(`${API_BASE}/api/projects/${projectId}/draft/pages`, {
          headers,
        });
        if (!pagesResponse.ok) throw new Error('Failed to load pages');
        const pages: Page[] = await pagesResponse.json();

        set({ currentDraft: draft, pages });
        return draft;
      },

      updateDesignSystem: async (projectId: string, designSystem: DS) => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) {
          throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE}/api/projects/${projectId}/draft`, {
          method: 'PATCH',
          headers: {
            ...headers,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ design_system: designSystem }),
        });
        if (!response.ok) throw new Error('Failed to update design system');
        const draft: DraftResponse = await response.json();
        set({ currentDraft: draft });
      },

      updateNavigation: async (projectId: string, navigation: NC) => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) {
          throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE}/api/projects/${projectId}/draft`, {
          method: 'PATCH',
          headers: {
            ...headers,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ navigation }),
        });
        if (!response.ok) throw new Error('Failed to update navigation');
        const draft: DraftResponse = await response.json();
        set({ currentDraft: draft });
      },

      addPage: async (projectId: string, page: PageCreate) => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) {
          throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE}/api/projects/${projectId}/draft/pages`, {
          method: 'POST',
          headers: {
            ...headers,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(page),
        });
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to add page');
        }
        const newPage: Page = await response.json();
        set((state) => ({ pages: [...state.pages, newPage] }));
        return newPage;
      },

      updatePage: async (projectId: string, pageId: string, updates: Partial<PageCreate>) => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) {
          throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE}/api/projects/${projectId}/draft/pages/${pageId}`, {
          method: 'PATCH',
          headers: {
            ...headers,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updates),
        });
        if (!response.ok) throw new Error('Failed to update page');
        const updated: Page = await response.json();
        set((state) => ({
          pages: state.pages.map((p) => (p.id === pageId ? updated : p)),
        }));
        return updated;
      },

      deletePage: async (projectId: string, pageId: string) => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) {
          throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE}/api/projects/${projectId}/draft/pages/${pageId}`, {
          method: 'DELETE',
          headers,
        });
        if (!response.ok) throw new Error('Failed to delete page');
        set((state) => ({ pages: state.pages.filter((p) => p.id !== pageId) }));
      },

      reorderPages: async (projectId: string, pageIds: string[]) => {
        const headers = getAuthHeaders();
        if (!headers.Authorization) {
          throw new Error('Not authenticated');
        }

        const response = await fetch(`${API_BASE}/api/projects/${projectId}/draft/pages/reorder`, {
          method: 'POST',
          headers: {
            ...headers,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ page_ids: pageIds }),
        });
        if (!response.ok) throw new Error('Failed to reorder pages');
        set((state) => {
          const pageMap = new Map(state.pages.map((p) => [p.id, p]));
          const reordered = pageIds
            .map((id) => pageMap.get(id))
            .filter((p): p is Page => p !== undefined);
          return { pages: reordered };
        });
      },
    }),
    {
      name: GUEST_PROJECTS_KEY,
      storage: createJSONStorage(() => localStorage),
    }
  )
);
