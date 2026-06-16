import { useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "./Sidebar";
import { BottomNav } from "./BottomNav";
import { TopBar } from "./TopBar";
import { CatRoomPanel } from "./CatRoomPanel";
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

  useEffect(() => {
    if (pending.length > prevCount.current) {
      setBadgeShake(true);
      const t = setTimeout(() => setBadgeShake(false), 500);
      return () => clearTimeout(t);
    }
    prevCount.current = pending.length;
  }, [pending.length]);

  return (
    <div className="flex h-screen overflow-hidden bg-[#F5F4F2]">
      {/* Left sidebar — desktop only */}
      <div className="hidden lg:flex">
        <Sidebar pendingCount={pending.length} badgeShake={badgeShake} />
      </div>

      {/* Center column */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-8 pb-24 lg:pb-8">
          <Outlet />
        </main>

        {/* Mobile bottom nav */}
        <div className="lg:hidden">
          <BottomNav pendingCount={pending.length} currentPath={location.pathname} />
        </div>
      </div>

      {/* Right panel — desktop only */}
      <div className="hidden lg:flex">
        <CatRoomPanel />
      </div>

      <ToastContainer />
    </div>
  );
}
