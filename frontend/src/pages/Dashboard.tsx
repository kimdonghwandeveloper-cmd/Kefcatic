import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { assistantsApi } from "@/api/assistants";
import { approvalsApi } from "@/api/approvals";
import { auditApi } from "@/api/audit";
import { Card } from "@/components/ui/Card";
import { Divider } from "@/components/ui/Divider";

function SummaryCard({
  label,
  value,
  sub,
  onClick,
  warn,
}: {
  label: string;
  value: number;
  sub?: string;
  onClick?: () => void;
  warn?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={!onClick}
      className="flex flex-col gap-1 rounded-card border border-[#e8e8e8] bg-white p-5 text-left transition-colors hover:border-[#d1d1d1] disabled:cursor-default"
    >
      <span className="text-xs text-[#9a9a9a]">{label}</span>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold text-[#0a0a0a]">{value}</span>
        {warn && value > 0 && (
          <span className="text-sm text-[#0a0a0a]">⚠</span>
        )}
      </div>
      {sub && <span className="text-xs text-[#9a9a9a]">{sub}</span>}
    </button>
  );
}

const STATUS_LABEL: Record<string, string> = {
  pending: "대기 중",
  running: "실행 중",
  waiting_approval: "승인 대기",
  completed: "완료",
  failed: "실패",
  cancelled: "취소됨",
};

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: assistants = [] } = useQuery({
    queryKey: ["assistants"],
    queryFn: assistantsApi.list,
  });
  const { data: pending = [] } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => approvalsApi.list("pending"),
  });
  const { data: taskRuns } = useQuery({
    queryKey: ["audit", "task-runs"],
    queryFn: () => auditApi.listTaskRuns({ size: 5 }),
  });

  const activeCount = assistants.filter((a) => a.is_active).length;
  const recentRuns = taskRuns?.items ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[#0a0a0a]">대시보드</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <SummaryCard
          label="오늘 처리된 일"
          value={recentRuns.filter((r) => r.status === "completed").length}
          sub="완료된 태스크"
        />
        <SummaryCard
          label="확인할 일"
          value={pending.length}
          sub="승인 대기 중"
          onClick={pending.length > 0 ? () => navigate("/approvals") : undefined}
        />
        <SummaryCard
          label="실행 중인 비서"
          value={activeCount}
          sub={`전체 ${assistants.length}개 중`}
        />
        <SummaryCard
          label="연결 문제"
          value={0}
          sub="모든 앱 정상"
          warn
        />
      </div>

      {/* Approvals Preview */}
      {pending.length > 0 && (
        <Card padding="md">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[#0a0a0a]">승인 대기</h2>
            <button
              onClick={() => navigate("/approvals")}
              className="text-xs text-[#5c5c5c] hover:text-[#0a0a0a] transition-colors"
            >
              전체 보기 →
            </button>
          </div>
          <div className="space-y-2">
            {pending.slice(0, 3).map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-button bg-[#f5f5f5] px-3 py-2"
              >
                <div className="flex flex-col">
                  <span className="text-sm text-[#0a0a0a]">
                    {item.action?.action_type ?? "액션"}
                  </span>
                  <span className="text-xs text-[#9a9a9a]">
                    {new Date(item.requested_at).toLocaleString("ko-KR")}
                  </span>
                </div>
                <span className="text-xs text-[#5c5c5c]">대기 중</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recent Activity */}
      <Card padding="md">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[#0a0a0a]">최근 활동</h2>
          <button
            onClick={() => navigate("/activity")}
            className="text-xs text-[#5c5c5c] hover:text-[#0a0a0a] transition-colors"
          >
            전체 보기 →
          </button>
        </div>
        {recentRuns.length === 0 ? (
          <p className="text-sm text-[#9a9a9a] py-4 text-center">아직 실행 기록이 없어요.</p>
        ) : (
          <div className="divide-y divide-[#e8e8e8]">
            {recentRuns.map((run) => (
              <div key={run.id} className="flex items-center justify-between py-2.5">
                <div className="flex flex-col">
                  <span className="text-sm text-[#0a0a0a]">{run.assistant_name ?? "비서"}</span>
                  <span className="text-xs text-[#9a9a9a]">
                    {run.started_at
                      ? new Date(run.started_at).toLocaleString("ko-KR")
                      : "-"}
                  </span>
                </div>
                <span className="text-xs text-[#5c5c5c]">
                  {STATUS_LABEL[run.status] ?? run.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
