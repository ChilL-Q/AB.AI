import { create } from "zustand";
import { api, login as apiLogin, logout as apiLogout } from "../lib/api";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  team_id: string | null;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  setUser: (user: User | null) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: true,
  setUser: (user) => set({ user, loading: false }),
  login: async (email, password) => {
    await apiLogin(email, password);
    const { data } = await api.get("/me");
    set({ user: data, loading: false });
  },
  logout: async () => {
    await apiLogout();
    set({ user: null, loading: false });
  },
  fetchMe: async () => {
    try {
      const { data } = await api.get("/me");
      set({ user: data, loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },
}));