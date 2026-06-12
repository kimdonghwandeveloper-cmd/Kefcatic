import { useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "./Sidebar";
import { BottomNav } from "./BottomNav";
import { TopBar } from "./TopBar";
import { ToastContainer } from "@/components/ui/Toast";
import { approvalsApi } from "@/api/approvals";

export function AppLayout() {
  const location = useLocation();
  const prevCount = useRef(0);
  const [badgeShake, setBadgeShake] = useState(false);

  const { data: pending = [] } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => approvalsApi.list("pending"),
    refetchInterval: 30_000,
  });

  // Shake badge when pending count increases
  useEffect(() => {
    if (pending.length > prevCount.current) {
      setBadgeShake(true);
      const t = setTimeout(() => setBadgeShake(false), 500);
      return () => clearTimeout(t);
    }
    prevCount.current = pending.length;
  }, [pending.length]);

  return (
    <div className="flex h-screen overflow-hidden bg-[#f5f5f5]">
      {/* Sidebar — hidden below lg */}
      <div className="hidden lg:flex">
        <Sidebar pendingCount={pending.length} badgeShake={badgeShake} />
      </div>

      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6 pb-20 lg:pb-6">
          <Outlet />
        </main>

        {/* Mobile bottom nav */}
        <div className="lg:hidden">
          <BottomNav pendingCount={pending.length} currentPath={location.pathname} />
        </div>
      </div>

      <ToastContainer />
    </div>
  );
}
