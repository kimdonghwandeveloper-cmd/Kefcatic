import { useToastStore } from "../stores/toastStore";

export function ToastContainer() {
  const { toasts, dismiss } = useToastStore();

  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
      {toasts.map((t) => (
        <div
          key={t.id}
          onClick={() => dismiss(t.id)}
          className={[
            "px-4 py-3 rounded-lg text-sm cursor-pointer shadow-sm border transition-all",
            t.type === "error"
              ? "bg-white border-gray-300 text-gray-900"
              : t.type === "success"
              ? "bg-gray-900 text-white border-gray-900"
              : "bg-white border-gray-200 text-gray-700",
          ].join(" ")}
        >
          {t.type === "error" && (
            <span className="mr-2 text-gray-500">!</span>
          )}
          {t.message}
        </div>
      ))}
    </div>
  );
}
