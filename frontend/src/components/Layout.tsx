import { Link, useLocation } from "react-router-dom";
import { ToastContainer } from "./Toast";

interface NavItem {
  to: string;
  label: string;
}

const NAV: NavItem[] = [
  { to: "/", label: "대시보드" },
  { to: "/approvals", label: "승인 인박스" },
  { to: "/history", label: "실행 이력" },
  { to: "/cat-room", label: "고양이 방" },
];

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className="w-52 border-r border-border flex flex-col py-6 px-4 shrink-0">
        <div className="mb-8">
          <span className="text-sm font-semibold tracking-tight">Kefcatic</span>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={[
                "px-3 py-2 rounded-md text-sm transition-colors",
                pathname === item.to
                  ? "bg-gray-100 text-gray-900 font-medium"
                  : "text-gray-500 hover:text-gray-900 hover:bg-gray-50",
              ].join(" ")}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-8 py-8">{children}</div>
      </main>

      <ToastContainer />
    </div>
  );
}
