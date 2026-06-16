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
  completed: "text-[#1A1918] font-medium",
  failed: "text-[#C0392B]",
  running: "text-[#2D2B29] font-medium",
  waiting_approval: "text-[#1A1918] font-medium",
  pending: "text-[#A8A5A2]",
  cancelled: "text-[#A8A5A2]",
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
      <tr className="border-b border-[#E2E1DE] hover:bg-[#F5F4F2] transition-colors">
        <td className="py-3 px-4 text-[11px] text-[#A8A5A2] whitespace-nowrap">
          {run.started_at ? new Date(run.started_at).toLocaleString("ko-KR") : "-"}
        </td>
        <td className="py-3 px-4 text-[13px] font-medium text-[#1A1918]">
          {run.assistant_name ?? "비서"}
        </td>
        <td className="py-3 px-4 text-[13px]">
          <StatusCell status={run.status} />
        </td>
        <td className="py-3 px-4">
          {run.result_summary && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="text-[13px] text-[#6B6966] hover:text-[#1A1918] transition-colors"
            >
              {expanded ? "접기 ▲" : "근거 ▼"}
            </button>
          )}
        </td>
        <td className="py-3 px-4 text-[11px] text-[#A8A5A2]">
          {run.completed_at
            ? new Date(run.completed_at).toLocaleString("ko-KR")
            : "-"}
        </td>
      </tr>
      {expanded && run.result_summary && (
        <tr className="bg-[#F5F4F2]">
          <td colSpan={5} className="px-4 py-3">
            <pre className="text-[11px] text-[#6B6966] whitespace-pre-wrap">
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
      <h1 className="font-heading text-[20px] font-semibold text-[#1A1918]">기록</h1>

      <div className="rounded-card border border-[#E2E1DE] bg-white overflow-hidden shadow-card">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#E2E1DE] bg-[#F5F4F2]">
              <th className="py-2.5 px-4 text-left text-[11px] font-medium tracking-widest text-[#A8A5A2] uppercase">시간</th>
              <th className="py-2.5 px-4 text-left text-[11px] font-medium tracking-widest text-[#A8A5A2] uppercase">비서</th>
              <th className="py-2.5 px-4 text-left text-[11px] font-medium tracking-widest text-[#A8A5A2] uppercase">상태</th>
              <th className="py-2.5 px-4 text-left text-[11px] font-medium tracking-widest text-[#A8A5A2] uppercase">근거</th>
              <th className="py-2.5 px-4 text-left text-[11px] font-medium tracking-widest text-[#A8A5A2] uppercase">완료</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-[13px] text-[#A8A5A2]">
                  불러오는 중...
                </td>
              </tr>
            ) : runs.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-[13px] text-[#A8A5A2]">
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
          <span className="text-[#A8A5A2] text-[13px]">총 {total}개</span>
          <div className="flex gap-1">
            <button
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1.5 rounded-button border border-[#E2E1DE] text-[13px] hover:bg-[#EFEFED] disabled:opacity-40"
            >
              이전
            </button>
            <span className="px-3 py-1.5 text-[13px] text-[#6B6966]">
              {page} / {totalPages}
            </span>
            <button
              disabled={page === totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 rounded-button border border-[#E2E1DE] text-[13px] hover:bg-[#EFEFED] disabled:opacity-40"
            >
              다음
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
