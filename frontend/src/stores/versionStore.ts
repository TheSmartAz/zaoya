import { create } from 'zustand';
import { Version } from '@/types/version';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

interface VersionState {
  versions: Version[];
  currentVersionId: string | null;
  projectId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setProjectId: (projectId: string) => void;
  loadVersions: (projectId?: string) => Promise<void>;
  createVersion: (version: Omit<Version, 'id' | 'number'>) => Promise<Version>;
  restoreVersion: (versionId: string) => Promise<Version>;
  getCurrentVersion: () => Version | null;
  getVersionHistory: () => Version[];
  clearVersions: () => void;
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === 'string') return data.detail;
    if (Array.isArray(data?.detail)) return data.detail.join(', ');
    if (data?.detail?.errors && Array.isArray(data.detail.errors)) {
      return data.detail.errors.join(', ');
    }
  } catch (error) {
    // Ignore parse errors
  }
  return `Request failed (${response.status})`;
}

export const useVersionStore = create<VersionState>((set, get) => ({
  versions: [],
  currentVersionId: null,
  projectId: null,
  isLoading: false,
  error: null,

  setProjectId: (projectId: string) => set({
    projectId,
    versions: [],
    currentVersionId: null,
    error: null,
  }),

  loadVersions: async (projectId?: string) => {
    const targetProjectId = projectId || get().projectId;
    if (!targetProjectId) return;

    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/api/versions/${targetProjectId}`);
      if (!response.ok) {
        throw new Error(await parseError(response));
      }

      const data = await response.json();
      set({
        versions: data.versions || [],
        currentVersionId: data.currentVersionId || null,
        isLoading: false,
      });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load versions',
      });
    }
  },

  createVersion: async (version) => {
    const response = await fetch(`${API_BASE}/api/versions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(version),
    });

    if (!response.ok) {
      const message = await parseError(response);
      set({ error: message });
      throw new Error(message);
    }

    const created: Version = await response.json();
    set((state) => ({
      versions: [...state.versions, created],
      currentVersionId: created.id,
      error: null,
    }));

    return created;
  },

  restoreVersion: async (versionId) => {
    const response = await fetch(`${API_BASE}/api/versions/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ versionId }),
    });

    if (!response.ok) {
      const message = await parseError(response);
      set({ error: message });
      throw new Error(message);
    }

    const restored: Version = await response.json();

    set((state) => ({
      versions: [...state.versions, restored],
      currentVersionId: restored.id,
      error: null,
    }));

    return restored;
  },

  getCurrentVersion: () => {
    const { versions, currentVersionId } = get();
    return versions.find((v) => v.id === currentVersionId) || null;
  },

  getVersionHistory: () => get().versions,

  clearVersions: () => set({
    versions: [],
    currentVersionId: null,
    projectId: null,
    error: null,
  }),
}));
