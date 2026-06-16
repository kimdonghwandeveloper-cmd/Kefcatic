import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { assistantsApi } from "@/api/assistants";
import { approvalsApi } from "@/api/approvals";
import { auditApi } from "@/api/audit";
import { useAssistantStore } from "@/stores/assistantStore";
import { IsometricRoom } from "@/components/cat/IsometricRoom";
import { Button } from "@/components/ui/Button";

function MetricCard({
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
      className="flex flex-col gap-1 rounded-card border border-[#E2E1DE] bg-white p-6 text-left shadow-card transition-colors hover:border-[#2D2B29] disabled:cursor-default disabled:hover:border-[#E2E1DE]"
    >
      <span className="text-[12px] font-medium tracking-widest text-[#A8A5A2] uppercase">{label}</span>
      <div className="flex items-baseline gap-2 mt-2">
        <span className="text-[36px] font-semibold leading-none text-[#1A1918]">{value}</span>
        {warn && value > 0 && (
          <span className="text-[14px] text-[#C0392B]">주의</span>
        )}
      </div>
      {sub && <span className="text-[14px] text-[#A8A5A2] mt-1">{sub}</span>}
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

const STATUS_COLOR: Record<string, string> = {
  completed: "text-[#6B6966]",
  failed: "text-[#C0392B]",
  running: "text-[#1A1918] font-medium",
  waiting_approval: "text-[#2D2B29] font-medium",
  pending: "text-[#A8A5A2]",
  cancelled: "text-[#A8A5A2]",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { selectedId } = useAssistantStore();

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
  const selectedAssistant = assistants.find((a) => a.id === selectedId);

  /* ── Empty state ── */
  if (assistants.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] gap-8 text-center">
        <IsometricRoom className="w-full max-w-[400px] opacity-85" />
        <div className="space-y-3">
          <h2 className="font-heading text-[28px] font-semibold text-[#1A1918]">아직 비서가 없어요</h2>
          <p className="text-[16px] text-[#6B6966]">
            첫 번째 비서를 만들고 반복 작업을 자동화해보세요.
          </p>
        </div>
        <Button size="lg" onClick={() => navigate("/assistants/new")}>
          첫 번째 비서 만들기
        </Button>
        <div className="flex gap-8 mt-2">
          {[
            { icon: "✦", text: "유튜브 댓글 관리" },
            { icon: "✦", text: "메일 자동 응답" },
            { icon: "✦", text: "파일 자동 정리" },
          ].map((hint) => (
            <div key={hint.text} className="flex items-center gap-1.5 text-[14px] text-[#A8A5A2]">
              <span className="text-[11px]">{hint.icon}</span>
              {hint.text}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {selectedAssistant && (
        <div className="flex items-center gap-2 -mb-2">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#2D2B29]" />
          <span className="text-[13px] text-[#6B6966]">
            <span className="font-medium text-[#1A1918]">{selectedAssistant.name}</span>의 현황
          </span>
        </div>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label="오늘 완료"
          value={recentRuns.filter((r) => r.status === "completed").length}
          sub="처리된 태스크"
        />
        <MetricCard
          label="승인 대기"
          value={pending.length}
          sub={pending.length > 0 ? "확인 필요" : "모두 처리됨"}
          onClick={pending.length > 0 ? () => navigate("/approvals") : undefined}
        />
        <MetricCard
          label="활성 비서"
          value={activeCount}
          sub={`전체 ${assistants.length}명`}
        />
        <MetricCard
          label="연결 문제"
          value={0}
          sub="모든 앱 정상"
          warn
        />
      </div>

      {/* Pending approvals preview */}
      {pending.length > 0 && (
        <div className="rounded-card border border-[#E2E1DE] bg-white shadow-card overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#E2E1DE]">
            <h2 className="text-[13px] font-semibold text-[#1A1918]">승인 대기</h2>
            <button
              onClick={() => navigate("/approvals")}
              className="text-[13px] text-[#6B6966] hover:text-[#1A1918] transition-colors"
            >
              전체 보기 →
            </button>
          </div>
          <div className="divide-y divide-[#E2E1DE]">
            {pending.slice(0, 3).map((item) => (
              <div key={item.id} className="flex items-center justify-between px-5 py-3">
                <div className="flex flex-col gap-0.5">
                  <span className="text-[13px] font-medium text-[#1A1918]">
                    {item.action?.action_type ?? "액션"}
                  </span>
                  <span className="text-[11px] text-[#A8A5A2]">
                    {new Date(item.requested_at).toLocaleString("ko-KR")}
                  </span>
                </div>
                <span className="rounded-badge bg-[#EFEFED] px-2 py-0.5 text-[11px] font-medium text-[#6B6966]">
                  대기 중
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent activity */}
      <div className="rounded-card border border-[#E2E1DE] bg-white shadow-card overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#E2E1DE]">
          <h2 className="text-[13px] font-semibold text-[#1A1918]">최근 활동</h2>
          <button
            onClick={() => navigate("/activity")}
            className="text-[13px] text-[#6B6966] hover:text-[#1A1918] transition-colors"
          >
            전체 보기 →
          </button>
        </div>

        {recentRuns.length === 0 ? (
          <div className="py-10 text-center">
            <p className="text-[13px] text-[#A8A5A2]">아직 실행 기록이 없어요.</p>
          </div>
        ) : (
          <div className="divide-y divide-[#E2E1DE]">
            {recentRuns.map((run) => (
              <div key={run.id} className="flex items-center justify-between px-5 py-3">
                <div className="flex flex-col gap-0.5">
                  <span className="text-[13px] font-medium text-[#1A1918]">
                    {run.assistant_name ?? "비서"}
                  </span>
                  <span className="text-[11px] text-[#A8A5A2]">
                    {run.started_at
                      ? new Date(run.started_at).toLocaleString("ko-KR")
                      : "-"}
                  </span>
                </div>
                <span className={`text-[13px] ${STATUS_COLOR[run.status] ?? "text-[#6B6966]"}`}>
                  {STATUS_LABEL[run.status] ?? run.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
