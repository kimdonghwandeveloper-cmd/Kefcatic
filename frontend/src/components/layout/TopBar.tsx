import { useQuery } from "@tanstack/react-query";
import { assistantsApi } from "@/api/assistants";
import { useAssistantStore } from "@/stores/assistantStore";
import { useAuthStore } from "@/stores/authStore";
import { authApi } from "@/api/auth";
import { Button } from "@/components/ui/Button";

export function TopBar() {
  const { user, clearAuth } = useAuthStore();
  const { selectedId } = useAssistantStore();

  const { data: allAssistants = [] } = useQuery({
    queryKey: ["assistants"],
    queryFn: assistantsApi.list,
  });

  const selected = allAssistants.find((a) => a.id === selectedId);

  const handleLogout = async () => {
    await authApi.logout();
    clearAuth();
  };

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-[#E2E1DE] bg-white px-6">
      <div className="flex items-center gap-3">
        {selected ? (
          <>
            <span className="font-heading text-[15px] font-semibold text-[#1A1918]">{selected.name}</span>
            <span className="text-[#E2E1DE]">·</span>
            <span className="text-[13px] text-[#6B6966]">
              {selected.role_type ?? "일반 비서"}
            </span>
            <span className="inline-flex items-center gap-1 rounded-badge bg-[#EFEFED] px-2 py-0.5 text-[11px] font-medium text-[#6B6966]">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#2D2B29]" />
              {selected.is_active ? "활성 중" : "비활성"}
            </span>
          </>
        ) : (
          <span className="font-heading text-[15px] font-semibold text-[#1A1918]">대화</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {user && (
          <span className="text-[13px] text-[#6B6966]">{user.name ?? user.email}</span>
        )}
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          로그아웃
        </Button>
      </div>
    </header>
  );
}
