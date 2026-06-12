import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { approvalsApi, type ApprovalRequest } from "@/api/approvals";
import { CatIllustration } from "@/components/cat/CatIllustration";
import { Button } from "@/components/ui/Button";
import { Divider } from "@/components/ui/Divider";

function ApprovalCard({
  item,
  onApprove,
  onReject,
}: {
  item: ApprovalRequest;
  onApprove: (id: string, modified?: Record<string, unknown>) => void;
  onReject: (id: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editedText, setEditedText] = useState<string>(() => {
    const out = item.action?.output_data;
    return typeof out?.draft === "string" ? out.draft : "";
  });

  const input = item.action?.input_data;
  const output = item.action?.output_data;
  const originalComment = typeof input?.text === "string" ? input.text : null;
  const aiJudgement = typeof output?.classification === "string" ? output.classification : null;
  const draftReply = editedText || (typeof output?.draft === "string" ? output.draft : null);
  const assistantName = item.action?.assistant_name ?? "비서";
  const actionLabel = item.action?.action_type?.split(".").at(-1) ?? item.action?.action_type;

  const relTime = new Date(item.requested_at).toLocaleString("ko-KR");

  return (
    <div className="rounded-card border border-[#e8e8e8] bg-white p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CatIllustration state="waiting_approval" size={24} />
          <span className="text-sm font-medium text-[#0a0a0a]">{assistantName}</span>
          <span className="text-xs text-[#9a9a9a]">· {actionLabel}</span>
        </div>
        <span className="text-xs text-[#9a9a9a]">{relTime}</span>
      </div>

      <Divider />

      {/* Original */}
      {originalComment && (
        <div>
          <p className="text-xs text-[#9a9a9a] mb-1">원본</p>
          <p className="text-sm text-[#0a0a0a] bg-[#f5f5f5] rounded-button px-3 py-2">
            "{originalComment}"
          </p>
        </div>
      )}

      {/* AI judgement */}
      {aiJudgement && (
        <div>
          <p className="text-xs text-[#9a9a9a] mb-1">AI 판단</p>
          <p className="text-sm text-[#5c5c5c]">{aiJudgement}</p>
        </div>
      )}

      {/* Draft */}
      {draftReply !== null && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-[#9a9a9a]">제안 내용</p>
            <button
              onClick={() => setEditing((v) => !v)}
              className="text-xs text-[#5c5c5c] hover:text-[#0a0a0a] transition-colors"
            >
              {editing ? "취소" : "수정하기"}
            </button>
          </div>
          {editing ? (
            <textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              className="w-full rounded-button border border-[#0a0a0a] p-2 text-sm resize-none focus:outline-none"
              rows={3}
            />
          ) : (
            <p className="text-sm text-[#0a0a0a] bg-[#f5f5f5] rounded-button px-3 py-2">
              {draftReply}
            </p>
          )}
        </div>
      )}

      <Divider />

      {/* Actions */}
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="secondary"
          onClick={() => onReject(item.action_log_id)}
        >
          거절
        </Button>
        <Button
          size="sm"
          onClick={() =>
            onApprove(
              item.action_log_id,
              editing && editedText ? { draft: editedText } : undefined
            )
          }
        >
          {draftReply !== null ? "승인하고 게시 ↑" : "승인"}
        </Button>
      </div>
    </div>
  );
}

export default function Approvals() {
  const qc = useQueryClient();

  const { data: items = [], isLoading } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => approvalsApi.list("pending"),
    refetchInterval: 15_000,
  });

  const approve = useMutation({
    mutationFn: ({ id, modified }: { id: string; modified?: Record<string, unknown> }) =>
      approvalsApi.approve(id, modified),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals"] }),
  });

  const reject = useMutation({
    mutationFn: (id: string) => approvalsApi.reject(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals"] }),
  });

  const bulkApprove = useMutation({
    mutationFn: () => approvalsApi.bulkApprove(items.map((i) => i.action_log_id)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["approvals"] }),
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[#0a0a0a]">승인 대기</h1>
          {items.length > 0 && (
            <p className="text-sm text-[#9a9a9a] mt-0.5">{items.length}개 항목이 확인을 기다리고 있어요.</p>
          )}
        </div>
        {items.length > 1 && (
          <Button
            size="sm"
            variant="secondary"
            loading={bulkApprove.isPending}
            onClick={() => bulkApprove.mutate()}
          >
            전체 승인
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-48 rounded-card border border-[#e8e8e8] bg-white animate-pulse" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-20">
          <CatIllustration state="done" size={64} />
          <p className="text-sm text-[#9a9a9a]">확인할 항목이 없어요. 비서가 잘 하고 있어요.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <ApprovalCard
              key={item.id}
              item={item}
              onApprove={(id, modified) => approve.mutate({ id, modified })}
              onReject={(id) => reject.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
