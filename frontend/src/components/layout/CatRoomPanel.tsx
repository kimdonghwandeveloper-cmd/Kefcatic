import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { assistantsApi } from "@/api/assistants";
import { approvalsApi } from "@/api/approvals";
import { useAssistantStore } from "@/stores/assistantStore";
import { IsometricRoom } from "@/components/cat/IsometricRoom";
import { Button } from "@/components/ui/Button";

const ROLE_LABELS: Record<string, string> = {
  youtube_moderator: "YouTube 관리자",
  gmail_responder: "Gmail 응답 비서",
  drive_organizer: "Drive 정리 비서",
  slack_notifier: "Slack 알리미",
  notion_writer: "Notion 작가",
};

const CAT_STATE_DESC: Record<string, string> = {
  idle: "쉬고 있어요.",
  watching: "주변을 살펴보고 있어요.",
  reading: "내용을 읽고 있어요.",
  sorting: "항목을 분류하고 있어요.",
  drafting: "초안을 작성하고 있어요.",
  waiting_approval: "확인을 기다리고 있어요.",
  executing: "처리하고 있어요.",
  done: "작업을 마쳤어요.",
  error: "도움이 필요해요.",
};

interface ConfigRowProps {
  label: string;
  value: string;
}

function ConfigRow({ label, value }: ConfigRowProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-[#E2E1DE] last:border-0">
      <span className="text-[13px] text-[#6B6966]">{label}</span>
      <span className="text-[13px] font-medium text-[#1A1918]">{value}</span>
    </div>
  );
}

export function CatRoomPanel() {
  const navigate = useNavigate();
  const { selectedId, assistants: storeAssistants } = useAssistantStore();

  const { data: allAssistants = [] } = useQuery({
    queryKey: ["assistants"],
    queryFn: assistantsApi.list,
  });
  const { data: pending = [] } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => approvalsApi.list("pending"),
  });

  const selected = allAssistants.find((a) => a.id === selectedId);
  const storeEntry = storeAssistants.find((a) => a.id === selectedId);
  const catState = storeEntry?.catState ?? "idle";
  const pendingForSelected = pending.filter((p) => p.action?.assistant_name === selected?.name).length;

  if (!selected) {
    return (
      <aside className="w-[300px] shrink-0 border-l border-[#E2E1DE] bg-white flex flex-col items-center justify-center gap-4 p-6">
        <IsometricRoom className="w-full max-w-[240px] opacity-60" />
        <p className="text-[13px] text-[#A8A5A2] text-center">
          왼쪽에서 비서를 선택하면<br />상세 정보를 볼 수 있어요.
        </p>
      </aside>
    );
  }

  return (
    <aside className="w-[300px] shrink-0 border-l border-[#E2E1DE] bg-white flex flex-col overflow-y-auto no-scrollbar">
      {/* Illustration */}
      <div className="bg-[#F5F4F2] p-4 flex items-center justify-center border-b border-[#E2E1DE]">
        <IsometricRoom className="w-full max-w-[260px]" />
      </div>

      {/* Assistant identity */}
      <div className="px-5 pt-4 pb-3 border-b border-[#E2E1DE]">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-heading text-[16px] font-semibold text-[#1A1918]">{selected.name}</h2>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#2D2B29]" />
              <span className="text-[13px] text-[#6B6966]">
                {selected.is_active ? "활성 중" : "비활성"}
              </span>
            </div>
          </div>
          <button
            onClick={() => navigate(`/assistants/${selected.id}`)}
            className="flex h-7 w-7 items-center justify-center rounded-button text-[#A8A5A2] hover:bg-[#EFEFED] hover:text-[#1A1918] transition-colors"
            title="비서 설정"
          >
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-4 w-4">
              <circle cx="8" cy="8" r="2" />
              <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.1 3.1l1.4 1.4M11.5 11.5l1.4 1.4M3.1 12.9l1.4-1.4M11.5 4.5l1.4-1.4" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        {selected.description && (
          <p className="mt-2 text-[13px] text-[#6B6966] leading-relaxed">{selected.description}</p>
        )}
      </div>

      {/* Status */}
      <div className="px-5 py-3 border-b border-[#E2E1DE]">
        <p className="text-[13px] text-[#6B6966] italic">{CAT_STATE_DESC[catState]}</p>
      </div>

      {/* Configuration */}
      <div className="px-5 py-3 border-b border-[#E2E1DE]">
        <p className="text-[11px] font-medium tracking-widest text-[#A8A5A2] uppercase mb-2">구성</p>
        <ConfigRow label="역할" value={ROLE_LABELS[selected.role_type ?? ""] ?? "일반 비서"} />
        <ConfigRow label="상태" value={selected.is_active ? "활성" : "비활성"} />
        {pendingForSelected > 0 && (
          <ConfigRow label="승인 대기" value={`${pendingForSelected}건`} />
        )}
      </div>

      {/* Actions */}
      <div className="px-5 py-4 flex flex-col gap-2 mt-auto">
        <Button
          size="sm"
          className="w-full"
          onClick={() => assistantsApi.trigger(selected.id)}
        >
          지금 실행
        </Button>
        <Button
          variant="secondary"
          size="sm"
          className="w-full"
          onClick={() => navigate(`/assistants/${selected.id}`)}
        >
          상세 설정
        </Button>
        {pendingForSelected > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full"
            onClick={() => navigate("/approvals")}
          >
            승인 요청 확인 →
          </Button>
        )}
      </div>
    </aside>
  );
}
