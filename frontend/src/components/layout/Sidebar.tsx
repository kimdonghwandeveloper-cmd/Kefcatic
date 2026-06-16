import { clsx } from "clsx";
import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { assistantsApi } from "@/api/assistants";
import { useAssistantStore } from "@/stores/assistantStore";
import { useAuthStore } from "@/stores/authStore";
import { StatusDot } from "@/components/ui/Badge";

const navItems = [
  {
    to: "/",
    end: true,
    label: "대화",
    icon: (
      <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-4 w-4">
        <path d="M2 3h14a1 1 0 011 1v8a1 1 0 01-1 1H5l-3 3V4a1 1 0 011-1z" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    to: "/assistants",
    end: false,
    label: "비서 목록",
    icon: (
      <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-4 w-4">
        <circle cx="9" cy="6" r="3" />
        <path d="M2 16c0-3 3.1-5 7-5s7 2 7 5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    to: "/activity",
    end: false,
    label: "기록",
    icon: (
      <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-4 w-4">
        <circle cx="9" cy="9" r="7" />
        <path d="M9 5v4l2.5 2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    to: "/approvals",
    end: false,
    label: "승인 대기",
    icon: (
      <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-4 w-4">
        <path d="M9 11l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
        <rect x="2" y="4" width="14" height="11" rx="1.5" />
      </svg>
    ),
  },
  {
    to: "/settings",
    end: false,
    label: "설정",
    icon: (
      <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-4 w-4">
        <circle cx="9" cy="9" r="2.5" />
        <path d="M9 1.5v2M9 14.5v2M1.5 9h2M14.5 9h2M3.7 3.7l1.4 1.4M12.9 12.9l1.4 1.4M3.7 14.3l1.4-1.4M12.9 5.1l1.4-1.4" strokeLinecap="round" />
      </svg>
    ),
  },
];

interface SidebarProps {
  pendingCount?: number;
  badgeShake?: boolean;
}

export function Sidebar({ pendingCount = 0, badgeShake = false }: SidebarProps) {
  const { user } = useAuthStore();
  const { selectedId, setSelected } = useAssistantStore();

  const { data: assistants = [] } = useQuery({
    queryKey: ["assistants"],
    queryFn: assistantsApi.list,
  });

  return (
    <aside className="flex h-full w-[260px] shrink-0 flex-col bg-[#F5F4F2] border-r border-[#E2E1DE]">
      {/* Logo */}
      <div className="flex h-16 items-center px-6 border-b border-[#E2E1DE]">
        <span className="font-heading text-[16px] font-semibold tracking-tight text-[#1A1918]">
          Kefcatic
        </span>
      </div>

      {/* Primary nav */}
      <nav className="px-3 pt-4 pb-2 space-y-0.5">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-button px-3 py-2.5 text-[14px] transition-colors duration-fast",
                isActive
                  ? "bg-[#EFEFED] text-[#1A1918] font-medium"
                  : "text-[#6B6966] hover:bg-[#EFEFED] hover:text-[#1A1918]"
              )
            }
          >
            <span className="shrink-0 relative">
              {item.icon}
              {item.to === "/approvals" && pendingCount > 0 && (
                <span
                  className={clsx(
                    "absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#1A1918] text-white text-[9px] font-medium",
                    badgeShake && "badge-shake"
                  )}
                >
                  {pendingCount > 9 ? "9+" : pendingCount}
                </span>
              )}
            </span>
            <span className="text-[14px]">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Divider */}
      <div className="mx-3 border-t border-[#E2E1DE] my-3" />

      {/* Assistant list */}
      <div className="flex-1 overflow-y-auto no-scrollbar px-3">
        <div className="flex items-center justify-between px-3 py-1.5 mb-1">
          <span className="text-[11px] font-medium tracking-widest text-[#A8A5A2] uppercase">
            비서
          </span>
          <NavLink
            to="/assistants/new"
            className="flex h-5 w-5 items-center justify-center rounded text-[#A8A5A2] hover:text-[#1A1918] hover:bg-[#EFEFED] transition-colors"
            title="새 비서 만들기"
          >
            <svg viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-3.5 w-3.5">
              <path d="M7 2v10M2 7h10" strokeLinecap="round" />
            </svg>
          </NavLink>
        </div>

        <div className="space-y-0.5">
          {assistants.map((assistant) => (
            <button
              key={assistant.id}
              onClick={() => setSelected(selectedId === assistant.id ? null : assistant.id)}
              className={clsx(
                "w-full flex items-center gap-3 rounded-button px-3 py-2.5 text-left transition-colors duration-fast",
                selectedId === assistant.id
                  ? "bg-[#EFEFED] text-[#1A1918]"
                  : "text-[#6B6966] hover:bg-[#EFEFED] hover:text-[#1A1918]"
              )}
            >
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#E2E1DE] text-[11px] font-semibold text-[#6B6966]">
                {assistant.name.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[14px] font-medium truncate">{assistant.name}</p>
                <p className="text-[12px] text-[#A8A5A2] truncate">{assistant.role_type ?? "일반 비서"}</p>
              </div>
              <StatusDot active={assistant.is_active} />
            </button>
          ))}
        </div>
      </div>

      {/* User profile */}
      <div className="border-t border-[#E2E1DE] px-3 py-4">
        <div className="flex items-center gap-3 px-3 py-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#2D2B29] text-white text-[12px] font-semibold">
            {user?.name?.charAt(0) ?? user?.email?.charAt(0) ?? "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[14px] font-medium text-[#1A1918] truncate">
              {user?.name ?? user?.email ?? "사용자"}
            </p>
            <p className="text-[12px] text-[#A8A5A2]">Pro 플랜</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
