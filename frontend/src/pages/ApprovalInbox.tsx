import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { approvalsApi, type ApprovalRequest } from "../api/approvals";
import { StatusBadge } from "../components/StatusBadge";
import { useToastStore } from "../stores/toastStore";

const ACTION_LABELS: Record<string, string> = {
  "youtube.comment.reply": "답글 작성",
  "youtube.comment.hide": "댓글 숨김",
  "youtube.comment.list": "댓글 조회",
};

export function ApprovalInboxPage() {
  const qc = useQueryClient();
  const toast = useToastStore();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [rejectNote, setRejectNote] = useState<Record<string, string>>({});
  const [editInput, setEditInput] = useState<Record<string, string>>({});

  const { data: items = [], isLoading } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => approvalsApi.list("pending"),
    refetchInterval: 10_000,
  });

  const approveMutation = useMutation({
    mutationFn: ({ id, modified }: { id: string; modified?: Record<string, unknown> }) =>
      approvalsApi.approve(id, undefined, modified),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] });
      toast.push("승인되었습니다.", "success");
    },
    onError: () => toast.push("승인 중 오류가 발생했어요.", "error"),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) =>
      approvalsApi.reject(id, note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] });
      toast.push("거절되었습니다.");
    },
    onError: () => toast.push("거절 중 오류가 발생했어요.", "error"),
  });

  const bulkMutation = useMutation({
    mutationFn: (ids: string[]) => approvalsApi.bulkApprove(ids),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["approvals"] });
      setSelected(new Set());
      toast.push(`${data.approved}건 일괄 승인되었습니다.`, "success");
    },
  });

  const handleBulkApprove = () => {
    const ids = [...selected].map((reqId) => {
      const item = items.find((i) => i.id === reqId);
      return item?.action_log_id ?? reqId;
    });
    bulkMutation.mutate(ids);
  };

  if (isLoading) return <Loading />;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold">
          승인 인박스
          {items.length > 0 && (
            <span className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs bg-gray-900 text-white rounded-full">
              {items.length}
            </span>
          )}
        </h1>
        {selected.size > 0 && (
          <button
            onClick={handleBulkApprove}
            disabled={bulkMutation.isPending}
            className="px-3 py-1.5 bg-gray-900 text-white text-sm rounded-lg disabled:opacity-50"
          >
            {selected.size}건 일괄 승인
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-16 text-gray-400">
          <p className="text-sm">승인 대기 중인 항목이 없어요.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((item) => (
            <ApprovalCard
              key={item.id}
              item={item}
              isSelected={selected.has(item.id)}
              onToggleSelect={() => {
                setSelected((s) => {
                  const next = new Set(s);
                  next.has(item.id) ? next.delete(item.id) : next.add(item.id);
                  return next;
                });
              }}
              onApprove={(modified) =>
                approveMutation.mutate({ id: item.action_log_id, modified })
              }
              onReject={(note) =>
                rejectMutation.mutate({ id: item.action_log_id, note })
              }
              editValue={editInput[item.id] ?? ""}
              onEditChange={(v) =>
                setEditInput((prev) => ({ ...prev, [item.id]: v }))
              }
              rejectNote={rejectNote[item.id] ?? ""}
              onRejectNoteChange={(v) =>
                setRejectNote((prev) => ({ ...prev, [item.id]: v }))
              }
              isPending={approveMutation.isPending || rejectMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface ApprovalCardProps {
  item: ApprovalRequest;
  isSelected: boolean;
  onToggleSelect: () => void;
  onApprove: (modified?: Record<string, unknown>) => void;
  onReject: (note: string) => void;
  editValue: string;
  onEditChange: (v: string) => void;
  rejectNote: string;
  onRejectNoteChange: (v: string) => void;
  isPending: boolean;
}

function ApprovalCard({
  item,
  isSelected,
  onToggleSelect,
  onApprove,
  onReject,
  editValue,
  onEditChange,
  rejectNote,
  onRejectNoteChange,
  isPending,
}: ApprovalCardProps) {
  const [showEdit, setShowEdit] = useState(false);
  const [showReject, setShowReject] = useState(false);
  const log = item.action_log;
  const actionLabel = ACTION_LABELS[log?.action_type ?? ""] ?? log?.action_type;
  const input = log?.input_data ?? {};

  return (
    <div
      className={`border rounded-xl p-4 bg-white transition-colors ${
        isSelected ? "border-gray-900" : "border-border"
      }`}
    >
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="mt-1 accent-gray-900"
        />
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-medium text-gray-500">{actionLabel}</span>
            <StatusBadge status="pending_approval" />
            <span className="text-xs text-gray-400 ml-auto">
              {new Date(item.requested_at).toLocaleString("ko-KR")}
            </span>
          </div>

          {/* Original comment */}
          {input.text && (
            <div className="mb-2">
              <p className="text-xs text-gray-400 mb-1">원본 댓글</p>
              <p className="text-sm text-gray-700 bg-gray-50 rounded-lg px-3 py-2">
                {String(input.comment_id ?? "")}
              </p>
            </div>
          )}

          {/* Draft reply or hide target */}
          {log?.action_type === "youtube.comment.reply" && (
            <div className="mb-3">
              <p className="text-xs text-gray-400 mb-1">초안 답글</p>
              {showEdit ? (
                <textarea
                  value={editValue || String(input.text ?? "")}
                  onChange={(e) => onEditChange(e.target.value)}
                  rows={3}
                  className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-gray-900 resize-none"
                />
              ) : (
                <p className="text-sm text-gray-700 bg-gray-50 rounded-lg px-3 py-2">
                  {String(input.text ?? "")}
                </p>
              )}
            </div>
          )}

          {log?.action_type === "youtube.comment.hide" && (
            <p className="text-sm text-gray-500 mb-3">
              댓글 ID <code className="text-xs bg-gray-100 px-1 rounded">{String(input.comment_id ?? "")}</code>을 숨깁니다.
            </p>
          )}

          {/* Reject note */}
          {showReject && (
            <textarea
              placeholder="거절 사유 (선택)"
              value={rejectNote}
              onChange={(e) => onRejectNoteChange(e.target.value)}
              rows={2}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 mb-3 focus:outline-none focus:ring-1 focus:ring-gray-900 resize-none"
            />
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => {
                const modified =
                  showEdit && editValue
                    ? { ...input, text: editValue }
                    : undefined;
                onApprove(modified);
              }}
              disabled={isPending}
              className="px-3 py-1.5 bg-gray-900 text-white text-xs rounded-lg disabled:opacity-50 hover:bg-gray-700 transition-colors"
            >
              승인
            </button>

            {log?.action_type === "youtube.comment.reply" && (
              <button
                onClick={() => setShowEdit((v) => !v)}
                className="px-3 py-1.5 border border-gray-300 text-xs rounded-lg hover:bg-gray-50 transition-colors"
              >
                {showEdit ? "수정 취소" : "수정 후 승인"}
              </button>
            )}

            <button
              onClick={() => {
                if (showReject) {
                  onReject(rejectNote);
                  setShowReject(false);
                } else {
                  setShowReject(true);
                }
              }}
              disabled={isPending}
              className="px-3 py-1.5 border border-gray-200 text-gray-500 text-xs rounded-lg disabled:opacity-50 hover:bg-gray-50 transition-colors"
            >
              {showReject ? "거절 확인" : "거절"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Loading() {
  return (
    <div className="flex items-center justify-center h-48 text-sm text-gray-400">
      불러오는 중...
    </div>
  );
}
