import { create } from 'zustand';

interface UiState {
  toastMessage: string | null;
  setToastMessage: (value: string | null) => void;
}

export const useUiStore = create<UiState>((set) => ({
  toastMessage: null,
  setToastMessage: (value) => set({ toastMessage: value }),
}));
