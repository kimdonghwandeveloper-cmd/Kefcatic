interface StatusBadgeProps {
  status: string;
}

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-gray-900 text-white",
  executed: "bg-gray-900 text-white",
  approved: "bg-gray-900 text-white",
  running: "bg-gray-100 text-gray-700 border border-gray-300",
  pending: "bg-gray-100 text-gray-500",
  pending_approval: "border border-gray-900 text-gray-900 bg-white",
  waiting_approval: "border border-gray-900 text-gray-900 bg-white",
  failed: "text-gray-700",
  error: "text-gray-700",
  rejected: "text-gray-500",
  rolled_back: "text-gray-400",
  draft: "bg-gray-100 text-gray-500 border border-gray-200",
};

const STATUS_LABELS: Record<string, string> = {
  completed: "완료",
  executed: "실행됨",
  approved: "승인됨",
  running: "실행 중",
  pending: "대기",
  pending_approval: "승인 대기",
  waiting_approval: "승인 대기",
  failed: "실패",
  error: "오류",
  rejected: "거절됨",
  rolled_back: "롤백됨",
  draft: "초안",
  disabled: "비활성",
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] ?? "text-gray-400";
  const label = STATUS_LABELS[status] ?? status;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${style}`}>
      {(status === "failed" || status === "error") && (
        <span className="mr-1">!</span>
      )}
      {label}
    </span>
  );
}
