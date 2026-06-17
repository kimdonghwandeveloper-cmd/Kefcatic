import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assistantsApi, type Assistant } from "@/api/assistants";
import { useAssistantStore } from "@/stores/assistantStore";
import { Button } from "@/components/ui/Button";

const CONNECTOR_ICONS: Record<string, string> = {
  youtube: "▶",
  gmail: "✉",
  google_drive: "△",
  slack: "◆",
  notion: "◻",
};

function AssistantCard({ assistant }: { assistant: Assistant }) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { selectedId, setSelected } = useAssistantStore();
  const isSelected = selectedId === assistant.id;

  const toggle = useMutation({
    mutationFn: () =>
      assistantsApi.patch(assistant.id, { is_active: !assistant.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assistants"] }),
  });

  const trigger = useMutation({
    mutationFn: () => assistantsApi.trigger(assistant.id),
  });

  return (
    <div
      className={`rounded-card border bg-white shadow-card p-5 flex flex-col gap-4 transition-colors cursor-pointer ${
        isSelected ? "border-[#2D2B29]" : "border-[#E2E1DE] hover:border-[#A8A5A2]"
      }`}
      onClick={() => setSelected(isSelected ? null : assistant.id)}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-card bg-[#F5F4F2] text-[15px] font-semibold text-[#1A1918]">
            {assistant.name.charAt(0)}
          </div>
          <div>
            <h3 className="text-[15px] font-semibold text-[#1A1918]">{assistant.name}</h3>
            <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${
              assistant.is_active ? "text-[#1A1918]" : "text-[#A8A5A2]"
            }`}>
              <span className={`inline-block h-1.5 w-1.5 rounded-full ${
                assistant.is_active ? "bg-[#2D2B29]" : "bg-[#E2E1DE]"
              }`} />
              {assistant.is_active ? "활성" : "비활성"}
            </span>
          </div>
        </div>
      </div>

      <p className="text-[13px] text-[#6B6966] line-clamp-2 leading-relaxed">
        {assistant.description ?? "역할 설명이 없습니다."}
      </p>

      {assistant.role_type && (
        <div className="flex gap-1.5 flex-wrap">
          {Object.entries(CONNECTOR_ICONS)
            .slice(0, 3)
            .map(([type, icon]) => (
              <span
                key={type}
                className="flex h-6 w-6 items-center justify-center rounded-badge border border-[#E2E1DE] text-[11px] text-[#6B6966]"
                title={type}
              >
                {icon}
              </span>
            ))}
        </div>
      )}

      <div className="flex gap-2 pt-1 border-t border-[#E2E1DE]" onClick={(e) => e.stopPropagation()}>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => navigate(`/assistants/${assistant.id}`)}
        >
          열기
        </Button>
        <Button
          size="sm"
          variant="ghost"
          loading={trigger.isPending}
          onClick={() => trigger.mutate()}
        >
          실행
        </Button>
        <Button
          size="sm"
          variant="ghost"
          loading={toggle.isPending}
          onClick={() => toggle.mutate()}
        >
          {assistant.is_active ? "일시정지" : "활성화"}
        </Button>
      </div>
    </div>
  );
}

export default function Assistants() {
  const navigate = useNavigate();
  const { data: assistants = [], isLoading } = useQuery({
    queryKey: ["assistants"],
    queryFn: assistantsApi.list,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-[20px] font-semibold text-[#1A1918]">비서 목록</h1>
        <Button onClick={() => navigate("/assistants/new")}>새 비서 만들기</Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-48 rounded-card border border-[#E2E1DE] bg-white skeleton" />
          ))}
        </div>
      ) : assistants.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-card bg-[#EFEFED] text-3xl">
            🐱
          </div>
          <div className="space-y-1.5">
            <p className="text-[15px] font-medium text-[#1A1918]">아직 비서가 없어요</p>
            <p className="text-[13px] text-[#6B6966]">첫 번째 비서를 만들어 반복 작업을 맡겨보세요.</p>
          </div>
          <Button onClick={() => navigate("/assistants/new")}>새 비서 만들기</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {assistants.map((a) => (
            <AssistantCard key={a.id} assistant={a} />
          ))}
        </div>
      )}
    </div>
  );
}
