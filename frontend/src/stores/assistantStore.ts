import { create } from "zustand";
import type { CatState } from "@/components/cat/CatIllustration";

interface AssistantState {
  id: string;
  name: string;
  catState: CatState;
  pendingApprovals: number;
}

interface AssistantStoreState {
  assistants: AssistantState[];
  selectedId: string | null;
  setAssistants: (assistants: AssistantState[]) => void;
  updateCatState: (id: string, catState: CatState) => void;
  setSelected: (id: string | null) => void;
}

export const useAssistantStore = create<AssistantStoreState>((set) => ({
  assistants: [],
  selectedId: null,
  setAssistants: (assistants) => set({ assistants }),
  updateCatState: (id, catState) =>
    set((state) => ({
      assistants: state.assistants.map((a) => (a.id === id ? { ...a, catState } : a)),
    })),
  setSelected: (id) => set({ selectedId: id }),
}));
