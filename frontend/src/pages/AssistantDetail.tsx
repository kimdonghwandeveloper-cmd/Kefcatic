import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { assistantsApi, type AssistantPatch } from "@/api/assistants";
import { memoriesApi, type Memory, type MemoryCreate } from "@/api/memories";
import { approvalsApi } from "@/api/approvals";
import { auditApi } from "@/api/audit";
import { CatIllustration } from "@/components/cat/CatIllustration";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";

type Tab = "overview" | "approvals" | "activity" | "settings";

const MEMORY_TYPE_LABEL: Record<Memory["memory_type"], string> = {
  preference: "선호 설정",
  instruction: "지시 사항",
  context: "컨텍스트",
};

function MemoryCard({
  assistantId,
  memory,
}: {
  assistantId: string;
  memory: Memory;
}) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(memory.value);

  const update = useMutation({
    mutationFn: () => memoriesApi.update(assistantId, memory.key, value),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["memories", assistantId] });
      setEditing(false);
    },
  });

  const del = useMutation({
    mutationFn: () => memoriesApi.delete(assistantId, memory.key),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["memories", assistantId] }),
  });

  return (
    <div className="flex items-start justify-between py-3">
      <div className="flex-1 min-w-0 pr-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs text-[#9a9a9a]">{MEMORY_TYPE_LABEL[memory.memory_type]}</span>
          <span className="text-xs font-medium text-[#0a0a0a]">{memory.key}</span>
        </div>
        {editing ? (
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-full rounded-button border border-[#0a0a0a] px-2 py-1 text-sm resize-none focus:outline-none"
            rows={2}
          />
        ) : (
          <p className="text-sm text-[#5c5c5c] truncate">{memory.value}</p>
        )}
      </div>
      <div className="flex gap-1 shrink-0">
        {editing ? (
          <>
            <Button size="sm" loading={update.isPending} onClick={() => update.mutate()}>저장</Button>
            <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setValue(memory.value); }}>취소</Button>
          </>
        ) : (
          <>
            <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>수정</Button>
            <Button size="sm" variant="ghost" loading={del.isPending} onClick={() => del.mutate()}>삭제</Button>
          </>
        )}
      </div>
    </div>
  );
}

function AddMemoryForm({ assistantId }: { assistantId: string }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const { register, handleSubmit, reset } = useForm<MemoryCreate>({
    defaultValues: { memory_type: "preference" },
  });

  const create = useMutation({
    mutationFn: (data: MemoryCreate) => memoriesApi.create(assistantId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["memories", assistantId] });
      reset();
      setOpen(false);
    },
  });

  if (!open) {
    return (
      <Button size="sm" variant="secondary" onClick={() => setOpen(true)}>
        + 메모리 추가
      </Button>
    );
  }

  return (
    <form onSubmit={handleSubmit((d) => create.mutate(d))} className="space-y-3 rounded-button border border-[#e8e8e8] p-4">
      <div className="flex gap-3">
        <div className="flex-1">
          <Input label="키" {...register("key", { required: true })} placeholder="예: 선호_말투" />
        </div>
        <div>
          <label className="block text-label text-[#0a0a0a] mb-1">유형</label>
          <select
            {...register("memory_type")}
            className="h-9 rounded-button border border-[#d1d1d1] px-2 text-sm bg-white focus:outline-none focus:border-[#0a0a0a]"
          >
            <option value="preference">선호 설정</option>
            <option value="instruction">지시 사항</option>
            <option value="context">컨텍스트</option>
          </select>
        </div>
      </div>
      <Textarea label="값" {...register("value", { required: true })} placeholder="내용을 입력하세요." />
      <div className="flex gap-2">
        <Button size="sm" type="submit" loading={create.isPending}>저장</Button>
        <Button size="sm" variant="ghost" type="button" onClick={() => setOpen(false)}>취소</Button>
      </div>
    </form>
  );
}

