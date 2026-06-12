import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { auditApi, type TaskRun } from "@/api/audit";

const STATUS_LABEL: Record<string, string> = {
  pending: "대기 중",
  running: "실행 중",
  waiting_approval: "승인 대기",
  completed: "완료",
  failed: "실패",
  cancelled: "취소됨",
};

const STATUS_CLASS: Record<string, string> = {
  completed: "text-[#0a0a0a] font-medium",
  failed: "text-[#0a0a0a]",
  running: "text-[#5c5c5c]",
  waiting_approval: "text-[#0a0a0a]",
  pending: "text-[#9a9a9a]",
  cancelled: "text-[#9a9a9a]",
};

function StatusCell({ status }: { status: string }) {
  return (
    <span className={STATUS_CLASS[status] ?? "text-[#5c5c5c]"}>
      {status === "failed" && <span className="mr-1">⚠</span>}
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

function TaskRunRow({ run }: { run: TaskRun }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr className="border-b border-[#e8e8e8] hover:bg-[#f5f5f5] transition-colors">
        <td className="py-3 px-4 text-xs text-[#9a9a9a] whitespace-nowrap">
          {run.started_at ? new Date(run.started_at).toLocaleString("ko-KR") : "-"}
        </td>
        <td className="py-3 px-4 text-sm text-[#0a0a0a]">
          {run.assistant_name ?? "비서"}
        </td>
        <td className="py-3 px-4">
          <StatusCell status={run.status} />
        </td>
        <td className="py-3 px-4">
          {run.result_summary && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="text-xs text-[#5c5c5c] hover:text-[#0a0a0a] transition-colors"
            >
              {expanded ? "접기 ▲" : "판단 근거 ▼"}
            </button>
          )}
        </td>
        <td className="py-3 px-4 text-xs text-[#9a9a9a]">
          {run.completed_at
            ? new Date(run.completed_at).toLocaleString("ko-KR")
            : "-"}
        </td>
      </tr>
      {expanded && run.result_summary && (
        <tr className="bg-[#f5f5f5]">
          <td colSpan={5} className="px-4 py-3">
            <pre className="text-xs text-[#5c5c5c] whitespace-pre-wrap">
              {JSON.stringify(run.result_summary, null, 2)}
            </pre>
          </td>
        </tr>
      )}
    </>
  );
}

export default function ActivityLog() {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["audit", "task-runs", page],
    queryFn: () => auditApi.listTaskRuns({ page, size: 20 }),
  });

  const runs = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-[#0a0a0a]">활동 기록</h1>

      <div className="rounded-card border border-[#e8e8e8] bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#e8e8e8] bg-[#f5f5f5]">
              <th className="py-2.5 px-4 text-left text-xs font-medium text-[#9a9a9a]">시간</th>
              <th className="py-2.5 px-4 text-left text-xs font-medium text-[#9a9a9a]">비서</th>
              <th className="py-2.5 px-4 text-left text-xs font-medium text-[#9a9a9a]">상태</th>
              <th className="py-2.5 px-4 text-left text-xs font-medium text-[#9a9a9a]">판단 근거</th>
              <th className="py-2.5 px-4 text-left text-xs font-medium text-[#9a9a9a]">완료 시간</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-sm text-[#9a9a9a]">
                  불러오는 중...
                </td>
              </tr>
            ) : runs.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-sm text-[#9a9a9a]">
                  아직 실행 기록이 없어요.
                </td>
              </tr>
            ) : (
              runs.map((run) => <TaskRunRow key={run.id} run={run} />)
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-[#9a9a9a] text-xs">총 {total}개</span>
          <div className="flex gap-1">
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1 rounded-button border border-[#e8e8e8] text-xs hover:bg-[#f5f5f5] disabled:opacity-40"
            >
              이전
            </button>
            <span className="px-3 py-1 text-xs text-[#5c5c5c]">
              {page} / {totalPages}
            </span>
            <button
              disabled={page === totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1 rounded-button border border-[#e8e8e8] text-xs hover:bg-[#f5f5f5] disabled:opacity-40"
            >
              다음
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
