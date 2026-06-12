import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { assistantsApi, type AssistantCreate } from "@/api/assistants";
import { StepIndicator } from "@/components/shared/StepIndicator";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

const STEPS = ["역할 선택", "앱 연결", "권한 설정", "실행 조건", "최종 확인"];

const ROLE_PRESETS = [
  { type: "youtube_moderator", label: "YouTube 댓글 관리", icon: "▶", desc: "댓글 분류 · 답글 초안 · 스팸 관리" },
  { type: "gmail_responder", label: "Gmail 문의 처리", icon: "✉", desc: "메일 분류 · 답장 초안 작성" },
  { type: "custom", label: "직접 설정", icon: "✦", desc: "역할과 앱을 직접 선택합니다" },
];

const APPROVAL_OPTIONS = [
  { value: "auto", label: "자동 실행" },
  { value: "require_approval", label: "승인 필요" },
  { value: "always_manual", label: "항상 수동" },
  { value: "disabled", label: "허용 안 함" },
];

const DEFAULT_ACTIONS: Record<string, { type: string; label: string; desc: string; irreversible?: boolean }[]> = {
  youtube_moderator: [
    { type: "youtube.comment.reply", label: "답글 게시", desc: "YouTube에 답글을 게시합니다." },
    { type: "youtube.comment.hide", label: "댓글 숨김", desc: "댓글을 숨깁니다." },
    { type: "youtube.comment.delete", label: "댓글 삭제", desc: "댓글을 삭제합니다.", irreversible: true },
  ],
  gmail_responder: [
    { type: "gmail.reply.send", label: "답장 발송", desc: "이메일 답장을 발송합니다.", irreversible: true },
    { type: "gmail.label.apply", label: "레이블 변경", desc: "메일에 레이블을 적용합니다." },
  ],
};

interface FormData {
  name: string;
  description: string;
  system_prompt: string;
}

