import create from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '@api/client';

interface AuthState {
  token: string | null;
  user: any | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        try {
          const { access_token } = await authApi.login(username, password);
          set({ token: access_token, isAuthenticated: true });
          await useAuthStore.getState().fetchUser();
        } catch (error) {
          console.error('Login failed:', error);
          throw error;
        }
      },

      logout: () => {
        try {
          authApi.logout();
        } finally {
          set({ token: null, user: null, isAuthenticated: false });
        }
      },

      fetchUser: async () => {
        try {
          const user = await authApi.me();
          set({ user });
        } catch (error) {
          console.error('Failed to fetch user:', error);
          throw error;
        }
      },
    }),
    {
      name: 'auth-storage',
      getStorage: () => localStorage,
    }
  )
); 