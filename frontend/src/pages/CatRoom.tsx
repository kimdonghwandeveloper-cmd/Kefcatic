import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { assistantsApi } from "../api/assistants";
import { approvalsApi } from "../api/approvals";
import { auditApi } from "../api/audit";
import { CatIllustration, type CatState } from "../components/CatIllustration";
import { StatusBadge } from "../components/StatusBadge";

export function CatRoomPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: assistants = [] } = useQuery({
    queryKey: ["assistants"],
    queryFn: assistantsApi.list,
    refetchInterval: 15_000,
  });

  return (
    <div>
      <h1 className="text-lg font-semibold mb-2">고양이 방</h1>
      <p className="text-sm text-gray-400 mb-8">비서들이 일하고 있어요.</p>

      {assistants.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 border border-dashed border-gray-200 rounded-xl">
          <p className="text-sm text-gray-400">비서가 없어요.</p>
          <Link
            to="/assistants/new"
            className="text-sm font-medium text-gray-900 underline underline-offset-2"
          >
            첫 비서 만들기
          </Link>
        </div>
      ) : (
        <div className="flex gap-8">
          {/* Cat grid */}
          <div className="flex-1 grid grid-cols-2 gap-6">
            {assistants.map((a) => (
              <CatCard
                key={a.id}
                assistant={a}
                isSelected={selectedId === a.id}
                onClick={() => setSelectedId(selectedId === a.id ? null : a.id)}
              />
            ))}
          </div>

          {/* Side panel */}
          {selectedId && (
            <AssistantPanel
              assistantId={selectedId}
              onClose={() => setSelectedId(null)}
            />
          )}
        </div>
      )}
    </div>
  );
}

interface CatCardProps {
  assistant: { id: string; name: string; role_type: string | null; is_active: boolean };
  isSelected: boolean;
  onClick: () => void;
}

function CatCard({ assistant, isSelected, onClick }: CatCardProps) {
  const { data: stateData } = useQuery({
    queryKey: ["assistant-state", assistant.id],
    queryFn: () => assistantsApi.getState(assistant.id),
    refetchInterval: 5_000,
    enabled: assistant.is_active,
  });

  const catState: CatState = stateData?.cat_state ?? (assistant.is_active ? "idle" : "idle");
  const statusText: string = stateData?.status_text ?? (assistant.is_active ? "쉬고 있어요." : "비활성화됐어요.");

  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-3 p-5 border rounded-xl text-left transition-all hover:bg-gray-50 ${
        isSelected ? "border-gray-900" : "border-border"
      } ${!assistant.is_active ? "opacity-50" : ""}`}
    >
      <div className={`transition-transform ${catState === "executing" ? "animate-bounce" : ""}`}>
        <CatIllustration state={catState} size={96} />
      </div>
      <div className="w-full">
        <p className="text-sm font-medium truncate">{assistant.name}</p>
        <p className="text-xs text-gray-400 mt-0.5">{statusText}</p>
      </div>
    </button>
  );
}

function AssistantPanel({
  assistantId,
  onClose,
}: {
  assistantId: string;
  onClose: () => void;
}) {
  const { data: assistant } = useQuery({
    queryKey: ["assistant", assistantId],
    queryFn: () => assistantsApi.get(assistantId),
  });

  const { data: stateData } = useQuery({
    queryKey: ["assistant-state", assistantId],
    queryFn: () => assistantsApi.getState(assistantId),
    refetchInterval: 5_000,
  });

  const { data: pendingApprovals = [] } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => approvalsApi.list("pending"),
  });

  const { data: runs } = useQuery({
    queryKey: ["task-runs", assistantId],
    queryFn: () => auditApi.listTaskRuns({ assistant_id: assistantId, page: 1 }),
  });

  const myPendingCount = pendingApprovals.filter(
    (a) => a.action_log?.task_run_id && runs?.items.some((r) => r.id === a.action_log?.task_run_id)
  ).length;

  if (!assistant) return null;

  const catState: CatState = stateData?.cat_state ?? "idle";

  return (
    <div className="w-64 shrink-0 border border-border rounded-xl p-5 h-fit sticky top-8">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium">{assistant.name}</span>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-700 text-xs"
        >
          ✕
        </button>
      </div>

      <div className="flex justify-center mb-4">
        <CatIllustration state={catState} size={72} />
      </div>

      <p className="text-xs text-center text-gray-500 mb-4">
        {stateData?.status_text ?? "쉬고 있어요."}
      </p>

      <div className="flex flex-col gap-2 text-xs">
        <InfoRow label="역할" value={assistant.role_type ?? "—"} />
        <InfoRow label="상태">
          <StatusBadge status={assistant.is_active ? "completed" : "rejected"} />
        </InfoRow>

        {myPendingCount > 0 && (
          <Link
            to="/approvals"
            className="flex items-center justify-between px-3 py-2 border border-gray-900 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium">승인 대기</span>
            <span className="inline-flex items-center justify-center w-5 h-5 bg-gray-900 text-white rounded-full text-xs">
              {myPendingCount}
            </span>
          </Link>
        )}

        <div className="pt-2 border-t border-border mt-1">
          <p className="text-gray-400 mb-1">최근 활동</p>
          {(runs?.items ?? []).slice(0, 3).map((r) => (
            <Link
              key={r.id}
              to={`/history/${r.id}`}
              className="flex items-center justify-between py-1 hover:text-gray-900 transition-colors"
            >
              <span className="text-gray-500 truncate">
                {r.started_at ? new Date(r.started_at).toLocaleDateString("ko-KR") : "—"}
              </span>
              <StatusBadge status={r.status} />
            </Link>
          ))}
        </div>

        <div className="pt-2 flex flex-col gap-1 border-t border-border mt-1">
          <Link to={`/assistants/${assistantId}`} className="text-gray-500 hover:text-gray-900 transition-colors">
            설정 →
          </Link>
          <Link to={`/history?assistant_id=${assistantId}`} className="text-gray-500 hover:text-gray-900 transition-colors">
            전체 이력 →
          </Link>
        </div>
      </div>
    </div>
  );
}

function InfoRow({
  label,
  value,
  children,
}: {
  label: string;
  value?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-gray-400">{label}</span>
      {children ?? <span className="text-gray-700">{value}</span>}
    </div>
  );
}
