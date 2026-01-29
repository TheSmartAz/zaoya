import { create } from 'zustand'
import type { VersionDetail, VersionSummary, VersionListResponse, VersionQuota } from '@/types/version'
import type { Branch, BranchListResponse } from '@/types/branch'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface VersionStore {
  versions: VersionSummary[]
  branches: Branch[]
  activeBranchId: string | null
  quota: VersionQuota | null
  activeVersionId: string | null
  isLoading: boolean
  error: string | null

  loadVersions: (projectId: string, branchId?: string | null) => Promise<void>
  loadBranches: (projectId: string) => Promise<void>
  activateBranch: (projectId: string, branchId: string) => Promise<void>
  createBranch: (
    projectId: string,
    versionId: string,
    payload: { name: string; label?: string; set_active?: boolean }
  ) => Promise<Branch | null>
  getVersionDetail: (
    projectId: string,
    versionId: string,
    options?: { includeDiff?: boolean }
  ) => Promise<VersionDetail | null>
  pinVersion: (projectId: string, versionId: string, pin: boolean) => Promise<VersionSummary | null>
  rollbackPages: (
    projectId: string,
    versionId: string,
    pageIds: string[]
  ) => Promise<VersionSummary | null>
  restoreVersion: (projectId: string, versionId: string) => Promise<VersionSummary | null>
  setActiveVersion: (versionId: string | null) => void
}

export const useVersionStore = create<VersionStore>((set, get) => ({
  versions: [],
  branches: [],
  activeBranchId: null,
  quota: null,
  activeVersionId: null,
  isLoading: false,
  error: null,

  setActiveVersion: (versionId) => set({ activeVersionId: versionId }),

  loadVersions: async (projectId, branchId) => {
    set({ isLoading: true, error: null })
    try {
      const query = branchId ? `?branch_id=${branchId}` : ''
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/versions${query}`
      )
      if (!response.ok) throw new Error('Failed to load versions')
      const data = (await response.json()) as VersionListResponse
      set({ versions: data.versions || [], quota: data.quota || null, isLoading: false })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load versions',
        isLoading: false,
        quota: null,
      })
    }
  },

  loadBranches: async (projectId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/branches`)
      if (!response.ok) throw new Error('Failed to load branches')
      const data = (await response.json()) as BranchListResponse
      set({
        branches: data.branches || [],
        activeBranchId: data.active_branch_id || null,
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load branches',
      })
    }
  },

  activateBranch: async (projectId, branchId) => {
    const response = await fetch(
      `${API_BASE_URL}/api/projects/${projectId}/branches/${branchId}/activate`,
      { method: 'POST' }
    )
    if (!response.ok) throw new Error('Failed to activate branch')
    const branch = (await response.json()) as Branch
    set({ activeBranchId: branch.id })
  },

  createBranch: async (projectId, versionId, payload) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/versions/${versionId}/branch`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }
      )
      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || 'Failed to create branch')
      }
      const branch = (await response.json()) as Branch
      set((state) => ({
        branches: [...state.branches, branch],
        activeBranchId: payload.set_active === false ? state.activeBranchId : branch.id,
      }))
      return branch
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to create branch' })
      return null
    }
  },

  getVersionDetail: async (projectId, versionId, options) => {
    try {
      const query = options?.includeDiff ? '?include_diff=true' : ''
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/versions/${versionId}${query}`
      )
      if (!response.ok) throw new Error('Failed to load version')
      return (await response.json()) as VersionDetail
    } catch {
      return null
    }
  },

  pinVersion: async (projectId, versionId, pin) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/versions/${versionId}/pin`,
        { method: pin ? 'POST' : 'DELETE' }
      )
      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || 'Failed to update pin')
      }
      const version = (await response.json()) as VersionSummary
      const versions = get().versions.map((item) =>
        item.id === version.id ? version : item
      )
      set({ versions })
      return version
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to update pin' })
      return null
    }
  },

  rollbackPages: async (projectId, versionId, pageIds) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/versions/${versionId}/rollback`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ page_ids: pageIds }),
        }
      )
      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || 'Failed to rollback pages')
      }
      const version = (await response.json()) as VersionSummary
      await get().loadVersions(projectId, get().activeBranchId)
      return version
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to rollback pages' })
      return null
    }
  },

  restoreVersion: async (projectId, versionId) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/projects/${projectId}/versions/${versionId}/restore`,
        { method: 'POST' }
      )
      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || 'Failed to restore version')
      }
      const version = (await response.json()) as VersionSummary
      await get().loadVersions(projectId, get().activeBranchId)
      return version
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to restore version' })
      return null
    }
  },
}))
