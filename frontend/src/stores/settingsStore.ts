import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface Settings {
  language: string
  auto_detect_language: boolean
  preferred_model: string
  model_region: string
  default_design_system: Record<string, unknown> | null
  email_enabled: boolean
  email_submission_notifications: boolean
  email_weekly_analytics: boolean
  email_project_updates: boolean
  notification_email: string | null
  browser_notifications_enabled: boolean
  browser_notify_submissions: boolean
  browser_notify_published: boolean
  browser_notify_generation: boolean
}

interface SettingsStore extends Settings {
  isLoading: boolean
  error: string | null
  loadSettings: () => Promise<void>
  saveSettings: (settings: Partial<Settings>) => Promise<void>
}

const DEFAULT_SETTINGS: Settings = {
  language: 'en',
  auto_detect_language: true,
  preferred_model: 'glm-4.7',
  model_region: 'auto',
  default_design_system: null,
  email_enabled: true,
  email_submission_notifications: true,
  email_weekly_analytics: false,
  email_project_updates: false,
  notification_email: null,
  browser_notifications_enabled: true,
  browser_notify_submissions: true,
  browser_notify_published: true,
  browser_notify_generation: false,
}

const extractSettings = (state: Settings | SettingsStore): Settings => ({
  language: state.language,
  auto_detect_language: state.auto_detect_language,
  preferred_model: state.preferred_model,
  model_region: state.model_region,
  default_design_system: state.default_design_system,
  email_enabled: state.email_enabled,
  email_submission_notifications: state.email_submission_notifications,
  email_weekly_analytics: state.email_weekly_analytics,
  email_project_updates: state.email_project_updates,
  notification_email: state.notification_email,
  browser_notifications_enabled: state.browser_notifications_enabled,
  browser_notify_submissions: state.browser_notify_submissions,
  browser_notify_published: state.browser_notify_published,
  browser_notify_generation: state.browser_notify_generation,
})

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set, get) => ({
      ...DEFAULT_SETTINGS,
      isLoading: false,
      error: null,

      async loadSettings() {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${API_BASE_URL}/api/settings`)
          if (!response.ok) {
            throw new Error(`Failed to load settings: ${response.statusText}`)
          }
          const settings = (await response.json()) as Settings
          set({ ...DEFAULT_SETTINGS, ...settings, isLoading: false })
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : 'Failed to load settings',
            isLoading: false,
          })
        }
      },

      async saveSettings(updates: Partial<Settings>) {
        const nextSettings = { ...extractSettings(get()), ...updates }
        set({ ...updates })
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`${API_BASE_URL}/api/settings`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nextSettings),
          })
          if (!response.ok) {
            throw new Error(`Failed to save settings: ${response.statusText}`)
          }
          const settings = (await response.json()) as Settings
          set({ ...DEFAULT_SETTINGS, ...settings, isLoading: false })
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : 'Failed to save settings',
            isLoading: false,
          })
        }
      },
    }),
    {
      name: 'settings-store',
      partialize: (state) => extractSettings(state),
    }
  )
)