export default function CreateWizard() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [roleType, setRoleType] = useState("");
  const [approvalModes, setApprovalModes] = useState<Record<string, string>>({});

  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormData>();

  const create = useMutation({
    mutationFn: (data: AssistantCreate) => assistantsApi.create(data),
    onSuccess: () => navigate("/assistants"),
  });

  const formData = watch();
  const actions = DEFAULT_ACTIONS[roleType] ?? [];

  const handleNext = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const handleBack = () => setStep((s) => Math.max(s - 1, 0));

  const handleCreate = handleSubmit((data) => {
    create.mutate({
      name: data.name,
      description: data.description,
      role_type: roleType || undefined,
      system_prompt: data.system_prompt || undefined,
    });
  });

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-[#0a0a0a]">새 비서 만들기</h1>

      <StepIndicator steps={STEPS} currentStep={step} />

      {/* Step 0: 역할 선택 */}
      {step === 0 && (
        <Card>
          <h2 className="text-sm font-semibold text-[#0a0a0a] mb-4">어떤 일을 맡길까요?</h2>
          <div className="space-y-2 mb-6">
            {ROLE_PRESETS.map((preset) => (
              <button
                key={preset.type}
                onClick={() => setRoleType(preset.type)}
                className={`w-full flex items-center gap-4 rounded-button border p-4 text-left transition-colors ${
                  roleType === preset.type
                    ? "border-[#0a0a0a] bg-[#f5f5f5]"
                    : "border-[#e8e8e8] hover:border-[#d1d1d1]"
                }`}
              >
                <span className="text-lg w-6 text-center">{preset.icon}</span>
                <div>
                  <p className="text-sm font-medium text-[#0a0a0a]">{preset.label}</p>
                  <p className="text-xs text-[#9a9a9a]">{preset.desc}</p>
                </div>
              </button>
            ))}
          </div>

          <div className="space-y-4">
            <Input label="비서 이름" {...register("name", { required: "이름을 입력해주세요" })} error={errors.name?.message} placeholder="예: 댓글관리냥" />
            <Textarea label="역할 설명 (선택)" {...register("description")} placeholder="이 비서가 하는 일을 간단히 설명해주세요." />
          </div>
        </Card>
      )}

      {/* Step 1: 앱 연결 */}
      {step === 1 && (
        <Card>
          <h2 className="text-sm font-semibold text-[#0a0a0a] mb-4">어떤 앱과 연결할까요?</h2>
          <p className="text-sm text-[#9a9a9a] mb-4">
            앱 연결은 <span className="text-[#0a0a0a] font-medium">앱 연결</span> 화면에서도 설정할 수 있습니다.
          </p>
          <div className="flex items-center justify-center py-8 text-sm text-[#9a9a9a]">
            커넥터 연결은 비서 생성 후 설정 화면에서 진행할 수 있어요.
          </div>
        </Card>
      )}

      {/* Step 2: 권한 설정 */}
      {step === 2 && (
        <Card>
          <h2 className="text-sm font-semibold text-[#0a0a0a] mb-1">어떤 작업을 허용할까요?</h2>
          <p className="text-xs text-[#9a9a9a] mb-5">
            각 작업의 실행 방식을 설정합니다. 되돌리기 불가능한 작업은 기본값이 "승인 필요"입니다.
          </p>
          {actions.length === 0 ? (
            <p className="text-sm text-[#9a9a9a] text-center py-6">역할을 먼저 선택해주세요.</p>
          ) : (
            <div className="divide-y divide-[#e8e8e8]">
              {actions.map((action) => (
                <div key={action.type} className="flex items-center justify-between py-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-[#0a0a0a]">{action.label}</span>
                      {action.irreversible && (
                        <span className="text-[11px] text-[#5c5c5c] border border-[#d1d1d1] px-1.5 rounded-badge">
                          되돌리기 불가
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-[#9a9a9a]">{action.desc}</span>
                  </div>
                  <select
                    className="text-xs border border-[#d1d1d1] rounded-button px-2 py-1 bg-white text-[#0a0a0a] focus:outline-none focus:border-[#0a0a0a]"
                    value={approvalModes[action.type] ?? (action.irreversible ? "require_approval" : "auto")}
                    onChange={(e) =>
                      setApprovalModes((prev) => ({ ...prev, [action.type]: e.target.value }))
                    }
                  >
                    {APPROVAL_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Step 3: 실행 조건 */}
      {step === 3 && (
        <Card>
          <h2 className="text-sm font-semibold text-[#0a0a0a] mb-4">언제 실행할까요?</h2>
          <div className="space-y-3">
            {[
              { label: "매일 오전 9시", value: "0 9 * * *" },
              { label: "매시간", value: "0 * * * *" },
              { label: "수동 실행만", value: "" },
            ].map((opt) => (
              <label key={opt.value} className="flex items-center gap-3 cursor-pointer">
                <input type="radio" name="schedule" value={opt.value} className="accent-[#0a0a0a]" defaultChecked={opt.value === ""} />
                <span className="text-sm text-[#0a0a0a]">{opt.label}</span>
              </label>
            ))}
          </div>
        </Card>
      )}

      {/* Step 4: 최종 확인 */}
      {step === 4 && (
        <Card>
          <h2 className="text-sm font-semibold text-[#0a0a0a] mb-4">설정 요약</h2>
          <div className="divide-y divide-[#e8e8e8]">
            <div className="py-3 flex justify-between">
              <span className="text-xs text-[#9a9a9a]">비서 이름</span>
              <span className="text-sm text-[#0a0a0a]">{formData.name || "미입력"}</span>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-xs text-[#9a9a9a]">역할</span>
              <span className="text-sm text-[#0a0a0a]">
                {ROLE_PRESETS.find((r) => r.type === roleType)?.label ?? "미선택"}
              </span>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-xs text-[#9a9a9a]">설정된 권한</span>
              <span className="text-sm text-[#0a0a0a]">{actions.length}개</span>
            </div>
          </div>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-2">
        <Button variant="secondary" onClick={handleBack} disabled={step === 0}>
          이전
        </Button>
        {step < STEPS.length - 1 ? (
          <Button onClick={handleNext} disabled={step === 0 && !formData.name}>
            다음
          </Button>
        ) : (
          <Button onClick={handleCreate} loading={create.isPending}>
            비서 생성하기
          </Button>
        )}
      </div>
    </div>
  );
}
