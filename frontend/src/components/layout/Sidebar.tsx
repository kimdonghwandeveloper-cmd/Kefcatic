import { clsx } from "clsx";
import { NavLink } from "react-router-dom";

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    to: "/",
    label: "대시보드",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <rect x="2" y="2" width="7" height="7" rx="1" />
        <rect x="11" y="2" width="7" height="7" rx="1" />
        <rect x="2" y="11" width="7" height="7" rx="1" />
        <rect x="11" y="11" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    to: "/cat-room",
    label: "Cat Room",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <ellipse cx="10" cy="12" rx="7" ry="5" />
        <path d="M5 10 Q4 5 6 3 L8 7" strokeLinecap="round" />
        <path d="M15 10 Q16 5 14 3 L12 7" strokeLinecap="round" />
        <circle cx="8" cy="10" r="1" fill="currentColor" stroke="none" />
        <circle cx="12" cy="10" r="1" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
  {
    to: "/assistants",
    label: "내 비서",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <circle cx="10" cy="7" r="3" />
        <path d="M3 17c0-3.3 3.1-6 7-6s7 2.7 7 6" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    to: "/approvals",
    label: "승인 대기",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <path d="M9 11l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M3 5h14a1 1 0 011 1v10a1 1 0 01-1 1H3a1 1 0 01-1-1V6a1 1 0 011-1z" />
      </svg>
    ),
  },
  {
    to: "/activity",
    label: "활동 기록",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <path d="M3 10h2l2-6 3 12 2-8 2 4h3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    to: "/connectors",
    label: "앱 연결",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <path d="M10 3v4M10 13v4M3 10h4M13 10h4" strokeLinecap="round" />
        <circle cx="10" cy="10" r="3" />
      </svg>
    ),
  },
];

interface SidebarProps {
  pendingCount?: number;
  collapsed?: boolean;
}

export function Sidebar({ pendingCount = 0, collapsed = false }: SidebarProps) {
  return (
    <aside
      className={clsx(
        "flex h-full flex-col border-r border-[#e8e8e8] bg-white transition-all",
        collapsed ? "w-14" : "w-52"
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center border-b border-[#e8e8e8] px-4 gap-2">
        <span className="text-lg select-none">🐱</span>
        {!collapsed && (
          <span className="text-sm font-semibold text-[#0a0a0a] tracking-tight">Kefcatic</span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-button px-2 py-2 text-sm transition-colors",
                isActive
                  ? "bg-[#f5f5f5] text-[#0a0a0a] font-medium"
                  : "text-[#5c5c5c] hover:bg-[#f5f5f5] hover:text-[#0a0a0a]"
              )
            }
          >
            <span className="shrink-0 relative">
              {item.icon}
              {item.to === "/approvals" && pendingCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#0a0a0a] text-[#fafafa] text-[10px] font-medium">
                  {pendingCount > 9 ? "9+" : pendingCount}
                </span>
              )}
            </span>
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
