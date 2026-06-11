import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { assistantsApi } from "../api/assistants";
import { auditApi } from "../api/audit";
import { StatusBadge } from "../components/StatusBadge";
import { useToastStore } from "../stores/toastStore";

export function AssistantDetailPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const toast = useToastStore();

  const { data: assistant, isLoading } = useQuery({
    queryKey: ["assistant", id],
    queryFn: () => assistantsApi.get(id!),
    enabled: !!id,
  });

  const { data: runs } = useQuery({
    queryKey: ["task-runs", id],
    queryFn: () => auditApi.listTaskRuns({ assistant_id: id, page: 1 }),
    enabled: !!id,
  });

  const toggleMutation = useMutation({
    mutationFn: (active: boolean) => assistantsApi.update(id!, { is_active: active }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assistant", id] });
      qc.invalidateQueries({ queryKey: ["assistants"] });
      toast.push("비서 상태가 변경됐어요.", "success");
    },
  });

  const triggerMutation = useMutation({
    mutationFn: () => assistantsApi.trigger(id!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["task-runs", id] });
      toast.push("실행이 시작됐어요.", "success");
    },
    onError: () => toast.push("실행 중 오류가 발생했어요.", "error"),
  });

  if (isLoading) return <div className="text-sm text-gray-400 py-8 text-center">불러오는 중...</div>;
  if (!assistant) return <div className="text-sm text-gray-400 py-8 text-center">찾을 수 없어요.</div>;

  const config = assistant as any;

  return (
    <div>
      <Link to="/" className="text-xs text-gray-400 hover:text-gray-700 mb-4 inline-block">
        ← 대시보드
      </Link>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-lg font-semibold">{assistant.name}</h1>
          <p className="text-sm text-gray-400">{assistant.role_type}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => toggleMutation.mutate(!assistant.is_active)}
            disabled={toggleMutation.isPending}
            className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            {assistant.is_active ? "비활성화" : "활성화"}
          </button>
          <button
            onClick={() => triggerMutation.mutate()}
            disabled={triggerMutation.isPending || !assistant.is_active}
            className="px-3 py-1.5 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            {triggerMutation.isPending ? "실행 중..." : "수동 실행"}
          </button>
        </div>
      </div>

      {/* Info */}
      <div className="p-4 border border-border rounded-xl mb-6">
        <SectionRow label="상태">
          <StatusBadge status={assistant.is_active ? "completed" : "rejected"} />
        </SectionRow>
        {assistant.description && (
          <SectionRow label="설명">
            <span className="text-sm text-gray-700">{assistant.description}</span>
          </SectionRow>
        )}
      </div>

      {/* Recent runs */}
      <h2 className="text-sm font-medium text-gray-500 mb-3">최근 실행</h2>
      {(runs?.items ?? []).length === 0 ? (
        <p className="text-sm text-gray-400 mb-6">아직 실행 기록이 없어요.</p>
      ) : (
        <div className="flex flex-col gap-2 mb-6">
          {runs!.items.slice(0, 5).map((r) => (
            <Link
              key={r.id}
              to={`/history/${r.id}`}
              className="flex items-center justify-between px-4 py-3 border border-border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <span className="text-xs text-gray-500">
                {r.started_at ? new Date(r.started_at).toLocaleString("ko-KR") : "—"}
              </span>
              <StatusBadge status={r.status} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function SectionRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-4 py-2 border-b border-border last:border-0">
      <span className="text-xs text-gray-400 w-20 shrink-0">{label}</span>
      {children}
    </div>
  );
}
