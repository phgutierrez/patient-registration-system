import { create } from 'zustand';

interface User {
  id: number;
  username: string;
  full_name: string;
  role: 'admin' | 'medico' | 'enfermeiro';
}

interface AuthState {
  currentUser: User | null;
  setCurrentUser: (user: User | null) => void;
  setAccessToken: (token: string | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  currentUser: null,
  setCurrentUser: (user) => set({ currentUser: user }),
  setAccessToken: (token) => {
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  },
}));
