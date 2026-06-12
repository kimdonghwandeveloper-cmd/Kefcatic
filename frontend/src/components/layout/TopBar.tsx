import { useAuthStore } from "@/stores/authStore";
import { authApi } from "@/api/auth";
import { Button } from "@/components/ui/Button";

interface TopBarProps {
  title?: string;
}

export function TopBar({ title }: TopBarProps) {
  const { user, clearAuth } = useAuthStore();

  const handleLogout = async () => {
    await authApi.logout();
    clearAuth();
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-[#e8e8e8] bg-white px-6">
      {title && <h1 className="text-sm font-semibold text-[#0a0a0a]">{title}</h1>}
      {!title && <div />}
      <div className="flex items-center gap-3">
        {user && (
          <span className="text-sm text-[#5c5c5c]">{user.name ?? user.email}</span>
        )}
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          로그아웃
        </Button>
      </div>
    </header>
  );
}