export default function AssistantDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");

  const { data: assistant, isLoading } = useQuery({
    queryKey: ["assistant", id],
    queryFn: () => assistantsApi.get(id!),
    enabled: !!id,
  });

  const { data: memories = [] } = useQuery({
    queryKey: ["memories", id],
    queryFn: () => memoriesApi.list(id!),
    enabled: !!id && tab === "settings",
  });

  const { data: pendingApprovals = [] } = useQuery({
    queryKey: ["approvals", "pending", id],
    queryFn: () => approvalsApi.list("pending"),
    enabled: !!id && tab === "approvals",
  });

  const { data: taskRuns } = useQuery({
    queryKey: ["audit", "task-runs", id],
    queryFn: () => auditApi.listTaskRuns({ assistant_id: id, size: 10 }),
    enabled: !!id && tab === "activity",
  });

  const { register, handleSubmit } = useForm<AssistantPatch>();

  const patch = useMutation({
    mutationFn: (data: AssistantPatch) => assistantsApi.patch(id!, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assistant", id] }),
  });

  const toggle = useMutation({
    mutationFn: () => assistantsApi.patch(id!, { is_active: !assistant?.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assistant", id] }),
  });

  const trigger = useMutation({
    mutationFn: () => assistantsApi.trigger(id!),
  });

  if (isLoading) {
    return <div className="text-sm text-[#9a9a9a] py-8 text-center">불러오는 중...</div>;
  }

  if (!assistant) {
    return (
      <div className="text-sm text-[#9a9a9a] py-8 text-center">
        비서를 찾을 수 없습니다.{" "}
        <button onClick={() => navigate("/assistants")} className="underline">목록으로</button>
      </div>
    );
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: "overview", label: "현재 작업" },
    { key: "approvals", label: `승인 대기${pendingApprovals.length > 0 ? ` (${pendingApprovals.length})` : ""}` },
    { key: "activity", label: "활동 기록" },
    { key: "settings", label: "설정" },
  ];

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <CatIllustration state="idle" size={48} />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold text-[#0a0a0a]">{assistant.name}</h1>
              <StatusBadge status={assistant.is_active ? "active" : "idle"} />
            </div>
            <p className="text-sm text-[#9a9a9a] mt-0.5">{assistant.description ?? "역할 설명 없음"}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button size="sm" loading={trigger.isPending} onClick={() => trigger.mutate()}>
            지금 실행
          </Button>
          <Button
            size="sm"
            variant="secondary"
            loading={toggle.isPending}
            onClick={() => toggle.mutate()}
          >
            {assistant.is_active ? "일시정지" : "활성화"}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-[#e8e8e8]">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm transition-colors border-b-2 -mb-px ${
              tab === key
                ? "border-[#0a0a0a] text-[#0a0a0a] font-medium"
                : "border-transparent text-[#9a9a9a] hover:text-[#5c5c5c]"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Overview */}
      {tab === "overview" && (
        <Card>
          <p className="text-sm text-[#9a9a9a] py-6 text-center">
            비서가 실행되면 현재 작업 상태가 여기에 표시됩니다.
          </p>
        </Card>
      )}

      {/* Approvals */}
      {tab === "approvals" && (
        <div className="space-y-4">
          {pendingApprovals.length === 0 ? (
            <Card>
              <p className="text-sm text-[#9a9a9a] py-6 text-center">확인할 항목이 없어요.</p>
            </Card>
          ) : (
            pendingApprovals.map((item) => (
              <Card key={item.id} padding="sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[#0a0a0a]">{item.action?.action_type}</p>
                    <p className="text-xs text-[#9a9a9a]">
                      {new Date(item.requested_at).toLocaleString("ko-KR")}
                    </p>
                  </div>
                  <Button size="sm" onClick={() => navigate("/approvals")}>확인하기</Button>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Activity */}
      {tab === "activity" && (
        <Card padding="sm">
          {(taskRuns?.items ?? []).length === 0 ? (
            <p className="text-sm text-[#9a9a9a] py-6 text-center">실행 기록이 없어요.</p>
          ) : (
            <div className="divide-y divide-[#e8e8e8]">
              {taskRuns!.items.map((run) => (
                <div key={run.id} className="flex items-center justify-between py-3 px-2">
                  <span className="text-sm text-[#0a0a0a]">
                    {run.started_at ? new Date(run.started_at).toLocaleString("ko-KR") : "-"}
                  </span>
                  <span className="text-xs text-[#5c5c5c]">{run.status}</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Settings */}
      {tab === "settings" && (
        <div className="space-y-6">
          {/* Basic info */}
          <Card>
            <h3 className="text-sm font-semibold text-[#0a0a0a] mb-4">기본 정보</h3>
            <form
              onSubmit={handleSubmit((d) => patch.mutate(d))}
              className="space-y-4"
            >
              <Input
                label="비서 이름"
                defaultValue={assistant.name}
                {...register("name")}
              />
              <Textarea
                label="역할 설명"
                defaultValue={assistant.description ?? ""}
                {...register("description")}
                rows={2}
              />
              <Button size="sm" type="submit" loading={patch.isPending}>
                저장
              </Button>
            </form>
          </Card>

          {/* Memory */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-[#0a0a0a]">메모리</h3>
              <span className="text-xs text-[#9a9a9a]">{memories.length}개</span>
            </div>

            {memories.length > 0 && (
              <div className="divide-y divide-[#e8e8e8] mb-4">
                {memories.map((m) => (
                  <MemoryCard key={m.id} assistantId={id!} memory={m} />
                ))}
              </div>
            )}

            <AddMemoryForm assistantId={id!} />
          </Card>
        </div>
      )}
    </div>
  );
}
