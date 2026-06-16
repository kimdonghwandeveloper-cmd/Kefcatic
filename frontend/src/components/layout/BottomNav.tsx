import { Link } from "react-router-dom";
import { clsx } from "clsx";

interface BottomNavProps {
  pendingCount: number;
  currentPath: string;
}

const items = [
  {
    to: "/",
    label: "홈",
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
    to: "/assistants",
    label: "비서",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <circle cx="10" cy="7" r="3" />
        <path d="M3 17c0-3.3 3.1-6 7-6s7 2.7 7 6" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    to: "/approvals",
    label: "승인",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <path d="M9 11l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M3 5h14a1 1 0 011 1v10a1 1 0 01-1 1H3a1 1 0 01-1-1V6a1 1 0 011-1z" />
      </svg>
    ),
    badge: true,
  },
  {
    to: "/activity",
    label: "기록",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <path d="M3 10h2l2-6 3 12 2-8 2 4h3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    to: "/settings",
    label: "설정",
    icon: (
      <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-5 w-5">
        <circle cx="10" cy="10" r="3" />
        <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M4.2 15.8l1.4-1.4M14.4 5.6l1.4-1.4" strokeLinecap="round" />
      </svg>
    ),
  },
];

export function BottomNav({ pendingCount, currentPath }: BottomNavProps) {
  return (
    <nav className="fixed bottom-0 inset-x-0 z-40 flex border-t border-[#E2E1DE] bg-white pb-safe">
      {items.map((item) => {
        const isActive =
          item.to === "/" ? currentPath === "/" : currentPath.startsWith(item.to);
        return (
          <Link
            key={item.to}
            to={item.to}
            className={clsx(
              "flex flex-1 flex-col items-center gap-1 py-2 text-[10px] transition-colors",
              isActive ? "text-[#1A1918] font-medium" : "text-[#A8A5A2]"
            )}
          >
            <span className="relative">
              {item.icon}
              {item.badge && pendingCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#1A1918] text-white text-[9px] font-medium">
                  {pendingCount > 9 ? "9+" : pendingCount}
                </span>
              )}
            </span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
