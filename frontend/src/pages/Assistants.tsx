import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assistantsApi, type Assistant } from "@/api/assistants";
import { CatIllustration } from "@/components/cat/CatIllustration";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";

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

  const toggle = useMutation({
    mutationFn: () =>
      assistantsApi.patch(assistant.id, { is_active: !assistant.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["assistants"] }),
  });

  const trigger = useMutation({
    mutationFn: () => assistantsApi.trigger(assistant.id),
  });

  return (
    <div className="rounded-card border border-[#e8e8e8] bg-white p-5 flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <CatIllustration state="idle" size={32} />
          <div>
            <h3 className="text-sm font-semibold text-[#0a0a0a]">{assistant.name}</h3>
            <StatusBadge status={assistant.is_active ? "active" : "idle"} className="mt-0.5" />
          </div>
        </div>
      </div>

      <p className="text-sm text-[#5c5c5c] line-clamp-2">
        {assistant.description ?? "역할 설명이 없습니다."}
      </p>

      {assistant.role_type && (
        <div className="flex gap-1.5">
          {Object.entries(CONNECTOR_ICONS)
            .slice(0, 2)
            .map(([type, icon]) => (
              <span
                key={type}
                className="flex h-6 w-6 items-center justify-center rounded-badge border border-[#e8e8e8] text-xs text-[#5c5c5c]"
                title={type}
              >
                {icon}
              </span>
            ))}
        </div>
      )}

      <div className="flex gap-2 pt-1 border-t border-[#e8e8e8]">
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
        <h1 className="text-xl font-semibold text-[#0a0a0a]">내 비서</h1>
        <Button onClick={() => navigate("/assistants/new")}>새 비서 만들기</Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-48 rounded-card border border-[#e8e8e8] bg-white animate-pulse" />
          ))}
        </div>
      ) : assistants.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-20">
          <CatIllustration state="idle" size={64} />
          <p className="text-sm text-[#9a9a9a]">아직 비서가 없어요. 첫 번째 비서를 만들어보세요.</p>
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
