import { useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { assistantsApi, type CreateAssistantInput } from "../api/assistants";
import { apiClient } from "../api/client";
import { useToastStore } from "../stores/toastStore";

const STEPS = ["역할 설정", "커넥터 연결", "실행 조건", "권한 설정", "검토 및 저장"] as const;

interface FormValues {
  name: string;
  description: string;
  role_type: string;
  system_prompt: string;
  cron_expression: string;
  approval_reply: string;
  approval_hide: string;
}

export function NewAssistantPage() {
  const [step, setStep] = useState(0);
  const [connectorLinked, setConnectorLinked] = useState(false);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const toast = useToastStore();

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormValues>({
    defaultValues: {
      role_type: "youtube_moderator",
      approval_reply: "require_approval",
      approval_hide: "require_approval",
      cron_expression: "0 9 * * *",
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateAssistantInput) => assistantsApi.create(data),
    onSuccess: (assistant) => {
      qc.invalidateQueries({ queryKey: ["assistants"] });
      toast.push(`'${assistant.name}' 비서가 생성됐어요.`, "success");
      navigate(`/assistants/${assistant.id}`);
    },
    onError: () => toast.push("비서 생성 중 오류가 발생했어요.", "error"),
  });

  const onSubmit = (values: FormValues) => {
    createMutation.mutate({
      name: values.name,
      description: values.description,
      role_type: values.role_type,
      system_prompt: values.system_prompt,
      config: {
        cron_expression: values.cron_expression,
        approval_modes: {
          "youtube.comment.reply": values.approval_reply,
          "youtube.comment.hide": values.approval_hide,
        },
      },
    });
  };

  const handleYouTubeConnect = async () => {
    try {
      const res = await apiClient.get<{ url: string }>("/connectors/youtube/auth-url");
      window.location.href = res.data.url;
    } catch {
      toast.push("YouTube 연결 URL을 가져오지 못했어요.", "error");
    }
  };

  return (
    <div>
      <h1 className="text-lg font-semibold mb-6">새 비서 만들기</h1>

      {/* Step indicator */}
      <div className="flex items-center gap-1 mb-8">
        {STEPS.map((label, i) => (
          <div key={i} className="flex items-center gap-1">
            <div
              className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium transition-colors ${
                i < step
                  ? "bg-gray-900 text-white"
                  : i === step
                  ? "border-2 border-gray-900 text-gray-900"
                  : "border border-gray-200 text-gray-400"
              }`}
            >
              {i < step ? "✓" : i + 1}
            </div>
            {i < STEPS.length - 1 && (
              <div className={`w-8 h-px ${i < step ? "bg-gray-900" : "bg-gray-200"}`} />
            )}
          </div>
        ))}
      </div>
      <p className="text-sm font-medium mb-6">{STEPS[step]}</p>

      <form onSubmit={handleSubmit(onSubmit)}>
        {step === 0 && (
          <div className="flex flex-col gap-4">
            <Field label="비서 이름 *">
              <input
                {...register("name", { required: true })}
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-900"
                placeholder="예: YouTube 댓글 관리 비서"
              />
            </Field>
            <Field label="설명">
              <input
                {...register("description")}
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-900"
                placeholder="이 비서가 하는 일을 간단히 설명해주세요."
              />
            </Field>
            <Field label="역할">
              <select
                {...register("role_type")}
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-900"
              >
                <option value="youtube_moderator">YouTube 댓글 관리</option>
                <option value="gmail_responder" disabled>Gmail 문의 정리 (Phase 3)</option>
              </select>
            </Field>
            <Field label="비서 지침">
              <textarea
                {...register("system_prompt")}
                rows={3}
                placeholder="답변 스타일, 금지 표현, 특별 지시사항 등을 입력하세요."
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-900 resize-none"
              />
            </Field>
          </div>
        )}

        {step === 1 && (
          <div className="flex flex-col gap-4">
            <div className="p-4 border border-border rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-sm font-medium">YouTube</p>
                  <p className="text-xs text-gray-400">YouTube Data API v3</p>
                </div>
                {connectorLinked ? (
                  <span className="text-xs text-gray-500">연결됨 ✓</span>
                ) : (
                  <button
                    type="button"
                    onClick={handleYouTubeConnect}
                    className="px-3 py-1.5 text-xs border border-gray-900 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    연결하기
                  </button>
                )}
              </div>
              {!connectorLinked && (
                <button
                  type="button"
                  onClick={() => setConnectorLinked(true)}
                  className="text-xs text-gray-400 underline"
                >
                  이미 연결됐어요 (테스트용)
                </button>
              )}
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="flex flex-col gap-4">
            <Field label="자동 실행 스케줄 (Cron)">
              <input
                {...register("cron_expression")}
                className="w-full border border-border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-gray-900"
                placeholder="0 9 * * * (매일 오전 9시)"
              />
              <p className="text-xs text-gray-400 mt-1">cron 표현식 형식: 분 시 일 월 요일</p>
            </Field>
          </div>
        )}

        {step === 3 && (
          <div className="flex flex-col gap-4">
            <p className="text-xs text-gray-500 mb-2">각 액션에 대한 승인 정책을 설정하세요.</p>
            <Field label="답글 작성">
              <ApprovalSelect {...register("approval_reply")} />
            </Field>
            <Field label="댓글 숨김">
              <ApprovalSelect {...register("approval_hide")} />
            </Field>
          </div>
        )}

        {step === 4 && (
          <div className="flex flex-col gap-3">
            <SummaryRow label="이름" value={watch("name")} />
            <SummaryRow label="역할" value={watch("role_type")} />
            <SummaryRow label="스케줄" value={watch("cron_expression")} />
            <SummaryRow label="답글 정책" value={watch("approval_reply")} />
            <SummaryRow label="숨김 정책" value={watch("approval_hide")} />
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <button
            type="button"
            onClick={() => setStep((s) => s - 1)}
            disabled={step === 0}
            className="px-4 py-2 text-sm border border-border rounded-lg disabled:opacity-30 hover:bg-gray-50 transition-colors"
          >
            이전
          </button>

          {step < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              다음
            </button>
          ) : (
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg disabled:opacity-50 hover:bg-gray-700 transition-colors"
            >
              {createMutation.isPending ? "저장 중..." : "저장 및 활성화"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {children}
    </div>
  );
}

function ApprovalSelect(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-900"
    >
      <option value="auto">자동 실행</option>
      <option value="require_approval">실행 전 승인 필요</option>
      <option value="draft_only">초안만 생성</option>
      <option value="always_manual">항상 수동</option>
      <option value="disabled">비활성</option>
    </select>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-4 text-sm py-2 border-b border-border">
      <span className="text-gray-400 w-24 shrink-0">{label}</span>
      <span className="text-gray-700">{value || "—"}</span>
    </div>
  );
}
