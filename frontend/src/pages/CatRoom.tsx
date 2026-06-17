import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { assistantsApi } from "@/api/assistants";
import { useAssistantStore } from "@/stores/assistantStore";
import { CatIllustration, CAT_STATE_TEXT, type CatState } from "@/components/cat/CatIllustration";
import { Button } from "@/components/ui/Button";

export default function CatRoom() {
  const navigate = useNavigate();
  const { selectedId, setSelected, assistants: storeAssistants } = useAssistantStore();

  const { data: assistants = [] } = useQuery({
    queryKey: ["assistants"],
    queryFn: assistantsApi.list,
  });

  const getState = (id: string): CatState =>
    storeAssistants.find((a) => a.id === id)?.catState ?? "idle";

  if (assistants.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 text-center">
        <CatIllustration state="idle" size={64} />
        <div className="space-y-1.5">
          <p className="text-[15px] font-medium text-[#1A1918]">아직 비서가 없어요</p>
          <p className="text-[13px] text-[#6B6966]">비서를 만들면 여기서 실시간 상태를 볼 수 있어요.</p>
        </div>
        <Button onClick={() => navigate("/assistants/new")}>첫 번째 비서 만들기</Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="font-heading text-[20px] font-semibold text-[#1A1918]">비서 현황</h1>
      <p className="text-[13px] text-[#6B6966]">
        비서를 선택하면 오른쪽 패널에서 상세 정보를 확인할 수 있어요.
      </p>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {assistants.map((assistant) => {
          const state = getState(assistant.id);
          const isSelected = selectedId === assistant.id;
          return (
            <button
              key={assistant.id}
              onClick={() => setSelected(isSelected ? null : assistant.id)}
              className={`flex flex-col items-center gap-3 rounded-card border bg-white p-5 text-center shadow-card transition-colors ${
                isSelected
                  ? "border-[#2D2B29]"
                  : "border-[#E2E1DE] hover:border-[#A8A5A2]"
              }`}
            >
              <CatIllustration state={state} size={48} />
              <div>
                <p className="text-[13px] font-semibold text-[#1A1918]">{assistant.name}</p>
                <p className="text-[11px] text-[#A8A5A2] mt-0.5">{CAT_STATE_TEXT[state]}</p>
              </div>
              <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${
                assistant.is_active ? "text-[#1A1918]" : "text-[#A8A5A2]"
              }`}>
                <span className={`inline-block h-1.5 w-1.5 rounded-full ${
                  assistant.is_active ? "bg-[#2D2B29]" : "bg-[#E2E1DE]"
                }`} />
                {assistant.is_active ? "활성" : "비활성"}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
