import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { assistantsApi } from "../api/assistants";
import { approvalsApi } from "../api/approvals";
import { auditApi } from "../api/audit";
import { StatusBadge } from "../components/StatusBadge";

export function DashboardPage() {
  const { data: assistants = [] } = useQuery({
    queryKey: ["assistants"],
    queryFn: assistantsApi.list,
  });

  const { data: pendingApprovals = [] } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => approvalsApi.list("pending"),
  });

  const { data: recentRuns } = useQuery({
    queryKey: ["task-runs", "recent"],
    queryFn: () => auditApi.listTaskRuns({ page: 1 }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold">대시보드</h1>
        <Link
          to="/assistants/new"
          className="px-3 py-1.5 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-700 transition-colors"
        >
          + 새 비서
        </Link>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard
          label="활성 비서"
          value={assistants.filter((a) => a.is_active).length}
        />
        <StatCard
          label="승인 대기"
          value={pendingApprovals.length}
          highlight={pendingApprovals.length > 0}
          linkTo="/approvals"
        />
        <StatCard
          label="오늘 실행"
          value={recentRuns?.items.filter((r) => isToday(r.started_at)).length ?? 0}
        />
      </div>

      {/* Active assistants */}
      <section className="mb-8">
        <h2 className="text-sm font-medium text-gray-500 mb-3">활성 비서</h2>
        {assistants.length === 0 ? (
          <EmptyState message="아직 비서가 없어요." cta="첫 비서 만들기" ctaTo="/assistants/new" />
        ) : (
          <div className="flex flex-col gap-2">
            {assistants.map((a) => (
              <Link
                key={a.id}
                to={`/assistants/${a.id}`}
                className="flex items-center justify-between px-4 py-3 border border-border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div>
                  <p className="text-sm font-medium">{a.name}</p>
                  <p className="text-xs text-gray-400">{a.role_type ?? "—"}</p>
                </div>
                <StatusBadge status={a.is_active ? "completed" : "rejected"} />
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Recent runs */}
      <section>
        <h2 className="text-sm font-medium text-gray-500 mb-3">최근 실행</h2>
        {(recentRuns?.items ?? []).length === 0 ? (
          <p className="text-sm text-gray-400">실행 이력이 없어요.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {(recentRuns?.items ?? []).slice(0, 5).map((r) => (
              <Link
                key={r.id}
                to={`/history/${r.id}`}
                className="flex items-center justify-between px-4 py-3 border border-border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div>
                  <p className="text-xs text-gray-500">
                    {r.started_at ? new Date(r.started_at).toLocaleString("ko-KR") : "—"}
                  </p>
                </div>
                <StatusBadge status={r.status} />
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({
  label,
  value,
  highlight,
  linkTo,
}: {
  label: string;
  value: number;
  highlight?: boolean;
  linkTo?: string;
}) {
  const inner = (
    <div
      className={`px-4 py-4 border rounded-lg ${
        highlight ? "border-gray-900" : "border-border"
      }`}
    >
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  );
  return linkTo ? <Link to={linkTo}>{inner}</Link> : <div>{inner}</div>;
}

function EmptyState({
  message,
  cta,
  ctaTo,
}: {
  message: string;
  cta: string;
  ctaTo: string;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-10 border border-dashed border-gray-200 rounded-lg">
      <p className="text-sm text-gray-400">{message}</p>
      <Link
        to={ctaTo}
        className="text-sm font-medium text-gray-900 underline underline-offset-2"
      >
        {cta}
      </Link>
    </div>
  );
}

function isToday(dateStr: string | null): boolean {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}
