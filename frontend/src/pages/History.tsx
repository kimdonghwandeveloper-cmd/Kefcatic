import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { auditApi } from "../api/audit";
import { StatusBadge } from "../components/StatusBadge";

const ACTION_LABELS: Record<string, string> = {
  "youtube.comment.reply": "답글 작성",
  "youtube.comment.hide": "댓글 숨김",
  "youtube.comment.list": "댓글 조회",
};

export function HistoryPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["task-runs", statusFilter, page],
    queryFn: () =>
      auditApi.listTaskRuns({ status: statusFilter || undefined, page }),
  });

  return (
    <div>
      <h1 className="text-lg font-semibold mb-6">실행 이력</h1>

      {/* Filter */}
      <div className="flex gap-2 mb-4">
        {["", "completed", "running", "failed", "waiting_approval"].map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={`px-3 py-1 text-xs rounded-lg border transition-colors ${
              statusFilter === s
                ? "bg-gray-900 text-white border-gray-900"
                : "border-border text-gray-500 hover:bg-gray-50"
            }`}
          >
            {s === "" ? "전체" : <StatusBadge status={s} />}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="text-sm text-gray-400 py-8 text-center">불러오는 중...</div>
      ) : (data?.items ?? []).length === 0 ? (
        <div className="text-sm text-gray-400 py-8 text-center">실행 이력이 없어요.</div>
      ) : (
        <>
          <div className="flex flex-col gap-2">
            {data!.items.map((r) => (
              <Link
                key={r.id}
                to={`/history/${r.id}`}
                className="flex items-center justify-between px-4 py-3 border border-border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div>
                  <p className="text-sm text-gray-700">
                    {r.started_at
                      ? new Date(r.started_at).toLocaleString("ko-KR")
                      : "—"}
                  </p>
                  {r.result_summary && (
                    <p className="text-xs text-gray-400 mt-0.5">
                      처리 {(r.result_summary as any).total ?? 0}건
                    </p>
                  )}
                </div>
                <StatusBadge status={r.status} />
              </Link>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex justify-between items-center mt-4 text-xs text-gray-400">
            <span>총 {data!.total}건</span>
            <div className="flex gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-2 py-1 border border-border rounded disabled:opacity-30"
              >
                이전
              </button>
              <span className="px-2 py-1">{page}</span>
              <button
                disabled={page * data!.page_size >= data!.total}
                onClick={() => setPage((p) => p + 1)}
                className="px-2 py-1 border border-border rounded disabled:opacity-30"
              >
                다음
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function HistoryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ["task-run-detail", id],
    queryFn: () => auditApi.getTaskRunDetail(id!),
    enabled: !!id,
  });

  if (isLoading) return <div className="text-sm text-gray-400 py-8 text-center">불러오는 중...</div>;
  if (!data) return <div className="text-sm text-gray-400 py-8 text-center">찾을 수 없어요.</div>;

  return (
    <div>
      <Link to="/history" className="text-xs text-gray-400 hover:text-gray-700 mb-4 inline-block">
        ← 이력 목록
      </Link>
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-lg font-semibold">실행 상세</h1>
        <StatusBadge status={data.status} />
      </div>

      <div className="mb-6 p-4 border border-border rounded-xl">
        <Row label="시작" value={data.started_at ? new Date(data.started_at).toLocaleString("ko-KR") : "—"} />
        <Row label="완료" value={data.completed_at ? new Date(data.completed_at).toLocaleString("ko-KR") : "—"} />
        {data.error_message && (
          <Row label="오류" value={data.error_message} />
        )}
        {data.result_summary && (
          <Row label="요약" value={JSON.stringify(data.result_summary)} />
        )}
      </div>

      <h2 className="text-sm font-medium text-gray-500 mb-3">액션 로그 ({data.action_logs.length}건)</h2>
      <div className="flex flex-col gap-2">
        {data.action_logs.map((log) => (
          <div key={log.id} className="border border-border rounded-xl px-4 py-3">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium">
                {ACTION_LABELS[log.action_type] ?? log.action_type}
              </span>
              <StatusBadge status={log.status} />
            </div>
            {log.input_data && (
              <pre className="text-xs bg-gray-50 rounded-lg px-3 py-2 overflow-x-auto text-gray-600">
                {JSON.stringify(log.input_data, null, 2)}
              </pre>
            )}
            {log.output_data && (
              <pre className="text-xs bg-gray-50 rounded-lg px-3 py-2 mt-1 overflow-x-auto text-gray-600">
                {JSON.stringify(log.output_data, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-4 text-sm py-1">
      <span className="text-gray-400 w-16 shrink-0">{label}</span>
      <span className="text-gray-700 break-all">{value}</span>
    </div>
  );
}
