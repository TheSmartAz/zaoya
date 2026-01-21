import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { AuthState, AuthActions, User } from '@/types/auth';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const AUTH_BYPASS = import.meta.env.VITE_BYPASS_AUTH === 'true' || import.meta.env.DEV;
const DEV_TOKEN = 'dev-bypass-token';
const DEV_USER: User = {
  id: 'dev-user',
  email: 'dev@zaoya.app',
  name: 'Dev User',
  avatar_url: null,
  provider: 'dev',
  created_at: new Date().toISOString(),
};

interface AuthStore extends AuthState, AuthActions {}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: AUTH_BYPASS ? DEV_USER : null,
      token: AUTH_BYPASS ? DEV_TOKEN : null,
      isLoading: !AUTH_BYPASS,

      setAuth: (user: User, token: string) => {
        set({ user, token, isLoading: false });
      },

      logout: () => {
        if (AUTH_BYPASS) {
          set({ user: DEV_USER, token: DEV_TOKEN, isLoading: false });
          return;
        }
        set({ user: null, token: null, isLoading: false });
      },

      updateUser: (user: User) => {
        set({ user });
      },

      checkAuth: async () => {
        if (AUTH_BYPASS) {
          set({ user: DEV_USER, token: DEV_TOKEN, isLoading: false });
          return;
        }
        const token = get().token;
        if (!token) {
          set({ isLoading: false });
          return;
        }

        try {
          const response = await fetch(`${API_BASE}/api/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          });

          if (response.ok) {
            const user = await response.json();
            set({ user, isLoading: false });
          } else {
            set({ user: null, token: null, isLoading: false });
          }
        } catch {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'zaoya-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
      }),
      onRehydrateStorage: () => (state) => {
        if (AUTH_BYPASS && state) {
          state.setAuth(DEV_USER, DEV_TOKEN);
        }
      },
    }
  )
);

// Helper to get auth headers
export function getAuthHeaders(): Record<string, string> {
  if (AUTH_BYPASS) {
    return { Authorization: `Bearer ${DEV_TOKEN}` };
  }
  const token = useAuthStore.getState().token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Helper to check if user is authenticated
export function isAuthenticated(): boolean {
  if (AUTH_BYPASS) {
    return true;
  }
  return !!useAuthStore.getState().token;
}
