import { Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { approvalsApi } from "@/api/approvals";

export function AppLayout() {
  const { data: pending = [] } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => approvalsApi.list("pending"),
    refetchInterval: 30_000,
  });

  return (
    <div className="flex h-screen overflow-hidden bg-[#f5f5f5]">
      <Sidebar pendingCount={pending.length} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
