import { useEffect, useState } from "react";
import { create } from "zustand";

type ToastType = "default" | "error";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastStore {
  toasts: Toast[];
  push: (message: string, type?: ToastType) => void;
  remove: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  push: (message, type = "default") => {
    const id = crypto.randomUUID();
    set((s) => ({ toasts: [...s.toasts, { id, message, type }] }));
    setTimeout(() => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })), 3500);
  },
  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export const toast = {
  show: (message: string) => useToastStore.getState().push(message),
  error: (message: string) => useToastStore.getState().push(message, "error"),
};

function ToastItem({ item, onDismiss }: { item: Toast; onDismiss: () => void }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  return (
    <div
      className={`
        flex items-center gap-3 rounded-card border bg-white px-4 py-3 shadow-sm
        transition-all duration-250 ease-in-out
        ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}
        ${item.type === "error" ? "border-[#C0392B]" : "border-[#E2E1DE]"}
      `}
    >
      {item.type === "error" && <span className="text-[13px] text-[#C0392B]">⚠</span>}
      <span className="text-[13px] text-[#1A1918]">{item.message}</span>
      <button
        onClick={onDismiss}
        className="ml-auto text-[#A8A5A2] hover:text-[#1A1918] transition-colors text-[11px]"
      >
        ✕
      </button>
    </div>
  );
}

export function ToastContainer() {
  const { toasts, remove } = useToastStore();

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 w-72 pointer-events-none">
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <ToastItem item={t} onDismiss={() => remove(t.id)} />
        </div>
      ))}
    </div>
  );
}
