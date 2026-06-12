import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { assistantsApi } from "@/api/assistants";
import { approvalsApi } from "@/api/approvals";
import { CatIllustration, CAT_STATE_TEXT, type CatState } from "@/components/cat/CatIllustration";
import { useAssistantStore } from "@/stores/assistantStore";
import { Button } from "@/components/ui/Button";
import { Divider } from "@/components/ui/Divider";

const ROLE_STATE_TEXT: Record<string, Partial<Record<CatState, string>>> = {
  youtube_moderator: {
    reading: "댓글을 살펴보고 있어요.",
    drafting: "답글 초안을 작성하고 있어요.",
    waiting_approval: "초안을 물어왔어요. 확인해주세요.",
    executing: "답글을 게시하고 있어요.",
  },
  gmail_responder: {
    reading: "메일을 읽고 있어요.",
    drafting: "답장 초안을 쓰고 있어요.",
    waiting_approval: "답장 초안을 물어왔어요.",
  },
};

function getStateText(roleType: string | null, state: CatState): string {
  if (roleType && ROLE_STATE_TEXT[roleType]?.[state]) {
    return ROLE_STATE_TEXT[roleType][state]!;
  }
  return CAT_STATE_TEXT[state];
}

export default function CatRoom() {
  const navigate = useNavigate();
  const { selectedId, setSelected } = useAssistantStore();
  const [localStates] = useState<Record<string, CatState>>({});

  const { data: assistants = [] } = useQuery({
    queryKey: ["assistants"],
    queryFn: assistantsApi.list,
  });
  const { data: pending = [] } = useQuery({
    queryKey: ["approvals", "pending"],
    queryFn: () => approvalsApi.list("pending"),
  });

  const selected = assistants.find((a) => a.id === selectedId);
  const selectedState: CatState = localStates[selectedId ?? ""] ?? "idle";

  const positions = assistants.map((_, i) => ({
    left: `${20 + (i % 4) * 22}%`,
    top: `${30 + Math.floor(i / 4) * 30}%`,
  }));

  const pendingForSelected = pending.filter(
    (p) => p.action?.assistant_name === selected?.name
  ).length;

  return (
    <div className="flex gap-4 h-[calc(100vh-8rem)]">
      {/* Canvas */}
      <div className="flex-1 flex flex-col">
        <h1 className="text-xl font-semibold text-[#0a0a0a] mb-4">Cat Room</h1>
        <div className="flex-1 relative rounded-card border border-[#e8e8e8] bg-white overflow-hidden">
          {/* Room background */}
          <svg
            className="absolute inset-0 w-full h-full opacity-30"
            viewBox="0 0 800 400"
            preserveAspectRatio="xMidYMid slice"
          >
            {/* Desk */}
            <rect x="80" y="280" width="640" height="12" rx="3" fill="#d1d1d1" />
            <rect x="100" y="292" width="16" height="80" rx="2" fill="#d1d1d1" />
            <rect x="684" y="292" width="16" height="80" rx="2" fill="#d1d1d1" />
            {/* Window */}
            <rect x="320" y="40" width="160" height="120" rx="4" fill="none" stroke="#e8e8e8" strokeWidth="2" />
            <line x1="400" y1="40" x2="400" y2="160" stroke="#e8e8e8" strokeWidth="1" />
            <line x1="320" y1="100" x2="480" y2="100" stroke="#e8e8e8" strokeWidth="1" />
          </svg>

          {/* Cats */}
          {assistants.length === 0 ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
              <CatIllustration state="idle" size={64} />
              <p className="text-sm text-[#9a9a9a]">아직 비서가 없어요.</p>
              <Button size="sm" onClick={() => navigate("/assistants/new")}>
                첫 번째 비서 만들기
              </Button>
            </div>
          ) : (
            assistants.map((assistant, i) => {
              const state: CatState = localStates[assistant.id] ?? "idle";
              const isSelected = selectedId === assistant.id;
              return (
                <button
                  key={assistant.id}
                  onClick={() => setSelected(isSelected ? null : assistant.id)}
                  className="absolute flex flex-col items-center gap-1 group"
                  style={positions[i]}
                >
                  <div
                    className={`rounded-full p-1 transition-all ${
                      isSelected ? "bg-[#f5f5f5] ring-2 ring-[#0a0a0a]" : "hover:bg-[#f5f5f5]"
                    }`}
                  >
                    <CatIllustration state={state} size={64} />
                  </div>
                  <span className="text-xs font-medium text-[#0a0a0a]">{assistant.name}</span>
                  <span className="text-[11px] text-[#9a9a9a]">
                    {getStateText(assistant.role_type, state)}
                  </span>
                </button>
              );
            })
          )}
        </div>

        {/* Activity Feed */}
        <div className="mt-3 rounded-card border border-[#e8e8e8] bg-white p-4">
          <h3 className="text-xs font-medium text-[#5c5c5c] mb-2">최근 활동</h3>
          <p className="text-xs text-[#9a9a9a]">비서가 작업을 시작하면 여기에 표시됩니다.</p>
        </div>
      </div>

      {/* Right Panel */}
      {selected && (
        <div className="w-64 shrink-0 rounded-card border border-[#e8e8e8] bg-white p-5 flex flex-col gap-4">
          <div className="flex flex-col items-center gap-2">
            <CatIllustration state={selectedState} size={64} />
            <h2 className="text-sm font-semibold text-[#0a0a0a]">{selected.name}</h2>
            <p className="text-xs text-[#9a9a9a] text-center">{selected.description ?? "역할 설명 없음"}</p>
          </div>

          <Divider />

          <div className="text-xs text-[#5c5c5c]">
            {getStateText(selected.role_type, selectedState)}
          </div>

          {pendingForSelected > 0 && (
            <>
              <Divider />
              <div className="flex items-center justify-between">
                <span className="text-xs text-[#0a0a0a]">
                  승인 대기 {pendingForSelected}개
                </span>
                <button
                  onClick={() => navigate("/approvals")}
                  className="text-xs font-medium text-[#0a0a0a] hover:underline"
                >
                  확인하기 →
                </button>
              </div>
            </>
          )}

          <Divider />

          <div className="flex flex-col gap-2">
            <Button
              size="sm"
              onClick={() => assistantsApi.trigger(selected.id)}
            >
              지금 실행
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate(`/assistants/${selected.id}`)}
            >
              설정
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
