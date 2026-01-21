import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Project, ProjectState } from '@/types/project';
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
    }),
    {
      name: GUEST_PROJECTS_KEY,
      storage: createJSONStorage(() => localStorage),
    }
  )
);
